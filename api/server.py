"""OLFACTRA local API (FastAPI).

Run locally:

    uvicorn api.server:app --reload --port 8010
    curl 'http://127.0.0.1:8010/api/recommend?mood=sleep&space=bedroom&style=floral'

The API is read-mostly and stateless: it exposes the same libraries the web
workbench ships with, so a lab server can serve the engine to other tools. No
user data is stored, and nothing is sent anywhere else.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field

from olfactra_core import (
    __version__, atlas, compare, descriptors, exporter, molecule, provenance, recommender, studio,
)

app = FastAPI(
    title="OLFACTRA API",
    version=__version__,
    description=(
        "Clean-room MIT fragrance intelligence: scent history atlas, public molecule "
        "library, dilution studio with a safety gate, and an interpretable accord "
        "recommender. Proposes candidates — never replaces sensory or GC-MS validation."
    ),
    license_info={"name": "MIT", "url": "https://github.com/sunbear5020/olfactra"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class FormulaSpec(BaseModel):
    """One side of a comparison: a formulation request plus an optional name."""

    product_type: str = Field("edp", description="reed_diffuser, room_spray, linen_mist, eau_de_cologne, edt, edp, body_oil, solid_perfume")
    volume_ml: float = Field(50.0, gt=0, le=5000)
    load_pct: float | None = Field(None, gt=0, le=100)
    accord: dict[str, float] = Field(
        default_factory=lambda: {"linalool": 40, "geraniol": 30, "cedrol": 30},
        description="molecule_id -> share of the concentrate (%)",
    )
    label: str | None = Field(None, description="이름(선택). 없으면 제형 이름을 씁니다.")


class CompareRequest(BaseModel):
    a: FormulaSpec
    b: FormulaSpec


class FormulateRequest(BaseModel):
    product_type: str = Field("edp", description="reed_diffuser, room_spray, linen_mist, eau_de_cologne, edt, edp, body_oil, solid_perfume")
    volume_ml: float = Field(50.0, gt=0, le=5000)
    load_pct: float | None = Field(None, gt=0, le=100)
    accord: dict[str, float] = Field(
        default_factory=lambda: {"linalool": 40, "geraniol": 30, "cedrol": 30},
        description="molecule_id -> share of the concentrate (%)",
    )


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": __version__,
        "schema_version": exporter.SCHEMA_VERSION,
        "license": "MIT",
        "indicators": len(provenance.INDICATORS),
        "molecules": len(molecule.MOLECULES),
        "atlas_entries": len(atlas.ATLAS),
        "accords": len(recommender.ACCORDS),
        "product_types": len(studio.PRODUCT_TYPES),
    }


@app.get("/api/provenance")
def get_provenance(kind: str | None = Query(None, pattern="^(measured|derived|heuristic)$"),
                   context: str | None = None) -> dict[str, Any]:
    """The indicator registry: formula, source, evidence class and boundary."""
    payload = provenance.as_dict()
    items = payload["indicators"]
    if kind:
        items = [i for i in items if i["kind"] == kind]
    if context:
        items = [i for i in items if context in i["used_in"]]
    payload["indicators"] = items
    payload["descriptors"] = descriptors.as_dict()
    payload["returned"] = len(items)
    return payload


@app.get("/api/descriptors")
def get_descriptors() -> dict[str, Any]:
    """Derived molecular descriptors (Crippen LogP, Ertl TPSA) and their method."""
    return {
        **descriptors.as_dict(),
        "molecules": {m.id: descriptors.profile(m.id) for m in molecule.MOLECULES},
    }


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "version": __version__,
        "dimensions": recommender.dimensions(),
        "products": [p.as_dict() for p in studio.product_types()],
        "families": [
            {"id": f, "label": molecule.FAMILY_LABELS_KO[f]} for f in molecule.FAMILIES
        ],
        "notes": [{"id": n, "label": molecule.NOTE_LABELS_KO[n]} for n in molecule.NOTES],
        "categories": [{"id": k, "label": v} for k, v in atlas.CATEGORIES.items()],
        "stats": {
            "molecules": molecule.library_stats(),
            "atlas": atlas.stats(),
        },
    }


@app.get("/api/molecules")
def list_molecules(q: str | None = None, note: str | None = None,
                   family: str | None = None) -> list[dict]:
    items = molecule.find(q) if q else list(molecule.all_molecules())
    if note:
        items = [m for m in items if m.note == note]
    if family:
        items = [m for m in items if m.families.get(family, 0) >= 0.2]
    return [m.as_dict() for m in items]


@app.get("/api/molecules/{molecule_id}")
def get_molecule(molecule_id: str, top_k: int = Query(5, ge=1, le=20)) -> dict:
    try:
        m = molecule.get(molecule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        **m.as_dict(),
        "similar": [
            {"id": s.id, "name_ko": s.name_ko, "score": score}
            for s, score in molecule.similar(m.id, top_k)
        ],
        "atlas_entries": [e.id for e in atlas.by_molecule(m.id)],
    }


@app.get("/api/molecules/{molecule_id}/similar")
def get_similar(molecule_id: str, top_k: int = Query(5, ge=1, le=20)) -> list[dict]:
    try:
        return [
            {"id": s.id, "name_ko": s.name_ko, "score": score, "note": s.note}
            for s, score in molecule.similar(molecule_id, top_k)
        ]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/atlas")
def list_atlas(q: str | None = None, category: str | None = None) -> list[dict]:
    items = atlas.search(q) if q else atlas.by_category(category)
    if q and category:
        items = [e for e in items if e.category == category]
    return [e.as_dict() for e in sorted(items, key=lambda e: e.year)]


@app.get("/api/atlas/{entry_id}")
def get_atlas_entry(entry_id: str) -> dict:
    try:
        entry = atlas.get(entry_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        **entry.as_dict(),
        "molecules_detail": [molecule.get(m).as_dict() for m in entry.molecules],
    }


@app.get("/api/accords")
def list_accords() -> list[dict]:
    return [a.as_dict() for a in recommender.accords()]


@app.get("/api/recommend")
def recommend(
    mood: str | None = None,
    season: str | None = None,
    space: str | None = None,
    style: str | None = None,
    limit: int = Query(3, ge=1, le=15),
) -> dict:
    try:
        picks = recommender.recommend(
            mood=mood, season=season, space=space, style=style, limit=limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"query": {"mood": mood, "season": season, "space": space, "style": style},
            "results": [p.as_dict() for p in picks]}


@app.get("/api/recommend/{accord_id}")
def recommend_one(accord_id: str, product_type: str | None = None,
                  volume_ml: float = 50.0) -> dict:
    try:
        accord = recommender.get_accord(accord_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown accord: {accord_id}") from exc
    product = product_type or accord.product_hint
    formula = studio.formulate(product, volume_ml, None, accord.materials)
    return {"accord": accord.as_dict(), "formula": formula.as_dict()}


@app.post("/api/formulate")
def formulate(req: FormulateRequest) -> dict:
    try:
        formula = studio.formulate(req.product_type, req.volume_ml, req.load_pct, req.accord)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return formula.as_dict()


@app.post("/api/recipe")
def recipe(req: FormulateRequest, fmt: str = Query("json", pattern="^(csv|json|md)$")) -> Response:
    try:
        formula = studio.formulate(req.product_type, req.volume_ml, req.load_pct, req.accord)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if fmt == "csv":
        return PlainTextResponse(
            exporter.formula_to_csv(formula),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="olfactra-recipe.csv"'},
        )
    if fmt == "md":
        return PlainTextResponse(
            exporter.formula_to_markdown(formula),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="olfactra-report.md"'},
        )
    return Response(
        exporter.formula_to_json(formula),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="olfactra-recipe.json"'},
    )


@app.post("/api/compare")
def compare_formulas(req: CompareRequest, fmt: str = Query("json", pattern="^(json|md)$")) -> Response:
    """Compare two formulas: note pyramid, property profile and safety headroom."""
    try:
        a = studio.formulate(req.a.product_type, req.a.volume_ml, req.a.load_pct, req.a.accord)
        b = studio.formulate(req.b.product_type, req.b.volume_ml, req.b.load_pct, req.b.accord)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = compare.compare_formulas(
        a, b,
        label_a=req.a.label or a.product_type.name_ko,
        label_b=req.b.label or b.product_type.name_ko,
    )
    if fmt == "md":
        return PlainTextResponse(
            compare.markdown(result),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="olfactra-compare.md"'},
        )
    return Response(json.dumps(result.as_dict(), ensure_ascii=False), media_type="application/json")


@app.get("/api/library.csv", response_class=PlainTextResponse)
def library_csv(kind: str = Query("molecules", pattern="^(molecules|atlas)$")) -> PlainTextResponse:
    body = exporter.molecule_table_csv() if kind == "molecules" else exporter.atlas_table_csv()
    return PlainTextResponse(body, media_type="text/csv; charset=utf-8")
