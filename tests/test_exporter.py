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


# ------------------------------------------------------------------ v0.2.0 reports
def test_json_bundle_declares_its_schema(sample_formula):
    data = json.loads(exporter.formula_to_json(sample_formula))
    assert data["schema_version"] == exporter.SCHEMA_VERSION == "0.2.0"
    assert data["meta"]["schema_version"] == "0.2.0"
    assert data["meta"]["version"] == "0.2.0"
    # the methodology travels with the numbers
    methodology = data["methodology"]
    assert methodology["schema_version"] == "0.2.0"
    assert len(methodology["indicators"]) >= 12
    assert {k["id"] for k in methodology["kinds"]} == {"measured", "derived", "heuristic"}


def test_json_can_omit_the_methodology_for_size(sample_formula):
    lean = json.loads(exporter.formula_to_json(sample_formula, include_methodology=False))
    assert "methodology" not in lean
    assert lean["schema_version"] == "0.2.0"
    assert lean["formula"]["product_type"] == "edp"


def test_xlsx_has_a_methodology_sheet(sample_formula, tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    path = exporter.formula_to_xlsx(sample_formula, tmp_path / "recipe.xlsx")
    wb = openpyxl.load_workbook(path)
    assert "Methodology" in wb.sheetnames
    ws = wb["Methodology"]
    header = [c.value for c in ws[1]]
    assert header[:4] == ["indicator", "label_ko", "evidence", "unit"]
    assert ws.max_row >= 12
    kinds = {ws.cell(row=i, column=3).value for i in range(2, ws.max_row + 1)}
    assert kinds == {"측정", "유도·계산", "휴리스틱"}


def test_markdown_report_has_every_section(sample_formula):
    text = exporter.formula_to_markdown(sample_formula)
    for heading in ("# OLFACTRA 배합 보고서", "## 1. 계량표", "## 2. 노트 피라미드",
                    "## 3. 물성 프로파일", "## 4. 안전 판정", "## 5. 방법론·출처·경계",
                    "## 6. 재현"):
        assert heading in text, heading
    assert "리날룰" in text
    assert "schema `0.2.0`" in text
    assert "python -m olfactra_core formulate" in text
    assert "FEI · HEL" in text
    # the property profile is present and labelled as derived
    assert "평균 계산 LogP" in text and "유도(Crippen)" in text
    assert "평균 TPSA" in text and "유도(Ertl)" in text


def test_markdown_report_shows_warnings_when_over(sample_formula):
    from olfactra_core import studio

    over = studio.formulate("edp", 50, 25, {"limonene": 100})
    text = exporter.formula_to_markdown(over)
    assert "상한 초과" in text
    assert "### 주의 사항" in text


def test_write_recipe_dispatches_markdown(sample_formula, tmp_path):
    path = exporter.write_recipe(sample_formula, tmp_path / "report.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# OLFACTRA 배합 보고서")
    assert "| No | 원료 |" in text


def test_export_markdown_accepts_a_custom_title(sample_formula, tmp_path):
    path = exporter.export_markdown(sample_formula, tmp_path / "lab.md", title="실험 3 — 숲 배합")
    assert path.read_text(encoding="utf-8").splitlines()[0] == "# 실험 3 — 숲 배합"
