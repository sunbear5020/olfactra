import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from api.server import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["license"] == "MIT"
    assert data["molecules"] >= 40


def test_meta():
    data = client.get("/api/meta").json()
    assert data["dimensions"]["moods"]
    assert any(p["id"] == "edp" for p in data["products"])
    assert data["stats"]["molecules"]["molecules"] >= 40


def test_molecules_list_and_filter():
    everything = client.get("/api/molecules").json()
    assert len(everything) >= 40
    floral = client.get("/api/molecules", params={"family": "floral"}).json()
    assert floral and all(m["families"].get("floral", 0) >= 0.2 for m in floral)
    found = client.get("/api/molecules", params={"q": "편백"}).json()
    assert any(m["id"] == "hinokitiol" for m in found)


def test_molecule_detail_and_404():
    data = client.get("/api/molecules/limonene").json()
    assert data["formula"] == "C10H16"
    assert data["similar"]
    assert "atlas_entries" in data
    assert client.get("/api/molecules/nope").status_code == 404


def test_similar_endpoint():
    data = client.get("/api/molecules/linalool/similar", params={"top_k": 3}).json()
    assert len(data) == 3
    assert data[0]["score"] >= data[-1]["score"]


def test_atlas_endpoints():
    items = client.get("/api/atlas").json()
    assert len(items) >= 20
    assert items == sorted(items, key=lambda e: e["year"])
    forest = client.get("/api/atlas", params={"category": "forest"}).json()
    assert len(forest) == 2
    entry = client.get("/api/atlas/frankincense").json()
    assert entry["name_ko"].startswith("유향")
    assert entry["molecules_detail"]
    assert client.get("/api/atlas/nope").status_code == 404


def test_accords_endpoint():
    accords = client.get("/api/accords").json()
    assert len(accords) >= 10


def test_recommend_endpoint():
    r = client.get("/api/recommend", params={"mood": "sleep", "space": "bedroom", "style": "floral"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert results
    assert results[0]["accord"]["materials_detail"]
    assert client.get("/api/recommend", params={"mood": "grumpy"}).status_code == 422


def test_recommend_one_returns_formula():
    data = client.get("/api/recommend/forest-breath", params={"volume_ml": 100}).json()
    assert data["formula"]["rows"]
    assert data["formula"]["total_mass_g"] > 0


def test_formulate_endpoint():
    payload = {
        "product_type": "edp",
        "volume_ml": 50,
        "load_pct": 20,
        "accord": {"linalool": 40, "geraniol": 30, "cedrol": 30},
    }
    data = client.post("/api/formulate", json=payload).json()
    assert data["finished_load_pct_ww"] > 0
    assert data["status"] in ("ok", "caution", "over")
    assert len(data["rows"]) == 3
    bad = client.post("/api/formulate", json={**payload, "product_type": "shampoo"})
    assert bad.status_code == 422


def test_recipe_downloads():
    payload = {"product_type": "edp", "volume_ml": 30, "load_pct": 15,
               "accord": {"linalool": 50, "vanillin": 50}}
    csv = client.post("/api/recipe", params={"fmt": "csv"}, json=payload)
    assert csv.status_code == 200
    assert "text/csv" in csv.headers["content-type"]
    assert "리날룰" in csv.text
    js = client.post("/api/recipe", params={"fmt": "json"}, json=payload)
    assert js.status_code == 200
    assert js.json()["formula"]["product_type"] == "edp"


def test_library_csv_endpoint():
    r = client.get("/api/library.csv", params={"kind": "molecules"})
    assert r.status_code == 200
    assert "smiles" in r.text
