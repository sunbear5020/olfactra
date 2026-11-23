"""OLFACTRA PROVENANCE — every indicator, its formula, its source, its limit.

Why this module exists
----------------------
OLFACTRA prints numbers, and a number without its provenance is a claim.  This
registry states, for each indicator the engine shows, three things:

``kind``
    * ``measured`` — a value published in a dataset or public record (Pyrfume's
      extracts of Keller 2016 / Dravnieks 1985 / Mainland 2015, PubChem records).
    * ``derived`` — computed from public inputs by a stated, reproducible method
      (dilution arithmetic, RDKit conformers, Crippen LogP, Ertl TPSA).
    * ``heuristic`` — a curated or rule-based ranking aid with no measured
      target (odour-family weights, harmony, the safety working ceiling, the
      schematic docking fit).  Treat these as arguments to test, not facts.

``formula``
    the actual arithmetic, in plain text, so anyone can recompute the number.

``references``
    the DOI/URL a reader can check, with what each source contributes.

``boundary``
    what the indicator does **not** mean.  This is the part that keeps the tool
    honest: a heuristic that is labelled a heuristic cannot be mistaken for a
    measurement, and an unmeasured molecule stays marked as unmeasured.

The same registry feeds the Markdown/Excel reports, the ``/api/provenance``
endpoint and the web workbench's *Methodology & Boundaries* panel, so the paper
trail cannot drift between outputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

#: label + colour key used by every renderer for the three evidence classes
KINDS: dict[str, str] = {
    "measured": "측정",
    "derived": "유도·계산",
    "heuristic": "휴리스틱",
}

KIND_ORDER: tuple[str, ...] = ("measured", "derived", "heuristic")

KIND_DESCRIPTION_KO: dict[str, str] = {
    "measured": "공개 데이터셋·공개 레코드에 실린 실측값입니다. 원문(DOI)에서 직접 확인할 수 있습니다.",
    "derived": "공개 입력값에서 정해진 방법으로 계산한 값입니다. 방법과 입력이 함께 적혀 있어 재현할 수 있습니다.",
    "heuristic": "측정 대상이 없는 규칙·경험 기반 지표입니다. 순위를 돕는 근거일 뿐, 측정값이나 예측이 아닙니다.",
}


@dataclass(frozen=True)
class Reference:
    """One checkable source."""

    label: str
    detail: str
    url: str = ""
    doi: str = ""

    @property
    def link(self) -> str:
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return self.url

    def as_dict(self) -> dict[str, str]:
        return {"label": self.label, "detail": self.detail,
                "url": self.url, "doi": self.doi, "link": self.link}

    def as_markdown(self) -> str:
        tail = f" <{self.link}>" if self.link else ""
        return f"**{self.label}** — {self.detail}{tail}"


@dataclass(frozen=True)
class Indicator:
    """One number the engine shows, with its method and its limit."""

    id: str
    label_ko: str
    label_en: str
    kind: str
    unit: str
    formula: str
    inputs: tuple[str, ...]
    basis_ko: str
    boundary_ko: str
    used_in: tuple[str, ...]
    references: tuple[Reference, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label_ko": self.label_ko,
            "label_en": self.label_en,
            "kind": self.kind,
            "kind_label": KINDS[self.kind],
            "unit": self.unit,
            "formula": self.formula,
            "inputs": list(self.inputs),
            "basis_ko": self.basis_ko,
            "boundary_ko": self.boundary_ko,
            "used_in": list(self.used_in),
            "references": [r.as_dict() for r in self.references],
        }


# --------------------------------------------------------------------------- sources
_PUBCHEM = Reference(
    "PubChem compound records",
    "분자식·분자량·SMILES·CID — 43개 향료 분자의 공개 레코드",
    url="https://pubchem.ncbi.nlm.nih.gov/",
)
_PYRFUME = Reference(
    "Pyrfume Data (MIT)",
    "공개 후각 데이터의 배포본 — 아래 세 데이터셋을 CID로 매칭해 사용",
    url="https://github.com/pyrfume/pyrfume-data",
    doi="10.1038/s41597-024-04051-z",
)
_KELLER = Reference(
    "Keller & Vosshall 2016",
    "480개 분자의 쾌적도·강도·친숙도 평정(0–100)과 20개 의미 기술어",
    doi="10.1186/s12868-016-0287-2",
)
_DRAVNIEKS = Reference(
    "Dravnieks 1985 (ASTM DS61)",
    "물질별 146개 기술어 향 프로파일",
    doi="10.1520/DS61-EB",
)
_MAINLAND = Reference(
    "Mainland et al. 2015",
    "세포 기반 스크린에서 측정된 인간 후각 수용체 반응",
    doi="10.1038/sdata.2015.2",
)
_RDKIT_ETKDG = Reference(
    "Riniker & Landrum 2015",
    "ETKDG 거리기하 3차원 임베딩 방법",
    doi="10.1021/acs.jcim.5b00654",
)
_MMFF = Reference(
    "Halgren 1996",
    "MMFF94/MMFF94s 힘장 — 임베딩된 구조의 에너지 최소화",
    doi="10.1002/(SICI)1096-987X(199604)17:5/6<490::AID-JCC1>3.0.CO;2-P",
)
_CRIPPEN = Reference(
    "Crippen 1988 / Wildman & Crippen 1999",
    "원자 기여도 방식의 계산 LogP",
    doi="10.1021/jm00356a005",
)
_ERTL = Reference(
    "Ertl, Rohde & Selzer 2000",
    "단편 기여도 방식의 위상 극성 표면적(TPSA)",
    doi="10.1021/jm000942e",
)
_BW = Reference(
    "Ballesteros & Weinstein 1995",
    "Class A GPCR 잔기 번호 체계 — 모식 수용체 잔기 표기에 사용",
    doi="10.1016/S0076-6879(95)43024-2",
)
_IFRA = Reference(
    "EU 화장품 규정 부속서 III / 공개 알레르겐 목록",
    "표시 의무 알레르겐 26종과 제품 유형별 표시 기준(0.001% leave-on)",
    url="https://eur-lex.europa.eu/eli/reg/2009/1223/oj",
)
_PUBLIC_GUIDANCE = Reference(
    "공개 조향·화장품 안전 가이드라인",
    "감작·자극 주의 성분에 대한 공개 문헌과 일반 조향 관행 요약",
    url="https://github.com/sunbear5020/olfactra/blob/main/NOTICE.md",
)


# --------------------------------------------------------------------------- registry
INDICATORS: tuple[Indicator, ...] = (
    Indicator(
        id="pubchem_record",
        label_ko="분자 동정 정보",
        label_en="Molecule identity",
        kind="measured",
        unit="—",
        formula="CID → (분자식, 분자량, SMILES, CAS)",
        inputs=("PubChem CID",),
        basis_ko=(
            "43개 향료 분자의 분자식·분자량·SMILES는 PubChem 공개 레코드에서 가져왔고, "
            "RDKit으로 분자식·정확질량을 다시 계산해 43개 전부 일치를 확인했습니다."
        ),
        boundary_ko=(
            "분자 동정은 '이 물질이 무엇인가'만 말합니다. 상용 원료의 순도·이성질체 조성·"
            "불순물은 포함하지 않으며, 같은 이름의 상업 원료라도 GC-MS 조성은 다를 수 있습니다."
        ),
        used_in=("MOLECULE", "STUDIO", "보고서"),
        references=(_PUBCHEM,),
    ),
    Indicator(
        id="logp_crippen",
        label_ko="계산 LogP (XLogP형)",
        label_en="Calculated LogP",
        kind="derived",
        unit="log10 (옥탄올/물)",
        formula="LogP = Σ(원자 기여도) + 보정항   [Crippen 1988 / Wildman–Crippen 1999]",
        inputs=("공개 SMILES", "RDKit MolLogP"),
        basis_ko=(
            "공개 SMILES의 원자 유형별 소수성 기여도를 합산하는 Crippen 방식을 RDKit으로 "
            "계산했습니다. datasets/descriptors_rdkit.json에 값과 방법, RDKit 버전을 함께 "
            "남겨 누구나 다시 계산할 수 있습니다."
        ),
        boundary_ko=(
            "계산값이며 실측 분배계수가 아닙니다. 이온화·pH·온도 효과가 없고, 이성질체 간 "
            "차이도 거칠게만 반영합니다. 휘발성이나 발향 지속시간의 대리값으로 쓰지 않습니다."
        ),
        used_in=("MOLECULE", "STUDIO", "비교", "보고서"),
        references=(_CRIPPEN, _PUBCHEM),
    ),
    Indicator(
        id="tpsa_ertl",
        label_ko="위상 극성 표면적 (TPSA)",
        label_en="Topological polar surface area",
        kind="derived",
        unit="Å²",
        formula="TPSA = Σ(극성 단편 기여도)   [Ertl, Rohde & Selzer 2000]",
        inputs=("공개 SMILES", "RDKit CalcTPSA"),
        basis_ko=(
            "N·O 계 극성 단편의 표면적 기여도를 합산했습니다. 분자의 극성 크기를 한 숫자로 "
            "비교하기 위한 값이며, 수용체 포켓 적합성과는 별개입니다."
        ),
        boundary_ko=(
            "2차원 단편 기반 추정치로 실제 분자 표면이나 용매화를 계산하지 않습니다. "
            "탄화수소계 테르펜은 0 Å²가 정상이며, '극성이 없다'는 뜻이지 '반응하지 않는다'는 뜻이 아닙니다."
        ),
        used_in=("MOLECULE", "STUDIO", "비교", "보고서"),
        references=(_ERTL, _PUBCHEM),
    ),
    Indicator(
        id="keller_2016",
        label_ko="단품 쾌적도·강도·친숙도",
        label_en="Single-molecule pleasantness / intensity / familiarity",
        kind="measured",
        unit="0–100 평정",
        formula="물질별 평정자 평균 (Keller & Vosshall 2016)",
        inputs=("Keller 2016 원자료", "PubChem CID 매칭"),
        basis_ko=(
            "약 50명 평정자가 480개 분자를 냄새 맡고 매긴 쾌적도·강도·친숙도의 평균입니다. "
            "43개 중 18개 분자에 값이 있습니다."
        ),
        boundary_ko=(
            "단품 측정값입니다. 혼합물의 향은 성분의 합이 아니므로(마스킹·상승·적응) "
            "아코드의 냄새나 쾌적도를 예측하지 않습니다. 값이 없는 분자는 '미측정'으로 표시하며 "
            "추정으로 채우지 않습니다."
        ),
        used_in=("ID", "MOLECULE", "보고서"),
        references=(_KELLER, _PYRFUME),
    ),
    Indicator(
        id="dravnieks_1985",
        label_ko="향 기술어 프로파일",
        label_en="Odour descriptor profile",
        kind="measured",
        unit="기술어별 사용도 %",
        formula="물질별 146개 기술어 사용도 (Dravnieks 1985)",
        inputs=("Dravnieks 1985 원자료", "PubChem CID 매칭"),
        basis_ko=(
            "ASTM DS61 향 프로파일의 기술어 사용도입니다. 분자 상세에서 대표 기술어 5개를 "
            "보여 주며, 43개 중 14개 분자에 값이 있습니다."
        ),
        boundary_ko=(
            "평정 패널의 언어 기반 기술이며, 화학 구조에서 유도한 값이 아닙니다. "
            "번역어는 근사 대응이고, 기술어 순위는 패널 구성에 따라 달라질 수 있습니다."
        ),
        used_in=("ID", "MOLECULE", "보고서"),
        references=(_DRAVNIEKS, _PYRFUME),
    ),
    Indicator(
        id="mainland_2015",
        label_ko="후각 수용체 반응",
        label_en="Human olfactory receptor response",
        kind="measured",
        unit="반응 수용체 / 시험 수용체",
        formula="세포 기반 스크린의 양성 반응 (농도–반응 통과 여부 포함)",
        inputs=("Mainland 2015 원자료", "PubChem CID 매칭"),
        basis_ko=(
            "이 분자가 실제로 활성화한 인간 후각 수용체 목록입니다. 3D 결합 뷰어에서 "
            "'문헌 보고 활성'으로 표시되는 근거입니다. 43개 중 8개 분자에 값이 있습니다."
        ),
        boundary_ko=(
            "시험된 수용체 패널 안에서의 결과이며, 전체 400여 개 수용체를 대표하지 않습니다. "
            "세포주 활성이 사람의 지각 강도나 쾌적도를 뜻하지도 않습니다."
        ),
        used_in=("MOLECULE", "3D 결합", "보고서"),
        references=(_MAINLAND, _PYRFUME),
    ),
    Indicator(
        id="hedonic_prior",
        label_ko="쾌적도 사전(prior)",
        label_en="Hedonic prior",
        kind="derived",
        unit="0–1 (가중 평균 재척도)",
        formula=(
            "coverage = Σ w(측정 분자) / Σ w ;  mean = Σ w·pleasantness / Σ w ;  "
            "prior = clamp((mean − 30) / 60, 0, 1) ;  FIT 가산 = 1.2 × prior"
        ),
        inputs=("Keller 2016 쾌적도", "아코드 비중"),
        basis_ko=(
            "측정된 구성 분자의 쾌적도를 비중으로 가중 평균해 0–1로 재척도하고, "
            "FIT 점수에 1.2점(총점 대비 작은 비중)만 더합니다. 커버리지가 15% 미만이면 "
            "아예 쓰지 않습니다."
        ),
        boundary_ko=(
            "실측값의 단순 가중 평균이며 혼합 효과를 모형화하지 않습니다. 순위를 살짝 "
            "흔드는 용도로만 쓰고, 결과 카드에 근거(측정 분자 수·커버리지·평균)를 항상 함께 표시합니다."
        ),
        used_in=("ID", "보고서"),
        references=(_KELLER, _PYRFUME),
    ),
    Indicator(
        id="odour_family_vector",
        label_ko="향조 벡터",
        label_en="Odour-family vector",
        kind="heuristic",
        unit="0–1 × 13 향조",
        formula="분자별 향조 가중치(0–1) 13차원 벡터; 유사도 = 코사인, 겹침 = Σ min(a_f, b_f)",
        inputs=("공개 향 설명", "정유 조성 문헌", "조향 관행"),
        basis_ko=(
            "공개 향 설명과 정유 조성 문헌을 읽고 13개 향조(시트러스·그린·플로럴…우디·"
            "레진·어시·캠퍼·머스크·스모키·파우더리) 축에 0–1로 정리한 수작업 가중치입니다."
        ),
        boundary_ko=(
            "측정된 향조 강도가 아닙니다. 같은 향조라도 사람이 느끼는 유사성은 다르며, "
            "가중치는 연구실의 서술 기준이므로 다른 문헌의 수치와 직접 비교할 수 없습니다."
        ),
        used_in=("ID", "MOLECULE", "비교", "보고서"),
        references=(_PUBCHEM,),
    ),
    Indicator(
        id="blend_harmony",
        label_ko="조화 지수",
        label_en="Blend harmony",
        kind="heuristic",
        unit="0–1",
        formula=(
            "pair = (0.55·overlap + 0.30·cosine + complement_lift) × note_factor(0/1/2노트: 0.85/1.0/0.75);  "
            "harmony = 평균(pair)"
        ),
        inputs=("향조 벡터", "노트 위치", "보완 쌍 목록"),
        basis_ko=(
            "향조가 겹치는 정도, 향조 벡터의 코사인 유사도, 탑–베이스 거리, 그리고 문헌에서 "
            "흔히 함께 쓰는 보완 쌍(플로럴+우디 등)에 작은 가산을 주어 쌍별 조화를 계산하고 "
            "아코드 전체를 평균합니다."
        ),
        boundary_ko=(
            "혼합의 실제 냄새를 예측하지 않습니다. 향조가 거의 겹치지 않는 조합도 조향가가 "
            "의도적으로 쓰면 좋은 향이 될 수 있고, 반대도 마찬가지입니다. 후보를 고르는 순위 지표입니다."
        ),
        used_in=("ID", "MOLECULE", "STUDIO", "비교", "보고서"),
        references=(_PUBCHEM,),
    ),
    Indicator(
        id="volatility_index",
        label_ko="휘발성 지수",
        label_en="Volatility index",
        kind="heuristic",
        unit="0–1 (1 = 가장 빠름)",
        formula="base(note) × clamp(170 / MW, 0.55, 1.20)   [base: 탑 0.92 · 미들 0.60 · 베이스 0.25]",
        inputs=("노트 분류", "분자량"),
        basis_ko=(
            "노트 분류(탑/미들/베이스)를 기본값으로 두고, 같은 노트 안에서는 분자량이 클수록 "
            "느리게 날아가도록 보정했습니다. 분자 지도의 세로축과 노트 축에 쓰입니다."
        ),
        boundary_ko=(
            "증기압 측정값이 아닙니다. 이 번들에는 공개 증기압 데이터가 없어 증기압·LogP로 "
            "휘발성을 추정하지 않았고, LogP는 별도 유도 지표로만 표시합니다. 실제 발향 속도는 "
            "매트릭스·캐리어·피부에서 크게 달라지므로 이 지수로 지속시간을 약속할 수 없습니다."
        ),
        used_in=("MOLECULE", "보고서"),
        references=(_PUBCHEM,),
    ),
    Indicator(
        id="dilution_arithmetic",
        label_ko="배합 계량·완성품 농도",
        label_en="Dilution arithmetic",
        kind="derived",
        unit="mL · g · % w/w",
        formula=(
            "V_frag = V_total × load/100 ;  m_i = (V_frag × share_i/100) × ρ_i ;  "
            "w/w_i = m_i / (Σm_i + Σm_carrier) × 100"
        ),
        inputs=("부향률", "배합비", "원료 밀도", "캐리어 비율·밀도"),
        basis_ko=(
            "부향률은 완성품 대비 향 농축액의 부피 비율로 정의하고, 각 원료의 g은 그 원료 "
            "자신의 밀도로 계산합니다. 안전 판정은 부피가 아니라 완성품 질량 기준(w/w)입니다."
        ),
        boundary_ko=(
            "이상적 혼합을 가정합니다. 실제로는 온도·수축·에멀션에 따라 부피가 더해지지 "
            "않을 수 있고, 원료 밀도는 공급원에 따라 몇 % 차이가 납니다. 라벨에는 w/w를 쓰세요."
        ),
        used_in=("STUDIO", "비교", "Excel", "보고서"),
        references=(_PUBCHEM,),
    ),
    Indicator(
        id="safety_gate",
        label_ko="안전 상한 게이트",
        label_en="Safety ceiling gate",
        kind="heuristic",
        unit="% w/w",
        formula=(
            "cap_i = working_cap_i × cap_scale(제형) ;  ratio_i = w/w_i / cap_i ;  "
            "ok < 0.6 ≤ caution < 1.0 < over"
        ),
        inputs=("원료별 실무 상한", "노출 경로 계수", "완성품 농도"),
        basis_ko=(
            "원료별 실무 상한은 공개 화장품·조향 가이드라인과 감작·자극 문헌을 요약해 정한 "
            "보수적 내부 기준입니다. 공간 확산 제형(리드 디퓨저 ×6, 룸 스프레이 ×3, 린넨 미스트 "
            "×1.5)은 피부 도포가 아니므로 같은 상한에 명시적 노출 경로 계수를 곱해 판정합니다."
        ),
        boundary_ko=(
            "IFRA 인증도, 규제 판단도, 화장품 안전성 평가(CPSR)의 대체도 아닙니다. "
            "환기·영유아·반려동물 주의는 계수로 완화되지 않으며, 판매·배포 전에는 별도의 "
            "안전성 평가가 필요합니다."
        ),
        used_in=("STUDIO", "비교", "Excel", "보고서"),
        references=(_IFRA, _PUBLIC_GUIDANCE),
    ),
    Indicator(
        id="note_pyramid",
        label_ko="노트 피라미드",
        label_en="Note pyramid",
        kind="heuristic",
        unit="% of concentrate",
        formula="share_note = Σ_{i∈note} share_i / Σ share",
        inputs=("원료별 노트 분류", "배합비"),
        basis_ko=(
            "각 원료를 탑/미들/베이스로 분류하고 배합비를 합산합니다. 분류는 공개 향 설명과 "
            "조향 관행(휘발 속도)에 따른 것으로, 탑=첫인상, 베이스=잔향의 구조를 봅니다."
        ),
        boundary_ko=(
            "노트 경계는 실제로 연속적입니다. 같은 원료도 농도·캐리어에 따라 다른 노트에서 "
            "느껴질 수 있고, 피라미드 비중이 냄새의 순서를 보장하지 않습니다."
        ),
        used_in=("ID", "STUDIO", "비교", "보고서"),
        references=(_PUBLIC_GUIDANCE,),
    ),
    Indicator(
        id="conformer_3d",
        label_ko="3차원 구조(conformer)",
        label_en="3-D conformer",
        kind="derived",
        unit="Å 좌표",
        formula="SMILES → ETKDGv3 임베딩(random seed 고정) → MMFF94s 에너지 최소화",
        inputs=("공개 SMILES", "RDKit"),
        basis_ko=(
            "공개 SMILES에서 수소를 붙여 ETKDGv3로 3차원 좌표를 만들고 MMFF94s로 최소화했습니다. "
            "결합 길이 0.9–1.75 Å, 중심 정렬, 결정론적 재현을 테스트로 검사합니다."
        ),
        boundary_ko=(
            "가장 낮은 에너지의 conformer 하나이며 앙상블이 아닙니다. 회전 가능한 결합이 많은 "
            "분자는 여러 형태를 오가고, 표시된 구조가 생체 활성 구조라는 보장은 없습니다. "
            "입체화학 제약을 풀어 임베딩한 분자(예: α-copaene)는 화면에 플래그로 표시합니다."
        ),
        used_in=("MOLECULE", "3D 결합"),
        references=(_RDKIT_ETKDG, _MMFF),
    ),
    Indicator(
        id="schematic_docking",
        label_ko="모식적 수용체 결합 fit",
        label_en="Schematic docking fit",
        kind="heuristic",
        unit="0–100 (모식)",
        formula=(
            "fit = 100×(0.62·min(1, raw/(0.52·N_res)) + 0.22·(1−unsat) + 0.16·min(1, 1.15·contacts/N_res)) "
            "− 7·clashes − 0.25·outside ;  raw = 1.15·hbond + 0.55·hydrophobic + 0.75·π"
        ),
        inputs=("conformer 좌표", "모식 7-TM 포켓", "Ballesteros–Weinstein 잔기"),
        basis_ko=(
            "Class A GPCR의 공개된 7회 관통 나선 배열을 이상화한 포켓에 분자를 강체로 넣어 "
            "보고(288 회전 × 7 위치), 잔기와의 수소결합·소수성·π 접촉 수와 거리로 점수를 냅니다. "
            "Mainland 2015에 실측 반응이 있는 조합은 '문헌 보고 활성'으로 따로 표시합니다."
        ),
        boundary_ko=(
            "힘장·용매·엔트로피가 없는 모식 모델이며, 출력값은 Kd·EC50·ΔG가 아닙니다. "
            "잔기는 PDB 원자 좌표가 아니라 번호로 표시한 모식 잔기입니다. 실제 결합 친화도나 "
            "독성 검증을 대체하지 않습니다."
        ),
        used_in=("MOLECULE", "3D 결합"),
        references=(_BW, _MAINLAND),
    ),
)

_BY_ID: dict[str, Indicator] = {i.id: i for i in INDICATORS}


def indicators() -> tuple[Indicator, ...]:
    return INDICATORS


def get(indicator_id: str) -> Indicator:
    return _BY_ID[indicator_id]


def by_kind(kind: str) -> list[Indicator]:
    if kind not in KINDS:
        raise KeyError(f"unknown evidence kind {kind!r}; choose from {tuple(KINDS)}")
    return [i for i in INDICATORS if i.kind == kind]


def counts() -> dict[str, int]:
    return {k: sum(1 for i in INDICATORS if i.kind == k) for k in KIND_ORDER}


def for_context(context: str) -> list[Indicator]:
    """Indicators that feed a given surface (ID, STUDIO, MOLECULE, 비교, 보고서…)."""
    return [i for i in INDICATORS if context in i.used_in]


def references() -> list[Reference]:
    """Every distinct reference, de-duplicated by DOI/URL."""
    seen: dict[str, Reference] = {}
    for ind in INDICATORS:
        for ref in ind.references:
            seen.setdefault(ref.link or ref.label, ref)
    return list(seen.values())


BOUNDARIES: dict[str, str] = {
    "science": (
        "OLFACTRA는 공개 분자·향조 데이터로 후보 배합을 제안합니다. 완성된 혼합물의 냄새를 "
        "예측하지 않으며, 관능평가·GC-MS 분석·안정성 시험을 대체하지 않습니다."
    ),
    "safety": (
        "실무 상한은 공개 가이드라인을 바탕으로 한 보수적 작업 기준입니다. IFRA 인증도 규제 "
        "판단도 아니며, 판매·배포 전에는 별도의 화장품 안전성 평가가 필요합니다."
    ),
    "model": (
        "휴리스틱 지표(향조 가중치·조화·휘발성·모식 도킹)는 순위를 돕는 근거일 뿐 측정값이 "
        "아닙니다. 측정값이 없는 분자는 추정으로 채우지 않고 '미측정'으로 남깁니다."
    ),
    "clean_room": (
        "모든 입력은 공개 데이터(SMILES·PubChem·Pyrfume·퍼블릭 도메인 문헌)이며, 상용 포뮬러·"
        "캡티브 원료·독점 SDK는 사용하지 않았습니다. MIT 라이선스."
    ),
}


def as_dict() -> dict[str, Any]:
    """Serialisable registry, used by the API, the reports and the web panel."""
    return {
        "schema_version": "0.2.0",
        "kinds": [{"id": k, "label": KINDS[k], "description_ko": KIND_DESCRIPTION_KO[k]}
                  for k in KIND_ORDER],
        "counts": counts(),
        "indicators": [i.as_dict() for i in INDICATORS],
        "references": [r.as_dict() for r in references()],
        "boundaries": dict(BOUNDARIES),
    }


def markdown_table(only: Iterable[str] | None = None) -> str:
    """A Markdown table of the registry — the appendix of every report."""
    chosen = [get(i) for i in only] if only else list(INDICATORS)
    lines = [
        "| 지표 | 근거 등급 | 수식·방법 | 경계 |",
        "| --- | --- | --- | --- |",
    ]
    for ind in chosen:
        formula = ind.formula.replace("|", "\\|")
        boundary = ind.boundary_ko.replace("|", "\\|")
        lines.append(f"| **{ind.label_ko}** ({ind.unit}) | {KINDS[ind.kind]} | {formula} | {boundary} |")
    return "\n".join(lines)


def markdown_references() -> str:
    return "\n".join(f"- {ref.as_markdown()}" for ref in references())
