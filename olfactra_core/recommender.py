"""OLFACTRA ID — a rule-based accord recommender.

How it decides (and what it does not do)
----------------------------------------
This is an interpretable, tag-matching recommender over a curated accord library,
not a trained scent-prediction model. It does not claim to know how a blend will
smell on a person's skin; it proposes *candidate* structures from public odor
descriptions, note placement and published material families, which a human then
smells, adjusts and validates (ideally with GC-MS when it matters).

Every result comes with the reasons it was chosen, the note balance it produces,
and the safety cautions the materials carry — so the suggestion can be argued
with rather than merely accepted.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import molecule as mol_lib

MOODS: dict[str, str] = {
    "calm": "차분함",
    "focus": "집중",
    "energy": "활력",
    "comfort": "포근함",
    "sleep": "수면",
    "romance": "설렘",
    "clean": "상쾌함",
}

SEASONS: dict[str, str] = {
    "spring": "봄",
    "summer": "여름",
    "autumn": "가을",
    "winter": "겨울",
}

SPACES: dict[str, str] = {
    "bedroom": "침실",
    "study": "서재",
    "living": "거실",
    "entry": "현관",
    "bath": "욕실",
    "office": "사무실",
}

STYLES: dict[str, str] = {
    "minimal": "미니멀",
    "warm": "따뜻한 우디",
    "floral": "플로럴",
    "green": "그린·숲",
    "classic": "클래식",
}

#: style -> odor families that should be reinforced
STYLE_FAMILIES: dict[str, dict[str, float]] = {
    "minimal": {"woody": 0.5, "resinous": 0.3, "citrus": 0.3},
    "warm": {"sweet": 0.6, "resinous": 0.5, "spicy": 0.4, "woody": 0.4},
    "floral": {"floral": 0.9, "powdery": 0.4, "fruity": 0.2},
    "green": {"green": 0.9, "woody": 0.5, "citrus": 0.3},
    "classic": {"resinous": 0.6, "woody": 0.5, "spicy": 0.3, "floral": 0.3},
}

#: space -> note emphasis, from ventilation and distance-to-nose practice
SPACE_NOTES: dict[str, dict[str, float]] = {
    "bedroom": {"base": 0.4, "top": -0.1},
    "study": {"middle": 0.4, "top": 0.2},
    "living": {"top": 0.1, "middle": 0.2, "base": 0.2},
    "entry": {"top": 0.5},
    "bath": {"top": 0.5, "middle": 0.2},
    "office": {"middle": 0.4, "top": 0.1},
}


@dataclass(frozen=True)
class Accord:
    id: str
    name_ko: str
    name_en: str
    tagline: str
    moods: dict[str, float]
    seasons: dict[str, float]
    spaces: dict[str, float]
    styles: dict[str, float]
    materials: dict[str, float]
    product_hint: str
    story: str
    caution: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id, "name_ko": self.name_ko, "name_en": self.name_en,
            "tagline": self.tagline, "moods": self.moods, "seasons": self.seasons,
            "spaces": self.spaces, "styles": self.styles,
            "materials": self.materials, "product_hint": self.product_hint,
            "story": self.story, "caution": self.caution,
        }


ACCORDS: tuple[Accord, ...] = (
    Accord(
        id="forest-breath", name_ko="숲의 호흡", name_en="Forest Breath",
        tagline="소나무와 편백이 만드는 아침 숲의 공기",
        moods={"calm": 1.0, "focus": 0.8, "clean": 0.4},
        seasons={"spring": 0.6, "summer": 0.7, "autumn": 1.0, "winter": 0.6},
        spaces={"study": 1.0, "living": 0.8, "office": 0.5, "bedroom": 0.4},
        styles={"green": 1.0, "minimal": 0.7, "classic": 0.3},
        materials={"alpha-pinene": 26, "sabinene": 22, "linalool": 16,
                   "bornyl acetate": 16, "beta-caryophyllene": 14, "cedrol": 6},
        product_hint="reed_diffuser",
        story="탑의 피넨·사비넨이 숲의 첫 호흡을, 보르닐 아세테이트가 솔잎의 수지를, "
              "카리오필렌·세드롤이 걷다 멈춘 자리의 무게를 맡습니다. 산림치유 공간의 "
              "가장 표준적인 뼈대입니다.",
        caution="테르펜 산화 주의 — 밀봉·냉암소 보관.",
    ),
    Accord(
        id="morning-forest", name_ko="아침 숲", name_en="Morning Forest",
        tagline="이슬이 마른 솔숲, 초록의 첫인상",
        moods={"energy": 1.0, "focus": 0.7, "clean": 0.6},
        seasons={"spring": 1.0, "summer": 0.9, "autumn": 0.4, "winter": 0.2},
        spaces={"entry": 1.0, "office": 1.0, "study": 0.6, "living": 0.4},
        styles={"green": 1.0, "minimal": 0.5},
        materials={"limonene": 28, "alpha-pinene": 24, "cis-3-hexen-1-ol": 8,
                   "myrcene": 14, "bornyl acetate": 16, "alpha-terpineol": 10},
        product_hint="room_spray",
        story="시스-3-헥세놀이 '갓 벤 풀'의 날카로움을 만들고, 리모넨·피넨이 빛을, "
              "미르센이 부드러움을 더합니다. 문을 열 때 필요한 각성 쪽 블렌드입니다.",
        caution="시스-3-헥세놀은 임팩트가 강함 — 8%를 넘기지 마세요.",
    ),
    Accord(
        id="hinoki-bath", name_ko="편백 욕실", name_en="Hinoki Bath",
        tagline="나무 욕조의 김이 올라올 때",
        moods={"calm": 1.0, "clean": 0.8, "sleep": 0.3},
        seasons={"winter": 1.0, "autumn": 0.7, "spring": 0.5, "summer": 0.3},
        spaces={"bath": 1.0, "bedroom": 0.4, "living": 0.3},
        styles={"green": 0.8, "minimal": 0.8, "classic": 0.4},
        materials={"sabinene": 34, "alpha-pinene": 18, "eucalyptol": 10,
                   "terpinen-4-ol": 12, "linalool": 18, "hinokitiol": 2, "limonene": 6},
        product_hint="room_spray",
        story="사비넨이 편백의 푸른 수지를, 1,8-시네올이 김이 올라오는 청량감을, "
              "터피넨-4-올이 젖은 나무의 흙 뉘앙스를 맡습니다. 히노키티올은 2% 이하의 "
              "미량으로만 — 향보다 '금속성 결'입니다.",
        caution="1,8-시네올 — 영유아·고양이 공간에서는 제외하세요.",
    ),
    Accord(
        id="yuja-tea", name_ko="유자차", name_en="Yuja Tea",
        tagline="겨울 부엌의 따뜻한 유자청",
        moods={"comfort": 1.0, "energy": 0.5, "calm": 0.3},
        seasons={"winter": 1.0, "autumn": 0.8, "spring": 0.3, "summer": 0.2},
        spaces={"living": 1.0, "entry": 0.6, "bedroom": 0.4},
        styles={"warm": 1.0, "minimal": 0.3},
        materials={"limonene": 34, "gamma-decalactone": 12, "linalool": 18,
                   "vanillin": 12, "alpha-terpinene": 12, "cinnamaldehyde": 2,
                   "benzyl benzoate": 10},
        product_hint="reed_diffuser",
        story="유자 과피의 리모넨에 γ-데카락톤(복숭아)과 바닐린을 얹어 '차의 온도'를 "
              "만듭니다. 계피 알데하이드는 2%의 불씨 — 없으면 심심하고, 넘으면 캔들 냄새가 됩니다.",
        caution="신남알데하이드 2% — 완성품 기준 0.2%를 넘지 않게.",
    ),
    Accord(
        id="lavender-moon", name_ko="라벤더 달빛", name_en="Lavender Moon",
        tagline="잠들기 전 이불 위의 공기",
        moods={"sleep": 1.0, "calm": 0.9, "comfort": 0.4},
        seasons={"spring": 0.7, "summer": 0.6, "autumn": 0.6, "winter": 0.5},
        spaces={"bedroom": 1.0, "bath": 0.5, "living": 0.2},
        styles={"minimal": 0.7, "floral": 0.6, "warm": 0.4},
        materials={"linalool": 42, "linalyl acetate": 24, "cedrol": 12,
                   "coumarin": 8, "terpinen-4-ol": 8, "alpha-bisabolol": 6},
        product_hint="linen_mist",
        story="리날룰·리날릴 아세테이트로 라벤더의 투명함을 세우고, 세드롤과 쿠마린이 "
              "이불의 무게를 받칩니다. 캠퍼가 많은 라벤더 오일을 쓰면 '약품 냄새'가 나므로 "
              "분자 단위로 조립하는 편이 안정적입니다.",
        caution="리날룰 산화물 감작 — 오래된 원료는 쓰지 마세요.",
    ),
    Accord(
        id="rose-garden", name_ko="장미 정원", name_en="Rose Garden",
        tagline="해 질 무렵의 다마스크 로즈",
        moods={"romance": 1.0, "comfort": 0.5, "calm": 0.4},
        seasons={"spring": 1.0, "summer": 0.8, "autumn": 0.3, "winter": 0.2},
        spaces={"bedroom": 0.8, "living": 0.8, "bath": 0.3},
        styles={"floral": 1.0, "warm": 0.5, "classic": 0.3},
        materials={"phenylethyl alcohol": 34, "geraniol": 22, "citronellol": 20,
                   "beta-ionone": 8, "benzyl acetate": 10,
                   "alpha-santalol": 6},
        product_hint="edp",
        story="페닐에틸 알코올의 '깨끗한 장미'에 게라니올·시트로넬롤의 달콤한 제라늄, "
              "β-이오논의 보랏빛 가루를 겹칩니다. 산탈롤이 바탕에서 받쳐 주면 잔향이 길어집니다.",
        caution="게라니올·시트로넬롤은 EU 표시 대상 알레르겐.",
    ),
    Accord(
        id="jasmine-evening", name_ko="자스민 저녁", name_en="Jasmine Evening",
        tagline="해가 진 뒤에 더 짙어지는 꽃",
        moods={"romance": 1.0, "calm": 0.4, "comfort": 0.3},
        seasons={"summer": 1.0, "spring": 0.7, "autumn": 0.5, "winter": 0.2},
        spaces={"living": 0.8, "bedroom": 0.8, "bath": 0.3},
        styles={"floral": 1.0, "warm": 0.4},
        materials={"benzyl acetate": 32, "cis-jasmone": 14, "methyl anthranilate": 6,
                   "beta-ionone": 10, "linalool": 18, "benzyl benzoate": 20},
        product_hint="edp",
        story="벤질 아세테이트의 과즙 꽃향에 시스-자스몬의 녹색 짙음을 얹고, "
              "메틸 안트라닐레이트로 오렌지꽃 쪽으로 살짝 밀어 줍니다. "
              "벤질 벤조에이트가 전체를 붙잡습니다.",
        caution="메틸 안트라닐레이트 6% — 완성품 1% 이내.",
    ),
    Accord(
        id="sandal-study", name_ko="샌달 우드 스터디", name_en="Sandal Study",
        tagline="책장과 백단향, 집중의 냄새",
        moods={"focus": 1.0, "calm": 0.8},
        seasons={"autumn": 0.9, "winter": 0.8, "spring": 0.5, "summer": 0.4},
        spaces={"study": 1.0, "office": 0.8, "bedroom": 0.3},
        styles={"minimal": 1.0, "warm": 0.6, "classic": 0.5},
        materials={"alpha-santalol": 30, "cedrol": 22, "benzyl benzoate": 16,
                   "linalool": 14, "coumarin": 8, "alpha-cedrene": 10},
        product_hint="reed_diffuser",
        story="α-산탈롤의 크리미한 목향을 세드롤이 각지게 받치고, 리날룰이 공기를 "
              "가볍게 만듭니다. '조용하지만 존재감 있는' 서재용 구성입니다.",
        caution="산탈롤은 야생 채취 대신 재배·합성 원료를 쓰세요.",
    ),
    Accord(
        id="cedar-spice", name_ko="시더 & 스파이스", name_en="Cedar & Spice",
        tagline="겨울 서재의 따뜻한 나무와 정향",
        moods={"comfort": 0.9, "focus": 0.6, "romance": 0.4},
        seasons={"winter": 1.0, "autumn": 0.9, "spring": 0.3, "summer": 0.2},
        spaces={"living": 0.9, "study": 0.8, "entry": 0.6},
        styles={"warm": 1.0, "classic": 0.7, "minimal": 0.3},
        materials={"alpha-cedrene": 28, "cedrol": 24, "beta-caryophyllene": 22,
                   "eugenol": 4, "cinnamaldehyde": 1, "vanillin": 9,
                   "benzyl benzoate": 12},
        product_hint="reed_diffuser",
        story="세드렌·세드롤의 마른 목향에 카리오필렌(후추)을 얹고, 정향 유제놀과 계피를 "
              "1~4%의 향신료로만 씁니다. 따뜻함은 바닐린이 마무리합니다.",
        caution="유제놀 0.5%·신남알데하이드 0.2% 상한 — 완성품 기준으로 계산하세요.",
    ),
    Accord(
        id="after-rain", name_ko="비 온 뒤 흙", name_en="After Rain",
        tagline="젖은 흙과 이끼, 숲의 바닥",
        moods={"calm": 1.0, "focus": 0.5, "comfort": 0.4},
        seasons={"autumn": 1.0, "spring": 0.8, "summer": 0.5, "winter": 0.4},
        spaces={"study": 0.8, "living": 0.8, "bath": 0.4, "bedroom": 0.3},
        styles={"green": 0.8, "minimal": 0.7, "classic": 0.4},
        materials={"patchoulol": 28, "terpinen-4-ol": 18, "cis-3-hexen-1-ol": 6,
                   "germacrene-d": 14, "beta-caryophyllene": 18, "guaiacol": 4,
                   "benzyl benzoate": 12},
        product_hint="room_spray",
        story="패츌롤의 축축한 흙에 터피넨-4-올의 젖은 나무, 게르마크렌 D의 청록, "
              "과이아콜 4%의 흙먼지를 겹칩니다. '페트리코'를 분해해 조립한 구성입니다.",
        caution="과이아콜 4% — 완성품 0.5% 이내. 환기 필수.",
    ),
    Accord(
        id="musk-linen", name_ko="머스크 리넨", name_en="Musk Linen",
        tagline="갓 세탁한 흰 셔츠의 잔향",
        moods={"clean": 1.0, "comfort": 0.7, "calm": 0.5},
        seasons={"spring": 0.9, "summer": 0.8, "autumn": 0.6, "winter": 0.5},
        spaces={"bedroom": 0.9, "bath": 0.7, "living": 0.5, "office": 0.5},
        styles={"minimal": 1.0, "floral": 0.4, "warm": 0.3},
        materials={"muscone": 18, "phenylethyl alcohol": 20, "linalool": 22,
                   "benzyl benzoate": 18, "vanillin": 10, "alpha-bisabolol": 12},
        product_hint="linen_mist",
        story="무스콘의 '피부 같은' 잔향에 페닐에틸 알코올의 깨끗한 꽃, 리날룰의 공기감을 "
              "얹습니다. 오일 없이 물·에탄올로만 만들어 섬유 얼룩을 피하는 설계입니다.",
        caution="린넨 미스트에는 캐리어 오일을 넣지 마세요(얼룩·산패).",
    ),
    Accord(
        id="tonka-vanilla", name_ko="통카 & 바닐라", name_en="Tonka & Vanilla",
        tagline="포근한 겨울 담요의 달콤함",
        moods={"comfort": 1.0, "sleep": 0.5, "romance": 0.6},
        seasons={"winter": 1.0, "autumn": 0.8, "spring": 0.3, "summer": 0.2},
        spaces={"bedroom": 0.9, "living": 0.8},
        styles={"warm": 1.0, "minimal": 0.3},
        materials={"coumarin": 26, "vanillin": 30, "benzyl benzoate": 20,
                   "beta-ionone": 6, "patchoulol": 8, "alpha-bisabolol": 10},
        product_hint="body_oil",
        story="쿠마린의 건초·아몬드와 바닐린의 크림이 축이고, β-이오논이 가루 같은 "
              "여운을, 패츌롤이 바닥의 흙을 담당합니다. 오일 베이스에서 특히 잘 붙습니다.",
        caution="쿠마린 1.5% 상한 — 완성품 기준. 바닐린은 과포화되면 결정이 석출됩니다.",
    ),
    Accord(
        id="citrus-clear", name_ko="시트러스 클리어", name_en="Citrus Clear",
        tagline="회의 전에 공기를 씻어내는 향",
        moods={"clean": 1.0, "energy": 0.9, "focus": 0.5},
        seasons={"summer": 1.0, "spring": 0.9, "autumn": 0.4, "winter": 0.3},
        spaces={"office": 1.0, "entry": 0.8, "bath": 0.8, "living": 0.4},
        styles={"minimal": 0.8, "green": 0.5},
        materials={"limonene": 36, "citral": 6, "alpha-terpineol": 18,
                   "myrcene": 16, "methyl salicylate": 4, "benzyl acetate": 12,
                   "alpha-pinene": 8},
        product_hint="room_spray",
        story="리모넨의 밝은 과피에 시트랄 6%의 날카로움, α-터피네올의 라일락 같은 "
              "부드러움을 더합니다. 메틸 살리실레이트 4%는 '깨끗한 약품' 뉘앙스의 스위치입니다.",
        caution="시트랄 0.5% 상한 — 완성품 기준. 압착 감귤 오일의 광독성 주의.",
    ),
    Accord(
        id="smoke-resin", name_ko="연기와 수지", name_en="Smoke & Resin",
        tagline="훈향과 재, 늦가을 저녁",
        moods={"calm": 0.8, "focus": 0.7, "comfort": 0.5},
        seasons={"autumn": 1.0, "winter": 1.0, "spring": 0.3, "summer": 0.2},
        spaces={"living": 0.8, "study": 0.8, "entry": 0.4},
        styles={"classic": 1.0, "warm": 0.8, "minimal": 0.4},
        materials={"beta-caryophyllene": 24, "patchoulol": 20, "benzyl benzoate": 18,
                   "vanillin": 14, "guaiacol": 4, "alpha-humulene": 12,
                   "coumarin": 8},
        product_hint="reed_diffuser",
        story="카리오필렌·후물렌의 후추 같은 수지에 패츌롤의 흙, 과이아콜 4%의 연기, "
              "바닐린의 달콤함을 겹칩니다. '불을 끈 뒤의 방'을 목표로 한 구성입니다.",
        caution="과이아콜 0.5% 상한. 연소 향이 아니라 확산·분무용으로만.",
    ),
    Accord(
        id="frankincense-rite", name_ko="유향 의식", name_en="Frankincense Rite",
        tagline="해 뜰 때의 신전, 유향과 수지",
        moods={"calm": 1.0, "focus": 0.9},
        seasons={"winter": 0.8, "autumn": 0.8, "spring": 0.6, "summer": 0.4},
        spaces={"study": 0.8, "living": 0.7, "bath": 0.4, "bedroom": 0.4},
        styles={"classic": 1.0, "minimal": 0.8},
        materials={"alpha-pinene": 30, "limonene": 16, "sabinene": 14, "linalool": 10,
                   "beta-caryophyllene": 16, "benzyl benzoate": 14},
        product_hint="reed_diffuser",
        story="유향 정유의 실제 주성분비(α-피넨 우세)를 그대로 따르는 구성입니다. "
              "단순하지만, 세 성분의 비율만으로 '고대 신전'과 '솔방울' 사이를 오갑니다.",
        caution="단순 구성 — 원료의 품질 차이가 결과를 크게 바꿉니다.",
    ),
)

_BY_ID: dict[str, Accord] = {a.id: a for a in ACCORDS}


@dataclass
class Suggestion:
    accord: Accord
    score: float
    reasons: list[str]
    note_balance: dict[str, float]
    family_profile: dict[str, float]
    harmony: float
    warnings: list[str]
    product_hint: str
    load_hint: tuple[float, float]

    def as_dict(self) -> dict:
        from .studio import get_product_type
        pt = get_product_type(self.product_hint)
        return {
            "accord": {
                **self.accord.as_dict(),
                "materials_detail": [
                    {**mol_lib.get(mid).as_dict(), "share_pct": share}
                    for mid, share in self.accord.materials.items()
                ],
            },
            "score": round(self.score, 1),
            "reasons": self.reasons,
            "note_balance": {k: round(v, 3) for k, v in self.note_balance.items()},
            "family_profile": {k: round(v, 3) for k, v in self.family_profile.items() if v},
            "harmony": self.harmony,
            "warnings": self.warnings,
            "product_hint": self.product_hint,
            "product_label": pt.name_ko,
            "load_hint": [pt.load_min, pt.load_max],
            "load_default": pt.load_default,
        }


def accords() -> tuple[Accord, ...]:
    return ACCORDS


def get_accord(accord_id: str) -> Accord:
    return _BY_ID[accord_id]


def _score(
    accord: Accord,
    mood: str | None, season: str | None,
    space: str | None, style: str | None,
) -> tuple[float, list[str]]:
    score = 0.0
    total = 0.0
    reasons: list[str] = []

    if mood:
        total += 3.0
        weight = accord.moods.get(mood, 0.0) * 3.0
        score += weight
        if mood in accord.moods:
            reasons.append(f"{MOODS[mood]} 기분에 {accord.moods[mood]:.1f} 만큼 맞습니다")
    if season:
        total += 1.5
        score += accord.seasons.get(season, 0.0) * 1.5
        if accord.seasons.get(season, 0) >= 0.7:
            reasons.append(f"{SEASONS[season]}에 잘 어울리는 향조 구성")
    if space:
        total += 2.0
        score += accord.spaces.get(space, 0.0) * 2.0
        if accord.spaces.get(space, 0) >= 0.7:
            reasons.append(f"{SPACES[space]} 공간의 발향 거리·환기에 맞습니다")
    if style:
        total += 2.0
        score += accord.styles.get(style, 0.0) * 2.0
        if accord.styles.get(style, 0) >= 0.7:
            reasons.append(f"{STYLES[style]} 스타일에 맞는 향조 축")

    # odor-family fit for the requested style
    if style:
        profile = _family_profile(accord)
        norm = sum(profile.values()) or 1.0
        profile = {k: v / norm for k, v in profile.items()}
        style_fit = sum(profile.get(fam, 0) * w for fam, w in STYLE_FAMILIES[style].items())
        score += style_fit * 4.0
        total += 4.0

    # note emphasis for the room
    if space:
        balance = _note_balance(accord)
        fit = sum(balance.get(note, 0) * w for note, w in SPACE_NOTES[space].items())
        score += max(0.0, fit) * 1.5
        total += 1.5

    pct = 100.0 * score / total if total else 0.0
    return min(100.0, pct), reasons


def _family_profile(accord: Accord) -> dict[str, float]:
    profile = {f: 0.0 for f in mol_lib.FAMILIES}
    total = sum(accord.materials.values()) or 1.0
    for mid, share in accord.materials.items():
        if mid not in {m.id for m in mol_lib.MOLECULES}:
            continue
        m = mol_lib.get(mid)
        for fam, w in m.families.items():
            profile[fam] += w * (share / total)
    return profile


def _note_balance(accord: Accord) -> dict[str, float]:
    balance = {n: 0.0 for n in mol_lib.NOTES}
    total = sum(accord.materials.values()) or 1.0
    for mid, share in accord.materials.items():
        if mid not in {m.id for m in mol_lib.MOLECULES}:
            continue
        balance[mol_lib.get(mid).note] += share / total
    return balance


def recommend(
    mood: str | None = None,
    season: str | None = None,
    space: str | None = None,
    style: str | None = None,
    limit: int = 3,
    exclude: tuple[str, ...] = (),
) -> list[Suggestion]:
    """Rank accords for the given conditions and return the best `limit` of them."""
    if mood and mood not in MOODS:
        raise ValueError(f"unknown mood {mood!r}; choose from {sorted(MOODS)}")
    if season and season not in SEASONS:
        raise ValueError(f"unknown season {season!r}; choose from {sorted(SEASONS)}")
    if space and space not in SPACES:
        raise ValueError(f"unknown space {space!r}; choose from {sorted(SPACES)}")
    if style and style not in STYLES:
        raise ValueError(f"unknown style {style!r}; choose from {sorted(STYLES)}")

    ranked: list[Suggestion] = []
    for accord in ACCORDS:
        if accord.id in exclude:
            continue
        score, reasons = _score(accord, mood, season, space, style)
        report = mol_lib.blend_report(
            {mid: share for mid, share in accord.materials.items() if share > 0}
        )
        from .studio import get_product_type
        pt = get_product_type(accord.product_hint)
        warnings = list(report.warnings)
        if accord.caution:
            warnings.append(accord.caution)
        ranked.append(Suggestion(
            accord=accord,
            score=score,
            reasons=reasons or ["조건이 지정되지 않아 향조 균형을 기준으로 제안했습니다"],
            note_balance=report.note_balance,
            family_profile=report.family_profile,
            harmony=report.mean_harmony,
            warnings=warnings,
            product_hint=accord.product_hint,
            load_hint=(pt.load_min, pt.load_max),
        ))

    ranked.sort(key=lambda s: (s.score, s.harmony), reverse=True)

    # one accord per dominant family cluster, so the three results are alternatives
    picked: list[Suggestion] = []
    seen_signature: set[tuple[str, ...]] = set()
    for item in ranked:
        signature = tuple(sorted(
            f for f, v in item.accord.materials.items() if v >= 15
        ))
        if any(len(set(signature) & set(s)) >= 3 for s in seen_signature):
            continue
        picked.append(item)
        seen_signature.add(signature)
        if len(picked) >= limit:
            break
    return picked


def dimensions() -> dict:
    return {
        "moods": [{"id": k, "label": v} for k, v in MOODS.items()],
        "seasons": [{"id": k, "label": v} for k, v in SEASONS.items()],
        "spaces": [{"id": k, "label": v} for k, v in SPACES.items()],
        "styles": [{"id": k, "label": v} for k, v in STYLES.items()],
    }
