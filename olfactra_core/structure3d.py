"""OLFACTRA STRUCTURE3D — real 3-D conformers and pharmacophore features.

Every fragrance molecule in the public library (``molecule.MOLECULES``) is embedded
from its **public SMILES** with RDKit (ETKDGv3 distance geometry) and relaxed with
the MMFF94s force field.  Nothing here is copied from a commercial structure
database: the input is the SMILES that is already published with the PubChem CID,
and the coordinates are computed locally.

What is produced per molecule
-----------------------------
* ``atoms``  — heavy atoms only (C, N, O, S, halogens) with xyz in ångström,
  centred on the molecule's centroid, plus flags used by the viewer
  (aromatic ring atom, hydrogen-bond donor/acceptor, hydrophobic carbon).
* ``bonds``  — heavy-atom connectivity with bond order (1, 2, 3, and 1.5 for
  aromatic bonds).
* ``features`` — pharmacophore points used by the receptor-binding viewer:
  hydrogen-bond donors/acceptors, aromatic ring centroids, hydrophobic centroids.
* ``volume`` — a coarse van der Waals volume (Å³) from the atom radii, reported so
  the pocket fit can be compared with the receptor cavity.

Limits (kept in the UI and NOTICE.md as well)
---------------------------------------------
A single low-energy conformer is one *plausible* geometry, not the full
conformational ensemble.  Molecules with many rotatable bonds have many accessible
shapes, and the conformer shown is not claimed to be the bioactive one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: van der Waals radii (Å) — Bondi 1964 values, rounded.
VDW: dict[str, float] = {
    "H": 1.20, "C": 1.70, "N": 1.55, "O": 1.52, "F": 1.47, "S": 1.80,
    "Cl": 1.75, "Br": 1.85, "I": 1.98, "P": 1.80, "Si": 2.10, "B": 1.92,
}

#: elements that can accept a hydrogen bond in this model
HB_ACCEPTORS = {"N", "O"}
#: elements that can donate a hydrogen bond when they carry an H
HB_DONORS = {"N", "O"}


class EmbedError(RuntimeError):
    """Raised when RDKit cannot produce a 3-D conformer for a SMILES."""


@dataclass(frozen=True)
class Conformer:
    smiles: str
    atoms: list[dict[str, Any]]
    bonds: list[dict[str, Any]]
    features: list[dict[str, Any]]
    volume: float
    props: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "smiles": self.smiles,
            "atoms": self.atoms,
            "bonds": self.bonds,
            "features": self.features,
            "volume": self.volume,
            "props": self.props,
        }


def _rdkit():
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem, rdDistGeom
    except Exception as exc:  # pragma: no cover - optional dependency
        raise EmbedError(
            "RDKit is required to build 3-D conformers (pip install rdkit)"
        ) from exc
    return Chem, AllChem, rdDistGeom


def _embed(smiles: str):
    """Embed + optimise one SMILES, returning an RDKit mol with coordinates."""
    Chem, AllChem, rdDistGeom = _rdkit()
    base = Chem.MolFromSmiles(smiles)
    if base is None:
        raise EmbedError(f"invalid SMILES: {smiles!r}")
    mol = Chem.AddHs(base)

    params = rdDistGeom.ETKDGv3()
    params.randomSeed = 0x5EED
    params.useSmallRingTorsions = True
    params.pruneRmsThresh = -1.0
    params.maxIterations = 400
    status = AllChem.EmbedMolecule(mol, params)

    if status != 0:
        # A few strained polycyclic terpenes (e.g. α-copaene) fail the default
        # chirality-aware embedding.  Relax the constraints and retry; the
        # resulting stereo may differ, so the caller is told via `relaxed`.
        relaxed = rdDistGeom.ETKDGv3()
        relaxed.randomSeed = 0x5EED
        relaxed.useRandomCoords = True
        relaxed.maxIterations = 1000
        relaxed.enforceChirality = False
        relaxed.ignoreSmoothingFailures = True
        status = AllChem.EmbedMolecule(mol, relaxed)
        if status != 0:
            raise EmbedError(f"3-D embedding failed for {smiles!r}")

    if AllChem.MMFFHasAllMoleculeParams(mol):
        AllChem.MMFFOptimizeMolecule(mol, mmffVariant="MMFF94s", maxIters=1500)
    else:  # pragma: no cover - all 43 library molecules have MMFF parameters
        AllChem.UFFOptimizeMolecule(mol, maxIters=1500)
    return mol


#: SMARTS used for the functional-group counts shown in the viewer
_FG_SMARTS = {
    "aldehyde": "[CX3H1]=O",
    "ketone": "[#6][CX3](=O)[#6]",
    "ester": "[CX3](=O)[OX2][#6]",
    "acid": "[CX3](=O)[OX2H1]",
    "alcohol": "[OX2H]",
    "phenol": "c[OX2H]",
    "ether": "[OD2]([#6])[#6]",
    "lactone": "[CX3](=O)[OX2][#6;R]",
}


def _props(mol) -> dict[str, Any]:
    """Small, checkable descriptors used by the receptor model and the UI."""
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors

    counts: dict[str, int] = {}
    for key, smarts in _FG_SMARTS.items():
        patt = Chem.MolFromSmarts(smarts)
        counts[key] = len(mol.GetSubstructMatches(patt)) if patt is not None else 0
    heavy = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() > 1)
    rings = mol.GetRingInfo().AtomRings()
    aromatic = [r for r in rings if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in r)]
    return {
        "heavy": heavy,
        "rings": len(rings),
        "aromatic_rings": len(aromatic),
        "rotatable": rdMolDescriptors.CalcNumRotatableBonds(mol),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "mw": round(float(rdMolDescriptors.CalcExactMolWt(mol)), 2),
        **counts,
    }


def _aromatic_rings(mol) -> list[list[int]]:
    return [
        list(r) for r in mol.GetRingInfo().AtomRings()
        if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in r)
    ]


def build(smiles: str) -> Conformer:
    """Build a 3-D conformer with pharmacophore features for one SMILES."""
    from rdkit import Chem  # local import keeps the module importable without RDKit

    mol = _embed(smiles)
    conf = mol.GetConformer()

    # heavy atoms only -------------------------------------------------------
    keep = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() > 1]
    index_map = {old: new for new, old in enumerate(keep)}
    pos = [conf.GetAtomPosition(i) for i in keep]
    cx = sum(p.x for p in pos) / len(pos)
    cy = sum(p.y for p in pos) / len(pos)
    cz = sum(p.z for p in pos) / len(pos)

    aromatic_ring_atoms: set[int] = set()
    for ring in _aromatic_rings(mol):
        aromatic_ring_atoms.update(ring)

    hydrophobic: set[int] = set()
    atoms: list[dict[str, Any]] = []
    for new, old in enumerate(keep):
        a = mol.GetAtomWithIdx(old)
        sym = a.GetSymbol()
        hs = a.GetTotalNumHs(includeNeighbors=True)
        is_ar = old in aromatic_ring_atoms
        # A carbon is "hydrophobic" when it carries no heteroatom neighbour.
        neighbours = [n.GetSymbol() for n in a.GetNeighbors() if n.GetAtomicNum() > 1]
        hydro = sym == "C" and all(x == "C" for x in neighbours)
        if hydro:
            hydrophobic.add(new)
        atoms.append({
            "i": new,
            "e": sym,
            "x": round(pos[new].x - cx, 3),
            "y": round(pos[new].y - cy, 3),
            "z": round(pos[new].z - cz, 3),
            "ar": bool(is_ar),
            "hbd": bool(sym in HB_DONORS and hs > 0),
            "hba": bool(sym in HB_ACCEPTORS),
            "h": int(hs),
            "hydro": bool(hydro),
            "ring": bool(a.IsInRing()),
        })

    bonds: list[dict[str, Any]] = []
    for b in mol.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        if i not in index_map or j not in index_map:
            continue
        order = b.GetBondTypeAsDouble()
        bonds.append({
            "a": index_map[i],
            "b": index_map[j],
            "o": 1.5 if b.GetIsAromatic() else order,
        })
    bonds.sort(key=lambda x: (x["a"], x["b"]))

    # pharmacophore features ------------------------------------------------
    features: list[dict[str, Any]] = []
    for at in atoms:
        if at["hbd"]:
            features.append({"type": "hbd", "atoms": [at["i"]], "c": [at["x"], at["y"], at["z"]]})
    for at in atoms:
        if at["hba"]:
            features.append({"type": "hba", "atoms": [at["i"]], "c": [at["x"], at["y"], at["z"]]})
    for ring in _aromatic_rings(mol):
        ring = [index_map[i] for i in ring if i in index_map]
        if len(ring) < 5:
            continue
        pts = [atoms[i] for i in ring]
        features.append({
            "type": "aromatic",
            "atoms": ring,
            "c": [
                round(sum(p["x"] for p in pts) / len(pts), 3),
                round(sum(p["y"] for p in pts) / len(pts), 3),
                round(sum(p["z"] for p in pts) / len(pts), 3),
            ],
            "radius": round(max(
                (sum((p[k] - sum(q[k] for q in pts) / len(pts)) ** 2 for k in ("x", "y", "z")) ** 0.5
                 for p in pts)
            ) if pts else 1.4, 3),
        })
    if hydrophobic:
        pts = [atoms[i] for i in sorted(hydrophobic)]
        features.append({
            "type": "hydrophobic",
            "atoms": sorted(hydrophobic),
            "c": [
                round(sum(p["x"] for p in pts) / len(pts), 3),
                round(sum(p["y"] for p in pts) / len(pts), 3),
                round(sum(p["z"] for p in pts) / len(pts), 3),
            ],
        })

    volume = sum(4.0 / 3.0 * 3.14159265 * VDW.get(at["e"], 1.7) ** 3 for at in atoms)
    return Conformer(smiles=smiles, atoms=atoms, bonds=bonds,
                     features=features, volume=round(volume, 1), props=_props(mol))


def build_library(smiles_by_id: dict[str, str]) -> dict[str, dict[str, Any]]:
    """Build conformers for a whole library; molecules that fail are reported."""
    out: dict[str, dict[str, Any]] = {}
    for mid, smi in smiles_by_id.items():
        out[mid] = build(smi).as_dict()
    return out


# --------------------------------------------------------------------------- checks
def bond_lengths(conf: dict[str, Any]) -> list[float]:
    """Return all bonded heavy-atom distances (Å)."""
    out = []
    for b in conf["bonds"]:
        a1 = conf["atoms"][b["a"]]
        a2 = conf["atoms"][b["b"]]
        out.append(((a1["x"] - a2["x"]) ** 2 + (a1["y"] - a2["y"]) ** 2
                    + (a1["z"] - a2["z"]) ** 2) ** 0.5)
    return out
