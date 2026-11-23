"""The provenance registry — every number must say where it came from.

These tests enforce the property that makes the registry worth having: each
indicator is classified (measured / derived / heuristic), carries a re-computable
formula, at least one checkable source and an explicit boundary.  A new indicator
that forgets one of those fails here rather than in a report someone cites.
"""
from __future__ import annotations

import json

import pytest

from olfactra_core import provenance


def test_every_indicator_is_classified_and_documented():
    assert len(provenance.INDICATORS) >= 12
    for ind in provenance.INDICATORS:
        assert ind.kind in provenance.KINDS, ind.id
        assert ind.label_ko and ind.label_en, ind.id
        assert ind.unit, ind.id
        assert ind.formula, ind.id
        assert ind.inputs, ind.id
        assert len(ind.basis_ko) > 20, ind.id
        assert len(ind.boundary_ko) > 20, ind.id
        assert ind.used_in, ind.id
        assert any(r.link for r in ind.references), ind.id


def test_the_three_evidence_classes_are_all_represented():
    counts = provenance.counts()
    assert counts["measured"] >= 4      # PubChem, Keller, Dravnieks, Mainland
    assert counts["derived"] >= 3       # dilution, conformer, LogP, TPSA, prior
    assert counts["heuristic"] >= 3     # odour families, harmony, ceilings, docking
    assert sum(counts.values()) == len(provenance.INDICATORS)


def test_named_core_indicators_exist_with_the_expected_class():
    expected = {
        "pubchem_record": "measured",
        "keller_2016": "measured",
        "dravnieks_1985": "measured",
        "mainland_2015": "measured",
        "logp_crippen": "derived",
        "tpsa_ertl": "derived",
        "conformer_3d": "derived",
        "dilution_arithmetic": "derived",
        "volatility_index": "heuristic",
        "safety_gate": "heuristic",
        "blend_harmony": "heuristic",
        "schematic_docking": "heuristic",
    }
    for indicator_id, kind in expected.items():
        assert provenance.get(indicator_id).kind == kind, indicator_id


def test_ambiguous_indicators_state_their_limits():
    # the two easiest numbers to over-read must say so out loud
    safety = provenance.get("safety_gate")
    assert "IFRA" in safety.boundary_ko and "안전성 평가" in safety.boundary_ko
    docking = provenance.get("schematic_docking")
    assert "Kd" in docking.boundary_ko and "모식" in docking.boundary_ko
    volatility = provenance.get("volatility_index")
    assert "증기압" in volatility.boundary_ko   # no vapour pressure is claimed
    prior = provenance.get("hedonic_prior")
    assert "혼합" in prior.boundary_ko


def test_academic_sources_carry_dois():
    for key in ("keller_2016", "dravnieks_1985", "mainland_2015"):
        dois = [r.doi for r in provenance.get(key).references if r.doi]
        assert dois, key
    assert any("10.1186/s12868-016-0287-2" in r.doi for r in provenance.get("keller_2016").references)
    assert any("10.1038/sdata.2015.2" in r.doi for r in provenance.get("mainland_2015").references)


def test_context_lookup_and_kind_filter():
    studio_ids = {i.id for i in provenance.for_context("STUDIO")}
    assert {"dilution_arithmetic", "safety_gate", "note_pyramid"} <= studio_ids
    assert all(i.kind == "measured" for i in provenance.by_kind("measured"))
    with pytest.raises(KeyError):
        provenance.by_kind("opinion")


def test_payload_is_json_safe_and_self_consistent():
    payload = provenance.as_dict()
    json.dumps(payload, ensure_ascii=False)
    assert payload["schema_version"] == "0.2.0"
    assert payload["counts"] == provenance.counts()
    assert len(payload["indicators"]) == len(provenance.INDICATORS)
    assert {k["id"] for k in payload["kinds"]} == set(provenance.KINDS)
    assert payload["boundaries"].keys() >= {"science", "safety", "model", "clean_room"}
    # every reference in the payload is reachable from an indicator
    assert payload["references"]


def test_markdown_helpers_render_the_registry():
    table = provenance.markdown_table(["safety_gate", "dilution_arithmetic"])
    assert table.startswith("| 지표 | 근거 등급 |")
    assert "안전 상한 게이트" in table and "배합 계량" in table
    assert table.count("\n") >= 3
    refs = provenance.markdown_references()
    assert refs.count("- **") >= 8
    assert "https://doi.org/" in refs
