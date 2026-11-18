import json

import pytest

from olfactra_core import exporter, studio


def test_csv_contains_recipe_and_metadata(sample_formula):
    text = exporter.formula_to_csv(sample_formula)
    header = text.splitlines()[0]
    for column in ("material_ko", "share_of_concentrate_pct", "finished_pct_ww", "cap_pct"):
        assert column in header
    assert "리날룰" in text
    assert "# license" in text
    assert "# volume_ml" in text


def test_json_roundtrip(sample_formula):
    data = json.loads(exporter.formula_to_json(sample_formula))
    assert data["formula"]["product_type"] == "edp"
    assert len(data["materials"]) == len(sample_formula.rows)
    assert data["meta"]["license"] == "MIT"
    assert "science_boundary" in data["meta"]


def test_xlsx_has_multiple_sheets(sample_formula, tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    path = exporter.formula_to_xlsx(sample_formula, tmp_path / "recipe.xlsx")
    assert path.exists() and path.stat().st_size > 3000
    wb = openpyxl.load_workbook(path)
    assert {"Formula", "Carrier", "Safety", "NotePyr", "Provenance"} <= set(wb.sheetnames)
    ws = wb["Formula"]
    assert ws.max_row == len(sample_formula.rows) + 1


@pytest.mark.parametrize("suffix", [".csv", ".json", ".xlsx"])
def test_write_recipe_dispatch(sample_formula, tmp_path, suffix):
    path = exporter.write_recipe(sample_formula, tmp_path / f"out{suffix}")
    assert path.exists()
    assert path.stat().st_size > 100


def test_write_recipe_rejects_unknown_suffix(sample_formula, tmp_path):
    with pytest.raises(ValueError):
        exporter.write_recipe(sample_formula, tmp_path / "out.pdf")


def test_library_tables():
    mols = exporter.molecule_table_csv()
    assert mols.count("\n") > 40
    assert "limonene" in mols
    entries = exporter.atlas_table_csv()
    assert "frankincense" in entries
    assert "유향" in entries
