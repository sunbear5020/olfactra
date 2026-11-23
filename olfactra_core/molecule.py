"""OLFACTRA MOLECULE — public fragrance-chemistry reference library.

Every structure in this module is drawn from open reference data (PubChem CID,
formula, molecular weight, SMILES). Nothing here is derived from proprietary
fragrance formulas, captives or trade-secret composition data.

Safety ceilings (`working_cap_pct`) are conservative *working* limits for DIY
blending in the finished product (% w/w equivalent), assembled from general
public cosmetic/fragrance guidance (EU declarable-allergen list, published
sensitizer notes, common perfumery practice). They are **not** IFRA
certificates and do not replace a real safety assessment before sale or
distribution.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from . import descriptors

FAMILIES: tuple[str, ...] = (
    "citrus", "green", "floral", "fruity", "sweet", "spicy",
    "woody", "resinous", "earthy", "camphor", "musky", "smoky", "powdery",
)

FAMILY_LABELS_KO: dict[str, str] = {
    "citrus": "시트러스",
    "green": "그린",
    "floral": "플로럴",
    "fruity": "프루티",
    "sweet": "스위트",
    "spicy": "스파이시",
    "woody": "우디",
    "resinous": "레지너스",
    "earthy": "어시",
    "camphor": "캠퍼",
    "musky": "머스크",
    "smoky": "스모키",
    "powdery": "파우더리",
}

NOTES: tuple[str, ...] = ("top", "middle", "base")
NOTE_LABELS_KO: dict[str, str] = {"top": "탑", "middle": "미들", "base": "베이스"}


@dataclass(frozen=True)
class Molecule:
    id: str
    name: str
    name_ko: str
    cas: str | None
    formula: str
    molecular_weight: float
    smiles: str
    pubchem_cid: int
    functional_group: str
    families: Mapping[str, float]
    note: str
    descriptor_ko: str
    descriptor_en: str
    natural_sources: tuple[str, ...]
    working_cap_pct: float
    cap_basis: str
    density_g_ml: float
    state: str

    # -- derived ---------------------------------------------------------
    @property
    def logp(self) -> float:
        """Calculated octanol–water partition coefficient (Crippen contributions).

        An estimate from a contribution model, not an experimental value — see
        :mod:`olfactra_core.descriptors` and the provenance registry.
        """
        return descriptors.value(self.id, "logp")

    @property
    def tpsa(self) -> float:
        """Topological polar surface area (Å², Ertl fragments) — a derived estimate."""
        return descriptors.value(self.id, "tpsa")

    @property
    def volatility(self) -> float:
        """0..1 volatility index used for the note/evaporation axis (higher = faster).

        Heuristic: a note-class base (top .92, middle .60, base .25) scaled by the
        molecular weight (``170 / MW`` clamped to 0.55–1.20).  It is **not** a
        vapour-pressure measurement and no measured vapour pressure is bundled;
        it only orders materials for the map and the note axis.
        """
        base = {"top": 0.92, "middle": 0.6, "base": 0.25}[self.note]
        # heavier molecules evaporate more slowly within a note class
        weight_factor = max(0.55, min(1.2, 170.0 / max(self.molecular_weight, 1.0)))
        return round(min(1.0, base * weight_factor), 3)

    def odor_vector(self, families: Sequence[str] = FAMILIES) -> tuple[float, ...]:
        return tuple(float(self.families.get(f, 0.0)) for f in families)

    def dominant_families(self, limit: int = 3) -> list[tuple[str, float]]:
        return sorted(self.families.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    @property
    def is_solid(self) -> bool:
        return self.state != "liquid"

    def density_or(self, fallback: float = 1.0) -> float:
        """Solids are weighed, not measured by volume; 1.0 g/mL is a nominal fallback."""
        return self.density_g_ml if not self.is_solid else fallback

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "name_ko": self.name_ko,
            "cas": self.cas,
            "formula": self.formula,
            "molecular_weight": self.molecular_weight,
            "logp": self.logp,
            "tpsa": self.tpsa,
            "smiles": self.smiles,
            "pubchem_cid": self.pubchem_cid,
            "functional_group": self.functional_group,
            "families": dict(self.families),
            "note": self.note,
            "volatility": self.volatility,
            "descriptor_ko": self.descriptor_ko,
            "descriptor_en": self.descriptor_en,
            "natural_sources": list(self.natural_sources),
            "working_cap_pct": self.working_cap_pct,
            "cap_basis": self.cap_basis,
            "density_g_ml": self.density_g_ml,
            "state": self.state,
        }


MOLECULES: tuple[Molecule, ...] = (
Molecule(
    id="alpha-pinene",
    name="α-Pinene",
    name_ko="α-피넨",
    cas="80-56-8",
    formula="C10H16",
    molecular_weight=136.23,
    smiles="CC1=CCC2CC1C2(C)C",
    pubchem_cid=6654,
    functional_group="bicyclic monoterpene hydrocarbon",
    families={"woody": 0.55, "resinous": 0.45, "green": 0.25, "camphor": 0.20},
    note="top",
    descriptor_ko="소나무·수지의 날카롭고 푸른 향",
    descriptor_en="sharp pine-resin, fresh turpentine",
    natural_sources=tuple("소나무(Pinus), 로즈메리, 유향".split(", ")),
    working_cap_pct=10,
    cap_basis="no published fine-fragrance restriction; oxidation control is the real limit",
    density_g_ml=0.858,
    state="liquid",
),
Molecule(
    id="beta-pinene",
    name="β-Pinene",
    name_ko="β-피넨",
    cas="127-91-3",
    formula="C10H16",
    molecular_weight=136.23,
    smiles="CC1(C2CCC(=C)C1C2)C",
    pubchem_cid=14896,
    functional_group="bicyclic monoterpene hydrocarbon",
    families={"woody": 0.50, "resinous": 0.40, "green": 0.20, "camphor": 0.15},
    note="top",
    descriptor_ko="솔잎의 부드러운 수지향",
    descriptor_en="soft pine, resinous green",
    natural_sources=tuple("소나무, 테레빈유, 홉".split(", ")),
    working_cap_pct=10,
    cap_basis="no published fine-fragrance restriction; oxidation control is the real limit",
    density_g_ml=0.866,
    state="liquid",
),
Molecule(
    id="limonene",
    name="Limonene",
    name_ko="리모넨",
    cas="138-86-3",
    formula="C10H16",
    molecular_weight=136.23,
    smiles="CC1=CCC(CC1)C(=C)C",
    pubchem_cid=22311,
    functional_group="monocyclic monoterpene hydrocarbon",
    families={"citrus": 1.00, "green": 0.15},
    note="top",
    descriptor_ko="감귤 껍질의 밝고 달콤한 향",
    descriptor_en="bright sweet citrus peel",
    natural_sources=tuple("감귤류 과피(오렌지·레몬·유자), 소나무".split(", ")),
    working_cap_pct=10,
    cap_basis="no published fine-fragrance restriction; oxidised limonene sensitises",
    density_g_ml=0.841,
    state="liquid",
),
Molecule(
    id="myrcene",
    name="Myrcene",
    name_ko="미르센",
    cas="123-35-3",
    formula="C10H16",
    molecular_weight=136.23,
    smiles="CC(=CCCC(=C)C=C)C",
    pubchem_cid=31253,
    functional_group="acyclic monoterpene hydrocarbon",
    families={"green": 0.45, "fruity": 0.25, "resinous": 0.20, "citrus": 0.10},
    note="top",
    descriptor_ko="풀잎과 망고를 닮은 부드러운 청량감",
    descriptor_en="green-fruity, mango and hop",
    natural_sources=tuple("홉, 월계수, 망고".split(", ")),
    working_cap_pct=10,
    cap_basis="no published fine-fragrance restriction; oxidises readily",
    density_g_ml=0.794,
    state="liquid",
),
Molecule(
    id="alpha-terpinene",
    name="α-Terpinene",
    name_ko="α-터피넨",
    cas="99-86-5",
    formula="C10H16",
    molecular_weight=136.23,
    smiles="CC1=CC=C(CC1)C(C)C",
    pubchem_cid=7462,
    functional_group="monocyclic monoterpene hydrocarbon",
    families={"citrus": 0.50, "green": 0.30, "woody": 0.20},
    note="top",
    descriptor_ko="레몬 같은 청량한 시트러스",
    descriptor_en="lemony, mildly green",
    natural_sources=tuple("티트리, 감귤류, 카다멈".split(", ")),
    working_cap_pct=10,
    cap_basis="no published fine-fragrance restriction; oxidises readily",
    density_g_ml=0.837,
    state="liquid",
),
Molecule(
    id="sabinene",
    name="Sabinene",
    name_ko="사비넨",
    cas="3387-41-5",
    formula="C10H16",
    molecular_weight=136.23,
    smiles="CC(C)C12CCC(=C)C1C2",
    pubchem_cid=18818,
    functional_group="bicyclic monoterpene hydrocarbon",
    families={"woody": 0.45, "green": 0.25, "spicy": 0.20, "resinous": 0.20},
    note="top",
    descriptor_ko="후추를 닮은 편백의 푸른 수지향",
    descriptor_en="peppery-pine, hinoki-like",
    natural_sources=tuple("편백(히노키), 주니퍼 베리, 흑후추".split(", ")),
    working_cap_pct=10,
    cap_basis="no published fine-fragrance restriction; oxidises readily",
    density_g_ml=0.842,
    state="liquid",
),
Molecule(
    id="linalool",
    name="Linalool",
    name_ko="리날룰",
    cas="78-70-6",
    formula="C10H18O",
    molecular_weight=154.25,
    smiles="CC(=CCCC(C)(C=C)O)C",
    pubchem_cid=6549,
    functional_group="monoterpene alcohol",
    families={"floral": 0.75, "citrus": 0.20, "green": 0.15, "woody": 0.10},
    note="middle",
    descriptor_ko="라벤더의 투명한 꽃향",
    descriptor_en="transparent lavender-floral",
    natural_sources=tuple("라벤더, 베르가못, 고수".split(", ")),
    working_cap_pct=20,
    cap_basis="EU declarable allergen; oxidised linalool sensitises",
    density_g_ml=0.86,
    state="liquid",
),
Molecule(
    id="linalyl acetate",
    name="Linalyl Acetate",
    name_ko="리날릴 아세테이트",
    cas="115-95-7",
    formula="C12H20O2",
    molecular_weight=196.29,
    smiles="CC(=CCCC(C)(C=C)OC(=O)C)C",
    pubchem_cid=8294,
    functional_group="monoterpene ester",
    families={"floral": 0.60, "fruity": 0.35, "citrus": 0.20, "sweet": 0.10},
    note="top",
    descriptor_ko="베르가못의 과즙감 있는 꽃향",
    descriptor_en="bergamot-lavender, fruity floral",
    natural_sources=tuple("라벤더, 베르가못, 세이지".split(", ")),
    working_cap_pct=20,
    cap_basis="EU declarable allergen",
    density_g_ml=0.895,
    state="liquid",
),
Molecule(
    id="geraniol",
    name="Geraniol",
    name_ko="제라니올",
    cas="106-24-1",
    formula="C10H18O",
    molecular_weight=154.25,
    smiles="CC(=CCC/C(=C/CO)/C)C",
    pubchem_cid=637566,
    functional_group="monoterpene alcohol",
    families={"floral": 0.85, "sweet": 0.20, "fruity": 0.10},
    note="middle",
    descriptor_ko="장미·제라늄의 달콤한 꽃향",
    descriptor_en="rosy, sweet geranium",
    natural_sources=tuple("장미, 제라늄, 팔마로사".split(", ")),
    working_cap_pct=10,
    cap_basis="EU declarable allergen",
    density_g_ml=0.889,
    state="liquid",
),
Molecule(
    id="citronellol",
    name="Citronellol",
    name_ko="시트로넬롤",
    cas="106-22-9",
    formula="C10H20O",
    molecular_weight=156.26,
    smiles="CC(CCC=C(C)C)CCO",
    pubchem_cid=8842,
    functional_group="monoterpene alcohol",
    families={"floral": 0.80, "green": 0.20, "fruity": 0.10},
    note="middle",
    descriptor_ko="장미의 부드럽고 살짝 시트러스한 꽃향",
    descriptor_en="soft rosy, citrus-tinged",
    natural_sources=tuple("장미, 제라늄, 시트로넬라".split(", ")),
    working_cap_pct=15,
    cap_basis="EU declarable allergen",
    density_g_ml=0.855,
    state="liquid",
),
Molecule(
    id="citral",
    name="Citral",
    name_ko="시트랄",
    cas="5392-40-5",
    formula="C10H16O",
    molecular_weight=152.23,
    smiles="CC(=CCC/C(=C/C=O)/C)C",
    pubchem_cid=638011,
    functional_group="monoterpene aldehyde (mixture of geranial/neral)",
    families={"citrus": 0.60, "green": 0.30, "sweet": 0.15, "floral": 0.10},
    note="top",
    descriptor_ko="레몬그라스의 강렬한 레몬향",
    descriptor_en="powerful lemongrass-lemon",
    natural_sources=tuple("레몬그라스, 레몬 머틀, 리트세아".split(", ")),
    working_cap_pct=1,
    cap_basis="strong skin sensitizer — keep as a trace accent",
    density_g_ml=0.888,
    state="liquid",
),
Molecule(
    id="alpha-terpineol",
    name="α-Terpineol",
    name_ko="α-터피네올",
    cas="98-55-5",
    formula="C10H18O",
    molecular_weight=154.25,
    smiles="CC1=CCC(CC1)C(C)(C)O",
    pubchem_cid=17100,
    functional_group="monoterpene alcohol",
    families={"floral": 0.50, "woody": 0.30, "citrus": 0.15, "camphor": 0.10},
    note="middle",
    descriptor_ko="라일락과 솔잎이 겹친 향",
    descriptor_en="lilac-pine, soft floral",
    natural_sources=tuple("라일락, 소나무, 카제풋".split(", ")),
    working_cap_pct=10,
    cap_basis="EU declarable allergen",
    density_g_ml=0.934,
    state="liquid",
),
Molecule(
    id="terpinen-4-ol",
    name="Terpinen-4-ol",
    name_ko="터피넨-4-올",
    cas="562-74-3",
    formula="C10H18O",
    molecular_weight=154.25,
    smiles="CC1=CCC(CC1)(C(C)C)O",
    pubchem_cid=11230,
    functional_group="monocyclic monoterpene alcohol",
    families={"woody": 0.35, "earthy": 0.30, "spicy": 0.20, "green": 0.15, "camphor": 0.10},
    note="middle",
    descriptor_ko="티트리의 흙 섞인 약초향",
    descriptor_en="earthy herbal, tea-tree",
    natural_sources=tuple("티트리, 편백, 주니퍼".split(", ")),
    working_cap_pct=10,
    cap_basis="general cosmetic guidance; avoid broken skin",
    density_g_ml=0.934,
    state="liquid",
),
Molecule(
    id="eucalyptol",
    name="1,8-Cineole",
    name_ko="1,8-시네올",
    cas="470-82-6",
    formula="C10H18O",
    molecular_weight=154.25,
    smiles="CC1(C2CCC(O1)(CC2)C)C",
    pubchem_cid=2758,
    functional_group="monoterpene ether (oxide)",
    families={"camphor": 0.70, "green": 0.30, "woody": 0.20},
    note="top",
    descriptor_ko="유칼립투스의 시원한 청량감",
    descriptor_en="cool eucalyptus, camphoraceous",
    natural_sources=tuple("유칼립투스, 로즈메리, 녹나무".split(", ")),
    working_cap_pct=5,
    cap_basis="airway irritant at high dose; avoid around infants and cats",
    density_g_ml=0.922,
    state="liquid",
),
Molecule(
    id="camphor",
    name="Camphor",
    name_ko="캠퍼",
    cas="76-22-2",
    formula="C10H16O",
    molecular_weight=152.23,
    smiles="CC1(C2CCC1(C(=O)C2)C)C",
    pubchem_cid=2537,
    functional_group="bicyclic monoterpene ketone",
    families={"camphor": 0.90, "woody": 0.20, "resinous": 0.10},
    note="top",
    descriptor_ko="녹나무의 강한 장뇌향",
    descriptor_en="strong camphor, cool",
    natural_sources=tuple("녹나무, 로즈메리, 세이지".split(", ")),
    working_cap_pct=2,
    cap_basis="restricted for children; avoid in infant and pet areas",
    density_g_ml=0.992,
    state="solid",
),
Molecule(
    id="fenchone",
    name="Fenchone",
    name_ko="펜콘",
    cas="1195-79-5",
    formula="C10H16O",
    molecular_weight=152.23,
    smiles="CC1(C2CCC(C2)(C1=O)C)C",
    pubchem_cid=14525,
    functional_group="bicyclic monoterpene ketone",
    families={"camphor": 0.75, "sweet": 0.15, "earthy": 0.15, "woody": 0.10},
    note="top",
    descriptor_ko="회향의 달콤한 장뇌향",
    descriptor_en="sweet camphor, fennel-like",
    natural_sources=tuple("회향, 라벤더".split(", ")),
    working_cap_pct=2,
    cap_basis="camphoraceous ketone; conservative ceiling",
    density_g_ml=0.946,
    state="liquid",
),
Molecule(
    id="bornyl acetate",
    name="Bornyl Acetate",
    name_ko="보르닐 아세테이트",
    cas="5655-61-8",
    formula="C12H20O2",
    molecular_weight=196.29,
    smiles="CC(=O)O[C@@H]1C[C@@H]2CC[C@]1(C2(C)C)C",
    pubchem_cid=93009,
    functional_group="monoterpene ester",
    families={"woody": 0.50, "resinous": 0.35, "camphor": 0.25, "sweet": 0.10},
    note="middle",
    descriptor_ko="전나무·소나무의 발사믹한 수지향",
    descriptor_en="balsamic pine, fir-needle",
    natural_sources=tuple("소나무, 전나무, 발레리안".split(", ")),
    working_cap_pct=10,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=0.985,
    state="liquid",
),
Molecule(
    id="beta-caryophyllene",
    name="β-Caryophyllene",
    name_ko="β-카리오필렌",
    cas="87-44-5",
    formula="C15H24",
    molecular_weight=204.35,
    smiles="C/C/1=C\\CCC(=C)[C@H]2CC([C@@H]2CC1)(C)C",
    pubchem_cid=5281515,
    functional_group="bicyclic sesquiterpene hydrocarbon",
    families={"woody": 0.55, "spicy": 0.35, "resinous": 0.20, "earthy": 0.15},
    note="base",
    descriptor_ko="후추와 정향을 닮은 건조한 목향",
    descriptor_en="dry peppery wood, clove hint",
    natural_sources=tuple("정향, 코파이바, 흑후추".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction; oxidation gives off-notes",
    density_g_ml=0.902,
    state="liquid",
),
Molecule(
    id="alpha-humulene",
    name="α-Humulene",
    name_ko="α-후물렌",
    cas="6753-98-6",
    formula="C15H24",
    molecular_weight=204.35,
    smiles="C/C/1=C\\CC(/C=C/C/C(=C/CC1)/C)(C)C",
    pubchem_cid=5281520,
    functional_group="macrocyclic sesquiterpene hydrocarbon",
    families={"woody": 0.60, "spicy": 0.25, "resinous": 0.15},
    note="base",
    descriptor_ko="홉의 쌉싸름한 목향",
    descriptor_en="dry woody, hop-like",
    natural_sources=tuple("홉, 세이지, 생강".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=0.89,
    state="liquid",
),
Molecule(
    id="alpha-santalol",
    name="α-Santalol",
    name_ko="α-산탈롤",
    cas="115-71-9",
    formula="C15H24O",
    molecular_weight=220.35,
    smiles="C/C(=C/CC[C@@]1(C2C[C@H]3C1([C@H]3C2)C)C)/CO",
    pubchem_cid=11085337,
    functional_group="tricyclic sesquiterpene alcohol",
    families={"woody": 0.80, "resinous": 0.25, "sweet": 0.15, "floral": 0.10},
    note="base",
    descriptor_ko="백단향의 크리미하고 따뜻한 목향",
    descriptor_en="creamy warm sandalwood",
    natural_sources=tuple("백단향(Santalum album) 심재".split(", ")),
    working_cap_pct=20,
    cap_basis="wild Santalum album is IUCN Vulnerable; use plantation or synthetic",
    density_g_ml=0.977,
    state="liquid",
),
Molecule(
    id="patchoulol",
    name="Patchoulol",
    name_ko="파출롤",
    cas=None,
    formula="C15H26O",
    molecular_weight=222.37,
    smiles="C[C@H]1CCC2([C@@]3(C1CC(C2(C)C)CC3)C)O",
    pubchem_cid=442384,
    functional_group="tricyclic sesquiterpene alcohol",
    families={"woody": 0.65, "earthy": 0.45, "resinous": 0.15},
    note="base",
    descriptor_ko="패츌리의 축축한 흙·나무향",
    descriptor_en="damp earthy patchouli",
    natural_sources=tuple("패츌리(Pogostemon cablin)".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=0.97,
    state="solid",
),
Molecule(
    id="cedrol",
    name="Cedrol",
    name_ko="세드롤",
    cas="77-53-2",
    formula="C15H26O",
    molecular_weight=222.37,
    smiles="C[C@@H]1CC[C@@H]2[C@]13CC[C@@]([C@H](C3)C2(C)C)(C)O",
    pubchem_cid=65575,
    functional_group="tricyclic sesquiterpene alcohol",
    families={"woody": 0.80, "resinous": 0.20, "sweet": 0.10, "earthy": 0.10},
    note="base",
    descriptor_ko="삼나무의 마른 연필 같은 목향",
    descriptor_en="dry cedar-pencil wood",
    natural_sources=tuple("삼나무·향나무 심재(Cedrus, Juniperus)".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=1.01,
    state="solid",
),
Molecule(
    id="alpha-cedrene",
    name="α-Cedrene",
    name_ko="α-세드렌",
    cas="469-61-4",
    formula="C15H24",
    molecular_weight=204.35,
    smiles="C[C@@H]1CC[C@@H]2[C@]13CC=C([C@H](C3)C2(C)C)C",
    pubchem_cid=6431015,
    functional_group="tricyclic sesquiterpene hydrocarbon",
    families={"woody": 0.75, "resinous": 0.20, "green": 0.10},
    note="base",
    descriptor_ko="시더우드의 건조한 수지향",
    descriptor_en="dry cedarwood resin",
    natural_sources=tuple("시더우드(Juniperus virginiana)".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=0.933,
    state="liquid",
),
Molecule(
    id="alpha-copaene",
    name="α-Copaene",
    name_ko="α-코파엔",
    cas=None,
    formula="C15H24",
    molecular_weight=204.35,
    smiles="CC1=CC[C@H]2[C@H]3C1[C@]2(CC[C@H]3C(C)C)C",
    pubchem_cid=70678558,
    functional_group="tricyclic sesquiterpene hydrocarbon",
    families={"woody": 0.70, "spicy": 0.20, "resinous": 0.15},
    note="base",
    descriptor_ko="코파이바의 부드러운 목향",
    descriptor_en="soft woody copaiba",
    natural_sources=tuple("코파이바, 일랑일랑, 흑후추".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=0.91,
    state="liquid",
),
Molecule(
    id="germacrene-d",
    name="Germacrene D",
    name_ko="게르마크렌 D",
    cas="23986-74-5",
    formula="C15H24",
    molecular_weight=204.35,
    smiles="C/C/1=C\\CCC(=C)/C=C/[C@@H](CC1)C(C)C",
    pubchem_cid=5317570,
    functional_group="germacrane sesquiterpene hydrocarbon",
    families={"woody": 0.50, "green": 0.30, "earthy": 0.20, "fruity": 0.10},
    note="base",
    descriptor_ko="숲 흙과 풀잎이 섞인 청록 목향",
    descriptor_en="green-earthy forest wood",
    natural_sources=tuple("일랑일랑, 목련, 소나무".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction; oxidises",
    density_g_ml=0.865,
    state="liquid",
),
Molecule(
    id="delta-cadinene",
    name="δ-Cadinene",
    name_ko="δ-카디넨",
    cas="483-76-1",
    formula="C15H24",
    molecular_weight=204.35,
    smiles="CC1=C[C@H]2[C@@H](CCC(=C2CC1)C)C(C)C",
    pubchem_cid=441005,
    functional_group="cadinane sesquiterpene hydrocarbon",
    families={"woody": 0.65, "spicy": 0.20, "earthy": 0.20},
    note="base",
    descriptor_ko="큐벱의 건조한 후추 목향",
    descriptor_en="dry spicy wood, cubeb",
    natural_sources=tuple("큐벱, 주니퍼, 티트리".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=0.916,
    state="liquid",
),
Molecule(
    id="alpha-bisabolol",
    name="α-Bisabolol",
    name_ko="α-비사보롤",
    cas="515-69-5",
    formula="C15H26O",
    molecular_weight=222.37,
    smiles="CC1=CC[C@@H](CC1)[C@@](C)(CCC=C(C)C)O",
    pubchem_cid=1549992,
    functional_group="sesquiterpene alcohol",
    families={"floral": 0.55, "sweet": 0.30, "woody": 0.15, "powdery": 0.20},
    note="base",
    descriptor_ko="캐모마일의 포근한 꽃향",
    descriptor_en="soft chamomile floral",
    natural_sources=tuple("캐모마일(Matricaria chamomilla)".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=0.93,
    state="liquid",
),
Molecule(
    id="muscone",
    name="Muscone",
    name_ko="무스콘",
    cas="10403-00-6",
    formula="C16H30O",
    molecular_weight=238.41,
    smiles="C[C@@H]1CCCCCCCCCCCCC(=O)C1",
    pubchem_cid=7160826,
    functional_group="macrocyclic ketone",
    families={"musky": 1.00, "sweet": 0.15, "woody": 0.10},
    note="base",
    descriptor_ko="피부에 붙는 따뜻한 머스크",
    descriptor_en="warm skin-like musk",
    natural_sources=tuple("사향노루 분비물의 역사적 성분 — 현재는 합성품 사용".split(", ")),
    working_cap_pct=10,
    cap_basis="use synthetic muscone; animal-derived musk is CITES-protected",
    density_g_ml=0.92,
    state="liquid",
),
Molecule(
    id="benzyl acetate",
    name="Benzyl Acetate",
    name_ko="벤질 아세테이트",
    cas="140-11-4",
    formula="C9H10O2",
    molecular_weight=150.17,
    smiles="CC(=O)OCC1=CC=CC=C1",
    pubchem_cid=8785,
    functional_group="aromatic ester",
    families={"floral": 0.70, "fruity": 0.45, "sweet": 0.20},
    note="top",
    descriptor_ko="자스민의 달콤한 과즙 꽃향",
    descriptor_en="sweet jasmine, fruity",
    natural_sources=tuple("자스민, 일랑일랑".split(", ")),
    working_cap_pct=15,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=1.055,
    state="liquid",
),
Molecule(
    id="phenylethyl alcohol",
    name="Phenylethyl Alcohol",
    name_ko="페닐에틸 알코올",
    cas="60-12-8",
    formula="C8H10O",
    molecular_weight=122.16,
    smiles="C1=CC=C(C=C1)CCO",
    pubchem_cid=6054,
    functional_group="aromatic alcohol",
    families={"floral": 0.90, "sweet": 0.10},
    note="middle",
    descriptor_ko="장미의 가장 чист한 꽃향",
    descriptor_en="clean rose",
    natural_sources=tuple("장미(Rosa damascena)".split(", ")),
    working_cap_pct=25,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=1.017,
    state="liquid",
),
Molecule(
    id="cis-jasmone",
    name="cis-Jasmone",
    name_ko="시스-자스몬",
    cas="488-10-8",
    formula="C11H16O",
    molecular_weight=164.24,
    smiles="CC/C=C\\CC1=C(CCC1=O)C",
    pubchem_cid=1549018,
    functional_group="cyclopentenone",
    families={"floral": 0.80, "fruity": 0.20, "green": 0.10},
    note="middle",
    descriptor_ko="자스민의 짙고 녹색인 꽃향",
    descriptor_en="deep green jasmine",
    natural_sources=tuple("자스민(Jasminum)".split(", ")),
    working_cap_pct=5,
    cap_basis="general cosmetic guidance; strong odour impact",
    density_g_ml=0.94,
    state="liquid",
),
Molecule(
    id="beta-ionone",
    name="β-Ionone",
    name_ko="β-이오논",
    cas="79-77-6",
    formula="C13H20O",
    molecular_weight=192.30,
    smiles="CC1=C(C(CCC1)(C)C)/C=C/C(=O)C",
    pubchem_cid=638014,
    functional_group="ionone (C13 norisoprenoid ketone)",
    families={"floral": 0.70, "woody": 0.20, "fruity": 0.20, "sweet": 0.15},
    note="middle",
    descriptor_ko="제비꽃의 보랏빛 가루 향",
    descriptor_en="violet, powdery-sweet",
    natural_sources=tuple("제비꽃, 아이리스, 장미".split(", ")),
    working_cap_pct=5,
    cap_basis="general cosmetic guidance; very strong odour impact",
    density_g_ml=0.945,
    state="liquid",
),
Molecule(
    id="methyl anthranilate",
    name="Methyl Anthranilate",
    name_ko="메틸 안트라닐레이트",
    cas="134-20-3",
    formula="C8H9NO2",
    molecular_weight=151.16,
    smiles="COC(=O)C1=CC=CC=C1N",
    pubchem_cid=8635,
    functional_group="aromatic ester (anthranilate)",
    families={"floral": 0.70, "fruity": 0.30, "sweet": 0.10},
    note="middle",
    descriptor_ko="네롤리의 포도 같은 꽃향",
    descriptor_en="orange-blossom, grape-like",
    natural_sources=tuple("네롤리, 오렌지 블로섬, 포도".split(", ")),
    working_cap_pct=5,
    cap_basis="general cosmetic guidance",
    density_g_ml=1.168,
    state="liquid",
),
Molecule(
    id="vanillin",
    name="Vanillin",
    name_ko="바닐린",
    cas="121-33-5",
    formula="C8H8O3",
    molecular_weight=152.15,
    smiles="COC1=C(C=CC(=C1)C=O)O",
    pubchem_cid=1183,
    functional_group="phenolic aldehyde",
    families={"sweet": 0.85, "resinous": 0.20, "smoky": 0.10},
    note="base",
    descriptor_ko="바닐라의 달콤하고 크리미한 향",
    descriptor_en="creamy vanilla",
    natural_sources=tuple("바닐라(Vanilla planifolia) 숙성 협과".split(", ")),
    working_cap_pct=15,
    cap_basis="no published fine-fragrance restriction; can crystallise",
    density_g_ml=1.056,
    state="solid",
),
Molecule(
    id="coumarin",
    name="Coumarin",
    name_ko="쿠마린",
    cas="91-64-5",
    formula="C9H6O2",
    molecular_weight=146.14,
    smiles="C1=CC=C2C(=C1)C=CC(=O)O2",
    pubchem_cid=323,
    functional_group="lactone (benzopyrone)",
    families={"sweet": 0.55, "green": 0.20, "spicy": 0.10, "woody": 0.15},
    note="base",
    descriptor_ko="건초와 통카빈의 달콤한 향",
    descriptor_en="hay, tonka, almond-sweet",
    natural_sources=tuple("통카빈, 건초, 계피".split(", ")),
    working_cap_pct=2.5,
    cap_basis="EU declarable allergen; oral intake regulated separately",
    density_g_ml=0.935,
    state="solid",
),
Molecule(
    id="eugenol",
    name="Eugenol",
    name_ko="유제놀",
    cas="97-53-0",
    formula="C10H12O2",
    molecular_weight=164.20,
    smiles="COC1=C(C=CC(=C1)CC=C)O",
    pubchem_cid=3314,
    functional_group="phenolic allyl compound",
    families={"spicy": 0.85, "woody": 0.20, "smoky": 0.10, "sweet": 0.10},
    note="middle",
    descriptor_ko="정향의 뜨겁고 약간 마취되는 향",
    descriptor_en="hot clove, slightly numbing",
    natural_sources=tuple("정향, 계피 잎, 월계수".split(", ")),
    working_cap_pct=1,
    cap_basis="skin and mucosal irritant; keep well under ceiling; avoid in pet areas",
    density_g_ml=1.066,
    state="liquid",
),
Molecule(
    id="cinnamaldehyde",
    name="Cinnamaldehyde",
    name_ko="신남알데하이드",
    cas="104-55-2",
    formula="C9H8O",
    molecular_weight=132.16,
    smiles="C1=CC=C(C=C1)/C=C/C=O",
    pubchem_cid=637511,
    functional_group="aromatic aldehyde",
    families={"spicy": 0.90, "sweet": 0.15, "resinous": 0.10},
    note="middle",
    descriptor_ko="계피 껍질의 매운 단 향",
    descriptor_en="hot cinnamon bark",
    natural_sources=tuple("계피(Cinnamomum verum)".split(", ")),
    working_cap_pct=0.3,
    cap_basis="strong sensitizer; trace accent only",
    density_g_ml=1.048,
    state="liquid",
),
Molecule(
    id="benzyl benzoate",
    name="Benzyl Benzoate",
    name_ko="벤질 벤조에이트",
    cas="120-51-4",
    formula="C14H12O2",
    molecular_weight=212.24,
    smiles="C1=CC=C(C=C1)COC(=O)C2=CC=CC=C2",
    pubchem_cid=2345,
    functional_group="aromatic ester",
    families={"resinous": 0.40, "sweet": 0.25, "floral": 0.10, "woody": 0.10},
    note="base",
    descriptor_ko="발사믹 수지의 달콤한 고정향",
    descriptor_en="balsamic fixative, faintly sweet",
    natural_sources=tuple("페루 발삼, 톨루 발삼".split(", ")),
    working_cap_pct=20,
    cap_basis="no published fine-fragrance restriction; fixative",
    density_g_ml=1.118,
    state="liquid",
),
Molecule(
    id="guaiacol",
    name="Guaiacol",
    name_ko="과이아콜",
    cas="90-05-1",
    formula="C7H8O2",
    molecular_weight=124.14,
    smiles="COC1=CC=CC=C1O",
    pubchem_cid=460,
    functional_group="phenolic ether",
    families={"smoky": 0.80, "spicy": 0.20, "earthy": 0.20, "woody": 0.10},
    note="base",
    descriptor_ko="연기와 훈제한 나무의 향",
    descriptor_en="smoky, smoked wood",
    natural_sources=tuple("과이악우드, 훈연 향, 볶은 커피".split(", ")),
    working_cap_pct=1,
    cap_basis="irritant phenolic; trace use only",
    density_g_ml=1.129,
    state="solid",
),
Molecule(
    id="gamma-decalactone",
    name="γ-Decalactone",
    name_ko="γ-데카락톤",
    cas="706-14-9",
    formula="C10H18O2",
    molecular_weight=170.25,
    smiles="CCCCCCC1CCC(=O)O1",
    pubchem_cid=12813,
    functional_group="lactone",
    families={"fruity": 0.80, "sweet": 0.35, "floral": 0.10},
    note="middle",
    descriptor_ko="복숭아의 살구빛 과즙 향",
    descriptor_en="juicy peach",
    natural_sources=tuple("복숭아, 살구".split(", ")),
    working_cap_pct=15,
    cap_basis="no published fine-fragrance restriction",
    density_g_ml=0.95,
    state="liquid",
),
Molecule(
    id="cis-3-hexen-1-ol",
    name="cis-3-Hexen-1-ol",
    name_ko="시스-3-헥세놀",
    cas="928-96-1",
    formula="C6H12O",
    molecular_weight=100.16,
    smiles="CC/C=C\\CCO",
    pubchem_cid=5281167,
    functional_group="C6 aliphatic alcohol (green leaf alcohol)",
    families={"green": 1.00, "fruity": 0.15},
    note="top",
    descriptor_ko="갓 벤 풀잎의 날카로운 청록",
    descriptor_en="cut grass, fresh leaf",
    natural_sources=tuple("풀잎, 찻잎, 녹차".split(", ")),
    working_cap_pct=2,
    cap_basis="strong green impact; general cosmetic guidance",
    density_g_ml=0.848,
    state="liquid",
),
Molecule(
    id="hinokitiol",
    name="Hinokitiol",
    name_ko="히노키티올",
    cas="499-44-5",
    formula="C10H12O2",
    molecular_weight=164.20,
    smiles="CC(C)C1=CC(=O)C(=CC=C1)O",
    pubchem_cid=3611,
    functional_group="tropolone (7-membered phenolic ketone)",
    families={"woody": 0.50, "resinous": 0.30, "smoky": 0.10, "spicy": 0.10},
    note="middle",
    descriptor_ko="편백의 약간 금속성인 목향",
    descriptor_en="hinoki wood, faintly metallic",
    natural_sources=tuple("편백(Chamaecyparis obtusa), 측백".split(", ")),
    working_cap_pct=0.5,
    cap_basis="bioactive tropolone, not a routine fragrance material — research, trace only",
    density_g_ml=1.1,
    state="solid",
),
Molecule(
    id="methyl salicylate",
    name="Methyl Salicylate",
    name_ko="메틸 살리실레이트",
    cas="119-36-8",
    formula="C8H8O3",
    molecular_weight=152.15,
    smiles="COC(=O)C1=CC=CC=C1O",
    pubchem_cid=4133,
    functional_group="aromatic ester (salicylate)",
    families={"sweet": 0.40, "green": 0.30, "spicy": 0.20, "floral": 0.10},
    note="middle",
    descriptor_ko="겨울살이의 시원하고 단 향",
    descriptor_en="wintergreen, sweet-medicinal",
    natural_sources=tuple("겨울살이, 자작나무 껍질".split(", ")),
    working_cap_pct=2,
    cap_basis="toxic if ingested; keep away from children",
    density_g_ml=1.174,
    state="liquid",
),
)

_BY_ID: dict[str, Molecule] = {m.id: m for m in MOLECULES}
_BY_CAS: dict[str, Molecule] = {m.cas: m for m in MOLECULES if m.cas}


def all_molecules() -> tuple[Molecule, ...]:
    return MOLECULES


def get(molecule_id: str) -> Molecule:
    """Look up by id, CAS number, Korean or English name (case-insensitive)."""
    key = (molecule_id or "").strip()
    if key in _BY_ID:
        return _BY_ID[key]
    if key in _BY_CAS:
        return _BY_CAS[key]
    low = key.lower()
    for mol in MOLECULES:
        if low in (mol.id.lower(), mol.name.lower(), mol.name_ko.lower()):
            return mol
    raise KeyError(f"unknown molecule: {molecule_id!r}")


def find(query: str) -> list[Molecule]:
    """Fuzzy search over id, names, formula, family and natural sources."""
    q = (query or "").strip().lower()
    if not q:
        return list(MOLECULES)
    hits = []
    for mol in MOLECULES:
        haystack = " ".join([
            mol.id, mol.name, mol.name_ko, mol.formula, mol.functional_group,
            mol.descriptor_ko, mol.descriptor_en, " ".join(mol.natural_sources),
            " ".join(mol.families),
        ]).lower()
        if q in haystack:
            hits.append(mol)
    return hits


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return round(dot / (na * nb), 4)


def similarity(a: Molecule | str, b: Molecule | str) -> float:
    """Odour-profile cosine similarity, 0..1."""
    ma = get(a) if isinstance(a, str) else a
    mb = get(b) if isinstance(b, str) else b
    return cosine(ma.odor_vector(), mb.odor_vector())


def similar(molecule_id: str, top_k: int = 5) -> list[tuple[Molecule, float]]:
    """Most similar molecules by odour profile (itself excluded)."""
    target = get(molecule_id)
    scored = [(m, similarity(target, m)) for m in MOLECULES if m.id != target.id]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:top_k]


def note_distance(a: Molecule, b: Molecule) -> int:
    return abs(NOTES.index(a.note) - NOTES.index(b.note))


def family_overlap(a: Molecule, b: Molecule) -> float:
    """How much of the weaker profile is echoed by the other (0..1).

    Cosine similarity punishes small, sharp profiles; this overlap measure answers
    the more useful perfumery question — "is there anything both materials share?"
    """
    shared = sum(min(a.families.get(f, 0.0), b.families.get(f, 0.0)) for f in FAMILIES)
    return round(min(1.0, shared), 4)


def blend_score(a: Molecule | str, b: Molecule | str) -> float:
    """0..1 harmony estimate for a pair.

    Combines shared odour families (overlap and cosine) with the classic
    top/middle/base spread rule: pairs from adjacent notes blend more easily than
    a top with a base, and a few complementary pairs (floral + woody, citrus +
    resinous, sweet + smoky, musky + floral) get a small lift.

    This is a heuristic for *candidate* selection. It is not a trained model and
    does not predict the smell of the mixture; smell it.
    """
    ma = get(a) if isinstance(a, str) else a
    mb = get(b) if isinstance(b, str) else b
    overlap = family_overlap(ma, mb)
    sim = similarity(ma, mb)
    span = note_distance(ma, mb)
    note_factor = {0: 0.85, 1: 1.0, 2: 0.75}[span]
    complement = {
        frozenset(("floral", "woody")): 0.12,
        frozenset(("citrus", "resinous")): 0.10,
        frozenset(("green", "woody")): 0.08,
        frozenset(("sweet", "spicy")): 0.08,
        frozenset(("smoky", "sweet")): 0.07,
        frozenset(("musky", "floral")): 0.09,
        frozenset(("floral", "citrus")): 0.07,
        frozenset(("woody", "spicy")): 0.06,
    }
    dom_a = {f for f, v in ma.families.items() if v >= 0.2}
    dom_b = {f for f, v in mb.families.items() if v >= 0.2}
    lift = 0.0
    for pair, value in complement.items():
        if (pair & dom_a) and (pair & dom_b):
            lift = max(lift, value)
    base = 0.55 * overlap + 0.30 * sim
    return round(min(1.0, max(0.0, (base + lift) * note_factor)), 4)


@dataclass
class BlendReport:
    materials: list[tuple[Molecule, float]]
    weights: list[float]
    note_balance: dict[str, float]
    family_profile: dict[str, float]
    mean_harmony: float
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "materials": [
                {**m.as_dict(), "share_pct": round(w, 2)}
                for m, w in zip(self.materials, self.weights)
            ],
            "note_balance": {k: round(v, 3) for k, v in self.note_balance.items()},
            "family_profile": {k: round(v, 3) for k, v in self.family_profile.items() if v},
            "mean_harmony": self.mean_harmony,
            "warnings": self.warnings,
        }


def blend_report(accord: Mapping[str, float]) -> BlendReport:
    """Evaluate an accord: {molecule_id: share_pct} (shares are normalised to 1)."""
    if not accord:
        raise ValueError("accord must contain at least one material")
    total = sum(accord.values())
    if total <= 0:
        raise ValueError("accord shares must sum to a positive number")
    weights = [accord[k] / total for k in accord]
    materials = [get(k) for k in accord]

    note_balance = {n: 0.0 for n in NOTES}
    for mol, w in zip(materials, weights):
        note_balance[mol.note] += w

    family_profile = {f: 0.0 for f in FAMILIES}
    for mol, w in zip(materials, weights):
        for f, v in mol.families.items():
            family_profile[f] += v * w

    pairs = 0
    harmony_sum = 0.0
    for i in range(len(materials)):
        for j in range(i + 1, len(materials)):
            harmony_sum += blend_score(materials[i], materials[j])
            pairs += 1
    mean_harmony = round(harmony_sum / pairs, 4) if pairs else 1.0

    warnings: list[str] = []
    if len(materials) == 1:
        warnings.append("한 가지 원료만으로는 향의 층(탑·미들·베이스)이 만들어지지 않습니다.")
    if note_balance["top"] == 0:
        warnings.append("탑 노트가 없습니다 — 첫인상이 무거울 수 있습니다.")
    if note_balance["base"] == 0:
        warnings.append("베이스 노트가 없습니다 — 지속력이 짧아집니다.")
    if note_balance["top"] > 0.6:
        warnings.append("탑 노트 비중이 높습니다 — 휘발이 빠르고 잔향이 약해집니다.")
    low_harmony = [
        (m1.name_ko, m2.name_ko)
        for i, m1 in enumerate(materials)
        for m2 in materials[i + 1:]
        if blend_score(m1, m2) < 0.10
    ]
    if low_harmony:
        pair_text = ", ".join(f"{a}·{b}" for a, b in low_harmony[:3])
        warnings.append(f"향조가 거의 겹치지 않는 조합: {pair_text} — 소량으로 두거나 사이를 잇는 원료를 하나 두세요")
    return BlendReport(
        materials=materials,
        weights=weights,
        note_balance=note_balance,
        family_profile=family_profile,
        mean_harmony=mean_harmony,
        warnings=warnings,
    )


def family_matrix() -> dict[str, dict[str, list[str]]]:
    """Family x note grid of molecule ids — the MOLECULE matrix view."""
    grid: dict[str, dict[str, list[str]]] = {f: {n: [] for n in NOTES} for f in FAMILIES}
    for mol in MOLECULES:
        for fam, weight in mol.families.items():
            if weight >= 0.2:
                grid[fam][mol.note].append(mol.id)
    return grid


def library_stats() -> dict:
    return {
        "molecules": len(MOLECULES),
        "by_note": {n: sum(1 for m in MOLECULES if m.note == n) for n in NOTES},
        "by_family": {
            f: sum(1 for m in MOLECULES if m.families.get(f, 0) >= 0.2) for f in FAMILIES
        },
        "mean_molecular_weight": round(
            sum(m.molecular_weight for m in MOLECULES) / len(MOLECULES), 2
        ),
    }
