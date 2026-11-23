"""OLFACTRA DOCKING — schematic receptor–ligand binding for the 3-D viewer.

What this module is
-------------------
A **schematic, geometry-based** docking model for teaching and exploration. Each
of the four representative olfactory receptors is represented by

* an *idealised* 7-transmembrane (7-TM) α-helix bundle built from the published
  layout of class A GPCRs (TM3 facing the pocket, TM5/TM6/TM7 forming the roof of
  the cavity), and
* a set of 10–13 **model residues** placed at the class A pocket positions and
  named with Ballesteros–Weinstein numbers (e.g. ``Phe6.51``, ``Asn7.39``) rather
  than with residue numbers from a specific Protein Data Bank entry, because this
  project only uses structures and sequence-level facts that are public.

It is **not** a physics-based docking program. There is no force field, no
solvent model, no entropy term and no scoring function fitted to measured
affinities, so the numbers it prints are *not* Kd, EC50 or ΔG. The pose is the
best of a small deterministic rigid-body search of the molecule's single MMFF
conformer inside the cavity, scored by the number and type of contacts it can
make with the model residues. Read it as a picture of *how the chemistry could
fit*, not as a measurement.

Binding evidence
----------------
Where the human-receptor screening data of Mainland et al. (2015, Scientific
Data; distributed by Pyrfume) contains a measured response for the same odorant
and receptor, the viewer says so explicitly ("문헌 보고 활성"). The rest is
labelled as schematic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterable

import numpy as np

#: side-chain length (Å) from Cα to the functional group / ring centroid
SIDECHAIN: dict[str, float] = {
    "Ala": 1.5, "Val": 2.6, "Leu": 3.4, "Ile": 3.6, "Met": 4.1,
    "Phe": 4.4, "Tyr": 5.5, "Trp": 5.4, "Ser": 2.4, "Thr": 2.7,
    "Asn": 3.6, "Gln": 4.6, "Asp": 3.7, "Glu": 4.8, "His": 4.4,
    "Cys": 2.4, "Lys": 5.8, "Arg": 6.4,
}

#: residue chemistry used by the contact model
POLAR = {"Ser", "Thr", "Asn", "Gln", "Asp", "Glu", "Tyr", "His", "Cys"}
AROMATIC = {"Phe", "Tyr", "Trp", "His"}
HYDROPHOBIC = {"Val", "Leu", "Ile", "Met", "Phe", "Trp", "Cys", "Ala"}

AMINO_KO = {
    "Ala": "알라닌", "Val": "발린", "Leu": "류신", "Ile": "이소류신", "Met": "메티오닌",
    "Phe": "페닐알라닌", "Tyr": "티로신", "Trp": "트립토판", "Ser": "세린", "Thr": "트레오닌",
    "Asn": "아스파라긴", "Gln": "글루타민", "Asp": "아스파르트산", "Glu": "글루탐산",
    "His": "히스티딘", "Cys": "시스테인", "Lys": "라이신", "Arg": "아르기닌",
}


# --------------------------------------------------------------------------- geometry
@dataclass(frozen=True)
class Helix:
    """One idealised α-helix of the bundle."""
    name: str
    angle: float            # azimuth around the bundle axis (degrees)
    radius: float           # distance of the helix axis from the bundle axis (Å)
    tilt: float             # tilt of the helix axis away from the membrane normal (degrees)
    twist: float            # direction of the tilt (degrees)
    n_res: int = 28
    phase: float = 0.0      # start angle of the Cα spiral (degrees)

    def axis(self) -> np.ndarray:
        t = math.radians(self.tilt)
        p = math.radians(self.twist)
        return np.array([math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t)])

    def origin(self) -> np.ndarray:
        a = math.radians(self.angle)
        z = -0.5 * (self.n_res - 1) * 1.5
        return np.array([self.radius * math.cos(a), self.radius * math.sin(a), z])

    def point(self, t: float) -> np.ndarray:
        """Cα position at fractional height t (0 = intracellular end, 1 = top)."""
        axis = self.axis()
        step = (self.n_res - 1) * 1.5 * t
        base = self.origin() + axis * step
        # local frame perpendicular to the axis
        ref = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(ref, axis)) > 0.95:
            ref = np.array([1.0, 0.0, 0.0])
        u = np.cross(axis, ref)
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        ang = math.radians(self.phase) + 100.0 * (self.n_res - 1) * t
        r = 2.3
        return base + u * (r * math.cos(ang)) + v * (r * math.sin(ang))

    def path(self, steps: int = 34) -> list[list[float]]:
        return [[round(float(x), 2) for x in self.point(i / (steps - 1))] for i in range(steps)]


@dataclass(frozen=True)
class Residue:
    aa: str
    label: str          # e.g. "6.51"
    helix: str          # helix name the side chain hangs from
    t: float            # fractional position along that helix
    note: str = ""

    @property
    def full_label(self) -> str:
        return f"{self.aa}{self.label}"

    @property
    def kind(self) -> str:
        if self.aa in POLAR:
            return "polar"
        if self.aa in AROMATIC:
            return "aromatic"
        return "hydrophobic"


@dataclass(frozen=True)
class Receptor:
    id: str
    name: str
    gene: str
    class_name: str
    ligands_ko: str
    description_ko: str
    helices: tuple[Helix, ...]
    residues: tuple[Residue, ...]
    pocket_center: tuple[float, float, float]
    pocket_radius: float
    sign_odor_ko: str
    evidence_note_ko: str

    @lru_cache(maxsize=8)
    def residue_positions(self) -> list[dict[str, Any]]:
        """Place each model residue's side-chain functional group in the cavity.

        The side chain is drawn from its Cα toward the pocket centre and stopped
        on a shell of roughly ``pocket_radius`` around the centre, so the model
        residues line the cavity instead of filling it — which is what a ligand
        pocket looks like.  Residues with a long side chain reach a little
        further in; small ones stop short.
        """
        centre = np.array(self.pocket_center)
        by_name = {h.name: h for h in self.helices}
        out = []
        for res in self.residues:
            h = by_name[res.helix]
            # pick the point on this helix whose Cα sits nearest the pocket axis:
            # that is the rotamer whose side chain points into the cavity
            best_t, ca = res.t, h.point(res.t)
            best_d = float(np.linalg.norm(ca - centre))
            for step in range(-4, 5):
                t2 = min(0.97, max(0.5, res.t + 0.01 * step))
                p2 = h.point(t2)
                d2 = float(np.linalg.norm(p2 - centre))
                if d2 < best_d:
                    best_t, ca, best_d = t2, p2, d2
            v = centre - ca
            norm = np.linalg.norm(v)
            if norm < 1.0:                      # degenerate: fall back to the axis
                v = np.array([0.0, 0.0, 1.0])
                norm = 1.0
            length = SIDECHAIN.get(res.aa, 3.5)
            # the side-chain functional group lines a shell just inside the cavity
            shell = self.pocket_radius * (0.86 + 0.08 * (length / 4.4))
            reach = max(1.5, min(length, norm - shell))
            pos = ca + (v / norm) * reach
            out.append({
                "aa": res.aa,
                "aa_ko": AMINO_KO.get(res.aa, res.aa),
                "label": res.full_label,
                "bw": res.label,
                "helix": res.helix,
                "kind": res.kind,
                "polar": res.aa in POLAR,
                "aromatic": res.aa in AROMATIC,
                "hydrophobic": res.aa in HYDROPHOBIC,
                "note": res.note,
                "ca": [round(float(x), 2) for x in ca],
                "pos": [round(float(x), 2) for x in pos],
                "reach": round(float(reach), 2),
                "t": round(float(best_t), 3),
            })
        return out

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "gene": self.gene,
            "class": self.class_name,
            "ligands_ko": self.ligands_ko,
            "description_ko": self.description_ko,
            "sign_odor_ko": self.sign_odor_ko,
            "evidence_note_ko": self.evidence_note_ko,
            "pocket_center": list(self.pocket_center),
            "pocket_radius": self.pocket_radius,
            "helices": [{"name": h.name, "path": h.path()} for h in self.helices],
            "residues": self.residue_positions(),
        }


# --------------------------------------------------------------------------- receptors
_H = lambda name, angle, radius, tilt, twist, phase: Helix(  # noqa: E731
    name=name, angle=angle, radius=radius, tilt=tilt, twist=twist, phase=phase
)

# The four bundles differ in helix tilt/length and, more importantly, in the
# chemistry of the model pocket residues — that is what makes one molecule fit
# one receptor better than another in this model.
_HELICES_A = (
    _H("TM1", 12, 9.4, 6, 102, 0),
    _H("TM2", 64, 8.7, 7, 154, 40),
    _H("TM3", 119, 9.1, 5, 209, 80),
    _H("TM4", 171, 10.2, 7, 261, 120),
    _H("TM5", 226, 9.9, 6, 316, 160),
    _H("TM6", 286, 9.6, 8, 16, 200),
    _H("TM7", 340, 8.8, 6, 70, 240),
)

RECEPTORS: tuple[Receptor, ...] = (
    Receptor(
        id="or1a1",
        name="OR1A1",
        gene="OR1A1",
        class_name="Class A GPCR (7-TM)",
        ligands_ko="시트러스 · 테르펜 · 페놀류",
        description_ko=(
            "인간 후각 수용체 중 가장 널리 연구된 하나로, 시트러스·꽃·페놀 계열의 "
            "작은 테르펜과 방향족 분자에 반응하는 것으로 보고되었습니다. 포켓이 비교적 "
            "작고 소수성 잔기가 많아, 유연한 긴 사슬보다 단단한 고리형 분자가 잘 들어갑니다."
        ),
        sign_odor_ko="시트러스·테르펜",
        evidence_note_ko="Mainland 2015 데이터에 OR1A1 반응이 실측된 향료가 여러 개 있습니다.",
        helices=_HELICES_A,
        residues=(
            Residue("Phe", "3.32", "TM3", 0.74),
            Residue("Leu", "3.29", "TM3", 0.66),
            Residue("Ser", "3.36", "TM3", 0.80, "TM3의 극성 잔기"),
            Residue("Ile", "4.60", "TM4", 0.72),
            Residue("Leu", "5.42", "TM5", 0.70),
            Residue("Phe", "5.43", "TM5", 0.76),
            Residue("Ser", "5.46", "TM5", 0.82),
            Residue("Tyr", "6.48", "TM6", 0.74),
            Residue("Phe", "6.51", "TM6", 0.80),
            Residue("Phe", "6.52", "TM6", 0.86),
            Residue("Val", "6.55", "TM6", 0.68),
            Residue("Asn", "7.39", "TM7", 0.76),
            Residue("Ile", "7.43", "TM7", 0.70),
        ),
        pocket_center=(0.4, 0.2, 10.2),
        pocket_radius=5.0,
    ),
    Receptor(
        id="or2j3",
        name="OR2J3",
        gene="OR2J3",
        class_name="Class A GPCR (7-TM)",
        ligands_ko="그린 · 알데하이드 · C6 알코올",
        description_ko=(
            "풀잎·오이 계열의 '그린' 냄새에 해당하는 C6 알코올과 알데하이드에 반응하는 "
            "수용체로 보고되었습니다. 카보닐 산소를 잡아 주는 극성 잔기와, 탄화수소 꼬리를 "
            "감싸는 소수성 잔기가 함께 놓인 포켓으로 모식화했습니다."
        ),
        sign_odor_ko="그린·알데하이드",
        evidence_note_ko="Mainland 2015 데이터에 cis-3-hexen-1-ol·cinnamaldehyde의 OR2J3 반응이 기록되어 있습니다.",
        helices=_HELICES_A,
        residues=(
            Residue("Phe", "3.32", "TM3", 0.74),
            Residue("Leu", "3.29", "TM3", 0.64),
            Residue("Ser", "3.36", "TM3", 0.82, "알데하이드 카보닐과 수소결합"),
            Residue("Ile", "4.60", "TM4", 0.70),
            Residue("Leu", "5.42", "TM5", 0.68),
            Residue("Phe", "5.43", "TM5", 0.78),
            Residue("Thr", "5.46", "TM5", 0.84, "극성 앵커"),
            Residue("Tyr", "6.48", "TM6", 0.72),
            Residue("Phe", "6.51", "TM6", 0.82),
            Residue("Val", "6.55", "TM6", 0.66),
            Residue("Asn", "7.39", "TM7", 0.78),
            Residue("Ile", "7.43", "TM7", 0.70),
        ),
        pocket_center=(0.2, 0.6, 10.0),
        pocket_radius=5.2,
    ),
    Receptor(
        id="or5an1",
        name="OR5AN1",
        gene="OR5AN1",
        class_name="Class A GPCR (7-TM)",
        ligands_ko="머스크 · 대형 고리형",
        description_ko=(
            "거대 고리형 머스크에 반응하는 것으로 공개 문헌에 보고된 수용체입니다. "
            "포켓이 크고 방향족 잔기가 많은 것으로 모식화했으며, 그래서 작은 테르펜보다 "
            "부피가 큰 머스크·우디 분자가 잘 맞습니다."
        ),
        sign_odor_ko="머스크·우디",
        evidence_note_ko="Pyrfume 번들에는 OR5AN1–muscone 직접 측정이 없고, ethylene brassylate 양성 기록만 있습니다.",
        helices=tuple(
            _H(h.name, h.angle, h.radius * 1.16, h.tilt, h.twist, h.phase) for h in _HELICES_A
        ),
        residues=(
            Residue("Leu", "3.29", "TM3", 0.66),
            Residue("Phe", "3.32", "TM3", 0.76),
            Residue("Ile", "4.60", "TM4", 0.72),
            Residue("Leu", "5.42", "TM5", 0.68),
            Residue("Phe", "5.43", "TM5", 0.78),
            Residue("Phe", "6.51", "TM6", 0.82),
            Residue("Phe", "6.52", "TM6", 0.88),
            Residue("Tyr", "6.48", "TM6", 0.72),
            Residue("Trp", "6.58", "TM6", 0.62, "소수성 지붕"),
            Residue("Val", "6.55", "TM6", 0.68),
            Residue("Ile", "7.43", "TM7", 0.70),
            Residue("Asn", "7.39", "TM7", 0.78),
        ),
        pocket_center=(0.3, 0.3, 10.6),
        pocket_radius=6.6,
    ),
    Receptor(
        id="or1g1",
        name="OR1G1",
        gene="OR1G1",
        class_name="Class A GPCR (7-TM)",
        ligands_ko="플로럴 · 에스터 · 지방족 알코올",
        description_ko=(
            "에스터와 지방족 알코올에 넓게 반응하는 수용체로 알려져 있습니다. "
            "에스터의 카보닐을 받아 주는 극성 잔기를 포켓 위쪽에, 부피가 큰 알코올 "
            "꼬리를 받는 소수성 바닥을 아래쪽에 두어 모식화했습니다."
        ),
        sign_odor_ko="플로럴·에스터",
        evidence_note_ko="Pyrfume 번들(Mainland 2015)에는 이 수용체의 실측 반응이 포함되어 있지 않습니다.",
        helices=_HELICES_A,
        residues=(
            Residue("Ser", "3.36", "TM3", 0.80),
            Residue("Phe", "3.32", "TM3", 0.72),
            Residue("Leu", "3.29", "TM3", 0.64),
            Residue("Leu", "4.57", "TM4", 0.70),
            Residue("Phe", "5.43", "TM5", 0.76),
            Residue("Leu", "5.42", "TM5", 0.68),
            Residue("Thr", "5.46", "TM5", 0.84, "에스터 카보닐 앵커"),
            Residue("Tyr", "6.48", "TM6", 0.74),
            Residue("Phe", "6.51", "TM6", 0.80),
            Residue("Asn", "7.39", "TM7", 0.78),
            Residue("Ile", "7.43", "TM7", 0.70),
        ),
        pocket_center=(0.5, 0.3, 10.1),
        pocket_radius=5.4,
    ),
)

_BY_ID = {r.id: r for r in RECEPTORS}


def receptor(rid: str) -> Receptor:
    return _BY_ID[rid]


def receptors() -> tuple[Receptor, ...]:
    return RECEPTORS


# --------------------------------------------------------------------------- poses
def _rotations(n: int = 288) -> list[np.ndarray]:
    """A deterministic, roughly uniform set of rotations (golden-spiral + roll)."""
    rots: list[np.ndarray] = []
    golden = math.pi * (3.0 - math.sqrt(5.0))
    n_axis = 24
    n_roll = max(4, n // n_axis)
    for i in range(n_axis):
        z = 1.0 - 2.0 * (i + 0.5) / n_axis
        r = math.sqrt(max(0.0, 1.0 - z * z))
        theta = golden * i
        k = np.array([r * math.cos(theta), r * math.sin(theta), z])
        # a reference vector perpendicular to k
        ref = np.array([0.0, 0.0, 1.0]) if abs(k[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        u = np.cross(k, ref)
        u /= np.linalg.norm(u)
        v = np.cross(k, u)
        for j in range(n_roll):
            phi = 2.0 * math.pi * j / n_roll
            m = np.column_stack([u, v, k])          # maps molecular axes onto (u, v, k)
            roll = np.array([
                [math.cos(phi), -math.sin(phi), 0.0],
                [math.sin(phi), math.cos(phi), 0.0],
                [0.0, 0.0, 1.0],
            ])
            rots.append(m @ roll)
    return rots


_ROTATIONS = _rotations()


@dataclass
class Pose:
    receptor: str
    molecule: str
    rotation: list[list[float]]
    translation: list[float]
    fit: float
    chemotype: float
    chemotype_note: str
    contacts: int
    hbonds: int
    hydrophobic: int
    pi: int
    clashes: int
    interactions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def rank(self) -> float:
        """Combined ordering used to pick a default receptor (documented heuristic)."""
        return round(0.65 * self.fit + 0.35 * self.chemotype * 100.0, 1)

    def as_dict(self) -> dict[str, Any]:
        return {
            "receptor": self.receptor,
            "molecule": self.molecule,
            "rotation": [[round(v, 4) for v in row] for row in self.rotation],
            "translation": [round(v, 3) for v in self.translation],
            "fit": self.fit,
            "chemotype": self.chemotype,
            "chemotype_note": self.chemotype_note,
            "rank": self.rank,
            "contacts": self.contacts,
            "hbonds": self.hbonds,
            "hydrophobic": self.hydrophobic,
            "pi": self.pi,
            "clashes": self.clashes,
            "interactions": self.interactions,
        }


#: What each receptor is reported to respond to, as a coarse chemotype rule.
#: This is a *heuristic* used only to pick a sensible default receptor; the fit
#: value itself comes from the geometry of the pose.
CHEMOTYPE_KO = {
    "or1a1": "작은 고리형 테르펜·방향족",
    "or2j3": "알데하이드·C6 알코올(그린)",
    "or5an1": "부피가 큰 고리형·머스크",
    "or1g1": "에스터·지방족 알코올",
}


def chemotype_affinity(receptor_id: str, props: dict[str, Any]) -> tuple[float, str]:
    """Coarse chemotype agreement (0–1) between a receptor and a molecule."""
    heavy = int(props.get("heavy", 0))
    rings = int(props.get("rings", 0))
    arom = int(props.get("aromatic_rings", 0))
    ester = int(props.get("ester", 0)) + int(props.get("lactone", 0))
    alde = int(props.get("aldehyde", 0))
    oh = int(props.get("alcohol", 0))
    ether = int(props.get("ether", 0))
    ketone = int(props.get("ketone", 0))

    if receptor_id == "or1a1":
        s, bits = 0.35, []
        if rings and heavy <= 12:
            s += 0.35; bits.append("고리형 소형 분자")
        if arom:
            s += 0.20; bits.append("방향족 고리")
        if heavy <= 11:
            s += 0.15; bits.append("작은 분자량")
        if ester:
            s -= 0.10
    elif receptor_id == "or2j3":
        s, bits = 0.30, []
        if alde:
            s += 0.50; bits.append("알데하이드")
        if oh and heavy <= 9:
            s += 0.30; bits.append("C6 계열 알코올")
        elif oh:
            s += 0.15; bits.append("알코올")
        if heavy <= 10:
            s += 0.10; bits.append("짧은 탄소 사슬")
    elif receptor_id == "or5an1":
        s, bits = 0.25, []
        if heavy >= 15:
            s += 0.40; bits.append("큰 부피(15원자 이상)")
        elif heavy >= 13:
            s += 0.20; bits.append("중간 부피")
        if rings and heavy >= 13:
            s += 0.25; bits.append("고리 구조")
        if ketone or ester:
            s += 0.05
    else:  # or1g1
        s, bits = 0.30, []
        if ester:
            s += 0.45; bits.append("에스터기")
        if oh and heavy >= 9:
            s += 0.30; bits.append("긴 알코올 사슬")
        elif oh:
            s += 0.15; bits.append("알코올")
        if ether:
            s += 0.10
        if 10 <= heavy <= 15:
            s += 0.15; bits.append("중간 크기")

    return min(1.0, max(0.0, round(s, 3))), (", ".join(bits) if bits else "뚜렷한 화학형 일치 없음")


def _score_pose(lig: np.ndarray, lig_flags: dict[str, np.ndarray], residues: list[dict],
                centre: np.ndarray, radius: float) -> tuple[float, list[dict], dict]:
    """Score one rigid-body placement of the ligand inside the pocket."""
    atoms = lig
    hb = 0.0
    hyd = 0.0
    pi = 0.0
    clashes = 0
    detail: list[dict] = []
    polar = lig_flags["polar"]
    hydro = lig_flags["hydro"]
    arom = lig_flags["aromatic"]

    # keep the molecule inside the cavity, centred rather than pushed to a wall
    far = np.linalg.norm(atoms - centre, axis=1)
    outside = float(np.sum(np.maximum(0.0, far - radius * 1.45)))
    drift = float(np.linalg.norm(atoms.mean(axis=0) - centre))

    for res in residues:
        pos = np.array(res["pos"])
        d = np.linalg.norm(atoms - pos, axis=1)
        i_min = int(np.argmin(d))
        dmin = float(d[i_min])
        best = None
        if res["polar"]:
            # hydrogen bond: a ligand donor/acceptor within 2.5–3.6 Å of the
            # residue's functional group
            for idx in np.nonzero(polar)[0]:
                if 2.55 <= d[idx] <= 3.6:
                    q = 1.0 - abs(float(d[idx]) - 2.95) / 0.7
                    if best is None or q > best["q"]:
                        best = {"type": "hbond", "atom": int(idx), "d": float(d[idx]), "q": q}
        if res["aromatic"]:
            # π interaction: aromatic carbon / ring centroid 3.3–5.0 Å from the
            # aromatic residue's ring centre
            for idx in np.nonzero(arom)[0]:
                for dd in (d[idx],):
                    if 3.3 <= float(dd) <= 5.0:
                        q = 1.0 - abs(float(dd) - 4.1) / 0.9
                        if best is None or q > best["q"]:
                            best = {"type": "pi", "atom": int(idx), "d": float(dd), "q": q}
        if res["hydrophobic"]:
            # hydrophobic contact: ligand carbon 3.2–4.6 Å from side-chain centroid
            for idx in np.nonzero(hydro)[0]:
                if 3.2 <= float(d[idx]) <= 4.6:
                    q = 1.0 - abs(float(d[idx]) - 3.9) / 0.8
                    if best is None or q > best["q"]:
                        best = {"type": "hydrophobic", "atom": int(idx), "d": float(d[idx]), "q": q}
        # steric clash with the side-chain envelope (heavy-atom radius ~1.8 Å)
        if dmin < 2.05:
            clashes += 1
        if best:
            if best["type"] == "hbond":
                hb += best["q"]
            elif best["type"] == "pi":
                pi += best["q"]
            else:
                hyd += best["q"]
            detail.append({
                "residue": res["label"],
                "aa": res["aa"],
                "kind": best["type"],
                "atom": best["atom"],
                "distance": round(best["d"], 2),
            })

    contacts = len(detail)
    raw = 1.15 * hb + 0.55 * hyd + 0.75 * pi
    # A polar group buried without a partner is a real cost in a hydrophobic
    # cavity, so unsatisfied donors/acceptors are penalised, not ignored.
    n_polar = int(lig_flags["polar"].sum())
    hbonded = {d["atom"] for d in detail if d["kind"] == "hbond"}
    unsat = 1.0 - (len(hbonded) / n_polar) if n_polar else 0.0
    return raw, detail, {
        "contacts": contacts, "hbonds": sum(1 for d in detail if d["kind"] == "hbond"),
        "hydrophobic": sum(1 for d in detail if d["kind"] == "hydrophobic"),
        "pi": sum(1 for d in detail if d["kind"] == "pi"), "clashes": clashes,
        "unsat": round(float(unsat), 3), "drift": round(drift, 3),
        "outside": round(float(outside), 3),
    }


_WINDOW = {
    "hbond": (2.55, 3.6, 2.95, 0.7),
    "pi": (3.3, 5.0, 4.1, 0.9),
    "hydrophobic": (3.2, 4.6, 3.9, 0.8),
}


def _placements(xyz: np.ndarray, centre: np.ndarray,
                offsets: Iterable[tuple[float, float, float]]) -> tuple[np.ndarray, np.ndarray]:
    """Every (rotation, offset) placement of one conformer, stacked.

    Returns ``(coords, rotations)`` with ``coords`` of shape
    ``(n_place, n_atom, 3)`` in the same order the serial search visits them.
    """
    rots = np.stack(_ROTATIONS)                      # (288, 3, 3)
    placed = xyz @ rots.transpose(0, 2, 1)           # (288, n_atom, 3)
    offsets = list(offsets)
    # rotation-major order, so ties resolve exactly as the serial loop did
    coords = np.stack([placed + (centre + np.array(off)) for off in offsets], axis=1)
    return coords.reshape(-1, xyz.shape[0], 3), rots


def _score_batch(coords: np.ndarray, flags: dict[str, np.ndarray],
                 residue_xyz: np.ndarray, residue_kind: dict[str, np.ndarray],
                 centre: np.ndarray, radius: float) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Vectorised version of :func:`_score_pose` — every candidate placement at once.

    It returns the same ``raw`` contact score, clash count, burial terms and
    unsatisfied-polar fraction the serial scorer produces, so the search picks the
    same pose.  The per-residue breakdown of the winning pose is still built by the
    serial scorer, which keeps the displayed detail identical.
    """
    diff = coords[:, :, None, :] - residue_xyz[None, None, :, :]
    d = np.sqrt(np.einsum("cajk,cajk->caj", diff, diff))          # (C, atom, residue)
    n_place = coords.shape[0]
    n_res = residue_xyz.shape[0]

    best_q = np.full((n_place, n_res), -np.inf)
    best_kind = np.zeros((n_place, n_res), dtype=np.int8)
    best_atom = np.zeros((n_place, n_res), dtype=np.int64)

    flag_key = {"hbond": "polar", "pi": "aromatic", "hydrophobic": "hydro"}
    for code, kind in enumerate(("hbond", "pi", "hydrophobic"), start=1):
        atoms = np.nonzero(flags[flag_key[kind]])[0]
        res_idx = np.nonzero(residue_kind[kind])[0]
        if not len(atoms) or not len(res_idx):
            continue
        lo, hi, ideal, width = _WINDOW[kind]
        sub = d[:, atoms][:, :, res_idx]                           # (C, n_kind_atom, n_kind_res)
        window = (sub >= lo) & (sub <= hi)
        q = np.where(window, 1.0 - np.abs(sub - ideal) / width, -np.inf)
        qs = q.max(axis=1)                                         # (C, n_kind_res)
        idx = atoms[q.argmax(axis=1)]                              # ligand atom, per (C, res)
        better = qs > best_q[:, res_idx]
        best_q[:, res_idx] = np.where(better, qs, best_q[:, res_idx])
        best_kind[:, res_idx] = np.where(better, np.int8(code), best_kind[:, res_idx])
        best_atom[:, res_idx] = np.where(better, idx, best_atom[:, res_idx])

    hit = np.isfinite(best_q)
    n_polar = int(flags["polar"].sum())
    hb = np.where(hit & (best_kind == 1), best_q, 0.0).sum(axis=1)
    pi = np.where(hit & (best_kind == 2), best_q, 0.0).sum(axis=1)
    hyd = np.where(hit & (best_kind == 3), best_q, 0.0).sum(axis=1)

    # distinct hbonded ligand atoms, per placement
    hb_mask = hit & (best_kind == 1)
    hb_atoms = np.zeros((n_place, coords.shape[1]), dtype=bool)
    rows = np.arange(n_place)[:, None]
    hb_atoms[rows, np.where(hb_mask, best_atom, 0)] = hb_mask
    unsat = 1.0 - (hb_atoms.sum(axis=1) / n_polar) if n_polar else np.zeros(n_place)

    clashes = (d.min(axis=1) < 2.05).sum(axis=1)

    rel = coords - centre
    far = np.sqrt(np.einsum("cak,cak->ca", rel, rel))
    outside = np.maximum(0.0, far - radius * 1.45).sum(axis=1)
    drift = np.linalg.norm(coords.mean(axis=1) - centre, axis=1)

    raw = 1.15 * hb + 0.55 * hyd + 0.75 * pi
    return raw, {
        "contacts": hit.sum(axis=1),
        "hbonds": (hit & (best_kind == 1)).sum(axis=1),
        "hydrophobic": (hit & (best_kind == 3)).sum(axis=1),
        "pi": (hit & (best_kind == 2)).sum(axis=1),
        "clashes": clashes,
        "unsat": np.round(unsat, 3),
        "drift": np.round(drift, 3),
        "outside": np.round(outside, 3),
    }


def _fit(raw: float, stats: dict, nres: int) -> float:
    """Turn a pose's contact statistics into a 0–100 *schematic* fit value."""
    contact_score = raw / (0.52 * nres)
    coverage = stats["contacts"] / nres
    fit = (0.62 * min(1.0, contact_score)
           + 0.22 * (1.0 - stats["unsat"])
           + 0.16 * min(1.0, coverage * 1.15))
    return max(0.0, min(100.0, 100.0 * fit - 7.0 * stats["clashes"]
                               - 0.25 * stats["outside"]))


def dock(receptor_id: str, molecule_id: str, conformer: dict[str, Any]) -> Pose:
    """Find the best rigid-body placement of one conformer in one receptor pocket."""
    rec = receptor(receptor_id)
    residues = rec.residue_positions()
    xyz = np.array([[a["x"], a["y"], a["z"]] for a in conformer["atoms"]], dtype=float)
    flags = {
        "polar": np.array([bool(a["hbd"] or a["hba"]) for a in conformer["atoms"]]),
        "hydro": np.array([bool(a["hydro"]) for a in conformer["atoms"]]),
        "aromatic": np.array([bool(a["ar"]) for a in conformer["atoms"]]),
    }
    centre = np.array(rec.pocket_center, dtype=float)

    offsets = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.9), (0.0, 0.0, -0.9),
               (0.9, 0.0, 0.0), (-0.9, 0.0, 0.0), (0.0, 0.9, 0.0), (0.0, -0.9, 0.0)]
    coords, rots = _placements(xyz, centre, offsets)
    residue_xyz = np.array([r["pos"] for r in residues], dtype=float)
    residue_kind = {
        "hbond": np.array([bool(r["polar"]) for r in residues]),
        "pi": np.array([bool(r["aromatic"]) for r in residues]),
        "hydrophobic": np.array([bool(r["hydrophobic"]) for r in residues]),
    }
    raw_scores, _stats = _score_batch(coords, flags, residue_xyz, residue_kind,
                                      centre, rec.pocket_radius)
    # first maximum wins, exactly as the serial `score > best[0]` comparison did
    winner = int(np.argmax(raw_scores))
    n_off = len(offsets)
    rot = rots[winner // n_off]
    t = centre + np.array(offsets[winner % n_off])
    # rebuild the per-residue detail of the winning pose with the serial scorer
    score, detail, stats = _score_pose(coords[winner], flags, residues, centre, rec.pocket_radius)
    fit = _fit(score, stats, len(residues))
    chem, bits = chemotype_affinity(receptor_id, conformer.get("props", {}))
    detail.sort(key=lambda d: {"hbond": 0, "pi": 1, "hydrophobic": 2}[d["kind"]])
    # one line per residue, best 8 kept for the viewer
    seen: set[str] = set()
    interactions = []
    for d in detail:
        if d["residue"] in seen:
            continue
        seen.add(d["residue"])
        interactions.append(d)
        if len(interactions) >= 8:
            break
    return Pose(
        receptor=receptor_id, molecule=molecule_id,
        rotation=[[float(v) for v in row] for row in rot],
        translation=[float(v) for v in t],
        fit=round(fit, 1),
        chemotype=round(min(1.0, max(0.0, chem)), 3),
        chemotype_note=bits,
        contacts=stats["contacts"], hbonds=stats["hbonds"],
        hydrophobic=stats["hydrophobic"], pi=stats["pi"], clashes=stats["clashes"],
        interactions=interactions,
    )


def dock_library(receptor_id: str, conformers: dict[str, dict[str, Any]]) -> dict[str, dict]:
    """Dock every molecule of the library into one receptor."""
    return {mid: dock(receptor_id, mid, conf).as_dict() for mid, conf in conformers.items()}


def receptor_payload() -> list[dict[str, Any]]:
    """Serialisable receptor definitions for the web viewer."""
    return [r.as_dict() for r in RECEPTORS]
