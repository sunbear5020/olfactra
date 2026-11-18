"""3-D conformers and the schematic receptor-docking model.

These tests check the *properties that must hold if the geometry is real*: bond
lengths inside a plausible range, a centred molecule, orthonormal rotations,
H-bond distances inside the hydrogen-bond window, and a deterministic result.
They do not (and cannot) test "correct binding affinity" — this model has no
affinity to test.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from olfactra_core import docking, molecule, structure3d


@pytest.fixture(scope="module")
def conformers():
    return {m.id: structure3d.build(m.smiles).as_dict() for m in molecule.MOLECULES}


def test_every_library_molecule_has_a_conformer(conformers):
    assert len(conformers) == len(molecule.MOLECULES) == 43
    for mid, conf in conformers.items():
        assert conf["atoms"], mid
        assert conf["bonds"], mid


def test_heavy_atom_counts_match_the_smiles(conformers):
    for m in molecule.MOLECULES:
        conf = conformers[m.id]
        # count non-hydrogen atoms directly from the library formula
        expected = sum(
            int("".join(ch for ch in part if ch.isdigit()) or 1)
            for part in _split_formula(m.formula)
            if part[0] != "H"
        )
        assert len(conf["atoms"]) == expected, m.id


def _split_formula(formula: str) -> list[str]:
    out, buf = [], ""
    for ch in formula:
        if ch.isupper() and buf:
            out.append(buf)
            buf = ch
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def test_bond_lengths_are_chemically_plausible(conformers):
    for mid, conf in conformers.items():
        lengths = structure3d.bond_lengths(conf)
        assert lengths, mid
        assert min(lengths) > 0.9, (mid, min(lengths))
        assert max(lengths) < 1.75, (mid, max(lengths))


def test_conformers_are_centred_and_finite(conformers):
    for mid, conf in conformers.items():
        coords = np.array([[a["x"], a["y"], a["z"]] for a in conf["atoms"]])
        assert np.isfinite(coords).all(), mid
        assert abs(coords.mean(axis=0)).max() < 0.02, mid


def test_conformer_carries_functional_group_props(conformers):
    assert conformers["vanillin"]["props"]["aldehyde"] == 1
    assert conformers["vanillin"]["props"]["phenol"] == 1
    assert conformers["linalyl acetate"]["props"]["ester"] == 1
    assert conformers["coumarin"]["props"]["lactone"] >= 1
    assert conformers["linalool"]["props"]["alcohol"] == 1
    assert all(c["volume"] > 0 for c in conformers.values())


def test_pharmacophore_features_are_present(conformers):
    linalool = conformers["linalool"]["features"]
    kinds = {f["type"] for f in linalool}
    assert {"hbd", "hba", "hydrophobic"} <= kinds
    vanillin = conformers["vanillin"]["features"]
    assert "aromatic" in {f["type"] for f in vanillin}


# --------------------------------------------------------------------- receptors
def test_four_receptors_with_seven_helices_each():
    assert [r.id for r in docking.RECEPTORS] == ["or1a1", "or2j3", "or5an1", "or1g1"]
    for rec in docking.RECEPTORS:
        assert len(rec.helices) == 7
        assert [h.name for h in rec.helices] == [f"TM{i}" for i in range(1, 8)]
        assert 10 <= len(rec.residues) <= 13
        labels = [r.label for r in rec.residues]
        assert len(labels) == len(set(labels))


def test_residues_line_the_cavity():
    for rec in docking.RECEPTORS:
        centre = np.array(rec.pocket_center)
        for res in rec.residue_positions():
            d = float(np.linalg.norm(np.array(res["pos"]) - centre))
            assert rec.pocket_radius * 0.7 <= d <= rec.pocket_radius * 1.7, (rec.id, res["label"], d)


# -------------------------------------------------------------------------- poses
@pytest.fixture(scope="module")
def poses(conformers):
    return {
        (rec.id, mid): docking.dock(rec.id, mid, conf).as_dict()
        for rec in docking.RECEPTORS
        for mid, conf in conformers.items()
    }


def test_every_molecule_has_a_pose_in_every_receptor(poses, conformers):
    assert len(poses) == 4 * len(conformers) == 172
    for (rid, mid), pose in poses.items():
        assert 0 <= pose["fit"] <= 100, (rid, mid)
        assert len(pose["interactions"]) <= 8
        assert pose["receptor"] == rid and pose["molecule"] == mid


def test_rotations_are_rigid(poses):
    for (rid, mid), pose in poses.items():
        R = np.array(pose["rotation"])
        assert np.allclose(R @ R.T, np.eye(3), atol=1e-3), (rid, mid)
        assert math.isclose(float(np.linalg.det(R)), 1.0, abs_tol=1e-3), (rid, mid)


def test_interaction_distances_fall_in_their_windows(poses):
    windows = {"hbond": (2.5, 3.7), "hydrophobic": (3.1, 4.7), "pi": (3.2, 5.1)}
    for (rid, mid), pose in poses.items():
        for it in pose["interactions"]:
            lo, hi = windows[it["kind"]]
            assert lo <= it["distance"] <= hi, (rid, mid, it)


def test_poses_are_deterministic(conformers):
    a = docking.dock("or1a1", "linalool", conformers["linalool"]).as_dict()
    b = docking.dock("or1a1", "linalool", conformers["linalool"]).as_dict()
    assert a["rotation"] == b["rotation"]
    assert a["translation"] == b["translation"]
    assert a["fit"] == b["fit"]


def test_chemotype_heuristic_matches_the_reported_ligand_classes(poses):
    # muscone (a macrocyclic musk) should rank highest in the large musk pocket
    ranking = {rid: poses[(rid, "muscone")]["rank"] for rid in ("or1a1", "or2j3", "or5an1", "or1g1")}
    assert max(ranking, key=ranking.get) == "or5an1"
    # an aldehyde (citral) should get more chemotype credit from OR2J3 than from the musk pocket
    assert poses[("or2j3", "citral")]["chemotype"] > poses[("or5an1", "citral")]["chemotype"]


def test_receptor_payload_is_serialisable():
    payload = docking.receptor_payload()
    assert len(payload) == 4
    for rec in payload:
        assert len(rec["helices"]) == 7
        assert rec["helices"][0]["path"]
        assert rec["residues"][0]["pos"]
