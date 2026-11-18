import pytest

from olfactra_core import studio


def test_product_catalogue_is_complete():
    ids = {p.id for p in studio.product_types()}
    assert {"reed_diffuser", "room_spray", "linen_mist", "eau_de_cologne", "edt", "edp",
            "body_oil", "solid_perfume"} == ids
    for p in studio.product_types():
        assert 0 < p.load_min <= p.load_default <= p.load_max <= 100
        assert abs(sum(c.ratio for c in p.carriers) - 1.0) < 1e-9
        assert p.exposure in ("skin", "surface")


def test_volume_and_mass_conservation(sample_formula):
    f = sample_formula
    frag_ml = sum(r.volume_ml for r in f.rows)
    base_ml = sum(c["volume_ml"] for c in f.carrier_rows)
    assert frag_ml == pytest.approx(f.volume_ml * f.load_pct / 100, rel=1e-6)
    assert frag_ml + base_ml == pytest.approx(f.volume_ml, rel=1e-6)
    masses = sum(r.mass_g for r in f.rows) + sum(c["mass_g"] for c in f.carrier_rows)
    assert masses == pytest.approx(f.total_mass_g, rel=1e-6)
    assert f.fragrance_mass_g == pytest.approx(sum(r.mass_g for r in f.rows), rel=1e-9)


def test_shares_are_normalised():
    f = studio.formulate("edp", 100, 20, {"linalool": 2, "geraniol": 1, "cedrol": 1})
    shares = {r.id: r.share_pct for r in f.rows}
    assert shares["linalool"] == pytest.approx(50.0, rel=1e-3)
    assert shares["geraniol"] == pytest.approx(25.0, rel=1e-3)


def test_finished_percentage_matches_definition(sample_formula):
    f = sample_formula
    assert f.finished_load_pct_ww > 0
    for r in f.rows:
        assert r.finished_pct_ww == pytest.approx(r.mass_g / f.total_mass_g * 100, rel=1e-9)
        assert r.cap_ratio == pytest.approx(r.finished_pct_ww / r.cap_pct, rel=1e-9)


def test_restricted_material_over_ceiling_is_flagged():
    # eugenol ceiling is 1 % of a leave-on product; 100 % share at 20 % load is far above it
    f = studio.formulate("edp", 50, 20, {"eugenol": 100})
    assert f.status == "over"
    assert f.rows[0].status == "over"
    assert any("유제놀" in w for w in f.warnings)


def test_trace_amount_is_within_ceiling():
    f = studio.formulate("edp", 50, 20, {"linalool": 98, "eugenol": 2})
    eugenol = next(r for r in f.rows if r.id == "eugenol")
    assert eugenol.status in ("ok", "caution")
    assert f.status != "over"


def test_ambient_formats_relax_dermal_ceiling_but_keep_notes():
    diffuser = studio.formulate("reed_diffuser", 100, 20, {"eugenol": 8, "limonene": 92})
    edp = studio.formulate("edp", 100, 20, {"eugenol": 8, "limonene": 92})
    d_eug = next(r for r in diffuser.rows if r.id == "eugenol")
    e_eug = next(r for r in edp.rows if r.id == "eugenol")
    assert d_eug.cap_pct == pytest.approx(e_eug.cap_pct * 6.0)
    assert any("노출 경로 보정" in w for w in diffuser.warnings)
    assert any("고양이" in w or "반려동물" in w for w in diffuser.warnings)


def test_load_above_product_maximum_warns():
    f = studio.formulate("linen_mist", 100, 12, {"linalool": 100})
    assert f.status == "over"
    assert any("권장 상한" in w for w in f.warnings)


def test_default_load_is_used_when_omitted():
    f = studio.formulate("room_spray", 100, None, {"limonene": 100})
    assert f.load_pct == studio.get_product_type("room_spray").load_default


def test_solid_material_warning_and_weights():
    f = studio.formulate("edp", 100, 20, {"vanillin": 50, "linalool": 50})
    vanillin = next(r for r in f.rows if r.id == "vanillin")
    assert vanillin.is_solid
    assert any("고체 원료" in w for w in f.warnings)


def test_allergen_list_is_reported():
    f = studio.formulate("edp", 100, 20, {"limonene": 50, "linalool": 50})
    assert "리모넨" in f.allergens and "리날룰" in f.allergens


def test_invalid_inputs_raise():
    with pytest.raises(KeyError):
        studio.formulate("shampoo", 50, 10, {"linalool": 100})
    with pytest.raises(ValueError):
        studio.formulate("edp", 0, 10, {"linalool": 100})
    with pytest.raises(ValueError):
        studio.formulate("edp", 50, 0, {"linalool": 100})
    with pytest.raises(ValueError):
        studio.formulate("edp", 50, 10, {})
    with pytest.raises(ValueError):
        studio.formulate("edp", 50, 10, None)


def test_propose_max_share_respects_exposure_route():
    skin = studio.propose_max_share("citral", "edp")
    ambient = studio.propose_max_share("citral", "reed_diffuser")
    assert 0 <= skin <= 100
    assert ambient > skin


def test_dilution_table():
    table = studio.dilution_table("edp", 100)
    assert len(table) == 6
    row = next(r for r in table if r["load_pct"] == 20)
    assert row["fragrance_ml"] == pytest.approx(20)
    assert row["base_ml"] == pytest.approx(80)
    assert row["within_range"] is True


def test_as_dict_is_json_safe(sample_formula):
    import json
    payload = json.dumps(sample_formula.as_dict(), ensure_ascii=False)
    assert "product_type" in payload
    assert sample_formula.as_dict()["rows"][0]["cap_pct"] > 0
