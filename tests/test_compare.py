"""Comparing two formulas — note pyramid, property profile, safety headroom.

The comparison must be *arithmetic over the studio result*, not a second engine:
these tests check that the numbers agree with ``studio.formulate`` and that the
differences point the way a perfumer would read them.
"""
from __future__ import annotations

import json

import pytest

from olfactra_core import compare, molecule, recommender, studio


@pytest.fixture(scope="module")
def comparison():
    return compare.compare_accords("forest-breath", "frankincense-rite", volume_a=100, volume_b=100)


def test_profile_is_consistent_with_the_formula(sample_formula):
    profile = compare.property_profile(sample_formula)
    assert profile["materials"] == len(sample_formula.rows)
    assert profile["fragrance_mass_g"] == pytest.approx(round(sample_formula.fragrance_mass_g, 3))
    # mass-weighted mean MW must sit inside the material range
    assert profile["min_mw"] <= profile["mean_mw"] <= profile["max_mw"]
    assert profile["min_logp"] <= profile["mean_logp"] <= profile["max_logp"]
    assert profile["max_tpsa"] >= profile["mean_tpsa"] >= 0
    assert profile["note_share_pct"]["middle"] == pytest.approx(90.0, abs=0.1)


def test_headroom_matches_the_worst_material(sample_formula):
    profile = compare.property_profile(sample_formula)
    worst = max(r.cap_ratio for r in sample_formula.rows)
    assert profile["max_cap_ratio"] == pytest.approx(round(worst, 3))
    assert profile["headroom_pct"] == pytest.approx(round(max(0.0, 1 - worst) * 100, 1))


def test_over_ceiling_formula_reports_no_headroom():
    # limonene in an EDP at a high load blows through the working ceiling
    formula = studio.formulate("edp", 50, 25, {"limonene": 100})
    profile = compare.property_profile(formula)
    assert profile["status"] == "over"
    assert profile["headroom_pct"] == 0.0
    assert profile["over"] == ["리모넨"]


def test_compare_rejects_non_formulas():
    with pytest.raises(TypeError):
        compare.compare_formulas({"linalool": 1}, {"linalool": 1})  # type: ignore[arg-type]


def test_comparison_exposes_both_sides_and_deltas(comparison):
    data = comparison.as_dict()
    json.dumps(data, ensure_ascii=False)
    assert data["schema_version"] == "0.2.0"
    assert data["labels"] == {"a": "숲의 호흡", "b": "유향 의식"}
    for side in ("a", "b"):
        assert data[side]["status"] in {"ok", "caution", "over"}
        assert data[side]["profile"]["materials"] >= 3
        assert data[side]["materials"]
    assert set(data["deltas"]) >= {"mean_mw", "mean_logp", "mean_tpsa", "headroom_pct"}
    assert data["deltas"]["mean_mw"] == pytest.approx(
        data["b"]["profile"]["mean_mw"] - data["a"]["profile"]["mean_mw"], abs=0.01
    )
    assert data["summary"] and isinstance(data["summary"][0], str)
    assert "compare" in data["boundaries"]


def test_exposure_route_shows_up_as_more_headroom():
    """The same concentrate in a reed diffuser must show more headroom than in an EDP."""
    materials = recommender.get_accord("forest-breath").materials
    diffuser = studio.formulate("reed_diffuser", 100, None, materials)
    edp = studio.formulate("edp", 100, None, materials)
    result = compare.compare_formulas(diffuser, edp, label_a="디퓨저", label_b="EDP")
    pd, pe = result.profile("a"), result.profile("b")
    assert pd["headroom_pct"] > pe["headroom_pct"]
    assert any("여유분" in line or "판정" in line for line in result.summary_ko())


def test_note_shift_is_named_in_the_summary():
    a = studio.formulate("edp", 50, 20, {"limonene": 80, "linalool": 20})       # top-heavy
    b = studio.formulate("edp", 50, 20, {"cedrol": 80, "patchoulol": 20})       # base-heavy
    result = compare.compare_formulas(a, b)
    text = " ".join(result.summary_ko())
    assert "노트" in text
    assert result.deltas()["note_top_pp"] < -50
    assert result.deltas()["note_base_pp"] > 50


def test_resolve_side_accepts_preset_and_inline_accord():
    formula, label = compare.resolve_side("forest-breath")
    assert label == "숲의 호흡"
    assert formula.product_type.id == "reed_diffuser"       # preset keeps its hint
    formula2, _ = compare.resolve_side("linalool=60,cedrol=40", product_type="edp", volume_ml=30)
    assert formula2.product_type.id == "edp" and formula2.volume_ml == 30
    with pytest.raises(ValueError):
        compare.parse_accord_text("linalool")


def test_markdown_report_covers_every_section(comparison):
    text = compare.markdown(comparison)
    for heading in ("## 1. 요약", "## 2. 노트 피라미드", "## 3. 물성 프로파일",
                    "## 4. 안전 여유분", "## 5. 방법론·출처·경계", "### 참고문헌"):
        assert heading in text, heading
    assert "LogP" in text and "TPSA" in text
    assert "휴리스틱" in text and "유도" in text
    assert text.endswith("\n")
    assert "FEI · HEL" in text


def test_every_pair_of_presets_can_be_compared():
    ids = [a.id for a in recommender.accords()]
    for left, right in zip(ids, ids[1:]):
        result = compare.compare_accords(left, right)
        data = result.as_dict()
        assert data["a"]["profile"]["materials"] > 0
        assert data["b"]["profile"]["materials"] > 0
        assert all(m in {x.id for x in molecule.MOLECULES} for m in
                   (r["id"] for r in data["a"]["materials"]))
