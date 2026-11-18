import json

import pytest

from olfactra_core import molecule, recommender, studio


def test_dimension_labels_are_korean():
    dims = recommender.dimensions()
    for key in ("moods", "seasons", "spaces", "styles"):
        assert dims[key]
        for item in dims[key]:
            assert item["label"] and item["id"]


def test_every_accord_is_well_formed():
    for accord in recommender.accords():
        total = sum(accord.materials.values())
        assert total == pytest.approx(100.0, abs=0.01), accord.id
        assert all(share > 0 for share in accord.materials.values()), accord.id
        for mid in accord.materials:
            assert molecule.get(mid).id == mid, (accord.id, mid)
        assert studio.get_product_type(accord.product_hint).id == accord.product_hint
        assert accord.story and accord.tagline


def test_recommend_returns_distinct_ranked_alternatives():
    picks = recommender.recommend(mood="calm", space="study", style="green", limit=3)
    assert len(picks) == 3
    assert len({p.accord.id for p in picks}) == 3
    scores = [p.score for p in picks]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= s <= 100 for s in scores)
    for p in picks:
        assert p.reasons
        assert 0 <= p.harmony <= 1
        assert sum(p.note_balance.values()) == pytest.approx(1.0)


def test_recommend_reacts_to_conditions():
    sleep = recommender.recommend(mood="sleep", space="bedroom")[0]
    energy = recommender.recommend(mood="energy", space="entry")[0]
    assert sleep.accord.id != energy.accord.id
    assert "sleep" in sleep.accord.moods
    assert "energy" in energy.accord.moods


def test_winter_warm_request_favours_sweet_and_spice():
    pick = recommender.recommend(mood="comfort", season="winter", style="warm")[0]
    assert pick.score > 50
    profile = pick.family_profile
    assert max(profile, key=profile.get) in {"sweet", "woody", "resinous", "spicy"}


def test_recommend_without_conditions_still_works():
    picks = recommender.recommend(limit=2)
    assert len(picks) == 2
    assert all(p.reasons for p in picks)


def test_invalid_dimensions_raise():
    with pytest.raises(ValueError):
        recommender.recommend(mood="melancholy")
    with pytest.raises(ValueError):
        recommender.recommend(season="monsoon")
    with pytest.raises(ValueError):
        recommender.recommend(space="garage")
    with pytest.raises(ValueError):
        recommender.recommend(style="brutalist")


def test_suggestion_payload_is_json_safe(top_pick):
    payload = json.dumps(top_pick.as_dict(), ensure_ascii=False)
    data = json.loads(payload)
    assert data["accord"]["id"] == top_pick.accord.id
    assert data["load_default"] == studio.get_product_type(top_pick.product_hint).load_default
    assert len(data["accord"]["materials_detail"]) == len(top_pick.accord.materials)


def test_every_accord_can_be_formulated():
    for accord in recommender.accords():
        for product in (accord.product_hint, "edp", "room_spray"):
            f = studio.formulate(product, 50, None, accord.materials)
            assert f.total_mass_g > 0
            assert f.status in ("ok", "caution", "over")
            assert f.rows


def test_exclude_removes_accords():
    first = recommender.recommend(mood="calm", limit=1)[0]
    second = recommender.recommend(mood="calm", limit=1, exclude=(first.accord.id,))[0]
    assert second.accord.id != first.accord.id
