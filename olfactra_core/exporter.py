"""OLFACTRA exporters — recipe output as CSV, JSON, Excel or Markdown.

Excel output is the one researchers actually send around, so it is written as a
small workbook with separate sheets: the formula itself, the safety check, the
note pyramid, a provenance sheet that states the licence and the limits of what
the numbers mean, and (0.2.0) a ``Methodology`` sheet that carries the indicator
registry from :mod:`olfactra_core.provenance`.

JSON output is a versioned bundle: ``schema_version`` names the document shape
(currently ``"0.2.0"``) so a downstream script can tell which layout it is
reading, and the methodology travels with the numbers instead of being left in a
PDF nobody opens.

The Markdown report (``formula_to_markdown`` / ``export_markdown``) is the
human-readable counterpart: the weighing table, the safety verdict, the property
profile and the provenance appendix in one file that renders on GitHub, in Notion
or in a lab notebook.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping

from . import __version__, atlas as atlas_lib, molecule as mol_lib, provenance, studio

#: document shape of the JSON bundle — bumped whenever a key changes meaning
SCHEMA_VERSION = "0.2.0"

RECIPE_COLUMNS = (
    "no", "material", "material_ko", "cas", "formula", "note", "share_of_concentrate_pct",
    "volume_ml", "mass_g", "finished_pct_ww", "cap_pct", "cap_ratio", "status",
    "allergen_label", "state",
)

PROVENANCE = {
    "project": "OLFACTRA",
    "schema_version": SCHEMA_VERSION,
    "version": __version__,
    "license": "MIT",
    "copyright": "Copyright (c) 2026 FEI · HEL Lab, Gyeongsang National University",
    "generated": date.today().isoformat(),
    "science_boundary": (
        "OLFACTRA proposes candidate formulas from public molecule and odour data. "
        "It does not predict how a blend will smell, and it does not replace GC-MS "
        "analysis, sensory evaluation, or a cosmetics safety assessment."
    ),
    "safety_boundary": (
        "Working ceilings are conservative internal limits assembled from public "
        "cosmetic/fragrance guidance. They are not IFRA certificates and not a "
        "regulatory opinion. Verify before any sale or distribution."
    ),
}


def recipe_rows(formula: studio.Formula) -> list[dict]:
    rows = []
    for i, row in enumerate(formula.rows, start=1):
        m = mol_lib.get(row.id)
        rows.append({
            "no": i,
            "material": row.name,
            "material_ko": row.name_ko,
            "cas": m.cas or "",
            "formula": m.formula,
            "note": mol_lib.NOTE_LABELS_KO[row.note],
            "share_of_concentrate_pct": round(row.share_pct, 2),
            "volume_ml": round(row.volume_ml, 3),
            "mass_g": round(row.mass_g, 3),
            "finished_pct_ww": round(row.finished_pct_ww, 4),
            "cap_pct": row.cap_pct,
            "cap_ratio": round(row.cap_ratio, 3),
            "status": row.status,
            "allergen_label": "Y" if row.allergen else "",
            "state": m.state,
        })
    return rows


def formula_to_dict(formula: studio.Formula, include_methodology: bool = True) -> dict:
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "meta": PROVENANCE,
        "formula": {
            "product_type": formula.product_type.id,
            "product_type_ko": formula.product_type.name_ko,
            "volume_ml": formula.volume_ml,
            "load_pct": formula.load_pct,
            "total_mass_g": round(formula.total_mass_g, 3),
            "fragrance_mass_g": round(formula.fragrance_mass_g, 3),
            "fragrance_volume_ml": round(formula.fragrance_volume_ml, 3),
            "finished_load_pct_ww": round(formula.finished_load_pct_ww, 3),
            "status": formula.status,
        },
        "materials": [r.as_dict() for r in formula.rows],
        "carriers": formula.carrier_rows,
        "note_balance": {k: round(v, 3) for k, v in formula.note_balance.items()},
        "allergens": formula.allergens,
        "warnings": formula.warnings,
    }
    if include_methodology:
        bundle["methodology"] = provenance.as_dict()
    return bundle


def formula_to_json(formula: studio.Formula, indent: int = 2,
                    include_methodology: bool = True) -> str:
    return json.dumps(
        formula_to_dict(formula, include_methodology=include_methodology),
        ensure_ascii=False, indent=indent,
    )


def formula_to_csv(formula: studio.Formula) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(RECIPE_COLUMNS), lineterminator="\n")
    writer.writeheader()
    for row in recipe_rows(formula):
        writer.writerow(row)
    buf.write("\n")
    meta = csv.writer(buf, lineterminator="\n")
    meta.writerow(["# product_type", formula.product_type.name_ko, formula.product_type.id])
    meta.writerow(["# volume_ml", formula.volume_ml])
    meta.writerow(["# load_pct", formula.load_pct])
    meta.writerow(["# finished_load_pct_ww", round(formula.finished_load_pct_ww, 3)])
    meta.writerow(["# total_mass_g", round(formula.total_mass_g, 3)])
    meta.writerow(["# status", formula.status])
    meta.writerow(["# license", PROVENANCE["license"], PROVENANCE["copyright"]])
    meta.writerow(["# warning", " ".join(formula.warnings)])
    return buf.getvalue()


def formula_to_xlsx(formula: studio.Formula, path: str | Path) -> Path:
    """Write a multi-sheet workbook. Requires pandas + openpyxl."""
    import pandas as pd

    sheets: dict[str, "pd.DataFrame"] = {
        "Formula": pd.DataFrame(recipe_rows(formula)),
        "Carrier": pd.DataFrame(formula.carrier_rows),
        "Safety": pd.DataFrame([
            {
                "material_ko": r.name_ko,
                "finished_pct_ww": round(r.finished_pct_ww, 4),
                "cap_pct": r.cap_pct,
                "cap_ratio": round(r.cap_ratio, 3),
                "status": r.status,
                "basis": mol_lib.get(r.id).cap_basis,
            }
            for r in formula.rows
        ]),
        "NotePyr": pd.DataFrame([
            {"note": mol_lib.NOTE_LABELS_KO[n], "share": round(v, 3)}
            for n, v in formula.note_balance.items()
        ]),
        "Methodology": pd.DataFrame([
            {
                "indicator": i.id,
                "label_ko": i.label_ko,
                "evidence": provenance.KINDS[i.kind],
                "unit": i.unit,
                "formula": i.formula,
                "boundary": i.boundary_ko,
                "references": " | ".join(r.label for r in i.references),
            }
            for i in provenance.INDICATORS
        ]),
        "Provenance": pd.DataFrame([
            {"key": k, "value": v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}
            for k, v in {
                **PROVENANCE,
                "product_type": formula.product_type.name_ko,
                "volume_ml": formula.volume_ml,
                "load_pct": formula.load_pct,
                "status": formula.status,
                "warnings": " | ".join(formula.warnings),
            }.items()
        ]),
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        for name, df in sheets.items():
            df.to_excel(xl, sheet_name=name[:31], index=False)
    return out


def write_recipe(formula: studio.Formula, path: str | Path) -> Path:
    """Dispatch on the file suffix: .csv, .json, .xlsx, .md."""
    out = Path(path)
    suffix = out.suffix.lower()
    if suffix == ".json":
        out.write_text(formula_to_json(formula), encoding="utf-8")
    elif suffix == ".csv":
        out.write_text(formula_to_csv(formula), encoding="utf-8-sig")
    elif suffix in (".xlsx", ".xlsm"):
        return formula_to_xlsx(formula, out)
    elif suffix in (".md", ".markdown"):
        export_markdown(formula, out)
    else:
        raise ValueError(
            f"unsupported recipe format {suffix!r}; use .csv, .json, .xlsx or .md"
        )
    return out


def molecule_table_csv() -> str:
    buf = io.StringIO()
    fields = ["id", "name", "name_ko", "cas", "formula", "molecular_weight", "smiles",
              "pubchem_cid", "functional_group", "note", "families", "descriptor_ko",
              "natural_sources", "working_cap_pct", "density_g_ml", "state"]
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for m in mol_lib.MOLECULES:
        writer.writerow({
            "id": m.id, "name": m.name, "name_ko": m.name_ko, "cas": m.cas or "",
            "formula": m.formula, "molecular_weight": m.molecular_weight,
            "smiles": m.smiles, "pubchem_cid": m.pubchem_cid,
            "functional_group": m.functional_group, "note": m.note,
            "families": json.dumps(dict(m.families), ensure_ascii=False),
            "descriptor_ko": m.descriptor_ko,
            "natural_sources": " / ".join(m.natural_sources),
            "working_cap_pct": m.working_cap_pct, "density_g_ml": m.density_g_ml,
            "state": m.state,
        })
    return buf.getvalue()


def atlas_table_csv() -> str:
    buf = io.StringIO()
    fields = ["id", "name_ko", "name_en", "botanical", "category", "era_label", "year",
              "region", "material_part", "molecules", "use_ko", "caution", "conservation"]
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for e in atlas_lib.ATLAS:
        writer.writerow({
            "id": e.id, "name_ko": e.name_ko, "name_en": e.name_en,
            "botanical": e.botanical, "category": e.category, "era_label": e.era_label,
            "year": e.year, "region": e.region, "material_part": e.material_part,
            "molecules": " / ".join(e.molecules), "use_ko": e.use_ko,
            "caution": e.caution, "conservation": e.conservation,
        })
    return buf.getvalue()


# --------------------------------------------------------------------------- markdown
def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|")


def formula_to_markdown(formula: studio.Formula, title: str | None = None) -> str:
    """A full research / formulation report in Markdown.

    Sections: weighing table, note pyramid, safety verdict with headroom, the
    molecular property profile (mass-weighted, derived descriptors), the
    methodology appendix and the licence.  Every figure carries its evidence
    class, so a reader can tell a measurement from a heuristic at a glance.
    """
    from . import compare as compare_lib  # local import: compare imports studio only

    profile = compare_lib.property_profile(formula)
    heading = title or f"OLFACTRA 배합 보고서 — {formula.product_type.name_ko}"
    status_ko = {"ok": "적합", "caution": "주의", "over": "상한 초과"}[formula.status]
    row_ko = {"ok": "적합", "caution": "주의", "over": "초과"}
    lines: list[str] = [
        f"# {heading}",
        "",
        f"- 버전: **OLFACTRA {__version__}** · JSON schema `{SCHEMA_VERSION}` · MIT License",
        f"- 생성일: {date.today().isoformat()}",
        f"- 제형: **{formula.product_type.name_ko}** ({formula.product_type.id}) · "
        f"{formula.volume_ml:g} mL · 부향률 {formula.load_pct:g}% "
        f"(완성품 {formula.finished_load_pct_ww:.2f}% w/w)",
        f"- 총 무게 {formula.total_mass_g:.2f} g (향 농축액 {formula.fragrance_mass_g:.2f} g)",
        f"- 안전 판정: **{status_ko}**",
        "",
        "> 이 보고서는 **후보 배합**을 계산한 것입니다. 완성된 혼합물의 냄새를 예측하지 않으며, "
        "관능평가·GC-MS 분석·안전성 평가를 대체하지 않습니다.",
        "",
        "## 1. 계량표",
        "",
        "| No | 원료 | CAS | 노트 | 비중 (%) | mL | g | 완성품 (% w/w) | 적용 상한 (%) | 판정 |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for i, row in enumerate(formula.rows, start=1):
        m = mol_lib.get(row.id)
        lines.append(
            f"| {i} | {_md_cell(row.name_ko)} ({_md_cell(row.name)}) | {m.cas or '—'} | "
            f"{mol_lib.NOTE_LABELS_KO[row.note]} | {row.share_pct:.1f} | {row.volume_ml:.3f} | "
            f"{row.mass_g:.3f} | {row.finished_pct_ww:.4f} | {row.cap_pct:g} | "
            f"{row_ko[row.status]} |"
        )
    lines += [
        "",
        "### 캐리어",
        "",
        "| 캐리어 | 역할 | 비율 (%) | mL | g |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for c in formula.carrier_rows:
        lines.append(
            f"| {_md_cell(c['name'])} | {_md_cell(c.get('role', ''))} | {c['ratio_pct']:.1f} | "
            f"{c['volume_ml']:.3f} | {c['mass_g']:.3f} |"
        )

    lines += ["", "## 2. 노트 피라미드", "", "| 노트 | 비중 (%) |", "| --- | ---: |"]
    for note in mol_lib.NOTES:
        lines.append(f"| {mol_lib.NOTE_LABELS_KO[note]} | {formula.note_balance.get(note, 0) * 100:.1f} |")

    lines += [
        "",
        "## 3. 물성 프로파일 (질량 가중 평균, 유도 지표)",
        "",
        "| 지표 | 값 | 근거 등급 |",
        "| --- | ---: | --- |",
        f"| 원료 수 | {profile['materials']} | — |",
        f"| 평균 분자량 (g/mol) | {profile['mean_mw']:.2f} | 측정(PubChem) |",
        f"| 분자량 범위 (g/mol) | {profile['min_mw']:.2f}–{profile['max_mw']:.2f} | 측정(PubChem) |",
        f"| 평균 계산 LogP | {profile['mean_logp']:.2f} | 유도(Crippen) |",
        f"| LogP 범위 | {profile['min_logp']:.2f}–{profile['max_logp']:.2f} | 유도(Crippen) |",
        f"| 평균 TPSA (Å²) | {profile['mean_tpsa']:.2f} | 유도(Ertl) |",
        f"| 고체 원료 비중 (%) | {profile['solid_share_pct']:.1f} | — |",
        "",
        "LogP와 TPSA는 공개 SMILES에서 계산한 **추정치**이며 실측값이 아닙니다. "
        "휘발성·발향 지속시간의 대리값으로 쓰지 마세요(지표 경계 참고).",
        "",
        "## 4. 안전 판정",
        "",
        f"- 판정: **{status_ko}**",
        f"- 최대 상한 사용률: {profile['max_cap_ratio'] * 100:.0f}% · 남은 여유분 {profile['headroom_pct']:.1f}%",
        f"- 표시 대상 알레르겐(EU 0.001% 이상): {', '.join(formula.allergens) or '없음'}",
        "",
    ]
    if formula.warnings:
        lines += ["### 주의 사항", ""] + [f"- {w}" for w in formula.warnings] + [""]
    else:
        lines += ["주의 사항이 없습니다.", ""]

    used = ["pubchem_record", "dilution_arithmetic", "safety_gate", "note_pyramid",
            "logp_crippen", "tpsa_ertl", "odour_family_vector", "blend_harmony"]
    lines += [
        "## 5. 방법론·출처·경계",
        "",
        "근거 등급: **측정** = 공개 데이터셋·레코드의 실측값, **유도·계산** = 공개 입력에서 "
        "정해진 방법으로 계산한 값, **휴리스틱** = 측정 대상이 없는 규칙 기반 지표.",
        "",
        provenance.markdown_table(used),
        "",
        f"> **과학적 경계** — {provenance.BOUNDARIES['science']}",
        "",
        f"> **안전 경계** — {provenance.BOUNDARIES['safety']}",
        "",
        f"> **모델 경계** — {provenance.BOUNDARIES['model']}",
        "",
        "### 참고문헌",
        "",
        provenance.markdown_references(),
        "",
        "## 6. 재현",
        "",
        "```bash",
        "python -m olfactra_core formulate"
        f" --product {formula.product_type.id} --volume {formula.volume_ml:g}"
        f" --load {formula.load_pct:g}"
        ' --accord "' + ",".join(f"{r.id}={r.share_pct:.2f}" for r in formula.rows) + '"'
        " --out report.md",
        "```",
        "",
        "---",
        "",
        "경상국립대학교 환경산림과학부 산림환경자원학과 **FEI · HEL 인간환경연구실** · "
        "`Copyright (c) 2026 FEI · HEL Lab, Gyeongsang National University` · MIT License",
    ]
    return "\n".join(lines).rstrip() + "\n"


def export_markdown(formula: studio.Formula, path: str | Path,
                    title: str | None = None) -> Path:
    """Write :func:`formula_to_markdown` to a file and return its path."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(formula_to_markdown(formula, title=title), encoding="utf-8")
    return out
