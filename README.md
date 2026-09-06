<div align="center">

# 📦 vax-proposal-kit

### 공고가 「도전」이 되는 순간, 제안서 재료가 위키에 도착하고 — 사람과 Claude가 게이트를 넘으며 초안을 쓴다

**입찰 제안 하네스 · 서버는 재료만, 판단·문장·디자인은 사람 + 개인 Claude**

[![skill](https://img.shields.io/badge/skill-vax--proposal-082567?style=for-the-badge)](skills/vax-proposal/SKILL.md)
[![gates](https://img.shields.io/badge/gates-P1→P6_%7C_2_hard_gates-1b4fc4?style=for-the-badge)](#-게이트--느낌으로-통과하지-않는다)
[![LLM calls on server](https://img.shields.io/badge/server_LLM_calls-0-0f7038?style=for-the-badge)](server/README.md)
[![selftest](https://img.shields.io/badge/proposal__material_selftest-48_pass-0f7038?style=for-the-badge)](server/proposal_material.py)
[![fonts](https://img.shields.io/badge/fonts-Freesentation_·_Paperlogy-141414?style=for-the-badge)](fonts/README.md)
[![license](https://img.shields.io/badge/fonts_license-SIL_OFL_1.1-8f5000?style=for-the-badge)](fonts/OFL.txt)

<br>

> **"제안서는 배치 작업이 아니라 판단 작업이다."**  
> 없는 실적을 지어내는 사고를 막으려면 사람이 중간에 검문해야 한다.  
> 그래서 서버는 **재료**를 만들고, 초안은 **사람 곁의 Claude**가 쓴다. — 한준, 2026-09-04

</div>

---

## ⚡ 60초 시작

```bash
git clone https://github.com/vaxport123/vax-proposal-kit
cd vax-proposal-kit && bash install.sh     # 스킬 → ~/.claude/skills · 글꼴 → 사용자 글꼴 폴더 (관리자 권한 불필요)
bash doctor.sh                             # 스킬·글꼴·파이썬·렌더러·판·커밋 훅·웹 검색·저장소 점검 + 커넥터 확인 방법
```

**처음이라면 [`START.md`](START.md)를 먼저 읽는다** — 읽는 순서, 커넥터가 무엇이 열려야 정상인지, 첫 사업 30분 코스가 한 쪽에 있다.

그다음 Claude에게 이렇게 말한다.

> **"준비 점검"** → 빠진 설치·연결을 Claude가 확인하고 한 번에 요구한다(P-1).
> **"새 사업 접수"** 또는 **"R26EX00000001 제안 진행해줘"** → RFP 원문 · 노션·피그마 연결 · 당신이 말로 주는 주요 방향 · 이전 제안서·담당자 메모·사진을 차례로 묻는다(P-0).

다 받은 뒤 재료 팩을 읽고 → 평가표를 검산하고 → 가점 게이트를 넘고 → 레퍼런스를 붙이고 → 방향 후보를 내어 **동의를 묻는다.** 초안 게이트를 통과해야 초안을 쓰고, 덱 게이트(심사 80점 · 재료점검 · 승인 · 피그마 연결)를 통과해야 Figma를 연다. 자료가 얇으면 요구하고, 끝나면 회고를 묻는다.

<details>
<summary>설치 옵션</summary>

```bash
bash install.sh --list       # 무엇이 깔리는지 미리보기
bash install.sh --no-fonts   # 글꼴 제외
bash install.sh --force      # 덮어쓰기
```
`marketplace` 항목(fluent-korean · humanize-korean · claw-hwp)은 스크립트가 못 깐다 — 출력되는 `/plugin` 명령을 Claude Code에서 1회 실행한다.
글꼴은 설치 뒤 Figma·PowerPoint·브라우저를 다시 열면 보인다.
판 번호는 `VERSION`에 있고 바뀐 내용은 [`CHANGELOG.md`](CHANGELOG.md)에 있다. 새 판을 낼 때는 사람이 `git tag v0.6.0`처럼 태그를 달면, 다른 직원의 `doctor.sh`가 「새 판 있음」을 알려 준다.
</details>

---

## 🔁 흐름 — ERP에서 Figma까지

```mermaid
flowchart LR
    A["① ERP<br/>입찰레이더 진행상태 = 도전<br/>+ 우리담당 지정"] --> B["② 서버 · 30분 안<br/>📦 제안 재료 팩<br/>📄 RFP 원문(추출)<br/><b>LLM 0콜</b>"]
    B --> C["③ 담당자<br/>clone → install.sh<br/>Notion 커넥터"]
    C --> D["④ Claude · vax-proposal<br/>P1 검산 → P2 가점 게이트<br/>P3 레퍼런스 → 방향 동의<br/>P4 초안 + 검토 3회<br/>P5 심사 게이트 ≥ 80"]
    D --> E["⑤ 재료 게이트 → 고스트 덱<br/>결정·반대·사진·숫자 없으면 안 만든다<br/>장 = 액션 타이틀 + 증거 하나 · 사람 승인"]
    E --> F["⑥ Figma<br/>한 장 시안 → 행별 제작 → validate<br/>전 장 화면 → 비판자 · 이때부터 Figma가 정본"]
    style B fill:#e7f3ea,stroke:#0f7038
    style D fill:#e7ecf7,stroke:#082567
    style F fill:#fbefda,stroke:#8f5000
```

| 단계 | 누가 | 무엇을 | 어디에 |
|---|---|---|---|
| ② | 서버 `proposal_material.py` | 캐시·덤프·학습 DB·위키 색인을 열 개 절로 모은다. 판본이 같으면 다시 쓰지 않는다 | 공고 페이지의 자식 페이지 2개 |
| ④ | 개인 Claude + `vax-proposal` | 재료 팩만 근거로 쓴다. 없는 것은 `⚠️ 확인필요`로 남긴다 | `bids/<사업명>/` (git 제외) |
| ⑤ | 개인 Claude + `deck.md` | **재료 게이트**(결정 한 문장·반대 셋·발주처 사진 6·우리 실물 6·숫자 5·카드 8 — 없으면 재료 요청서만) → **고스트 덱**(장 = 액션 타이틀 + 증거 하나 + 출처) → 대응표·반대 의견·리듬 → `proposal_lint.py --plan` → 비판자 → 사람 승인 | `06_재료점검.md` · `07_슬라이드계획_vN.md` |
| ⑥ | Figma MCP + `figma_slides_helpers.js` | 발주처 CI · Freesentation · 한 장 시안 확인 → 행별 제작 · `validate()` → 전 장 화면을 비판자에게. HTML 1장(`render_html.py`)은 필요할 때만 | Figma |

---

## 🚧 게이트 — 느낌으로 통과하지 않는다

| 게이트 | 기준 | 미달 시 |
|---|---|---|
| **① 가점 (P2)** | 정량 실점 합계 **≤ 5.0** — 신용등급·실적 건수·지체상금 단계표는 **RFP 원문 표**로 센다 | 정성 비중 ≥ 70%면 사람 판단, 아니면 중단(가점미달). 회복가능 실점은 `차단사항`에 기한과 함께 |
| **② 심사 (P5)** | 심사위원 페르소나 채점 **≥ 80** — 감점 사유를 먼저 전부 쓰고, 항목마다 제안서 안 근거 위치를 인용. 못 하면 0점 | 재작성 1회(상위 3건만) → 그래도 미달이면 중단(심사미달) |

**80점은 합격선이 아니라 착수선이다.** 통과 뒤에도 「질 수 있는 지점」은 발표자료에서 보강한다.

---

## ✍️ 글의 세 기준 (한준 2026-09-04 · 09-05 "3가지에 집중")

| 기준 | 한 줄 | 어디에 |
|---|---|---|
| **RFP 기준 인사이트 — 기관을 웹에서 읽는다** | **먼저 `probe_web.py`가 일곱 유형 검색·숫자 문장·공식 데이터 링크를 긁어 오고**, RFP 고유명사를 출발점으로 기관 홈페이지·보도자료·전년도 같은 사업·감사/회의록·상위 계획을 읽고, 「RFP 문장 ↔ 확인한 사실 ↔ 숨은 필요」로 배점 항목에 연결한다. 연결 안 되면 버린다 | [`writing.md`](skills/vax-proposal/references/writing.md) §2 → `03a_페인포인트.md` |
| **VAXPORT만의 색 — 카드 × 페인포인트** | 실물·등록·실적·사람·방식 카드에 「경쟁사가 못 쓰는 이유」를 붙이고, 페인포인트와 교차해 아이디어 열 개에서 셋을 고른다. 회사명을 가리고 읽어 경쟁사가 그대로 쓸 수 있으면 지운다 | [`writing.md`](skills/vax-proposal/references/writing.md) §3 → `03b_방향전략.md` |
| **AI 같지 않은 문장 — 말로 먼저** | 기억할 문장 하나 → 말로 먼저 → 구체에서 시작 → 한 사람 시점 → 소리 내어 읽기. AI 티는 낱말·리듬·구조 세 층에서 잡는다 | [`writing.md`](skills/vax-proposal/references/writing.md) §4 · `proposal-critic` A1~A9 |

---

## 🧪 실전 기록

| 날짜 | 공고 | 결과 |
|---|---|---|
| 2026-09-06 | 회사 손 덱 3개에서 레이아웃 뽑기 | 재도전(46)·생명지킴이(44)·공정자동화(54) 118장을 행 단위 화면으로 보고 대표 26장 좌표를 재어 하우스 문법(헤더 띠·제목 48 강조 구절·부제·결론 띠·쪽번호)과 틀 14종을 `layouts.json`으로 정본화. 와이어프레임 PNG·JS 좌표·Figma 라이브러리(15장)까지 한 정본에서 생성. 배운 것: 손 덱은 사진이 절반, 표는 5~8장, 카드 안에 늘 그림·숫자·사진 하나, 어두운 면은 장마다 카드 하나, 결론 띠는 「그래서」 |
| 2026-09-06 | 대학 캠퍼스 VR 건 v5를 세 번 고친 뒤 방향을 뒤집음 | 표·카드 두 얼굴 → 도식 10장 → 말투 세 번. 그래도 문서 같은 덱이었다. 원인은 **문단을 슬라이드에 흘려 넣는 파이프라인 자체**. 지운 것: 문단 전부 배치 규칙 · 절대 좌표로 쌓는 헬퍼(chrome·bar·body·part·toc) · 도식 14종을 덱에 쓰는 발상 · 개념도 레시피 6종. 넣은 것: 재료 게이트(§0) · 고스트 덱(장 = 액션 타이틀 + 증거 하나 + 출처) · 리듬 배분 · 증거 검사(`evidenceCheck`) · lint P4·P7·P8. 근거: Assertion-Evidence(Penn State) · 컨설팅 고스트 덱·액션 타이틀 · AI 덱이 밋밋한 이유는 입력 부재. 다음 일: 회사 손 덱 3개에서 레이아웃 컴포넌트 뽑기 |
| 2026-09-05 | 대학 캠퍼스 VR 건 덱 v5 46장 실제 제작(새 규칙 첫 완주) | 브리프 → 한 장 시안 → 행별 제작 → validate → 46장 화면 → 비판자 43건 반영. 배운 것: ① 본문 19px·문단 화면 배치가 캔버스 절반을 비웠다 → 문단은 노트, 글자 22 기준선, 도식 중심 ② 제목 사슬이 장마다 새 주제로 시작하고 「그 셋」이 흔들렸다 → 사슬 조건 셋(근거 통합·앞 제목 받기·붙여 읽기) ③ 규칙을 게이트로 올리면 글 문서가 된다 → 게이트는 RFP 관련만, 나머지는 경향 ④ Figma 토큰이 30분마다 끊긴다 → 노드 ID·진행을 상태 파일에 적어 재개 |
| 2026-09-05 | 대학 캠퍼스 VR 건 덱 두 판 비교 | 24장(네이티브)은 짜임새는 좋고 내용이 빠졌고, 46장(SVG 일괄)은 내용은 다 들어갔는데 하단 1/3 공백·13px 표·제목 중복으로 한 얼굴이 됐다. 원인은 하루에 여덟 번 덧붙인 규칙이 전부 「같게 만드는」 쪽이었기 때문. 규칙 파일 12개 → 글·덱·채점 셋으로 줄이고, 고정 좌표·장수 공식·결론 바 필수를 뺐다. 변주 규칙과 완성 덱 화면 검토를 넣었다 |
| 2026-09-04 | **대학 캠퍼스 VR 건** (예시 번호 R26EX00000001) | P0~P4 완주. 재료 팩 7초·17,000자, RFP 원문 33,465자 자식 페이지. P1 검산 100점 일치 · P2 실점 2~4 통과 · P3 매칭 12건 · 웹 조사 6건으로 컨셉 도출 · 초안 v1→v4(검토 3회). 이 과정에서 스크립트 결함 4건(배점 단위·기술:가격 어순·원문 미첨부·설치 스크립트 변수)을 잡아 고쳤다 |

---

## 🗂️ 저장소 지도

```
skills/vax-proposal/            ★ 스킬 (install.sh 가 ~/.claude/skills 에 복사하는 유일한 폴더)
  SKILL.md                        절차 P0~P6 · 원칙 7 (Claude가 읽는 두뇌)
  references/
    writing.md                  ★ 글 — 세 축: 페인포인트(기관 웹 조사) · 색채(카드 × 페인포인트 → 아이디어) · 문장(말로 먼저 · AI 티 세 층) + 방향 순서 · 점검표
    deck.md                     ★ 덱 — RFP 규칙 우선 · 제목 사슬 · 본문 전체 수록 · 도식 14종 · 색·글꼴·헤더·쪽번호 · 변주 · 완성 검사
    review-rubric.md              채점 — P5 페르소나 고정 · 감점 먼저 · 근거 인용 의무 · 반복 감점 패턴
    material-pack.md              서버 ↔ 스킬 계약 — 재료 팩 열 개 절 + RFP 원문 자식 페이지
    staffing-table.md · reference-index.template.md   서식 구조 (데이터는 위키에만)
    images.md · figma-howto.md    절차 — 사진 출처·사용권 · Figma MCP 실측 요령
    layouts.md · layouts.json   ★ 틀 — 회사 손 덱 3개(118장)에서 잰 하우스 문법 + 틀 14종 · Figma 라이브러리 링크
    guardrails.md                 공개 금지 정보 (render_html.py가 기계로 막는다)
  scripts/
    ../../scripts/preflight.py  ★ P-1 준비 점검 — Claude가 첫 동작으로 돌려 필수/권장을 판정하고 빠진 것을 사용자에게 한 번에 요구
    readiness.py                ★ 초안 게이트·덱 게이트 판정 — RFP·연결·방향·재료·승인이 다 갖춰지기 전에는 초안도 피그마도 시작하지 않는다
    gap_check.py                ★ 사업 폴더의 자료 결손을 세어 질문서 초안(재료 요청·회고 일곱) — Claude가 묻는 재료
    probe_web.py                ★ 발주처·과업 웹 재료 자동 수집 — 일곱 유형 검색(DuckDuckGo 무료) · 페이지 숫자 문장 · 공식 데이터 링크(대학알리미·알리오·지방재정365…) · 발상 기법 일곱별 자극 카드 → 03a_raw.md
    proposal_lint.py            ★ 초안·계획 정규식 검사 L1~L12 · P1~P6(번역투·빈 수사·40자·리듬·표·출처·브리프·제목 사슬·연속 유형·대응표) — LLM 없음 · 「상」은 RFP 관련만
    render_html.py                마크다운 → 회사 디자인 HTML 1장 (+ 공개 금지 검사)
    figures_svg.py                ```fig 블록 → SVG 도식·표 14종 (--no-title · 표 글자는 폭에 비례)
    img_fetch.py · figma_slides_helpers.js   사진 받기 + MANIFEST · Figma Slides 프리미티브 + validate + evidenceCheck(증거 없는 장·사진 없는 PART·발주처 없는 제목)
    figma_slides_diagrams.js      증거 레시피 넷(동선 지도·연결도·배치도·타임라인) + 표 채우기
    figma_slides_layouts.js       ★ 하우스 틀 14종(houseChrome · applyLayout · layoutFor) — 좌표는 references/layouts.json 정본에서 layout_wireframes.py 가 생성
    layout_wireframes.py          layouts.json → assets/layouts/*.png 와이어프레임 + JS 좌표 블록 (--selftest)
    ui_tokens.py                  디자인 정본 사본 (서버 ops/ui_tokens.py ← sync_tokens.sh)

server/                         서버에 두는 것의 초안·명세 (직원 PC에 설치되지 않음)
  proposal_material.py          ★ 도전 공고 → 📦 재료 팩 + 📄 RFP 원문 · LLM 0콜 · 셀프테스트 48건
  systemd/                        vax-proposal-material.timer / .service 사본
agents/proposal-critic.md       비판자 — lint 결과를 받아 A1~A9 · B1~B10(경향) · 완성 덱 화면(PNG) 검토
examples/                     ★ 이름을 가린 완성 예시 한 세트(가상 발주처) — 01~07 서식 · lint 통과 상태 유지(회귀 테스트)
loops/bid-loop/                 ★ /bid-loop 하네스 — 운행 규칙 · _STATE 상태 기계 · 야간 실행 래퍼
fonts/                          Freesentation · Paperlogy 각 9굵기 TTF (SIL OFL) + 설치기
assets/photos/                  회사 사진 81장 (회사소개서 마스터에서 추출, MANIFEST.md)
templates/company-intro/        회사소개서 마스터 v3 HTML (발표 톤 참고)
skills.tsv                      설치 매니페스트 — 승인 스킬의 정본
install.sh · doctor.sh          설치(커밋 훅 연결 포함) · 점검(판·훅·웹 검색 포함)
START.md                        처음 한 번은 이 순서로 — 읽는 순서 · 커넥터 점검 · 첫 사업 30분
CHANGELOG.md · VERSION          바뀐 것 · 판 번호(태그는 사람이 git tag v0.6.0)
.githooks/pre-commit            커밋 전 셀프테스트 여섯 종 + 공개 범위 검사(core.hooksPath로 켠다)
.github/ISSUE_TEMPLATE/         버그 신고 · 개선 요청 서식
bids/                           (git 제외) 사업 폴더 — _STATE.md · 01~04 산출물 · logs/
```

---

## 🧩 함께 담은 스킬 (`skills.tsv`)

| 역할 | 스킬 | 출처 | 방식 |
|---|---|---|---|
| 제안 상류 | `vax-proposal` | 이 저장소 | git |
| 한국어 문체 | `fluent-korean` | snflkd/fluent-korean (MIT) | marketplace |
| AI 티 윤문 | `humanize-korean` | epoko77-ai/im-not-ai (MIT) | marketplace |
| 영어 패턴 윤문 | `humanizer` | blader/humanizer | npx |
| 제안 리서치 | `deep-research` | Weizhena/Deep-Research-skills | git |
| HWP 생성·편집 | `claw-hwp` | DoHyun468/claw-hwp | marketplace |
| docx·pptx·xlsx·pdf | `doc-gen` | Anthropic 내장 | builtin |
| HWP 변환 | `hwp-convert` | hwp-mcp 내장 | builtin |
| HTML 디자인 방향 | `frontend-design` | Anthropic 내장 플러그인 | builtin |
| Figma 삽입·편집 | Figma MCP | Figma 공식 커넥터 | builtin |
| 제안 하류 (완성 서식) | `vax-exit-kit` | vax-wiki-gateway | git |

외부 스킬은 Tools DB(01.WIKI_AI) 보안 검토를 거쳐 「사용중」이 된 것만 넣는다. 후보·보류는 넣지 않는다.

<details>
<summary>검토 대기 후보</summary>

| 스킬 | 출처 | 의견 (2026-09-04) |
|---|---|---|
| **Figma 공식 `figma-use-slides`** | Figma MCP 커넥터 내장(설치 불필요) | **채택(2026-09-05)** — Slides 좌표 어긋남 회피·배치 검증 스크립트·안티패턴 16. `figma-howto.md` 전제에 넣었고 헬퍼 `validate()`로 옮겼다 |
| `yoonmoon` | amondnet/yoonmoon (MIT) | **채택(09-05 검토 완료)** — 파일 43개 전부 SKILL.md·참고 문서, 실행 코드 없음. `detect`(AI 가능성 판정)·`proofread`(맞춤법)만 쓰고 윤문은 humanize-korean 하나로. `skills.tsv` 등록 |
| `korean-skills` grammar-checker | daleseo/korean-skills | 검토 완료(프롬프트만, 안전). yoonmoon proofread와 겹쳐 **보류** — 하나만 쓴다 |
| `mcp-openverse` | neno-is-ooo/mcp-openverse | **채택(09-05 검토 완료)** — 289줄 TypeScript, 의존성 fastmcp·zod, api.openverse.org만 호출, 키·환경변수 없음. 판 0.1.1로 고정. 분위기용 사진에만(발주처 시설 사진은 못 찾는다). `skills.tsv` mcp 줄 |
| `browser-pilot` | Dev-GOM 마켓플레이스 | **제외(09-05 검토)** — 세션 시작 훅이 프로젝트 폴더에 스크립트를 복사하고 `npm install`·`npm run build`를 자동 실행, 종료 훅이 프로세스를 죽인다. 정상 도구지만 우리 기준(설치 시 자동 실행 금지)에 걸린다. 페인포인트 조사의 JS 페이지는 Claude에 이미 있는 Chrome DevTools MCP나 agent-browser(hermes와 같은 것)로 |
| `hwpx-plugins` · `easy-hwp` · k-skill HWP | airmang · nathankim0 · NomaDamas | hwp 제출용. claw-hwp와 비교해 하나만 |
| `axlabs-mckinsey-pptx` | seulee26/mckinsey-pptx (MIT) | 템플릿 40종. **디자인 자율 방향과 충돌**해 보류 |
| hanspell · Felo Slides · 2Slides | — | 제안서 본문을 외부 서버로 보낸다 → **대외비라 뺀다** |
</details>

---

## 🧭 정본은 한 곳에

| 무엇 | 정본 | 이 저장소에는 |
|---|---|---|
| 디자인 값 | 서버 `ops/ui_tokens.py` | 사본 (`sync_tokens.sh`로만 갱신) |
| 회사 팩트·실적·인증 | 위키 회사 팩트 DB · Certifications · Projects | 없음 — 재료 팩으로 받는다 |
| 실적 ↔ 기술요소 ↔ 재활용 문구 | 위키 [레퍼런스 색인](https://app.notion.com/p/3d16394f4c9981b493e3d4b5dc7884a9) (01.WIKI_AI / Company) | 없음 — 실명·재무·신용등급은 git에 두지 않는다 |
| 인력 데이터(성명·이력·4대보험) | 위키 색인 §I · Members · 인력구성 최신본 | 서식 구조만 (`staffing-table.md`) |
| 재료 팩 목차 | `references/material-pack.md` | 서버와 스킬이 함께 지키는 계약 — 한쪽만 바꾸지 않는다 |
| 완성 디자인 | Figma | 없음 — HTML은 초안이다 |

---

## 💬 문제가 생기면

저장소에 이슈를 올린다 — `.github/ISSUE_TEMPLATE/`의 「버그 신고」 또는 「개선 요청」 서식. 급하면 운영자(한준)에게 슬랙으로 알린다. 이슈에는 회사 사실·실명·공고번호·금액을 지우고 올린다.

---

## 📜 지키는 것

- 회사명·대표·실적·인증·신용등급·숫자는 **재료 팩에서만.** 임의 입력·추정·기억 인용 금지.
- 근거 없는 문장은 쓰지 않는다. `⚠️ 확인필요 — <무엇이 필요한지>`로 남긴다.
- 서버 주소·포트·모델명·채널 ID·내부 경로·토큰·임직원 실명은 산출물에 넣지 않는다. 렌더러가 기계로 막고, 실명은 사람이 본다.
- 방향(P3.5)은 사용자 동의 뒤에 전략으로 간다.
- 사람이 Figma·노션에서 고친 값이 정답이다. 되돌려 덮어쓰지 않는다.

<div align="center">
<sub>주식회사 백스포트 · 2026 · 서버 쪽 정본은 <code>vaxport123/vax-wiki-gateway</code></sub>
</div>
