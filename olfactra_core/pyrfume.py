"""OLFACTRA PYR — the public academic odour datasets, bundled and matched.

The numbers come from **Pyrfume Data** (MIT, https://github.com/pyrfume/pyrfume-data,
Hamel et al. 2024, Scientific Data, doi:10.1038/s41597-024-04051-z), reduced to
the molecules of this library by PubChem CID with
``tools/build_pyrfume_bundle.py`` and committed as
``olfactra_core/datasets/pyrfume_olfactra.json``.

Three sources are used:

* Keller & Vosshall 2016 (BMC Neuroscience, doi:10.1186/s12868-016-0287-2) —
  how pleasant, how strong and how familiar 480 molecules smelled to ~50 raters,
  plus 20 semantic descriptor ratings.
* Dravnieks 1985 (Atlas of Odor Character Profiles, ASTM DS61,
  doi:10.1520/DS61-EB) — 146-descriptor profiles per material.
* Mainland et al. 2015 (Scientific Data, doi:10.1038/sdata.2015.2) — which human
  olfactory receptors a molecule activated in a cell-based screen.

How it is allowed to be used
----------------------------
The measurements are **single-molecule** values. A blend is not the sum of its
parts: mixtures can smell pleasant while every component is rated unpleasant, or
the reverse, through masking, synergy and adaptation. So these numbers are used
as a *documented prior* — a small term in the ranking, and a reason shown to the
reader — never as a prediction of the finished accord. Molecules with no measured
value are marked as having none; we do not fill the gap with an estimate.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

BUNDLE = Path(__file__).resolve().parent / "datasets" / "pyrfume_olfactra.json"

#: weight (in FIT points) of the hedonic prior inside the ID score
HEDONIC_WEIGHT = 1.2
#: minimum share of the accord (0–1) that must carry measured pleasantness
MIN_COVERAGE = 0.15


@lru_cache(maxsize=1)
def bundle() -> dict[str, Any]:
    if not BUNDLE.exists():  # pragma: no cover - the file ships with the package
        return {"sources": {}, "coverage": {}, "molecules": {}}
    return json.loads(BUNDLE.read_text(encoding="utf-8"))


def sources() -> dict[str, Any]:
    return bundle().get("sources", {})


def coverage() -> dict[str, Any]:
    return bundle().get("coverage", {})


def profile(molecule_id: str) -> dict[str, Any] | None:
    """Measured data for one library molecule, or None when nothing matched."""
    return bundle().get("molecules", {}).get(molecule_id)


def keller(molecule_id: str) -> dict[str, Any] | None:
    p = profile(molecule_id)
    return (p or {}).get("keller_2016")


def dravnieks(molecule_id: str) -> dict[str, Any] | None:
    p = profile(molecule_id)
    return (p or {}).get("dravnieks_1985")


def mainland(molecule_id: str) -> dict[str, Any] | None:
    p = profile(molecule_id)
    return (p or {}).get("mainland_2015")


def receptors_reported(molecule_id: str) -> list[dict[str, Any]]:
    """Human ORs this molecule activated in Mainland et al. (2015)."""
    m = mainland(molecule_id)
    return list((m or {}).get("receptors", []))


def receptor_evidence(molecule_id: str, gene: str) -> dict[str, Any] | None:
    """Did the public screen see this molecule activate this receptor?"""
    for rec in receptors_reported(molecule_id):
        if rec["gene"] == gene:
            return rec
    return None


def title_of(kind: str) -> str:
    return {"keller_2016": "Keller & Vosshall 2016",
            "dravnieks_1985": "Dravnieks 1985",
            "mainland_2015": "Mainland et al. 2015"}.get(kind, kind)


def prior(materials: Mapping[str, float]) -> dict[str, Any] | None:
    """Weighted pleasantness prior for an accord (single-molecule measurements)."""
    total = sum(v for v in materials.values() if v > 0) or 1.0
    measured: list[dict[str, Any]] = []
    weighted, weight = 0.0, 0.0
    for mid, share in materials.items():
        if share <= 0:
            continue
        k = keller(mid)
        if not k or "pleasantness" not in k:
            continue
        measured.append({
            "id": mid,
            "share": round(100.0 * share / total, 1),
            "pleasantness": k["pleasantness"],
            "intensity": k.get("intensity"),
            "familiarity": k.get("familiarity"),
        })
        weighted += k["pleasantness"] * share
        weight += share
    if not weight:
        return None
    covered = weight / total
    if covered < MIN_COVERAGE:
        return None
    mean = weighted / weight
    # 30–90 on the rating scale is the range that actually occurs; map to 0–1
    value = max(0.0, min(1.0, (mean - 30.0) / 60.0))
    return {
        "value": round(value, 3),
        "mean": round(mean, 1),
        "coverage": round(covered, 3),
        "measured": measured,
    }


def material_evidence(molecule_id: str, name_ko: str) -> dict[str, Any]:
    """Everything measured for one molecule, shaped for the web page."""
    k = keller(molecule_id)
    d = dravnieks(molecule_id)
    m = mainland(molecule_id)
    out: dict[str, Any] = {"id": molecule_id, "name_ko": name_ko, "measured": bool(k or d or m)}
    if k:
        out["pleasantness"] = k.get("pleasantness")
        out["intensity"] = k.get("intensity")
        out["familiarity"] = k.get("familiarity")
        out["raters"] = k.get("n_raters")
        out["top_descriptors"] = k.get("top_descriptors", [])
    if d:
        out["dravnieks"] = d.get("top", [])
    if m:
        out["receptors"] = m.get("receptors", [])
        out["receptors_tested"] = m.get("n_receptors_tested")
    return out


def accord_evidence(materials: Mapping[str, float], names: Mapping[str, str]) -> dict[str, Any]:
    """Evidence block attached to every ID suggestion."""
    total = sum(v for v in materials.values() if v > 0) or 1.0
    rows = []
    covered = {"keller_2016": 0.0, "dravnieks_1985": 0.0, "mainland_2015": 0.0}
    for mid, share in materials.items():
        if share <= 0:
            continue
        ev = material_evidence(mid, names.get(mid, mid))
        ev["share"] = round(100.0 * share / total, 1)
        if ev.get("pleasantness") is not None:
            covered["keller_2016"] += share / total
        if ev.get("dravnieks"):
            covered["dravnieks_1985"] += share / total
        if ev.get("receptors"):
            covered["mainland_2015"] += share / total
        rows.append(ev)
    rows.sort(key=lambda r: r["share"], reverse=True)
    return {
        "materials": rows,
        "coverage": {k: round(v, 3) for k, v in covered.items()},
        "prior": prior(materials),
        "sources": [
            {**{"key": key}, **sources().get(key, {})} for key in
            ("keller_2016", "dravnieks_1985", "mainland_2015")
        ],
        "note": (
            "Pyrfume에 실린 공개 학술 데이터를 PubChem CID로 매칭한 단품 측정값입니다. "
            "혼합물의 향은 구성 성분의 합이 아니므로(마스킹·상승·적응) 이 값은 완성 아코드의 "
            "쾌적도를 예측하지 않습니다. 측정값이 없는 분자는 '미측정'으로 표시합니다."
        ),
    }


def stats() -> dict[str, Any]:
    cov = coverage()
    return {
        "matched": cov.get("any", 0),
        "library": cov.get("library", 0),
        **{k: cov.get(k, 0) for k in ("keller_2016", "dravnieks_1985", "mainland_2015")},
    }
