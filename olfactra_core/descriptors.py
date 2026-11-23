"""Derived molecular descriptors — LogP, TPSA and the H-bond/rotor counts.

Where the numbers come from
---------------------------
Every value is computed **locally from the public SMILES** published with each
PubChem CID and committed as ``datasets/descriptors_rdkit.json`` by
``tools/build_descriptors.py``.  Nothing is copied from a commercial descriptor
table, and the library does not need RDKit at runtime — it reads the JSON.

+-----------+-----------------------------------------------------------------+
| ``logp``  | Crippen (1988) atomic contributions, Wildman–Crippen (1999)      |
|           | corrections, via ``rdkit.Chem.Descriptors.MolLogP``             |
+-----------+-----------------------------------------------------------------+
| ``tpsa``  | Ertl, Rohde & Selzer (2000) fragment contributions, via          |
|           | ``rdkit.Chem.rdMolDescriptors.CalcTPSA``                        |
+-----------+-----------------------------------------------------------------+
| ``hbd``/  | Lipinski donor/acceptor counts (N, O, NH, OH)                    |
| ``hba``   |                                                                 |
+-----------+-----------------------------------------------------------------+
| ``rotb``  | rotatable (non-terminal, non-amide) single bonds                 |
+-----------+-----------------------------------------------------------------+

Science boundary
----------------
These are **estimates from a contribution model, not measurements**.  LogP here
is a calculated octanol–water partition coefficient (XLogP-style), not an
experimental value, and TPSA is a topological polar surface area computed from
2-D fragments — neither is a vapour pressure.  They are used to *describe* a
formula's molecular profile and to compare two formulas, not to predict how a
blend will smell or how fast it will evaporate.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent / "datasets" / "descriptors_rdkit.json"

#: which keys are shipped per molecule
FIELDS: tuple[str, ...] = ("logp", "tpsa", "hbd", "hba", "rotb")


@lru_cache(maxsize=1)
def _table() -> dict[str, Any]:
    if not DATA.exists():  # pragma: no cover - the file ships with the package
        return {"molecules": {}, "methods": {}}
    return json.loads(DATA.read_text(encoding="utf-8"))


def methods() -> dict[str, str]:
    return dict(_table().get("methods", {}))


def tool() -> str:
    return str(_table().get("tool", ""))


def coverage() -> dict[str, int]:
    return {"with_descriptors": len(_table().get("molecules", {}))}


def profile(molecule_id: str) -> dict[str, float]:
    """The committed descriptor row for one molecule (raises KeyError if absent)."""
    row = _table().get("molecules", {}).get(molecule_id)
    if row is None:
        raise KeyError(f"no committed descriptors for {molecule_id!r}")
    return {k: float(row[k]) for k in FIELDS}


def value(molecule_id: str, field: str) -> float:
    if field not in FIELDS:
        raise KeyError(f"unknown descriptor {field!r}; choose from {FIELDS}")
    return profile(molecule_id)[field]


def as_dict() -> dict[str, Any]:
    """Everything the web workbench and the provenance panel need."""
    table = _table()
    return {
        "schema_version": table.get("schema_version", "0.2.0"),
        "generated": table.get("generated"),
        "tool": table.get("tool"),
        "source": table.get("source"),
        "methods": table.get("methods", {}),
        "count": len(table.get("molecules", {})),
    }
