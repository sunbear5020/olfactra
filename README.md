# OLFACTRA

**The Intelligence of Scent** · *From a molecule to a memory of a place.*
**ID** (recommendation) · **STUDIO** (formulation) · **ATLAS** (history) · **MOLECULE** (chemistry)

Clean-room, public-data, **MIT-licensed** fragrance intelligence by
**FEI · HEL Lab, Gyeongsang National University**.

- Web workbench (browser only, no install): <https://sunbear5020.github.io/olfactra/>
- Workbench source in this repository: [`web/`](web/) — the same files the live site serves
- Python engine: this repository (`deploy/olfactra/`)
- Version: **0.1.0 (OLFACTRA Core)** · 43 molecules · 22 atlas entries · 15 accords · 8 product types

> **What OLFACTRA does and does not do.** It proposes *candidate* accords and
> formulas from public molecule and odour data, and it checks a formula against
> conservative working ceilings. It does **not** predict how a blend will smell,
> and it does not replace sensory evaluation, GC-MS analysis or a cosmetics
> safety assessment. Every number it prints is an argument to be tested, not a
> verdict.

---

## 한국어

### 무엇인가

OLFACTRA(올팩트라)는 **향을 '데이터'로 다루는 연구·창작 도구**입니다.
공개된 분자·식물·역사 자료를 바탕으로 (1) 기분·계절·공간·스타일에 맞는 향
프로필을 제안하고, (2) 디퓨저·룸스프레이·오 드 퍼퓸의 배합비를 계산하며,
(3) 고대부터 이어진 향의 기원을 기록하고, (4) 향 분자의 구조와 향조를
탐색합니다.

AI가 향을 완벽히 예측하는 것이 아니라, **공개 분자·향조 데이터로 후보 조합을
제안하고 실제 조향·GC-MS 실험 검증을 돕는** 위치에 있습니다.

### 4대 모듈

| 모듈 | 하는 일 | 코드 |
| --- | --- | --- |
| **OLFACTRA ID** | 기분·계절·공간·스타일 → 탑/미들/베이스 아코드 추천, 근거와 안전 경고 함께 | `olfactra_core/recommender.py` |
| **OLFACTRA STUDIO** | 제품 유형·총 용량·부향률 → 원료별 g/mL, 완성품 농도, 안전 상한 판정, 레시피 CSV/JSON/Excel | `olfactra_core/studio.py` |
| **OLFACTRA ATLAS** | 유향·몰약·삼나무·소나무 피톤치드·편백·유자 등 22개 항목의 기원·문헌·분자·주의사항 | `olfactra_core/atlas.py` |
| **OLFACTRA MOLECULE** | 43개 공개 향료 분자의 구조(SMILES)·분자량·작용기·향조 벡터, 유사도·조화 점수 | `olfactra_core/molecule.py` |

### 설치와 실행

```bash
cd deploy/olfactra
python -m venv .venv && source .venv/bin/activate     # 선택
pip install -r requirements.txt

python -m olfactra_core recommend --mood sleep --space bedroom --style floral
python -m olfactra_core formulate --product edp --volume 50 --load 20 \
    --accord "linalool=40,geraniol=25,phenylethyl alcohol=25,cedrol=10" --out recipe.xlsx
python -m olfactra_core molecule --similar linalool --top 5
python -m olfactra_core atlas --category forest
python -m olfactra_core demo --out olfactra-demo      # 예시 레시피 3종 × 3포맷
```

로컬 API(FastAPI):

```bash
uvicorn api.server:app --reload --port 8010
curl 'http://127.0.0.1:8010/api/recommend?mood=calm&space=study&style=green'
curl -X POST 'http://127.0.0.1:8010/api/formulate' -H 'Content-Type: application/json' \
  -d '{"product_type":"edp","volume_ml":50,"load_pct":20,"accord":{"linalool":60,"cedrol":40}}'
```

테스트:

```bash
python -m pytest -q        # 63 tests
```

### 웹 워크벤치 (이 저장소의 `web/`)

- **라이브**: <https://sunbear5020.github.io/olfactra/>
- **이 저장소 안의 원본**: `web/index.html` · `web/styles.css` · `web/app.js` · `web/data.js`
  (라이브 사이트와 같은 파일입니다. `data.js`는 `tools/build_web_data.py`로 엔진 라이브러리에서
  다시 만들 수 있습니다.)

설치 없이 내 컴퓨터에서 띄우려면:

```bash
cd web
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000 접속
```

이 저장소의 `web/`을 GitHub Pages로 공개하려면 Settings → Pages → Source를
`Deploy from a branch`, 브랜치 `main`, 폴더 `/web`으로 지정하면 됩니다.

### 배합 계산이 하는 일 (그리고 하지 않는 일)

- **부향률의 정의**: "20%"는 완성품의 20%가 향 농축액이라는 뜻입니다. 원료별
  완성품 농도는 `부향률 × 배합비`입니다. 이 둘을 혼동하면 향이 5배 강해집니다.
- **부피와 무게**: 계량은 부피로 하지만 안전 상한은 질량 기준입니다. 따라서
  원료 밀도로 g을 계산하고, 판정은 **완성품 w/w %** 로 합니다.
- **노출 경로**: 피부 도포 제품(EDP·EDT·바디 오일 등)은 피부 감작 상한을
  적용하고, 공간 확산 제품(리드 디퓨저 ×6, 룸 스프레이 ×3, 린넨 미스트 ×1.5)은
  같은 상한에 명시적 계수를 곱해 판정합니다. 계수와 기준값을 결과에 함께
  표시하므로, 언제든 숫자를 따져 물을 수 있습니다.
- **안전 상한의 성격**: 공개 문헌·일반 가이드라인을 바탕으로 한 **보수적 실무
  상한**입니다. IFRA 인증도, 규제 판단도 아니며, 판매·배포 전에는 별도의
  안전성 평가가 필요합니다. 자세한 경계는 `NOTICE.md`.

### 데이터 출처

- 분자의 분자식·분자량·SMILES·PubChem CID는 **PubChem** 공개 레코드에서 가져와
  RDKit으로 분자식·분자량을 교차 검증했습니다(43개 전부 일치).
- 향조 설명·천연 급원은 공개 향료화학·식물 정유 조성 문헌을 요약한 것입니다.
- 역사 항목은 헤로도토스·테오프라스토스·플리니우스·플루타르코스·구약성서 등
  **퍼블릭 도메인 1차 문헌**과 공개 박물관·논문 자료에 근거하며, 전승에 불과한
  내용은 본문에 "전승에 따르면"으로 표시했습니다.
- **상표·독점 포뮬러 일체 미포함.** 어떤 향수 회사의 레시피·캡티브 원료·
  기술자료도 사용하지 않았습니다.

### 로드맵

1. **Core 0.1 (지금)** — 분자 라이브러리, 아코드 추천, 배합·안전 게이트, 아틀라스, 정적 웹 워크벤치, 로컬 API.
2. **0.2** — GC-MS 피크 표 가져오기(공개 형식)·조성 매칭, 아코드 저장/버전 관리, 다국어(EN·JP) UI.
3. **0.3** — 실험 설계 모듈(희석 계열·패널 척도), 공개 데이터셋 기반 향조 임베딩 실험, 기관용 배포 패키지.

### CI (GitHub Actions)

세 파이썬 버전(3.10·3.11·3.12)에서 pytest와 CLI 스모크 테스트를 돌리는 워크플로를
`.github/ci-workflow.yml.template`로 두었습니다. 이 환경의 GitHub 연결 권한이
`.github/workflows/` 경로 쓰기를 허용하지 않아 템플릿으로 보관합니다.
GitHub 웹에서 이 파일을 `.github/workflows/ci.yml`로 옮기면(내용 그대로)
Actions가 다음 푸시부터 자동으로 돕니다. 로컬에서는 `python -m pytest -q`가 같은
검사입니다.

---

## English

### What it is

OLFACTRA treats scent as data. From public chemistry, botany and history it
(1) recommends an accord for a mood/season/room/style, (2) computes a DIY
formula with a safety gate, (3) documents the origins of aromatic materials, and
(4) lets you explore fragrance molecules and their odour profiles.

It is deliberately **not** a scent-prediction oracle. It narrows the search
space from public data and hands the candidate back to a human nose, a GC-MS
run, and a safety assessment.

### Quick start

```bash
pip install -r requirements.txt
python -m olfactra_core recommend --mood focus --space study --style minimal
python -m pytest -q
uvicorn api.server:app --port 8010
```

### Browser workbench (`web/`)

The workbench lives in this repository as well: `web/index.html`, `web/styles.css`,
`web/app.js`, `web/data.js` are what <https://sunbear5020.github.io/olfactra/> serves.
Run it locally:

```bash
cd web
python3 -m http.server 8000        # → http://localhost:8000
```

To publish this copy as well, set Settings → Pages → Source to branch `main`,
folder `/web`.

### API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | version, library counts, licence |
| GET | `/api/meta` | dimensions, product types, families, notes, stats |
| GET | `/api/molecules` | list/search (`q`, `note`, `family`) |
| GET | `/api/molecules/{id}` | one molecule + similar + atlas links |
| GET | `/api/molecules/{id}/similar` | odour-profile neighbours |
| GET | `/api/atlas`, `/api/atlas/{id}` | scent history archive |
| GET | `/api/accords` | the curated accord library |
| GET | `/api/recommend` | `mood`, `season`, `space`, `style`, `limit` |
| POST | `/api/formulate` | formula + per-material safety verdict |
| POST | `/api/recipe` | same formula as CSV/JSON download |
| GET | `/api/library.csv` | molecules or atlas as CSV |

### Layout

```
olfactra_core/
  molecule.py     # 43 public molecules, odour vectors, similarity, harmony, blend report
  atlas.py        # 22 historical/forest entries with sources and cautions
  studio.py       # product types, dilution math, exposure-aware safety gate
  recommender.py  # 15 curated accords, interpretable tag scoring
  exporter.py     # CSV / JSON / multi-sheet Excel
  cli.py          # python -m olfactra_core ...
api/server.py     # FastAPI
tests/            # pytest suite (63 tests)
tools/            # build_web_data.py — regenerates the web workbench data from this library
```

### Licence

MIT — `Copyright (c) 2026 FEI · HEL Lab, Gyeongsang National University`.
See `LICENSE` and `NOTICE.md` (clean-room statement, scientific and safety
boundaries, citation).
