#!/usr/bin/env python3
"""Build the bundled Pyrfume extract used by the OLFACTRA engine and web page.

    python tools/build_pyrfume_bundle.py --cache ../../tmp-pyrfume

Source: **Pyrfume Data** (https://github.com/pyrfume/pyrfume-data, MIT licence,
Hamel et al. 2024, *Scientific Data*, doi:10.1038/s41597-024-04051-z).

Three public academic odour datasets are reduced to the subset that matches the
43 fragrance molecules of this library by PubChem CID:

* ``keller_2016``    — Keller & Vosshall 2016, *BMC Neuroscience* 17:55,
  doi:10.1186/s12868-016-0287-2 — pleasantness / intensity / familiarity (0–100)
  and 20 semantic descriptor ratings, averaged over subjects and concentrations.
* ``dravnieks_1985`` — Dravnieks 1985, *Atlas of Odor Character Profiles* (ASTM
  DS61), doi:10.1520/DS61-EB — 146 descriptor profiles; the strongest descriptors
  per material are kept.
* ``mainland_2015``  — Mainland et al. 2015, *Scientific Data* 2:150002,
  doi:10.1038/sdata.2015.2 — human olfactory-receptor responses (which ORs a
  molecule activated in the luciferase screen and/or passed dose–response).

The output JSON is committed so the engine, the tests and the web page work
offline and reproduce byte-for-byte.  Every file used is recorded with its
SHA-256 so a reader can prove which snapshot the numbers came from.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import sys
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from olfactra_core import molecule as mol_lib  # noqa: E402

RAW = "https://raw.githubusercontent.com/pyrfume/pyrfume-data/main"
OUT = ROOT / "olfactra_core" / "datasets" / "pyrfume_olfactra.json"

FILES = {
    "keller_2016": ["manifest.toml", "molecules.csv", "stimuli.csv", "behavior.csv"],
    "dravnieks_1985": ["manifest.toml", "molecules.csv", "stimuli.csv",
                       "behavior_1.csv", "behavior_2.csv"],
    "mainland_2015": ["manifest.toml", "molecules.csv", "stimuli.csv",
                      "subjects.csv", "behavior_2.csv"],
}

SOURCE_META = {
    "keller_2016": {
        "label": "Keller & Vosshall 2016",
        "title": "Olfactory perception of chemically diverse molecules",
        "journal": "BMC Neuroscience 17:55",
        "doi": "10.1186/s12868-016-0287-2",
        "measured": "쾌적도·강도·친숙도(0–100), 20개 감각 기술어",
    },
    "dravnieks_1985": {
        "label": "Dravnieks 1985",
        "title": "Atlas of Odor Character Profiles",
        "journal": "ASTM DS61",
        "doi": "10.1520/DS61-EB",
        "measured": "146개 향 기술어 프로파일",
    },
    "mainland_2015": {
        "label": "Mainland et al. 2015",
        "title": "Human olfactory receptor responses to odorants",
        "journal": "Scientific Data 2:150002",
        "doi": "10.1038/sdata.2015.2",
        "measured": "인간 후각수용체(OR) 반응 스크리닝",
    },
}

KELLER_DESCRIPTORS = (
    "EDIBLE", "BAKERY", "SWEET", "FRUIT", "FISH", "GARLIC", "SPICES", "COLD",
    "SOUR", "BURNT", "ACID", "WARM", "MUSKY", "SWEATY", "AMMONIA/URINOUS",
    "DECAYED", "WOOD", "GRASS", "FLOWER", "CHEMICAL",
)
KELLER_HEDONIC = {
    "HOW PLEASANT IS THE SMELL?": "pleasantness",
    "HOW STRONG IS THE SMELL?": "intensity",
    "HOW FAMILIAR IS THE SMELL?": "familiarity",
}
#: English descriptor -> Korean gloss (only the ones shown in the UI)
TERM_KO = {
    "FLORAL": "플로럴", "ROSE": "장미", "VIOLETS": "제비꽃", "LAVENDER": "라벤더",
    "CITRUS": "시트러스", "FRUITY, CITRUS": "프루티·시트러스", "LEMON": "레몬",
    "ORANGE": "오렌지", "PINEAPPLE": "파인애플", "FRUITY, OTHER THAN CITRUS": "프루티(시트러스 외)",
    "SWEET": "단맛", "VANILLA": "바닐라", "CHOCOLATE": "초콜릿", "HONEY": "꿀",
    "WOODY, RESINOUS": "우디·레지너스", "CEDARWOOD": "시더우드", "OAK WOOD, COGNAC": "오크·코냑",
    "MUSKY": "머스크", "MINTY, PEPPERMINT": "민트", "CAMPHOR": "캠퍼", "EUCALYPTUS": "유칼립투스",
    "SPICY": "스파이시", "CLOVE": "정향", "CINNAMON": "시나몬", "GREEN, CRUSHED GRASS": "그린·풀잎",
    "GRASS": "풀", "HERBAL, GREEN": "허브·그린", "POWDERY": "파우더리", "SOAPY": "비누",
    "CHEMICAL": "화학적", "MEDICINAL": "약품", "BALSAMIC": "발사믹", "BURNT": "탄 냄새",
    "SMOKY": "스모키", "EARTHY, MOLDY": "어시·곰팡이", "MOLDY, MUSTY": "곰팡이·퀴퀴함",
    "FATTY": "지방", "WAXY": "왁스", "COOKED VEGETABLES": "익힌 채소",
    "RAW VEGETABLES": "생 채소", "PICKLE, SAUERKRAUT": "절임", "FISH": "생선", "SOUR": "신맛",
    "SHARP, PUNGENT, ACID": "날카로움·산미", "COLD": "차가움", "WARM": "따뜻함",
    "SWEATY": "땀", "AMMONIA/URINOUS": "암모니아·요", "DECAYED": "부패", "GARLIC": "마늘",
    "ONION": "양파", "ANISE, LICORICE": "아니스·감초", "COLOGNE": "코롱", "PERFUMERY": "향수",
    "FRAGRANT": "향기", "AROMATIC": "아로마", "ALMOND": "아몬드", "NUTTY, WALNUT ETC.": "견과",
    "NAIL POLISH REMOVER": "아세톤", "MOTHBALLS": "좀약", "TEALEAVES": "찻잎",
    "SPICES": "향신료", "EDIBLE": "식용", "BAKERY": "빵", "ACID": "산",
    "MAPLE SYRUP": "메이플시럽", "CARAMEL": "카라멜", "MALTY": "맥아", "RAISINS": "건포도",
    "MOLASSES": "당밀", "COCONUT": "코코넛", "SEASONING FOR MEAT": "고기 양념",
    "BLACK PEPPER": "흑후추", "GREEN PEPPER": "풋고추", "DILL": "딜", "CARAWAY": "캐러웨이",
    "TEA LEAVES": "찻잎", "LAUREL LEAVES": "월계수 잎", "GRAPE JUICE": "포도주스",
    "STRAWBERRY": "딸기", "APPLE, FRUIT": "사과", "PEAR": "배",
    "CANTALOUPE, HONEYDEW MELON": "멜론", "PEACH FRUIT": "복숭아", "BANANA": "바나나",
    "CHERRY, BERRY": "체리·베리", "PINEAPPLE ": "파인애플",
    "LIGHT": "가벼움", "HEAVY": "무거움", "SHARP": "날카로움", "FRESH": "상쾌함",
    "DRY": "건조함", "OILY": "기름", "BUTTERY": "버터", "CREAMY": "크림",
    "ETHEREAL": "에테르", "FRUITY": "프루티", "GREEN": "그린", "HERBAL": "허브",
    "LEAFY": "잎", "PINE": "소나무", "RESINOUS": "수지", "BALSAMIC ": "발사믹",
    "MUSTY": "퀴퀴함", "STALE": "지린", "SICKENING": "역겨움", "IRRITATING": "자극",
    "METALLIC": "금속", "RUBBER": "고무", "TAR": "타르", "TOBACCO": "담배",
    "LEATHER": "가죽", "ANIMAL": "동물", "SOAPY ": "비누", "CLEAN": "깨끗함",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(name: str, fname: str, cache: Path) -> Path:
    path = cache / name / fname
    if path.exists() and path.stat().st_size:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{RAW}/{name}/{fname}"
    print(f"  ↓ {url}")
    with urllib.request.urlopen(url, timeout=120) as resp, path.open("wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    return path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- datasets
def build_keller(cache: Path, cids: dict[str, str]) -> dict[str, dict]:
    stimuli = read_csv(cache / "keller_2016" / "stimuli.csv")
    cid_of = {r["Stimulus"]: (r["CIDs"] or "").strip() for r in stimuli}
    conc_of = {r["Stimulus"]: (r["Concentration"] or "").strip() for r in stimuli}

    values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    subjects: dict[str, set] = defaultdict(set)
    with (cache / "keller_2016" / "behavior.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sid = row["Stimulus"]
            if sid not in cid_of:
                continue
            try:
                val = float(row["Value"])
            except (TypeError, ValueError):
                continue
            values[sid][row["MeasurementValue"]].append(val)
            subjects[sid].add(row["Subject"])

    per_cid: dict[str, list[dict]] = defaultdict(list)
    for sid, meas in values.items():
        cid = cid_of[sid]
        if cid not in cids:
            continue
        rec = {"stimulus": int(sid), "concentration": conc_of[sid],
               "n_raters": len(subjects[sid])}
        for key, name in KELLER_HEDONIC.items():
            if meas.get(key):
                rec[name] = round(statistics.mean(meas[key]), 1)
        desc = {}
        for key in KELLER_DESCRIPTORS:
            if meas.get(key):
                v = round(statistics.mean(meas[key]), 1)
                if v > 0:
                    desc[key] = v
        rec["descriptors"] = desc
        per_cid[cid].append(rec)

    out: dict[str, dict] = {}
    for cid, recs in per_cid.items():
        mid = cids[cid]
        merged: dict[str, float] = {}
        for name in KELLER_HEDONIC.values():
            vals = [r[name] for r in recs if name in r]
            if vals:
                merged[name] = round(statistics.mean(vals), 1)
        desc: dict[str, list[float]] = defaultdict(list)
        for r in recs:
            for k, v in r["descriptors"].items():
                desc[k].append(v)
        top = sorted(((k, round(statistics.mean(v), 1)) for k, v in desc.items()),
                     key=lambda kv: kv[1], reverse=True)
        out[mid] = {
            "cid": int(cid),
            "stimuli": recs,
            "n_stimuli": len(recs),
            "n_raters": max(r["n_raters"] for r in recs),
            **merged,
            "descriptors": dict(top),
            "top_descriptors": [{"term": k, "score": v} for k, v in top[:6]],
        }
    return out


def build_dravnieks(cache: Path, cids: dict[str, str]) -> dict[str, dict]:
    stimuli = read_csv(cache / "dravnieks_1985" / "stimuli.csv")
    stim_of = {r["Stimulus"]: r for r in stimuli}

    use_rows = read_csv(cache / "dravnieks_1985" / "behavior_2.csv")
    app_rows = read_csv(cache / "dravnieks_1985" / "behavior_1.csv")
    if not use_rows:
        return {}
    terms = [k for k in use_rows[0].keys() if k != "Stimulus"]
    use = {r["Stimulus"]: r for r in use_rows}
    app = {r["Stimulus"]: r for r in app_rows}

    per_cid: dict[str, list[dict]] = defaultdict(list)
    for sid, row in use.items():
        meta = stim_of.get(sid)
        if not meta:
            continue
        cid = (meta.get("CID") or "").strip()
        if cid not in cids:
            continue
        scores = []
        for t in terms:
            try:
                v = float(row.get(t) or 0)
            except ValueError:
                v = 0.0
            if v <= 0:
                continue
            try:
                a = float((app.get(sid) or {}).get(t) or 0)
            except ValueError:
                a = 0.0
            scores.append((t, round(v, 1), round(a, 1)))
        scores.sort(key=lambda x: x[1], reverse=True)
        per_cid[cid].append({
            "stimulus": sid,
            "concentration": meta.get("Conc", ""),
            "top": [{"term": t, "use": u, "applicability": a} for t, u, a in scores[:8]],
        })

    out = {}
    for cid, recs in per_cid.items():
        agg: dict[str, list[float]] = defaultdict(list)
        for r in recs:
            for item in r["top"]:
                agg[item["term"]].append(item["use"])
        top = sorted(((k, round(statistics.mean(v), 1)) for k, v in agg.items()),
                     key=lambda kv: kv[1], reverse=True)[:8]
        out[cids[cid]] = {
            "cid": int(cid),
            "n_stimuli": len(recs),
            "n_descriptors": len(terms),
            "stimuli": recs,
            "top": [{"term": k, "use": v, "term_ko": TERM_KO.get(k, "")} for k, v in top],
        }
    return out


def build_mainland(cache: Path, cids: dict[str, str]) -> dict[str, dict]:
    stimuli = read_csv(cache / "mainland_2015" / "stimuli.csv")
    stim_of = {r["Stimulus"]: r for r in stimuli}
    subjects = read_csv(cache / "mainland_2015" / "subjects.csv")
    gene_of = {r["Subject"]: (r["Gene"] or "").strip() for r in subjects}

    tested: dict[str, set] = defaultdict(set)
    hits: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(dict))
    for row in read_csv(cache / "mainland_2015" / "behavior_2.csv"):
        sid = row["Stimulus"]
        if sid not in stim_of:
            continue
        cid = (stim_of[sid].get("CID") or "").strip()
        if cid not in cids:
            continue
        subject = row["Subject"]
        tested[cid].add(subject)
        gene = gene_of.get(subject, "")
        if not gene or gene.lower() == "pseudo":
            continue
        base = gene.split()[0]
        variant = gene[len(base):].strip()
        try:
            secondary = int(float(row.get("PassedSecondary") or 0))
        except ValueError:
            secondary = 0
        try:
            dose = int(float(row.get("PassedDR") or 0))
        except ValueError:
            dose = 0
        if not (secondary or dose):
            continue
        rec = hits[cid].setdefault(base, {"gene": base, "variants": [], "secondary": False,
                                          "dose_response": False, "ec50_log": None})
        rec["secondary"] = rec["secondary"] or bool(secondary)
        rec["dose_response"] = rec["dose_response"] or bool(dose)
        if variant and variant not in rec["variants"]:
            rec["variants"].append(variant)
        if row.get("EC50"):
            try:
                ec = float(row["EC50"])
            except ValueError:
                ec = None
            if ec is not None and rec["ec50_log"] is None:
                rec["ec50_log"] = round(ec, 2)

    out = {}
    for cid, by_gene in hits.items():
        recs = sorted(by_gene.values(),
                      key=lambda r: (not r["dose_response"], not r["secondary"], r["gene"]))
        out[cids[cid]] = {
            "cid": int(cid),
            "n_receptors_tested": len(tested[cid]),
            "receptors": recs,
            "n_active": len(recs),
        }
    return out


# --------------------------------------------------------------------------- main
def build(cache: Path) -> dict:
    cids = {str(m.pubchem_cid): m.id for m in mol_lib.MOLECULES}

    files_meta: dict[str, list[dict]] = {}
    for name, names in FILES.items():
        files_meta[name] = []
        for fname in names:
            path = fetch(name, fname, cache)
            files_meta[name].append({
                "name": fname,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })

    keller = build_keller(cache, cids)
    drav = build_dravnieks(cache, cids)
    main = build_mainland(cache, cids)

    molecules = sorted({*keller, *drav, *main}, key=lambda mid: [
        m.id for m in mol_lib.MOLECULES].index(mid))
    entries = {}
    for mid in molecules:
        item: dict = {}
        if mid in keller:
            item["keller_2016"] = keller[mid]
        if mid in drav:
            item["dravnieks_1985"] = drav[mid]
        if mid in main:
            item["mainland_2015"] = main[mid]
        entries[mid] = item

    library = [m.id for m in mol_lib.MOLECULES]
    return {
        "generated": date.today().isoformat(),
        "license": {
            "dataset": "Pyrfume Data — MIT License",
            "repository": "https://github.com/pyrfume/pyrfume-data",
            "citation": "Hamel et al. (2024) Pyrfume: A window to collective intel of smell. "
                        "Scientific Data, doi:10.1038/s41597-024-04051-z",
        },
        "sources": {
            key: {**SOURCE_META[key],
                  "url": f"https://github.com/pyrfume/pyrfume-data/tree/main/{key}",
                  "files": files_meta[key]}
            for key in SOURCE_META
        },
        "coverage": {
            "library": len(library),
            "keller_2016": len(keller),
            "dravnieks_1985": len(drav),
            "mainland_2015": len(main),
            "any": len(molecules),
            "unmeasured": [mid for mid in library if mid not in entries],
        },
        "molecules": entries,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", default=str(ROOT / "tools" / ".pyrfume_cache"),
                    help="folder holding the raw Pyrfume CSV files (downloaded if missing)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    data = build(Path(args.cache))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    cov = data["coverage"]
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    print(f"  matched {cov['any']}/{cov['library']} molecules — "
          f"Keller {cov['keller_2016']}, Dravnieks {cov['dravnieks_1985']}, "
          f"Mainland {cov['mainland_2015']}")
    print(f"  no measured data: {', '.join(cov['unmeasured'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
