#!/usr/bin/env python3
"""Build the derived molecular descriptors (LogP, TPSA, H-bond counts).

    python tools/build_descriptors.py                 # → olfactra_core/datasets/descriptors_rdkit.json
    python tools/build_descriptors.py --check         # verify the committed file still matches

Everything here is computed **locally from the public SMILES** already published
with each PubChem CID, so no proprietary descriptor table is used:

* ``logp`` — RDKit ``Descriptors.MolLogP`` (Crippen 1988 atomic contributions,
  Wildman & Crippen 1999).
* ``tpsa`` — RDKit ``rdMolDescriptors.CalcTPSA`` (Ertl, Rohde & Selzer 2000).
* ``hbd`` / ``hba`` / ``rotb`` — standard RDKit counts (Lipinski / rotatable-bond
  definition), used only as explanatory context.

These are **estimates from a contribution model**, not measurements.  The file
records the RDKit version and the method names so a reader can reproduce them.
The library itself never needs RDKit at runtime: it reads this JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from olfactra_core import molecule  # noqa: E402

OUT = ROOT / "olfactra_core" / "datasets" / "descriptors_rdkit.json"

METHODS = {
    "logp": "RDKit Descriptors.MolLogP — Crippen (1988) atomic contributions, Wildman & Crippen (1999) corrections",
    "tpsa": "RDKit rdMolDescriptors.CalcTPSA — Ertl, Rohde & Selzer (2000) fragment contributions",
    "hbd_hba": "RDKit CalcNumHBD / CalcNumHBA — Lipinski donor/acceptor definition (N, O, NH, OH)",
    "rotb": "RDKit CalcNumRotatableBonds — non-terminal single bonds, amide bonds excluded",
}


def build() -> dict:
    try:
        import rdkit
        from rdkit import Chem
        from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors
    except Exception as exc:  # pragma: no cover - optional dependency
        raise SystemExit(f"RDKit is required to rebuild descriptors: {exc}")

    molecules: dict[str, dict] = {}
    for m in molecule.MOLECULES:
        mol = Chem.MolFromSmiles(m.smiles)
        if mol is None:
            raise SystemExit(f"invalid SMILES for {m.id}: {m.smiles!r}")
        molecules[m.id] = {
            "cid": m.pubchem_cid,
            "smiles": m.smiles,
            "logp": round(float(Descriptors.MolLogP(mol)), 2),
            "tpsa": round(float(rdMolDescriptors.CalcTPSA(mol)), 2),
            "hbd": int(rdMolDescriptors.CalcNumHBD(mol)),
            "hba": int(rdMolDescriptors.CalcNumHBA(mol)),
            "rotb": int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        }
    return {
        "schema_version": "0.2.0",
        "generated": date.today().isoformat(),
        "source": "computed from the public SMILES of each PubChem CID, locally",
        "tool": f"RDKit {rdkit.__version__}",
        "methods": METHODS,
        "molecules": molecules,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="compare the committed file with a fresh build instead of writing")
    args = ap.parse_args()

    payload = build()
    body = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"missing {OUT}")
            return 1
        current = json.loads(OUT.read_text(encoding="utf-8"))
        drift = sorted(
            mid for mid in payload["molecules"]
            if current.get("molecules", {}).get(mid) != payload["molecules"][mid]
        )
        if drift:
            print(f"{len(drift)} molecules differ: {drift[:8]}")
            return 1
        print(f"descriptors are reproducible for {len(payload['molecules'])} molecules")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT} ({len(payload['molecules'])} molecules, RDKit {payload['tool'].split()[-1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
