"""OLFACTRA STUDIO — DIY dilution calculator with a safety gate.

What it computes
----------------
Given a product type, a total volume and a fragrance load, STUDIO splits the
bottle into a fragrance concentrate and a carrier base, converts every material
share into grams and millilitres using the material's own density, and compares
the resulting concentration in the *finished product* with a conservative
working ceiling.

Two things are easy to get wrong in DIY perfumery, so they are explicit here:

1. **% of what.**  A "20 % load" means 20 % of the finished bottle is fragrance
   concentrate — not that each material is 20 % of everything. Each material's
   finished-product share is ``load × share/100``.
2. **w/w vs v/v.**  Volumes are what you measure; safety limits are mass-based.
   STUDIO reports both and judges against the mass-based (w/w) figure.

The ceilings are internal, conservative working limits for hobby and research
blending, gathered from public cosmetic/fragrance guidance. They are not IFRA
certificates, not a regulatory opinion, and not a substitute for a real safety
assessment before selling or distributing anything.

Exposure route matters
----------------------
Skin sensitisation and irritation limits are written for products that stay on
skin. A reed diffuser is not rubbed into skin, so the binding limit there is
indoor air concentration rather than dermal dose; STUDIO therefore judges ambient
formats against the same ceiling multiplied by an explicit ``cap_scale``
(× 6 diffuser, × 3 room spray, × 1.5 linen mist) and shows both the base and the
effective ceiling in the output. Ventilation, children and pet warnings are
never relaxed by that factor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from . import molecule as mol_lib

#: Fragrance allergens that carry a labelling duty in the EU when they exceed
#: 0.001 % in leave-on and 0.01 % in rinse-off products (public Annex III list).
EU_DECLARABLE_ALLERGENS: tuple[str, ...] = (
    "limonene", "linalool", "citral", "geraniol", "citronellol", "eugenol", "coumarin",
)

#: Materials that need extra care around children, pets or airways.
CHILD_PET_FLAGS: dict[str, str] = {
    "eucalyptol": "1,8-시네올 — 영유아·고양이에게 위험",
    "camphor": "캠퍼 — 영유아 경련 위험 보고, 반려동물 주의",
    "fenchone": "캠퍼 계열 케톤 — 영유아 공간 주의",
    "eugenol": "유제놀 — 고양이 간 대사 취약, 점막 자극",
    "methyl salicylate": "메틸 살리실레이트 — 섭취 시 독성, 어린이 손이 닿지 않게",
    "cinnamaldehyde": "신남알데하이드 — 강한 감작 물질",
    "hinokitiol": "히노키티올 — 상용 향료 아님, 연구·미량",
}


@dataclass(frozen=True)
class Carrier:
    name: str
    ratio: float          # share of the carrier (base) phase
    density_g_ml: float
    role: str = ""


@dataclass(frozen=True)
class ProductType:
    id: str
    name_ko: str
    name_en: str
    load_default: float
    load_min: float
    load_max: float
    carriers: tuple[Carrier, ...]
    description: str
    cautions: tuple[str, ...] = ()
    exposure: str = "skin"      # skin | surface
    cap_scale: float = 1.0      # relaxed ceiling factor for non-skin exposure routes

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name_ko": self.name_ko,
            "name_en": self.name_en,
            "load_default": self.load_default,
            "load_min": self.load_min,
            "load_max": self.load_max,
            "carriers": [
                {"name": c.name, "ratio": c.ratio, "density_g_ml": c.density_g_ml, "role": c.role}
                for c in self.carriers
            ],
            "description": self.description,
            "cautions": list(self.cautions),
            "exposure": self.exposure,
            "cap_scale": self.cap_scale,
        }


PRODUCT_TYPES: dict[str, ProductType] = {
    "reed_diffuser": ProductType(
        id="reed_diffuser",
        name_ko="리드 디퓨저",
        name_en="Reed diffuser",
        load_default=20.0, load_min=15.0, load_max=25.0,
        carriers=(
            Carrier("다이프로필렌글리콜(DPG)", 0.55, 1.022, "점도·발향 조절"),
            Carrier("아이소프로필 미리스테이트(IPM)", 0.25, 0.853, "피부·표면 안전성이 높은 캐리어"),
            Carrier("에탄올 95%", 0.20, 0.805, "초기 발향"),
        ),
        description="막대에 향을 태워 공간으로 퍼뜨리는 무전원 확산 방식.",
        cautions=("가연성 액체 — 화기·직사광선 금지", "나무·가구 표면에 닿으면 얼룩이 남을 수 있음"),
        exposure="surface", cap_scale=6.0,
    ),
    "room_spray": ProductType(
        id="room_spray",
        name_ko="룸 스프레이",
        name_en="Room spray",
        load_default=5.0, load_min=3.0, load_max=8.0,
        carriers=(
            Carrier("에탄올 95%", 0.75, 0.805, "용해·건조"),
            Carrier("정제수", 0.25, 0.998, "자극 완화"),
        ),
        description="에탄올 기반 분무 — 순간 발향이 좋고 잔향은 짧다.",
        cautions=("에탄올 인화성 — 흡연·화기 근처 사용 금지", "물 비율이 높으면 테르펜이 뿌옇게 분리될 수 있음"),
        exposure="surface", cap_scale=3.0,
    ),
    "linen_mist": ProductType(
        id="linen_mist",
        name_ko="린넨·필로우 미스트",
        name_en="Linen & pillow mist",
        load_default=2.0, load_min=1.0, load_max=4.0,
        carriers=(
            Carrier("에탄올 95%", 0.45, 0.805, "용해"),
            Carrier("정제수", 0.55, 0.998, "섬유 잔류 최소화"),
        ),
        description="섬유에 뿌리는 저농도 미스트. 오일 프리로 설계한다.",
        cautions=("오일을 넣으면 얼룩·산패 위험 — 캐리어 오일 금지", "민감성 피부는 베개에 직접 분사하지 않기"),
        exposure="surface", cap_scale=1.5,
    ),
    "eau_de_cologne": ProductType(
        id="eau_de_cologne",
        name_ko="오 드 코롱",
        name_en="Eau de cologne",
        load_default=5.0, load_min=3.0, load_max=8.0,
        carriers=(
            Carrier("에탄올 95%", 0.80, 0.805, "용해·발향"),
            Carrier("정제수", 0.20, 0.998, "자극 완화"),
        ),
        description="가볍게 뿌리는 저농도 향수. 2~3시간 잔향.",
    ),
    "edt": ProductType(
        id="edt",
        name_ko="오 드 뚜왈렛 (EDT)",
        name_en="Eau de toilette",
        load_default=10.0, load_min=8.0, load_max=15.0,
        carriers=(
            Carrier("에탄올 95%", 0.85, 0.805, "용해"),
            Carrier("정제수", 0.15, 0.998, "자극 완화"),
        ),
        description="일상용 향수. 4~6시간 잔향.",
    ),
    "edp": ProductType(
        id="edp",
        name_ko="오 드 퍼퓸 (EDP)",
        name_en="Eau de parfum",
        load_default=20.0, load_min=15.0, load_max=25.0,
        carriers=(
            Carrier("에탄올 95%", 0.80, 0.805, "용해"),
            Carrier("정제수", 0.20, 0.998, "자극 완화"),
        ),
        description="농도 높은 향수. 6~8시간 잔향, 원료 안전 상한 관리가 중요.",
        cautions=("고농도 — 팔 안쪽 패치 테스트 24시간 권장",),
    ),
    "body_oil": ProductType(
        id="body_oil",
        name_ko="바디 오일 퍼퓸",
        name_en="Perfume body oil",
        load_default=2.0, load_min=1.0, load_max=3.0,
        carriers=(
            Carrier("호호바 오일", 0.70, 0.865, "안정성 높은 액체 왁스"),
            Carrier("분획 코코넛 오일", 0.30, 0.930, "가벼운 발림성"),
        ),
        description="오일 베이스에 향을 녹인 밀착형 향. 잔향이 길다.",
        cautions=("오일 산패 — 어두운 곳·6개월 내 사용", "직물 얼룩 주의"),
    ),
    "solid_perfume": ProductType(
        id="solid_perfume",
        name_ko="고체 향 (솔리드 퍼퓸)",
        name_en="Solid perfume",
        load_default=25.0, load_min=20.0, load_max=30.0,
        carriers=(
            Carrier("호호바 오일", 0.60, 0.865, "연화·피부 친화"),
            Carrier("비즈왁스", 0.40, 0.960, "형태 유지"),
        ),
        description="왁스에 향을 담아 손끝으로 바르는 형태. 휴대가 쉽다.",
        cautions=("왁스 녹이는 과정의 화상 주의", "고체 원료는 미리 분쇄·용해"),
    ),
}

REQUIRED_RATIO_TOLERANCE = 0.5   # %p


@dataclass
class MaterialRow:
    id: str
    name_ko: str
    name: str
    note: str
    share_pct: float            # share of the concentrate
    volume_ml: float            # neat material volume in the bottle
    mass_g: float               # neat material mass in the bottle
    finished_pct_ww: float      # mass % of the finished product
    cap_pct: float              # effective working ceiling for this exposure route
    cap_ratio: float            # finished_pct_ww / cap_pct
    status: str                 # ok | caution | over
    is_solid: bool
    allergen: bool
    cap_base_pct: float = 0.0   # ceiling before the exposure-route factor

    def as_dict(self) -> dict:
        return {
            "id": self.id, "name_ko": self.name_ko, "name": self.name,
            "note": self.note, "share_pct": round(self.share_pct, 2),
            "volume_ml": round(self.volume_ml, 3), "mass_g": round(self.mass_g, 3),
            "finished_pct_ww": round(self.finished_pct_ww, 4),
            "cap_pct": round(self.cap_pct, 3), "cap_base_pct": self.cap_base_pct,
            "cap_ratio": round(self.cap_ratio, 3),
            "status": self.status, "is_solid": self.is_solid, "allergen": self.allergen,
        }


@dataclass
class Formula:
    product_type: ProductType
    volume_ml: float
    load_pct: float
    rows: list[MaterialRow]
    carrier_rows: list[dict]
    total_mass_g: float
    fragrance_mass_g: float
    fragrance_volume_ml: float
    finished_load_pct_ww: float
    status: str                       # ok | caution | over
    warnings: list[str] = field(default_factory=list)
    allergens: list[str] = field(default_factory=list)
    note_balance: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "product_type": self.product_type.as_dict(),
            "volume_ml": self.volume_ml,
            "load_pct": self.load_pct,
            "rows": [r.as_dict() for r in self.rows],
            "carrier_rows": self.carrier_rows,
            "total_mass_g": round(self.total_mass_g, 3),
            "fragrance_mass_g": round(self.fragrance_mass_g, 3),
            "fragrance_volume_ml": round(self.fragrance_volume_ml, 3),
            "finished_load_pct_ww": round(self.finished_load_pct_ww, 3),
            "status": self.status,
            "warnings": self.warnings,
            "allergens": self.allergens,
            "note_balance": {k: round(v, 3) for k, v in self.note_balance.items()},
        }


def product_types() -> list[ProductType]:
    return list(PRODUCT_TYPES.values())


def get_product_type(product_type: str) -> ProductType:
    key = (product_type or "").strip().lower()
    if key in PRODUCT_TYPES:
        return PRODUCT_TYPES[key]
    for pt in PRODUCT_TYPES.values():
        if key in (pt.name_ko.lower(), pt.name_en.lower()):
            return pt
    raise KeyError(f"unknown product type: {product_type!r}")


def _normalise(accord: Mapping[str, float]) -> dict[str, float]:
    cleaned = {k: float(v) for k, v in accord.items() if float(v) > 0}
    if not cleaned:
        raise ValueError("accord must contain at least one material with a positive share")
    total = sum(cleaned.values())
    return {k: v / total * 100.0 for k, v in cleaned.items()}


def formulate(
    product_type: str,
    volume_ml: float,
    load_pct: float | None = None,
    accord: Mapping[str, float] | None = None,
) -> Formula:
    """Build a formula with per-material grams, millilitres and a safety verdict."""
    pt = get_product_type(product_type)
    if volume_ml <= 0:
        raise ValueError("volume_ml must be positive")
    load = pt.load_default if load_pct is None else float(load_pct)
    if load <= 0:
        raise ValueError("load_pct must be positive")
    if accord is None:
        raise ValueError("accord is required ({molecule_id: share_pct})")

    shares = _normalise(accord)
    warnings: list[str] = []

    frag_volume = volume_ml * load / 100.0
    base_volume = volume_ml - frag_volume

    rows: list[MaterialRow] = []
    frag_mass = 0.0
    for mid, share in shares.items():
        m = mol_lib.get(mid)
        neat_vol = frag_volume * share / 100.0
        neat_mass = neat_vol * m.density_or()
        frag_mass += neat_mass
        rows.append(MaterialRow(
            id=m.id, name_ko=m.name_ko, name=m.name, note=m.note,
            share_pct=share, volume_ml=neat_vol, mass_g=neat_mass,
            finished_pct_ww=0.0, cap_pct=m.working_cap_pct * pt.cap_scale, cap_ratio=0.0,
            cap_base_pct=m.working_cap_pct,
            status="ok", is_solid=m.is_solid, allergen=m.id in EU_DECLARABLE_ALLERGENS,
        ))

    carrier_rows = []
    base_mass = 0.0
    for carrier in pt.carriers:
        vol = base_volume * carrier.ratio
        mass = vol * carrier.density_g_ml
        base_mass += mass
        carrier_rows.append({
            "name": carrier.name, "role": carrier.role,
            "ratio_pct": round(carrier.ratio * 100, 2),
            "volume_ml": round(vol, 3), "mass_g": round(mass, 3),
            "density_g_ml": carrier.density_g_ml,
        })

    total_mass = frag_mass + base_mass
    finished_load = frag_mass / total_mass * 100.0 if total_mass else 0.0

    worst = 0.0
    allergens: list[str] = []
    for row in rows:
        row.finished_pct_ww = row.mass_g / total_mass * 100.0 if total_mass else 0.0
        row.cap_ratio = row.finished_pct_ww / row.cap_pct if row.cap_pct else 0.0
        if row.cap_ratio > 1.0:
            row.status = "over"
        elif row.cap_ratio >= 0.6:
            row.status = "caution"
        worst = max(worst, row.cap_ratio)
        if row.allergen and row.finished_pct_ww >= 0.001:
            allergens.append(row.name_ko)

    note_balance = {n: 0.0 for n in mol_lib.NOTES}
    for row in rows:
        note_balance[row.note] += row.share_pct / 100.0

    # ---- safety gate -------------------------------------------------
    if load > pt.load_max:
        warnings.append(
            f"부향률 {load:g}%가 {pt.name_ko} 권장 상한({pt.load_max:g}%)을 넘습니다 — "
            "향이 뭉개지고 피부·호흡기 자극 위험이 커집니다."
        )
    if load < pt.load_min:
        warnings.append(f"부향률 {load:g}%는 {pt.name_ko} 권장 하한({pt.load_min:g}%)보다 낮습니다 — 잔향이 거의 없습니다.")

    if pt.cap_scale != 1.0:
        warnings.append(
            f"노출 경로 보정: {pt.name_ko}은(는) 피부 도포 제품이 아니라 "
            f"공간 확산·분무 제형이므로 상한을 ×{pt.cap_scale:g}로 완화해 판정했습니다 "
            "(피부 기준 상한 × 노출 경로 계수). 환기·영유아·반려동물 주의는 완화되지 않습니다."
        )

    over = [r for r in rows if r.status == "over"]
    for row in over:
        warnings.append(
            f"{row.name_ko}: 완성품 {row.finished_pct_ww:.3f}% (적용 상한 {row.cap_pct:g}% = "
            f"피부 기준 {row.cap_base_pct:g}% × {pt.cap_scale:g}) — "
            f"{row.cap_ratio:.1f}배 초과. 배합비를 줄이거나 부향률을 낮추세요."
        )
    caution = [r for r in rows if r.status == "caution"]
    for row in caution:
        warnings.append(
            f"{row.name_ko}: 완성품 {row.finished_pct_ww:.3f}% — 적용 상한의 {row.cap_ratio * 100:.0f}%. "
            f"({mol_lib.get(row.id).cap_basis})"
        )

    pet_flags = [CHILD_PET_FLAGS[r.id] for r in rows if r.id in CHILD_PET_FLAGS]
    if pet_flags:
        warnings.append("영유아·반려동물 주의 성분: " + "; ".join(pet_flags))

    alcohol_ratio = sum(c.ratio for c in pt.carriers if "에탄올" in c.name)
    if alcohol_ratio > 0.3:
        warnings.append("에탄올 비율이 높습니다 — 인화성 액체이므로 화기·정전기·직사광선을 피하세요.")

    water_ratio = sum(c.ratio for c in pt.carriers if "수" in c.name)
    if water_ratio >= 0.5 and load >= 3:
        warnings.append("물 비율이 높습니다 — 테르펜이 뿌옇게 분리될 수 있어 사용 전 흔들어 쓰는 제형으로 설계하세요.")

    solids = [r for r in rows if r.is_solid]
    if solids:
        warnings.append(
            "고체 원료(" + ", ".join(r.name_ko for r in solids) + ")는 부피 대신 무게로 달아 "
            "에탄올이나 오일에 먼저 녹인 뒤 섞으세요. 시간이 지나면 결정이 석출될 수 있습니다."
        )

    if finished_load > load * 1.02:
        warnings.append(
            "캐리어 밀도가 낮아 향의 질량 비율(w/w)이 부피 기준(w/v)보다 높습니다 — "
            "수치를 라벨에 적을 때는 w/w를 쓰세요."
        )

    warnings.extend(pt.cautions)

    status = "over" if (over or load > pt.load_max) else ("caution" if caution else "ok")

    return Formula(
        product_type=pt,
        volume_ml=float(volume_ml),
        load_pct=load,
        rows=sorted(rows, key=lambda r: (mol_lib.NOTES.index(r.note), -r.share_pct)),
        carrier_rows=carrier_rows,
        total_mass_g=total_mass,
        fragrance_mass_g=frag_mass,
        fragrance_volume_ml=frag_volume,
        finished_load_pct_ww=finished_load,
        status=status,
        warnings=warnings,
        allergens=sorted(set(allergens)),
        note_balance=note_balance,
    )


def safety_sweep(molecule_id: str, product_type: str, volume_ml: float = 50.0) -> dict:
    """How much of one material is still inside its ceiling, at a given load."""
    pt = get_product_type(product_type)
    m = mol_lib.get(molecule_id)
    # mass fraction of the concentrate in the bottle at the default load, mass basis
    probe = propose_max_share(molecule_id, product_type)
    return {
        "molecule": m.id,
        "product_type": pt.id,
        "cap_pct": m.working_cap_pct,
        "max_safe_share_pct_of_concentrate": probe,
        "load_pct": pt.load_default,
        "basis": m.cap_basis,
    }


def propose_max_share(molecule_id: str, product_type: str, load_pct: float | None = None) -> float:
    """Largest share of the concentrate (%) that keeps a material under its ceiling."""
    pt = get_product_type(product_type)
    m = mol_lib.get(molecule_id)
    load = pt.load_default if load_pct is None else load_pct
    # finished % ≈ load * share * (fragrance density / bottle density); use 1.0 as first order
    share = m.working_cap_pct * pt.cap_scale / load * 100.0
    return round(min(100.0, max(0.0, share)), 2)


def dilution_table(product_type: str, volume_ml: float = 50.0,
                   loads: tuple[float, ...] = (5, 10, 15, 20, 25, 30)) -> list[dict]:
    pt = get_product_type(product_type)
    out = []
    for load in loads:
        out.append({
            "load_pct": load,
            "fragrance_ml": round(volume_ml * load / 100, 2),
            "base_ml": round(volume_ml * (1 - load / 100), 2),
            "within_range": pt.load_min <= load <= pt.load_max,
        })
    return out
