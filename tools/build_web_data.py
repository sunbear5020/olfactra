#!/usr/bin/env python3
"""Build the static workbench data file from the Python library (single source of truth).

    python tools/build_web_data.py                      # → web/data.js (this repository)
    python tools/build_web_data.py --out ../sunbear5020.github.io/olfactra/data.js   # live site copy

The generated `data.js` assigns ``window.OLFACTRA_DATA`` so the page works from
``file://`` as well as GitHub Pages. Molecule structures are rendered to SVG from
the public SMILES when RDKit is available (`pip install rdkit`); the same RDKit
build also produces the real 3-D conformer of every molecule and the schematic
receptor-docking poses used by the MOLECULE 3-D viewer. Without RDKit the file is
still complete, only the structure drawings, 3-D coordinates and poses are omitted.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from olfactra_core import (  # noqa: E402
    __version__, atlas, docking, exporter, molecule, pyrfume, recommender, structure3d, studio,
)

#: text used in the UI and NOTICE — kept in one place so they cannot drift apart
SCIENCE_3D_KO = (
    "이 3D 결합 모형은 Class A GPCR 후각 수용체의 공개된 구조 원리(7회 관통 나선 다발)를 "
    "바탕으로 한 교육·탐색용 모식적 도킹입니다. 잔기는 실제 PDB 좌표가 아니라 "
    "Ballesteros–Weinstein 번호로 표시한 모식 잔기이고, 거리는 그 모식 좌표에서 계산한 값입니다. "
    "실제 wet-lab 결합 친화도(Kd·EC50)나 임상·독성 검증을 대체하지 않습니다."
)


def structure_svg(smiles: str, width: int = 300, height: int = 190) -> str | None:
    try:
        from rdkit import Chem
        from rdkit.Chem.Draw import rdMolDraw2D
    except Exception:  # pragma: no cover - optional dependency
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.bondLineWidth = 1.7
    opts.minFontSize = 13
    opts.maxFontSize = 15
    opts.clearBackground = False
    opts.useBWAtomPalette()
    opts.padding = 0.08
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    # strip the xml prolog/comment that RDKit prepends
    start = svg.find("<svg")
    return svg[start:].strip() if start >= 0 else svg


def build(include_svg: bool = True, include_3d: bool = True, verbose: bool = True) -> dict:
    molecules = []
    conformers: dict[str, dict] = {}
    for m in molecule.MOLECULES:
        payload = m.as_dict()
        payload["pyrfume"] = pyrfume.material_evidence(m.id, m.name_ko)
        if include_svg:
            svg = structure_svg(m.smiles)
            if svg:
                payload["svg"] = svg
        if include_3d:
            try:
                conf = structure3d.build(m.smiles).as_dict()
            except structure3d.EmbedError as exc:  # pragma: no cover - defensive
                if verbose:
                    print(f"  ! no 3-D conformer for {m.id}: {exc}")
            else:
                conf.pop("smiles", None)
                conformers[m.id] = conf
                payload["conformer"] = conf
        molecules.append(payload)

    poses: dict[str, dict] = {}
    if include_3d and conformers:
        t0 = time.time()
        for receptor in docking.receptors():
            for mid, conf in conformers.items():
                pose = docking.dock(receptor.id, mid, conf)
                poses.setdefault(mid, {})[receptor.id] = pose.as_dict()
            if verbose:
                print(f"  docked {len(conformers)} molecules into {receptor.name} "
                      f"({time.time() - t0:.0f}s)")
        # the receptor this molecule fits best, used as the viewer's default
        for mid, by_rec in poses.items():
            best = max(by_rec.values(), key=lambda p: p["rank"])
            for m in molecules:
                if m["id"] == mid:
                    m["pose_default"] = best["receptor"]
                    break

    cov = pyrfume.coverage()
    return {
        "meta": {
            "version": __version__,
            "generated": date.today().isoformat(),
            "license": "MIT",
            "copyright": exporter.PROVENANCE["copyright"],
            "homepage": "https://sunbear5020.github.io/olfactra/",
            "source": "https://github.com/sunbear5020/olfactra",
            "science_boundary": exporter.PROVENANCE["science_boundary"],
            "safety_boundary": exporter.PROVENANCE["safety_boundary"],
            "science_3d": SCIENCE_3D_KO,
            "families": [{"id": f, "label": molecule.FAMILY_LABELS_KO[f]} for f in molecule.FAMILIES],
            "notes": [{"id": n, "label": molecule.NOTE_LABELS_KO[n]} for n in molecule.NOTES],
            "dimensions": recommender.dimensions(),
            "categories": [{"id": k, "label": v} for k, v in atlas.CATEGORIES.items()],
            "style_families": recommender.STYLE_FAMILIES,
            "space_notes": recommender.SPACE_NOTES,
            "pyrfume": {
                "coverage": cov,
                "sources": pyrfume.sources(),
                "license": pyrfume.bundle().get("license", {}),
                "generated": pyrfume.bundle().get("generated"),
                "note": (
                    "Pyrfume(MIT)에 실린 Keller & Vosshall 2016 · Dravnieks 1985 · "
                    "Mainland et al. 2015 데이터를 PubChem CID로 매칭한 단품 측정값입니다. "
                    "혼합물의 향은 성분의 합이 아니므로, 완성된 아코드의 쾌적도를 예측하지 않습니다."
                ),
            },
            "stats": {
                "molecules": molecule.library_stats(),
                "atlas": atlas.stats(),
                "accords": len(recommender.ACCORDS),
                "products": len(studio.PRODUCT_TYPES),
                "conformers": len(conformers),
                "poses": sum(len(v) for v in poses.values()),
                "pyrfume_matched": cov.get("any", 0),
                "receptors": len(docking.RECEPTORS),
            },
        },
        "molecules": molecules,
        "accords": [a.as_dict() for a in recommender.accords()],
        "atlas": [e.as_dict() for e in atlas.timeline()],
        "products": [p.as_dict() for p in studio.product_types()],
        "allergens": list(studio.EU_DECLARABLE_ALLERGENS),
        "pet_flags": studio.CHILD_PET_FLAGS,
        "receptors": docking.receptor_payload() if include_3d else [],
        "poses": poses,
    }


def _default_out() -> Path:
    """Prefer the workbench copy inside this repository, fall back to the website folder."""
    if (ROOT / "web").is_dir():
        return ROOT / "web" / "data.js"
    return ROOT.parent / "sunbear5020.github.io" / "olfactra" / "data.js"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(_default_out()))
    ap.add_argument("--no-svg", action="store_true", help="skip RDKit structure drawings")
    ap.add_argument("--no-3d", action="store_true", help="skip 3-D conformers and docking poses")
    args = ap.parse_args()

    data = build(include_svg=not args.no_svg, include_3d=not args.no_3d)
    body = "/* OLFACTRA data — generated by tools/build_web_data.py; do not edit by hand. */\n"
    body += "window.OLFACTRA_DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    with_svg = sum(1 for m in data["molecules"] if m.get("svg"))
    with_3d = sum(1 for m in data["molecules"] if m.get("conformer"))
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB) · "
          f"{len(data['molecules'])} molecules ({with_svg} with structure, {with_3d} with 3-D), "
          f"{len(data['atlas'])} atlas entries, {len(data['accords'])} accords, "
          f"{len(data['receptors'])} receptors, "
          f"{sum(len(v) for v in data['poses'].values())} poses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
