"""OLFACTRA ATLAS — the origins and history of scent, and the forest materials behind it.

Scope and limits
----------------
Every entry is built from *public* sources: ancient texts that are in the public
domain (Herodotus, Theophrastus, Pliny, Plutarch, the Hebrew Bible), museum and
herbarium descriptions, and peer-reviewed open literature on plant volatiles.
Where a claim is a later tradition rather than a primary record, the text says so
("전승에 따르면" / "attributed"). No proprietary formula, trademark, captive
material or trade-secret composition is reproduced here.

The dates are deliberately coarse (centuries, not years) because the historical
record for aromatic materials is almost always a range of first attestations,
not a single invention date.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

CATEGORIES: dict[str, str] = {
    "resin": "수지·향",
    "wood": "목재·수피",
    "flower": "꽃",
    "fruit": "과실",
    "spice": "향신료",
    "seed": "종자·열매",
    "animal": "동물성",
    "forest": "숲·산림치유",
    "history": "교역·문화사",
}


@dataclass(frozen=True)
class AtlasEntry:
    id: str
    name_ko: str
    name_en: str
    botanical: str
    category: str
    era_label: str
    year: int                      # 음수 = 기원전, 정렬용
    region: str
    material_part: str
    molecules: tuple[str, ...]
    story: str
    science: str
    use_ko: str
    sources: tuple[tuple[str, str], ...]   # (문헌, 설명)
    caution: str = ""
    conservation: str = ""
    ideas: tuple[str, ...] = field(default_factory=tuple)

    @property
    def category_label(self) -> str:
        return CATEGORIES.get(self.category, self.category)

    @property
    def era_short(self) -> str:
        return "기원전" if self.year < 0 else "기원후"

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name_ko": self.name_ko,
            "name_en": self.name_en,
            "botanical": self.botanical,
            "category": self.category,
            "category_label": self.category_label,
            "era_label": self.era_label,
            "year": self.year,
            "region": self.region,
            "material_part": self.material_part,
            "molecules": list(self.molecules),
            "story": self.story,
            "science": self.science,
            "use_ko": self.use_ko,
            "sources": [{"label": a, "detail": b} for a, b in self.sources],
            "caution": self.caution,
            "conservation": self.conservation,
            "ideas": list(self.ideas),
        }


ATLAS: tuple[AtlasEntry, ...] = (
    AtlasEntry(
        id="frankincense",
        name_ko="유향 · 프랑킨센스",
        name_en="Frankincense",
        botanical="Boswellia sacra / B. carteri",
        category="resin",
        era_label="고대 이집트·남아라비아 (기원전 3천년경~)",
        year=-3000,
        region="오만 도파르, 예멘 하드라마우트, 소말리아",
        material_part="수피에 상처를 내어 채취한 올레오검 수지",
        molecules=("alpha-pinene", "limonene", "myrcene", "sabinene", "beta-caryophyllene"),
        story=(
            "유향은 인류가 가장 오래 기록한 향 가운데 하나입니다. 기원전 15세기 "
            "하트셉수트 여왕의 푼트 원정을 그린 데이르 엘바흐리 신전 부조에는 유향 "
            "나무가 뿌리째 배에 실려 오는 장면이 남아 있고, 이집트 신전에서는 해 뜰 때 "
            "유향을 태우고 해 질 때 몰약을 태웠습니다. 헤로도토스는 『역사』 3권에서 "
            "아라비아의 유향나무와 그것을 지키는 날개 달린 뱀 이야기를 전합니다."
        ),
        science=(
            "유향 정유의 머리 향은 α-피넨이 이끌고, 리모넨·미르센·사비넨이 뒤를 받칩니다. "
            "수지 자체의 보스웰릭산 계열은 공개 문헌에서 항염 연구 대상으로 다뤄져 왔습니다. "
            "OLFACTRA에서는 '수지의 푸른 탑 노트 + 후추 같은 베이스'로 모델링합니다."
        ),
        use_ko="신전·명상 공간의 훈향. 오늘날에는 디퓨저·룸스프레이의 '숲의 성스러움' 축으로.",
        sources=(
            ("Herodotus, Histories III.107", "아라비아 유향과 수확 이야기"),
            ("Deir el-Bahari reliefs (Hatshepsut, c. 1470 BCE)", "푼트 원정과 유향나무 운반 부조"),
            ("Matthew 2:11", "동방박사의 예물 중 하나로 기록"),
            ("Plutarch, De Iside et Osiride", "이집트 제향 관행 기술"),
        ),
        caution="정유 원액은 피부 자극 가능. 임신부·영유아 공간에서는 환기와 저농도 사용.",
        conservation="Boswellia 채취는 지역사회 관리가 중요하며, 일부 개체군은 남획 연구 보고가 있음.",
        ideas=("유향 의식", "시더 & 스파이스"),
    ),
    AtlasEntry(
        id="myrrh",
        name_ko="몰약",
        name_en="Myrrh",
        botanical="Commiphora myrrha",
        category="resin",
        era_label="고대 이집트 (기원전 3천년경~)",
        year=-2900,
        region="이집트, 아라비아 남부, 동아프리카(소말리아·에티오피아)",
        material_part="수피에서 스스로 흘러나와 굳은 수지",
        molecules=("beta-caryophyllene", "eugenol", "guaiacol", "alpha-humulene"),
        story=(
            "몰약은 기원전 1550년경의 에베르스 파피루스에 이미 향료이자 방부 재료로 "
            "등장하고, 이집트의 미라 제작 과정에서 향과 방부를 겸해 쓰였습니다. "
            "구약의 아가서는 '몰약'을 사랑의 향으로 노래하고, 출애굽기 30장의 거룩한 "
            "관유 처방에도 몰약이 첫 재료로 나옵니다."
        ),
        science=(
            "몰약의 향은 푸라노세스퀴테르펜과 함께 소량의 유제놀·과이아콜이 만드는 "
            "쓸쓸한 연기·약재 느낌이 특징입니다. 같은 수지라도 유향이 '푸른 수지'라면 "
            "몰약은 '따뜻하고 쌉싸름한 수지'로, 두 재료는 고대부터 짝을 이뤄 쓰였습니다."
        ),
        use_ko="수지·스파이시 베이스. 유향과 1:1로 묶으면 고대 제향의 뼈대가 됩니다.",
        sources=(
            ("Ebers Papyrus (c. 1550 BCE)", "향료·방부 처방"),
            ("Song of Songs 1:13, 5:5", "몰약의 향 비유"),
            ("Exodus 30:23", "거룩한 관유의 재료"),
            ("Pliny, Naturalis Historia XII–XIII", "수지와 향유 교역 기술"),
        ),
        caution="유제놀 함유 → 완성품 0.5% 이하 권장. 피부 자극 가능.",
        conservation="야생 채취 의존. 수지 채취 인증·지역 관리 여부를 확인.",
        ideas=("연기와 수지",),
    ),
    AtlasEntry(
        id="kyphi",
        name_ko="키피 · 이집트 신전의 복합향",
        name_en="Kyphi",
        botanical="복합 처방 (수지·향신료·과실)",
        category="history",
        era_label="고대 이집트 신왕국 (기원전 2천년경~)",
        year=-2000,
        region="이집트 테베",
        material_part="수지·향신료·건과를 꿀과 포도주로 반죽해 숙성한 향",
        molecules=("alpha-pinene", "eugenol", "cinnamaldehyde", "beta-caryophyllene", "vanillin"),
        story=(
            "키피는 이집트 신전에서 해질녘에 태운 복합 향입니다. 플루타르코스는 "
            "『이시스와 오시리스에 대하여』에서 키피의 재료를 열여섯 가지로 전하는데, "
            "유향·몰약·시나몬·카시아·등나무 열매·꿀·포도주 등이 포함됩니다. 오늘날 "
            "재현 시도는 문헌 해석마다 재료가 달라 '정답'이 하나가 아니라는 점이 오히려 "
            "이 향의 성격을 보여 줍니다."
        ),
        science=(
            "키피는 '단일 원료'가 아니라 '블렌드'를 기록한 가장 오래된 사례 중 하나입니다. "
            "탑(수지의 피넨) → 미들(시나몬·유제놀) → 베이스(수지·바닐라)로 이어지는 "
            "3층 구조가 이미 기원전에 설계되어 있었던 셈입니다."
        ),
        use_ko="역사 재현 블렌드. 훈향·룸스프레이의 '고대 제향' 테마.",
        sources=(
            ("Plutarch, De Iside et Osiride 80", "키피 재료 목록"),
            ("Ebers Papyrus", "향 재료의 이집트 기록"),
        ),
        caution="계피 알데하이드·유제놀은 자극성 → 전체의 0.2% 이하로 흔적만.",
        ideas=("유향 의식", "시더 & 스파이스"),
    ),
    AtlasEntry(
        id="cedar-lebanon",
        name_ko="레바논 삼나무",
        name_en="Cedar of Lebanon",
        botanical="Cedrus libani",
        category="wood",
        era_label="페니키아·고대 이스라엘 (기원전 2천5백년~)",
        year=-2500,
        region="레바논 산맥, 시리아, 터키 타우루스",
        material_part="심재와 목재 증류 정유",
        molecules=("alpha-cedrene", "cedrol", "beta-caryophyllene", "alpha-copaene"),
        story=(
            "삼나무는 페니키아의 조선 재료이자 이집트의 목재 수입품이었고, "
            "열왕기상 6장은 솔로몬이 성전을 지을 때 레바논 삼나무를 들여왔다고 전합니다. "
            "오늘날 레바논 국기에도 그려진 이 나무는 '오래 견디는 향'의 상징이 되었습니다. "
            "실제 향료로 쓰는 시더우드는 같은 향나무과의 Juniperus virginiana 등 다른 "
            "수종인 경우가 많다는 점은 구분해서 봐야 합니다."
        ),
        science=(
            "시더우드의 특징은 α-세드렌·세드롤이 만드는 '마른 연필' 같은 목향입니다. "
            "세스퀴테르펜은 분자량이 커서(204~222) 휘발이 느리고, 그래서 미들~베이스의 "
            "뼈대로 쓰입니다. 피톤치드 연구에서도 침엽수 목재의 테르펜 방출이 측정됩니다."
        ),
        use_ko="목향 베이스. 서재·옷장·린넨 미스트에.",
        sources=(
            ("1 Kings 6:9–10", "성전 건축의 레바논 삼나무"),
            ("Theophrastus, Historia Plantarum", "삼나무와 목재 향 기술"),
            ("Pliny, Naturalis Historia XVI", "목재와 수지 이용"),
        ),
        caution="세드롤은 고체(상온) → 무게로 계량. 에탄올에 먼저 녹여 사용.",
        conservation="레바논 삼나무 자생지 보호 중. 향료용은 지속가능 조림 수종 사용 권장.",
        ideas=("시더 & 스파이스", "샌달 우드 스터디"),
    ),
    AtlasEntry(
        id="pine-phytoncide",
        name_ko="소나무 피톤치드",
        name_en="Pine phytoncide",
        botanical="Pinus densiflora (한국 소나무), P. sylvestris",
        category="forest",
        era_label="한국·동북아 산림 (기록 이전~)",
        year=-1000,
        region="한반도 전역, 만주, 시베리아",
        material_part="잎(솔잎)·수피·수지",
        molecules=("alpha-pinene", "beta-pinene", "myrcene", "sabinene", "bornyl acetate", "limonene"),
        story=(
            "피톤치드(phytoncide)라는 말은 1920~30년대 소련 식물학자 보리스 토킨이 "
            "식물이 내보내는 항균성 휘발 물질을 가리키며 만든 용어입니다. 한국에서는 "
            "솔잎·송진이 민간요법과 제사·명상 공간의 향으로 오래 쓰였고, 오늘날에는 "
            "산림치유 프로그램의 대표 향으로 자리 잡았습니다."
        ),
        science=(
            "소나무 잎의 주요 휘발 성분은 α-피넨·β-피넨·미르센 같은 모노테르펜입니다. "
            "이들은 분자량 136 전후로 휘발이 빨라 탑 노트를 이루며, 숲에서 측정되는 "
            "NVOC(식생 휘발성 유기화합물)의 상당 부분을 차지합니다. 산림치유 연구는 "
            "이런 물질의 흡입과 생리 반응(심박·코르티솔·면역 지표)의 관계를 다룹니다."
        ),
        use_ko="숲 재현의 탑 노트. 디퓨저·룸스프레이의 '산책 직후' 감각.",
        sources=(
            ("Li Q. et al., Environ Health Prev Med (2009)", "산림욕과 면역 지표 변화"),
            ("Antonelli M. et al., Int J Environ Res Public Health (2020)", "산림 VOC와 건강 리뷰"),
            ("Tokin B. P., phytoncide 개념 (1930년대)", "식물 휘발 항균 물질 용어"),
        ),
        caution="테르펜은 산화하면 피부 감작 물질이 됨 → 밀봉·냉암소 보관, 오래된 병은 폐기.",
        ideas=("숲의 호흡", "아침 숲"),
    ),
    AtlasEntry(
        id="hinoki",
        name_ko="편백 · 히노키",
        name_en="Hinoki cypress",
        botanical="Chamaecyparis obtusa",
        category="wood",
        era_label="일본·한국 (고대~)",
        year=700,
        region="일본 혼슈 이남, 한국 남부(제주·전남 일부 식재)",
        material_part="심재·잎",
        molecules=("sabinene", "alpha-pinene", "limonene", "bornyl acetate", "terpinen-4-ol", "hinokitiol"),
        story=(
            "편백은 일본에서 신사·목욕탕(히노키 부로)의 재료로 쓰여 왔고, 한국에서는 "
            "제주·남부의 편백 숲이 치유의 숲으로 조성되며 '피톤치드 향'의 대표가 "
            "되었습니다. 1936년 노조에 테츠오는 대만 편백에서 트로폴론 구조의 "
            "히노키티올을 분리해 보고했습니다."
        ),
        science=(
            "편백 잎 정유는 사비넨·α-피넨이 주성분이고, 히노키티올은 향이라기보다 "
            "생리활성(금속 이온 킬레이트) 성분입니다. 즉 '편백 향'의 대부분은 "
            "모노테르펜이 만들고, 히노키티올은 아주 미량의 금속성 뉘앙스로만 기여합니다. "
            "OLFACTRA는 이 둘을 분리해 모델링합니다."
        ),
        use_ko="욕실·사우나 공간. 나무 욕조의 김이 올라올 때의 향.",
        sources=(
            ("Nozoe T. (1936)", "히노키티올 분리·구조 보고"),
            ("日本 森林総合研究所, 樹木精油データ", "편백 정유 성분 조성"),
        ),
        caution="히노키티올은 상용 향료가 아님 — 연구·미량 용도. 1,8-시네올은 영유아·고양이 금기.",
        ideas=("편백 욕실", "숲의 호흡"),
    ),
    AtlasEntry(
        id="yuzu",
        name_ko="유자",
        name_en="Yuzu",
        botanical="Citrus junos",
        category="fruit",
        era_label="중국·한국·일본 (기록: 고려~)",
        year=1100,
        region="한국 남해안(고흥·완도·거제), 중국 양쯔강 유역, 일본",
        material_part="과피(플라베도 제외), 착즙액",
        molecules=("limonene", "alpha-terpinene", "linalool", "myrcene", "gamma-decalactone"),
        story=(
            "유자는 추위에 강한 감귤로 한국 남해안에서 겨울 과실로 재배되어 왔습니다. "
            "유자청·유자차·유자화채처럼 껍질과 과육을 함께 설탕에 절이는 방식이 "
            "한국적이며, 겨울철 따뜻한 향의 기억으로 남습니다."
        ),
        science=(
            "유자 과피 정유의 주성분은 리모넨이고 α-터피넨·리날룰이 특유의 '쌉싸름한 "
            "감귤' 느낌을 더합니다. 감귤류 껍질에는 푸라노쿠마린이 있을 수 있어 "
            "압착 오일을 고농도로 피부에 쓰면 광독성 위험이 있습니다(증류 오일은 낮음)."
        ),
        use_ko="겨울 거실·현관. 유자차를 닮은 따뜻한 시트러스.",
        sources=(
            ("한국 전통 식문화 문헌의 유자청 기록", "유자 가공·보존 방식"),
            ("Citrus 정유 성분 공개 데이터", "과피 테르펜 조성"),
        ),
        caution="압착 감귤 오일은 광독성 주의. 피부 도포용은 증류·저농도.",
        ideas=("유자차", "시트러스 클리어"),
    ),
    AtlasEntry(
        id="agarwood",
        name_ko="침향",
        name_en="Agarwood / Oud",
        botanical="Aquilaria malaccensis, A. sinensis",
        category="wood",
        era_label="인도·동남아·중국 (고대~)",
        year=-500,
        region="인도 아삼, 베트남, 캄보디아, 인도네시아, 중국 하이난",
        material_part="상처·진균 감염에 대한 방어 반응으로 생긴 수지 함유 심재",
        molecules=("beta-caryophyllene", "alpha-humulene", "guaiacol", "delta-cadinene"),
        story=(
            "침향은 건강한 나무에서 나지 않습니다. 상처를 입고 곰팡이와 상호작용한 "
            "나무가 수년에 걸쳐 만들어 내는 수지 심재만이 향을 냅니다. 그래서 "
            "인도·중국·중동에서 '귀한 향'의 대명사가 되었고, 불교·이슬람 의례의 향으로 "
            "쓰였습니다. 현재 야생 개체는 국제거래 규제(CITES 부속서 II) 대상입니다."
        ),
        science=(
            "침향의 향은 세스퀴테르펜과 소량의 페놀류(과이아콜 계열)가 만드는 "
            "달콤·연기·수지의 복합입니다. 같은 나무라도 수지 침착 정도에 따라 향이 "
            "크게 달라, 원료의 '등급'이 곧 화학 조성의 차이입니다."
        ),
        use_ko="베이스의 무게. 단독으로도 층이 되지만 가격·윤리 문제로 대체 블렌드가 많습니다.",
        sources=(
            ("CITES Appendices (Aquilaria spp.)", "국제거래 규제"),
            ("공개 목재 정유 성분 연구", "수지 침착과 세스퀴테르펜 조성"),
        ),
        caution="과이아콜은 자극성 페놀 → 흔적 사용. 연소 향은 환기 필수.",
        conservation="CITES II. 야생 채취품 대신 인증 plantation 재료 또는 대체 블렌드 권장.",
        ideas=("연기와 수지", "시더 & 스파이스"),
    ),
    AtlasEntry(
        id="rose",
        name_ko="장미 · 다마스크 로즈",
        name_en="Rose",
        botanical="Rosa damascena, R. centifolia",
        category="flower",
        era_label="페르시아·로마 (고대~), 증류는 중세",
        year=-600,
        region="페르시아, 로마, 터키 이스파르타, 불가리아 카잔르크",
        material_part="만개 직전의 꽃잎",
        molecules=("phenylethyl alcohol", "geraniol", "citronellol", "beta-ionone", "benzyl acetate"),
        story=(
            "로마의 연회는 장미 꽃잎을 뿌리고 장미수를 뿌리는 것으로 유명했고, "
            "페르시아에서는 장미수를 증류하는 기술이 발달했습니다. 장미수 증류를 "
            "이븐 시나(아비센나)와 연결하는 이야기는 널리 전해지지만, 확정된 단일 "
            "기록이라기보다 전승으로 보는 편이 안전합니다. 오늘날 장미 오일의 중심지는 "
            "터키 이스파르타와 불가리아 카잔르크입니다."
        ),
        science=(
            "장미 향의 핵심은 페닐에틸 알코올(깨끗한 꽃), 게라니올·시트로넬롤(달콤한 "
            "제라늄), β-이오논(보랏빛 가루감)의 조합입니다. 천연 장미 오일은 이 조성비가 "
            "품종·수확 시각에 따라 달라지며, 같은 '장미'라도 향이 다른 이유입니다."
        ),
        use_ko="플로럴 미들. 단독으로도 완성되지만 목향 베이스와 만나면 지속력이 생깁니다.",
        sources=(
            ("Pliny, Naturalis Historia XXI", "로마의 장미 이용"),
            ("Theophrastus, De Odoribus", "꽃 향료 제조"),
            ("공개 장미 정유 성분 연구", "품종별 조성 차이"),
        ),
        caution="게라니올·시트로넬롤은 EU 표시 대상 알레르겐. 2~3% 이하 권장.",
        ideas=("장미 정원",),
    ),
    AtlasEntry(
        id="jasmine",
        name_ko="자스민",
        name_en="Jasmine",
        botanical="Jasminum sambac, J. grandiflorum",
        category="flower",
        era_label="인도·중국 (고대~), 프랑스 그라스 18세기",
        year=-300,
        region="인도, 중국 남부, 이집트, 프랑스 그라스",
        material_part="해질 무렵 채취한 꽃",
        molecules=("benzyl acetate", "cis-jasmone", "methyl anthranilate", "beta-ionone", "benzyl benzoate"),
        story=(
            "자스민은 인도에서 신에게 바치는 꽃이자 머리에 꽂는 향이었고, 중국에서는 "
            "차에 우려 마셨습니다. 18세기 이후 프랑스 그라스에서 냉침법(앙플뢰라주)으로 "
            "자스민 오일을 얻으면서 유럽 향수의 핵심이 되었습니다. 자스민 꽃은 해가 진 "
            "뒤에 향이 강해져, 밤에 따는 것이 원칙으로 전해집니다."
        ),
        science=(
            "자스민 향은 벤질 아세테이트의 달콤한 과즙 꽃향과 시스-자스몬의 녹색·짙은 "
            "꽃향이 축을 이룹니다. 메틸 안트라닐레이트는 포도·오렌지꽃 같은 뉘앙스를 "
            "더합니다. 이 세 물질의 비율만 바꿔도 '자스민'에서 '오렌지꽃'까지 이동합니다."
        ),
        use_ko="저녁 공간의 플로럴. 소량으로도 존재감이 큼.",
        sources=(
            ("그라스 향수 산업사 공개 자료", "앙플뢰라주 공정"),
            ("공개 자스민 정유 성분 연구", "주요 성분 조성"),
        ),
        caution="메틸 안트라닐레이트·시스-자스몬은 1~2% 이하. 임신부 고농도 사용 지양.",
        ideas=("자스민 저녁", "장미 정원"),
    ),
    AtlasEntry(
        id="sandalwood",
        name_ko="백단향",
        name_en="Sandalwood",
        botanical="Santalum album",
        category="wood",
        era_label="인도 (기원전 1천년~)",
        year=-1000,
        region="인도 마이소르·카르나타카, 인도네시아 티모르",
        material_part="30년 이상 자란 심재",
        molecules=("alpha-santalol", "alpha-bisabolol", "beta-caryophyllene", "cedrol"),
        story=(
            "백단향은 인도 사원의 향가루이자 장례·명상의 향으로 쓰여 왔고, "
            "마이소르의 백단향은 왕실 관리 대상이었습니다. 나무가 향을 만들기까지 "
            "수십 년이 걸려 남획되었고, 지금은 재배·인증 재료가 중심입니다."
        ),
        science=(
            "백단향 특유의 크리미한 목향은 α-산탈롤이 만듭니다. 분자량 220의 "
            "세스퀴테르펜 알코올로 휘발이 느려 베이스로 기능하며, 피부에 오래 남습니다. "
            "천연 산탈롤은 공급이 제한적이어서 공개 구조를 바탕으로 한 합성 대체품이 "
            "널리 쓰입니다."
        ),
        use_ko="명상·서재의 베이스. 린넨 미스트의 잔향.",
        sources=(
            ("인도 마이소르 산림국 공개 기록", "백단향 관리·재배"),
            ("공개 산탈롤 성분 연구", "α-산탈롤 구조와 향 특성"),
        ),
        caution="고농도·장기 사용 시 피부 자극 사례. 저농도로.",
        conservation="야생 Santalum album은 IUCN 적색목록 취약(VU) 종. 재배·인증 재료 사용 권장.",
        ideas=("샌달 우드 스터디",),
    ),
    AtlasEntry(
        id="patchouli",
        name_ko="패츌리",
        name_en="Patchouli",
        botanical="Pogostemon cablin",
        category="wood",
        era_label="동남아 (고대~), 유럽 19세기",
        year=1500,
        region="인도네시아 수마트라, 인도, 필리핀",
        material_part="건조·발효시킨 잎",
        molecules=("patchoulol", "beta-caryophyllene", "alpha-copaene", "guaiacol"),
        story=(
            "패츌리는 인도 직물, 특히 캐시미어 숄에 향을 입히는 데 쓰였습니다. "
            "19세기 유럽에 숄이 수입되면서 '진짜 인도 숄의 냄새'로 인식되었고, "
            "이후 향수의 흙·나무 베이스로 자리 잡았습니다. 잎을 말려 발효시키는 "
            "과정이 향의 질을 좌우합니다."
        ),
        science=(
            "패츌롤은 삼환 구조의 세스퀴테르펜 알코올로, 낮은 휘발성과 높은 잔향력이 "
            "특징입니다. 흙·곰팡이 같은 뉘앙스는 소량의 페놀류가 더합니다. "
            "베이스 원료 중 '무게'를 담당하는 쪽입니다."
        ),
        use_ko="흙·나무 베이스. 과하면 곰팡이 냄새가 되므로 1% 이하부터 시작.",
        sources=(
            ("동남아 향료 식물 공개 자료", "재배·발효 공정"),
            ("공개 패츌리 정유 연구", "패츌롤 조성"),
        ),
        caution="패츌롤은 상온에서 고체에 가까움 → 에탄올에 미리 용해.",
        ideas=("비 온 뒤 흙", "연기와 수지"),
    ),
    AtlasEntry(
        id="clove",
        name_ko="정향",
        name_en="Clove",
        botanical="Syzygium aromaticum",
        category="spice",
        era_label="말루쿠 제도 (기원전~), 유럽 향료혁명 16세기",
        year=-200,
        region="인도네시아 말루쿠(암본), 마다가스카르, 잔지바르",
        material_part="건조한 꽃봉오리",
        molecules=("eugenol", "beta-caryophyllene", "alpha-humulene"),
        story=(
            "정향은 말루쿠 제도의 '향료 섬'에서만 나서 유럽인들이 항로를 찾아 나선 "
            "이유가 되었습니다. 16세기 포르투갈, 17세기 네덜란드가 무역을 독점했고, "
            "그 과정에서 향료 가격과 섬의 운명이 함께 흔들렸습니다. 한의학·아유르베다에서도 "
            "정향은 따뜻한 성질의 약재로 쓰였습니다."
        ),
        science=(
            "정향 향의 90%는 유제놀입니다. 유제놀은 페놀성 수산기를 가져 피부·점막 자극이 "
            "강하고, 치과에서 국소 마취·항균 용도로 연구된 물질입니다. "
            "그래서 '향이 좋다'와 '안전하다'가 다르며, 완성품 0.5% 이하가 실무 상한입니다."
        ),
        use_ko="스파이시 미들. 0.1~0.3%만으로도 향 전체를 따뜻하게 바꿉니다.",
        sources=(
            ("유럽 향료 무역사 공개 자료", "말루쿠 향료 독점"),
            ("출애굽기 30:23", "관유 재료로서의 계피·정향 계열 향신료"),
        ),
        caution="유제놀 0.5% 이하. 반려동물(특히 고양이) 공간 사용 금지 권장.",
        ideas=("시더 & 스파이스",),
    ),
    AtlasEntry(
        id="cinnamon",
        name_ko="계피 · 시나몬",
        name_en="Cinnamon",
        botanical="Cinnamomum verum (실론), C. cassia",
        category="spice",
        era_label="고대 이집트·실론 (기원전~)",
        year=-1500,
        region="스리랑카, 남인도, 중국 남부, 베트남",
        material_part="내피(수피)",
        molecules=("cinnamaldehyde", "eugenol", "coumarin", "benzyl benzoate"),
        story=(
            "계피는 이집트의 방부 향료로도 쓰였고, 중세 유럽에서는 후추와 함께 "
            "가장 값비싼 향신료였습니다. 실론 계피(C. verum)와 카시아(C. cassia)는 "
            "같은 '계피'로 팔리지만 화학 조성이 다릅니다. 카시아에는 쿠마린이 더 많아 "
            "식품·향료 모두에서 구분이 필요합니다."
        ),
        science=(
            "계피의 매운 단 향은 신남알데하이드가 만듭니다. 강한 피부 감작 물질로 "
            "알려져 있어 완성품 0.2% 이하의 '흔적' 사용이 안전합니다. "
            "쿠마린은 카시아에 많고 간독성 이슈로 식품 규제가 있으며, 향료에서도 "
            "1.5% 이하로 제한합니다."
        ),
        use_ko="따뜻한 미들. 겨울 블렌드의 '불씨' 역할, 아주 소량.",
        sources=(
            ("Herodotus, Histories II.86", "이집트 미라 제작에 쓰인 향료"),
            ("Pliny, Naturalis Historia XII", "계피 교역 기술"),
            ("Exodus 30:23–24", "관유의 계피·카시아"),
            ("EU 향료 알레르겐 목록", "신남알데하이드 표시 대상"),
        ),
        caution="신남알데하이드 0.2% 이하. 민감성 피부 패치 테스트 필수.",
        ideas=("시더 & 스파이스", "유자차"),
    ),
    AtlasEntry(
        id="vanilla",
        name_ko="바닐라",
        name_en="Vanilla",
        botanical="Vanilla planifolia",
        category="seed",
        era_label="메소아메리카 (고대~), 유럽 16세기",
        year=1400,
        region="멕시코 베라크루스, 마다가스카르, 인도네시아",
        material_part="발효·숙성시킨 협과(열매)",
        molecules=("vanillin", "guaiacol", "benzyl benzoate", "coumarin"),
        story=(
            "바닐라는 톡토낙(Totonac) 족이 재배한 향신료로, 아즈텍이 정복한 뒤 "
            "'tlilxochitl(검은 꽃)'로 불렸고 초콜릿 음료에 더해졌습니다. 16세기 "
            "스페인이 유럽에 소개했고, 19세기에는 마다가스카르 등 열대 지역으로 "
            "재배가 퍼졌습니다. 바닐라 향의 대부분은 수확 후 발효·숙성 과정에서 "
            "만들어집니다."
        ),
        science=(
            "바닐린은 4-하이드록시-3-메톡시벤즈알데하이드로, 분자량 152의 작은 분자이지만 "
            "지각 임계값이 매우 낮아 소량으로 강한 달콤함을 냅니다. 바닐라 협과에는 "
            "바닐린 외에 과이아콜·에스터가 함께 있어 '천연 바닐라'와 '합성 바닐린'의 "
            "차이가 생깁니다."
        ),
        use_ko="달콤한 베이스. 과하면 향수가 아니라 디저트가 됩니다.",
        sources=(
            ("메소아메리카 향신료 공개 사료", "톡토낙·아즈텍의 바닐라"),
            ("공개 바닐라 발효 연구", "숙성 중 바닐린 생성"),
        ),
        caution="바닐린은 고체 → 에탄올에 녹여 사용. 과량은 포화·결정 석출.",
        ideas=("통카 & 바닐라", "유자차"),
    ),
    AtlasEntry(
        id="tonka",
        name_ko="통카빈",
        name_en="Tonka bean",
        botanical="Dipteryx odorata",
        category="seed",
        era_label="아마존 (고대~), 유럽 19세기",
        year=1800,
        region="베네수엘라·브라질·가이아나",
        material_part="건조·숙성시킨 종자",
        molecules=("coumarin", "vanillin", "benzyl benzoate", "beta-ionone"),
        story=(
            "통카빈은 아마존 원주민의 향료였고, 18~19세기 유럽에서 '건초와 아몬드' 같은 "
            "달콤한 향으로 인기를 얻었습니다. 1868년 퍼킨이 쿠마린을 합성하면서 이 향은 "
            "값싼 대량 향료가 되었고, 1882년 푸제르 로얄 같은 푸제르 계열 향수의 "
            "출발점이 되었습니다."
        ),
        science=(
            "통카의 핵심은 쿠마린입니다. 벤조피론 구조로, 건초·아몬드·바닐라 사이의 "
            "달콤함을 만들며 베이스의 잔향을 늘립니다. 다만 EU에서는 표시 대상 "
            "알레르겐이고, 식품으로는 섭취량 제한이 있어 향료에서도 1.5% 이하로 씁니다."
        ),
        use_ko="달콤한 베이스. 바닐라와 2:1 정도로 묶으면 '포근함'이 완성됩니다.",
        sources=(
            ("Perkin W. H. (1868)", "쿠마린 최초 합성"),
            ("공개 향수사 자료 (Fougère Royale, 1882)", "쿠마린 기반 향수 계열의 출발"),
        ),
        caution="쿠마린 1.5% 이하. 임신 중 고농도 사용은 피함.",
        ideas=("통카 & 바닐라",),
    ),
    AtlasEntry(
        id="musk",
        name_ko="사향 · 머스크",
        name_en="Musk",
        botanical="Moschus moschiferus (역사적), 합성 무스콘",
        category="animal",
        era_label="고대 아시아 (기원전~), 합성 20세기",
        year=-500,
        region="히말라야·중국·시베리아, 오늘날은 실험실",
        material_part="역사적으로 사향노루의 분비낭 — 현재는 합성 또는 대체 원료",
        molecules=("muscone",),
        story=(
            "사향은 수천 년간 '가장 강한 동물성 향'으로 동아시아와 중동의 향 문화에 "
            "쓰였습니다. 그러나 사향노루 남획으로 야생 개체가 급감해 국제거래가 "
            "금지되었고, 1926년 루지치카가 무스콘 구조를 밝히면서 합성 원료 시대로 "
            "넘어갔습니다. OLFACTRA는 동물성 원료를 쓰지 않으며 합성 무스콘만 다룹니다."
        ),
        science=(
            "무스콘은 15원환 케톤(분자량 238)으로, 피부의 체온 같은 잔향을 냅니다. "
            "천연 사향의 복잡한 동물성 뉘앙스는 여러 성분의 합이지만, 단일 무스콘만으로도 "
            "'깨끗한 머스크'의 뼈대가 만들어집니다."
        ),
        use_ko="베이스의 '피부감'. 과하면 비누 냄새가 되므로 1~3%.",
        sources=(
            ("CITES Appendices (Moschus spp.)", "사향노루 국제거래 규제"),
            ("Ruzicka L. (1926)", "무스콘 구조 규명"),
        ),
        caution="합성 무스콘 사용. 동물성 사향은 윤리·법적 문제로 사용하지 않음.",
        conservation="야생 사향노루는 CITES 등재. 동물성 원료 대체 원칙.",
        ideas=("머스크 리넨",),
    ),
    AtlasEntry(
        id="lavender",
        name_ko="라벤더",
        name_en="Lavender",
        botanical="Lavandula angustifolia",
        category="flower",
        era_label="지중해 (로마~), 프로방스 19세기",
        year=100,
        region="프랑스 프로방스, 불가리아, 스페인, 크로아티아",
        material_part="개화 직전의 꽃대",
        molecules=("linalool", "linalyl acetate", "camphor", "terpinen-4-ol", "coumarin"),
        story=(
            "라벤더라는 이름은 라틴어 lavare(씻다)에서 왔다는 설명이 널리 퍼져 있습니다. "
            "로마인들이 목욕과 세탁에 향을 더하는 데 썼고, 중세 이후 프로방스의 "
            "라벤더 밭이 향료 산업의 중심이 되었습니다. 잠자리 향으로 쓰는 관습은 "
            "오늘날 수면 위생 제품으로 이어졌습니다."
        ),
        science=(
            "라벤더 향의 축은 리날룰(꽃·투명함)과 리날릴 아세테이트(과즙 꽃향)입니다. "
            "캠퍼가 많으면 '약품 냄새'가 되는데, 이는 품종과 증류 시점의 차이입니다. "
            "수면 연구에서는 라벤더 흡입의 주관적 이완 효과가 보고되지만, 효과 크기와 "
            "기전은 여전히 연구 주제입니다."
        ),
        use_ko="침실·수면. 라벤더 70% + 시더 20% + 통카 10%는 안전한 출발점.",
        sources=(
            ("Theophrastus, De Odoribus", "지중해 향료 식물"),
            ("공개 라벤더 정유 연구", "품종별 리날룰·캠퍼 비율"),
        ),
        caution="리날룰 산화물은 감작 물질 → 냉암소 보관, 1년 이상 된 오일 폐기 권장.",
        ideas=("라벤더 달빛", "머스크 리넨"),
    ),
    AtlasEntry(
        id="vetiver",
        name_ko="베티버 · 흙향 뿌리",
        name_en="Vetiver",
        botanical="Chrysopogon zizanioides",
        category="wood",
        era_label="인도 (고대~)",
        year=-500,
        region="인도 타밀나두, 아이티, 인도네시아",
        material_part="수년생 뿌리",
        molecules=("patchoulol", "beta-caryophyllene", "alpha-copaene", "guaiacol"),
        story=(
            "베티버(크하스)는 인도에서 방향 뿌리로, 더위를 식히는 발향 재료로 쓰였고 "
            "오늘날에는 토양 침식을 막는 식물로도 재배됩니다. 뿌리를 물에 적셔 "
            "공간을 식히는 '크하스 커튼'은 인도 여름의 지혜로 전해집니다."
        ),
        science=(
            "베티버 향은 흙·뿌리·나무가 겹친 무거운 베이스입니다. 주성분은 "
            "베티베론 계열 세스퀴테르펜 케톤이지만, OLFACTRA의 공개 분자 라이브러리에는 "
            "유사 프로파일(패츌롤·카리오필렌)로 근사해 모델링합니다."
        ),
        use_ko="흙 베이스. 비 온 뒤 아스팔트 같은 '페트리코' 향의 재료.",
        sources=(
            ("인도 향료 식물 공개 자료", "크하스 뿌리 이용"),
            ("공개 베티버 정유 연구", "세스퀴테르펜 조성"),
        ),
        caution="끈적한 잔류물 → 여과 후 사용. 저농도.",
        ideas=("비 온 뒤 흙",),
    ),
    AtlasEntry(
        id="forest-air",
        name_ko="숲의 공기 — 피톤치드와 NVOC",
        name_en="Forest air: phytoncides and NVOC",
        botanical="침엽수·활엽수 혼효림",
        category="forest",
        era_label="현대 산림과학 (20세기~)",
        year=1982,
        region="일본(신린요쿠), 한국(산림치유), 핀란드",
        material_part="숲 공기 중 식생 휘발성 유기화합물",
        molecules=("alpha-pinene", "beta-pinene", "myrcene", "limonene", "beta-caryophyllene", "cis-3-hexen-1-ol"),
        story=(
            "일본 임야청이 1982년 '신린요쿠(숲浴)'를 제안하면서 숲의 공기를 건강 자원으로 "
            "보는 관점이 제도화되었고, 한국에서는 2005년 산림문화·휴양에 관한 법률 이후 "
            "'산림치유'가 제도로 자리 잡았습니다. 숲의 향은 나무가 해충·미생물에 맞서 "
            "내보내는 휘발 물질과, 상처 난 잎에서 나오는 'green leaf volatiles'의 합입니다."
        ),
        science=(
            "숲 공기에는 모노테르펜(α-피넨·β-피넨·리모넨), 세스퀴테르펜, 그리고 "
            "잎이 다칠 때 나오는 C6 알코올(시스-3-헥세놀)이 함께 존재합니다. "
            "산림치유 연구는 이들 흡입이 코르티솔·심박 변이도·NK 세포 활성에 미치는 "
            "영향을 보고했지만, 대부분 규모가 작고 교란 요인(걷기·경관·기대 효과)이 "
            "함께 작용합니다. 그래서 OLFACTRA는 '향 = 치료'가 아니라 "
            "'향 = 환경 노출의 한 축'으로 다룹니다."
        ),
        use_ko="숲 재현 블렌드의 설계도. 탑(피넨) — 미들(리날룰·보르닐) — 베이스(카리오필렌).",
        sources=(
            ("Li Q. et al., Environ Health Prev Med 14 (2009)", "산림욕과 NK 활성"),
            ("Antonelli M. et al., IJERPH 17 (2020)", "산림 VOC와 건강 리뷰"),
            ("Kotera Y. et al., Int J Ment Health Addict (2022)", "신린요쿠·자연치료 심리 효과 체계적 문헌고찰"),
        ),
        caution="향은 의료 행위가 아님. 호흡기 질환자는 저농도·환기. 반려동물 공간 주의.",
        ideas=("숲의 호흡", "아침 숲", "비 온 뒤 흙"),
    ),
    AtlasEntry(
        id="incense-route",
        name_ko="유향의 길",
        name_en="The Incense Route",
        botanical="—",
        category="history",
        era_label="기원전 1천년~기원후 3세기",
        year=-800,
        region="오만·예멘 → 페트라·가자 → 지중해",
        material_part="유향·몰약 수지의 육상 교역로",
        molecules=("alpha-pinene", "beta-caryophyllene"),
        story=(
            "남아라비아에서 지중해까지 유향과 몰약을 나르던 대상로는 '유향의 길'로 "
            "불립니다. 낙타 대상이 오만·예멘의 산지에서 페트라와 가자로 수지를 옮겼고, "
            "이 교역의 이익이 남아라비아 도시국가의 부를 만들었습니다. 유향은 "
            "신전의 제향이자 왕의 예물이었고, 그 가격은 향의 희소성과 운반 거리에서 "
            "나왔습니다."
        ),
        science=(
            "유향 수지의 가치는 '향 성분의 함량'과 '입자 크기·색' 같은 물리적 등급으로 "
            "매겨졌습니다. 오늘날에도 유향 등급은 정유 함량과 α-피넨 비율로 설명되며, "
            "고대의 등급 체계가 화학 조성 차이와 크게 어긋나지 않는다는 점이 흥미롭습니다."
        ),
        use_ko="역사 테마 블렌드의 서사. '사막을 건너온 향'이라는 스토리 축.",
        sources=(
            ("Herodotus, Histories III", "아라비아 향료 교역"),
            ("Pliny, Naturalis Historia XII", "유향 등급과 가격"),
            ("Petra·Gaza 고고학 공개 자료", "유향로의 도시들"),
        ),
        caution="—",
        ideas=("유향 의식",),
    ),
    AtlasEntry(
        id="roman-perfume",
        name_ko="로마의 향유 문화",
        name_en="Roman unguenta",
        botanical="—",
        category="history",
        era_label="로마 공화정~제정 (기원전 1세기~기원후 4세기)",
        year=-100,
        region="로마, 폼페이, 알렉산드리아",
        material_part="올리브 오일 기반 향유(unguentum)",
        molecules=("phenylethyl alcohol", "geraniol", "benzyl benzoate", "alpha-pinene"),
        story=(
            "로마의 향유(unguentum)는 올리브 오일이나 포도주에 꽃·수지를 우려 만든 "
            "것으로, 목욕·연회·장례에 쓰였습니다. 폼페이에서는 향유를 담던 유리병"
            "(unguentarium)이 대량 출토되어 향이 일상용품이었음을 보여 줍니다. "
            "향을 과하게 쓰는 것은 사치로 비판받기도 했습니다."
        ),
        science=(
            "로마식 향유는 오일 베이스라 오늘날의 '오일 퍼퓸'과 구조가 비슷합니다. "
            "카리어 오일은 향의 휘발을 늦추지만 산패가 문제이므로, 현대 DIY에서는 "
            "호호바·분획 코코넛 오일처럼 안정성이 높은 베이스를 권합니다."
        ),
        use_ko="오일 퍼퓸·고체 향의 역사적 근거. 디퓨저보다 피부 밀착형.",
        sources=(
            ("Theophrastus, De Odoribus", "향유 제조법"),
            ("Pliny, Naturalis Historia XIII", "향유와 사치 비판"),
            ("폼페이 unguentarium 출토 자료", "향유 용기"),
        ),
        caution="오일 베이스는 산패·광산화 주의. 어린이 손이 닿지 않게.",
        ideas=("머스크 리넨", "장미 정원"),
    ),
)

_BY_ID: dict[str, AtlasEntry] = {e.id: e for e in ATLAS}


def all_entries() -> tuple[AtlasEntry, ...]:
    return ATLAS


def get(entry_id: str) -> AtlasEntry:
    key = (entry_id or "").strip().lower()
    if key in _BY_ID:
        return _BY_ID[key]
    for entry in ATLAS:
        if key in (entry.name_ko.lower(), entry.name_en.lower()):
            return entry
    raise KeyError(f"unknown atlas entry: {entry_id!r}")


def timeline(ascending: bool = True) -> list[AtlasEntry]:
    return sorted(ATLAS, key=lambda e: e.year, reverse=not ascending)


def search(query: str) -> list[AtlasEntry]:
    q = (query or "").strip().lower()
    if not q:
        return list(ATLAS)
    hits = []
    for entry in ATLAS:
        haystack = " ".join([
            entry.name_ko, entry.name_en, entry.botanical, entry.region,
            entry.material_part, entry.story, entry.science, entry.use_ko,
            " ".join(entry.molecules), entry.category_label,
        ]).lower()
        if q in haystack:
            hits.append(entry)
    return hits


def by_category(category: str | None = None) -> list[AtlasEntry]:
    if not category:
        return list(ATLAS)
    return [e for e in ATLAS if e.category == category]


def by_molecule(molecule_id: str) -> list[AtlasEntry]:
    return [e for e in ATLAS if molecule_id in e.molecules]


def eras() -> list[tuple[str, int]]:
    """(label, year) pairs for a coarse timeline axis."""
    buckets = [
        ("기원전 3천년", -3000), ("기원전 2천년", -2000), ("기원전 1천년", -1000),
        ("기원전 5세기", -500), ("기원전 1세기", -100), ("기원후 1~5세기", 100),
        ("기원후 중세", 800), ("기원후 15~17세기", 1500), ("근대 이후", 1800),
        ("현대", 1950),
    ]
    return buckets


def stats() -> dict:
    per_category: dict[str, int] = {}
    for entry in ATLAS:
        per_category[entry.category] = per_category.get(entry.category, 0) + 1
    return {
        "entries": len(ATLAS),
        "by_category": per_category,
        "regions": len({e.region for e in ATLAS}),
        "span_bce": min(e.year for e in ATLAS),
        "span_ce": max(e.year for e in ATLAS),
    }
