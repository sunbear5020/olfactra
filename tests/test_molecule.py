import math

import pytest

from olfactra_core import molecule as lib


def test_library_is_populated_and_unique():
    assert len(lib.MOLECULES) >= 40
    ids = [m.id for m in lib.MOLECULES]
    assert len(ids) == len(set(ids))


def test_every_molecule_has_consistent_chemistry():
    for m in lib.MOLECULES:
        assert m.formula[0] == "C", m.id
        assert 80 < m.molecular_weight < 320, m.id
        assert m.smiles and m.pubchem_cid > 0, m.id
        assert m.note in lib.NOTES, m.id
        assert m.state in ("liquid", "solid"), m.id
        assert m.working_cap_pct > 0, m.id
        assert 0.7 <= m.density_g_ml <= 1.3, m.id
        assert set(m.families) <= set(lib.FAMILIES), m.id
        assert 0 < max(m.families.values()) <= 1.0, m.id


def test_lookup_by_id_name_and_cas():
    assert lib.get("limonene").name_ko == "리모넨"
    assert lib.get("80-56-8").id == "alpha-pinene"
    assert lib.get("Linalool").id == "linalool"
    with pytest.raises(KeyError):
        lib.get("unobtainium")


def test_find_matches_korean_and_sources():
    assert any(m.id == "hinokitiol" for m in lib.find("편백"))
    assert any(m.id == "vanillin" for m in lib.find("바닐라"))
    assert lib.find("") == list(lib.MOLECULES)


def test_similarity_is_symmetric_and_bounded():
    for a, b in [("linalool", "geraniol"), ("limonene", "cedrol"), ("vanillin", "coumarin")]:
        s1, s2 = lib.similarity(a, b), lib.similarity(b, a)
        assert s1 == pytest.approx(s2, abs=1e-9)
        assert 0.0 <= s1 <= 1.0
    assert lib.similarity("muscone", "muscone") == pytest.approx(1.0)


def test_similar_excludes_self_and_is_ranked():
    result = lib.similar("linalool", top_k=5)
    assert len(result) == 5
    assert all(m.id != "linalool" for m, _ in result)
    scores = [s for _, s in result]
    assert scores == sorted(scores, reverse=True)
    assert result[0][0].note in ("top", "middle")  # linalool's nearest neighbours are light/floral


def test_blend_score_prefers_complementary_notes():
    assert lib.blend_score("linalool", "geraniol") > lib.blend_score("limonene", "cedrol")
    for pair in [("limonene", "alpha-pinene"), ("guaiacol", "vanillin"), ("muscone", "linalool")]:
        assert 0.0 <= lib.blend_score(*pair) <= 1.0


def test_blend_report_balances_notes_and_warns():
    report = lib.blend_report({"limonene": 60, "linalool": 40})
    assert sum(report.note_balance.values()) == pytest.approx(1.0)
    assert report.note_balance["base"] == 0
    assert any("베이스" in w for w in report.warnings)
    assert 0.0 <= report.mean_harmony <= 1.0
    assert report.as_dict()["materials"][0]["share_pct"] > 0


def test_blend_report_rejects_empty_accord():
    with pytest.raises(ValueError):
        lib.blend_report({})
    with pytest.raises(ValueError):
        lib.blend_report({"limonene": 0})


def test_family_matrix_and_stats():
    grid = lib.family_matrix()
    assert set(grid) == set(lib.FAMILIES)
    assert "linalool" in grid["floral"]["middle"]
    stats = lib.library_stats()
    assert stats["molecules"] == len(lib.MOLECULES)
    assert sum(stats["by_note"].values()) == len(lib.MOLECULES)
    assert 100 < stats["mean_molecular_weight"] < 250


def test_volatility_follows_note_class():
    top = lib.get("limonene").volatility
    base = lib.get("cedrol").volatility
    assert 0 <= base < top <= 1
    assert math.isclose(lib.get("camphor").volatility, lib.get("camphor").volatility)
