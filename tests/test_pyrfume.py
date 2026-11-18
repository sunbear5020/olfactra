"""The bundled Pyrfume extract, and how the ID recommender uses it.

The point of these tests is that the numbers are *traceable*: the bundle records
which Pyrfume files it came from, the values match the published aggregates, and
the recommender shows its evidence instead of hiding the prior inside a score.
"""
from __future__ import annotations

import pytest

from olfactra_core import molecule, pyrfume, recommender


def test_bundle_records_its_sources():
    src = pyrfume.sources()
    assert set(src) == {"keller_2016", "dravnieks_1985", "mainland_2015"}
    assert "10.1186/s12868-016-0287-2" in src["keller_2016"]["doi"]
    assert "10.1520/DS61-EB" in src["dravnieks_1985"]["doi"]
    assert "10.1038/sdata.2015.2" in src["mainland_2015"]["doi"]
    for key, meta in src.items():
        assert meta["files"], key
        assert all(len(f["sha256"]) == 64 for f in meta["files"]), key


def test_coverage_is_honest_about_the_gap():
    cov = pyrfume.coverage()
    assert cov["library"] == 43
    assert cov["any"] == 23
    assert cov["keller_2016"] == 18
    assert cov["dravnieks_1985"] == 14
    assert cov["mainland_2015"] == 8
    assert len(cov["unmeasured"]) == 43 - 23
    assert "muscone" in cov["unmeasured"]      # honestly listed, not estimated
    assert pyrfume.profile("muscone") is None


def test_keller_values_match_the_published_aggregate():
    lin = pyrfume.keller("linalool")
    assert lin is not None
    assert lin["pleasantness"] == pytest.approx(70.3, abs=0.2)
    assert lin["intensity"] == pytest.approx(47.4, abs=0.2)
    assert lin["familiarity"] == pytest.approx(50.2, abs=0.2)
    assert lin["n_raters"] >= 40
    assert any(d["term"] == "FLOWER" for d in lin["top_descriptors"])
    # the famously pleasant material must beat the harsh one in the same dataset
    assert pyrfume.keller("vanillin")["pleasantness"] > pyrfume.keller("guaiacol")["pleasantness"]


def test_dravnieks_profile_reads_like_the_material():
    eug = pyrfume.dravnieks("eugenol")
    assert eug is not None
    terms = [t["term"] for t in eug["top"]]
    assert "CLOVE" in terms[:3]
    assert eug["n_descriptors"] >= 140


def test_mainland_reports_real_orphan_receptors():
    lin = pyrfume.mainland("linalool")
    genes = [r["gene"] for r in lin["receptors"]]
    assert "OR51E2" in genes
    assert lin["n_receptors_tested"] > 100
    eug = pyrfume.receptors_reported("eugenol")
    assert "OR1A1" in [r["gene"] for r in eug]
    # a receptor the dataset never assayed for this odorant must not appear
    assert pyrfume.receptor_evidence("linalool", "OR1G1") is None


def test_hedonic_prior_needs_enough_measured_material():
    assert pyrfume.prior({"muscone": 50, "cedrol": 50}) is None
    prior = pyrfume.prior({"linalool": 40, "vanillin": 40, "muscone": 20})
    assert prior is not None
    assert prior["coverage"] == pytest.approx(0.8, abs=0.01)
    assert prior["mean"] > 60
    assert 0 <= prior["value"] <= 1


def test_suggestion_carries_the_evidence_block():
    picks = recommender.recommend(mood="calm", space="study", style="green", limit=1)
    assert picks
    data = picks[0].as_dict()
    ev = data["evidence"]
    assert len(ev["sources"]) == 3
    assert ev["materials"]
    measured = [m for m in ev["materials"] if m.get("pleasantness") is not None]
    assert measured, "at least one constituent should carry a measured value"
    for row in ev["materials"]:
        if row.get("pleasantness") is None:
            assert row["measured"] is False or "measured" in row


def test_hedonic_prior_shows_up_as_a_reason():
    picks = recommender.recommend(mood="romance", style="floral", limit=3)
    reasons = [r for p in picks for r in p.reasons]
    assert any("Keller & Vosshall 2016" in r for r in reasons)


def test_engine_library_and_bundle_agree_on_ids():
    ids = {m.id for m in molecule.MOLECULES}
    for mid in pyrfume.bundle()["molecules"]:
        assert mid in ids
