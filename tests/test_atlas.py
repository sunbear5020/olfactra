import pytest

from olfactra_core import atlas, molecule


def test_entries_and_categories():
    assert len(atlas.ATLAS) >= 20
    ids = [e.id for e in atlas.ATLAS]
    assert len(ids) == len(set(ids))
    for entry in atlas.ATLAS:
        assert entry.category in atlas.CATEGORIES
        assert entry.name_ko and entry.name_en
        assert entry.story and entry.science and entry.use_ko
        assert entry.sources, entry.id


def test_every_referenced_molecule_exists():
    for entry in atlas.ATLAS:
        assert entry.molecules, entry.id
        for mid in entry.molecules:
            assert molecule.get(mid).id == mid


def test_timeline_is_ordered():
    asc = atlas.timeline()
    years = [e.year for e in asc]
    assert years == sorted(years)
    desc = atlas.timeline(ascending=False)
    assert [e.year for e in desc] == sorted(years, reverse=True)


def test_search_and_filters():
    assert any(e.id == "frankincense" for e in atlas.search("유향"))
    assert any(e.id == "hinoki" for e in atlas.search("편백"))
    assert all(e.category == "forest" for e in atlas.by_category("forest"))
    assert len(atlas.by_category("forest")) == 2
    assert atlas.by_category(None) == list(atlas.ATLAS)


def test_by_molecule_links_atlas_and_library():
    entries = atlas.by_molecule("alpha-pinene")
    assert {"frankincense", "pine-phytoncide"}.issubset({e.id for e in entries})
    assert atlas.by_molecule("muscone")[0].id == "musk"


def test_get_and_stats():
    assert atlas.get("kyphi").name_en == "Kyphi"
    with pytest.raises(KeyError):
        atlas.get("not-a-real-entry")
    stats = atlas.stats()
    assert stats["entries"] == len(atlas.ATLAS)
    assert stats["span_bce"] <= -1000
    assert stats["span_ce"] >= 1900


def test_no_proprietary_or_trademarked_formula_content():
    """The atlas must describe history and public chemistry, not branded formulas."""
    banned = ("tobii", "proprietary formula", "trade secret", "©")
    for entry in atlas.ATLAS:
        text = " ".join([entry.story, entry.science, entry.use_ko]).lower()
        for word in banned:
            assert word not in text, (entry.id, word)
