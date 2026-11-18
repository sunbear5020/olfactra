"""OLFACTRA exporters — recipe output as CSV, JSON or Excel.

Excel output is the one researchers actually send around, so it is written as a
small workbook with separate sheets: the formula itself, the safety check, the
note pyramid, and a provenance sheet that states the licence and the limits of
what the numbers mean.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping

from . import __version__, atlas as atlas_lib, molecule as mol_lib, studio

RECIPE_COLUMNS = (
    "no", "material", "material_ko", "cas", "formula", "note", "share_of_concentrate_pct",
    "volume_ml", "mass_g", "finished_pct_ww", "cap_pct", "cap_ratio", "status",
    "allergen_label", "state",
)

PROVENANCE = {
    "project": "OLFACTRA",
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


def formula_to_dict(formula: studio.Formula) -> dict:
    return {
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


def formula_to_json(formula: studio.Formula, indent: int = 2) -> str:
    return json.dumps(formula_to_dict(formula), ensure_ascii=False, indent=indent)


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
    """Dispatch on the file suffix: .csv, .json, .xlsx."""
    out = Path(path)
    suffix = out.suffix.lower()
    if suffix == ".json":
        out.write_text(formula_to_json(formula), encoding="utf-8")
    elif suffix == ".csv":
        out.write_text(formula_to_csv(formula), encoding="utf-8-sig")
    elif suffix in (".xlsx", ".xlsm"):
        return formula_to_xlsx(formula, out)
    else:
        raise ValueError(f"unsupported recipe format {suffix!r}; use .csv, .json or .xlsx")
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
