# vax-proposal-kit — 제안서 작성 스킬셋 (개인 Claude용)

공고가 「도전」으로 확정되면 서버가 **재료 팩**(정량 지표·회사 자료·RFP 추출)을 위키에 써 두고,
직원은 자기 Claude에 이 스킬셋을 넣어 **제안 전략 → 초안 → HTML 디자인 → Figma**까지 진행한다.

서버는 더 이상 최종 문서·HTML을 자동으로 만들지 않는다. **판단·작성·렌더는 사람이 Claude와
함께 하고, 데이터·학습·추출은 서버가 맡는다.** (한준 2026-09-04 결정)

## 흐름

```
① [ERP]   입찰레이더에서 진행상태를 「도전」으로 바꾼다 (+ 우리담당 지정)
② [서버]  proposal_material.py 가 30분 안에 위키 정보를 모아 「📦 제안 재료 팩」을 그 공고 페이지 밑에 쓴다 (LLM 0콜)
③ [담당자] 이 저장소를 clone → install.sh 로 스킬 설치 → Claude에 Notion 커넥터 연결 → "R26BK… 제안 진행" 으로 시작
④ [Claude] 재료 팩 → P1 평가표 검산 → P2 가점 게이트 → P3 레퍼런스 → 방향·전략(동의) → P4 초안+검토 3회 → P5 심사 게이트
            → 회사 토큰으로 HTML 초안 1장 (scripts/render_html.py)
⑤ [Figma]  Figma 커넥터로 HTML을 슬라이드 프레임으로 넣는다 (references/figma-handoff.md)
⑥ [Figma+Claude] 세부 디자인·발표자료(ppt)는 Claude-Figma로 진행. 이때부터 Figma가 정본
```
(한준 2026-09-04 확정 흐름)

## 설치 (직원 PC)

```bash
git clone https://github.com/vaxport123/vax-proposal-kit
cd vax-proposal-kit && bash install.sh          # skills.tsv 의 스킬을 ~/.claude/skills 에 + 글꼴(Freesentation·Paperlogy)을 사용자 글꼴 폴더에 설치
bash install.sh --list                          # 무엇이 깔리는지 미리보기
bash install.sh --no-fonts                      # 글꼴은 빼고
```
글꼴은 설치 뒤 Figma·PowerPoint·브라우저를 다시 열면 보인다(`fonts/README.md`).
설치가 끝나면 `bash doctor.sh`로 점검한다 — 스킬·글꼴·파이썬·렌더러·저장소 최신 여부를 보고, Notion·Figma 커넥터는 Claude 안에서 확인하는 방법을 알려 준다.

또는 기존 `vax-wiki-gateway/skills/skills.tsv`에 이 저장소를 `git` 한 줄로 등록하면
직원은 늘 쓰던 `install.sh`로 함께 받는다.

`marketplace` 항목(fluent-korean · humanize-korean · claw-hwp)은 스크립트가 못 깐다 —
출력되는 `/plugin` 명령을 Claude Code에서 1회 실행한다.

## 저장소 구성

```
skills.tsv                    설치 매니페스트 (우리 스킬 + 승인 외부 스킬) — 정본
install.sh                    매니페스트를 읽어 설치 (vax-wiki-gateway 것과 같은 형식)
skills/vax-proposal/          ★ 우리 스킬
  SKILL.md                     절차·원칙 (Claude가 읽는 두뇌)
  references/material-pack.md  서버 ↔ 스킬 계약: 재료 팩의 고정 목차
  references/proposal-method.md  방향→전략→서술 방법론 (서버 bid_proposal_plan 에서 옮김)
  references/house-style.md    디자인 토큰 요약 + 「쉬운판」 문체 + 「대학생 강의처럼」 표현 수위
  references/distinctiveness.md ★ 색채 — AI 초안이 다 비슷해지는 문제와 규칙 7개, P4 검토 ③ 점검표
  references/staffing-table.md 투입인력표(조직도·총괄표·파트 구성) 서식 구조 — 데이터는 위키에서
  references/guardrails.md     공개 금지 정보·근거 없는 문장 금지·⚠️ 확인필요
  references/figma-handoff.md  HTML → Figma 삽입·조정 절차
  scripts/ui_tokens.py         디자인 정본 사본 (서버 ops/ui_tokens.py 에서 동기화)
  scripts/render_html.py       마크다운 → 회사 디자인 HTML 1장 (+ 공개 금지 검사)
server/                       서버에 둘 것 (여기서는 초안·명세만 관리, 배포는 서버에서)
  proposal_material.py         ★ 도전 공고 → 재료 팩 (LLM 0콜 · 셀프테스트 39건 · dry-run 확인 완료)
  sync_tokens.sh               ui_tokens.py 정본 → 스킬 사본 동기화
templates/company-intro/      회사소개서 마스터 v3(HTML, 발표 톤·슬라이드 구조 참고) — 직원 PC에 설치되지 않음
fonts/                        제안 슬라이드 글꼴 Freesentation·Paperlogy(각 9굵기 TTF, SIL OFL) — install.sh 가 사용자 글꼴 폴더에 자동 설치
  install-fonts.sh / .ps1      macOS·Linux / Windows 설치기(관리자 권한 불필요)
assets/photos/                회사 사진 81장(회사소개서 마스터에서 추출, MANIFEST.md에 사업별 캡션) — 슬라이드·발표자료용
scripts/extract_assets.py     위 사진을 HTML에서 다시 뽑는 스크립트(손으로 고치지 않는다)
doctor.sh                     설치 점검: 스킬·글꼴·파이썬·렌더러·저장소 최신 여부 + 커넥터 확인 방법 안내
bids/                         (git 제외) 사업 폴더 — _STATE.md · 01_평가표 · 02_가점진단 · 03_레퍼런스매핑 · 04_제안서 · logs/
agents/                       대표가 만든 agent.md 들 (규약은 agents/README.md)
loops/                        대표가 만든 루프·반복 절차 (규약은 loops/README.md)
  bid-loop/                    ★ /bid-loop 하네스 — P1~P6 게이트 · _STATE 상태 기계 · 심사 루브릭 · 야간 실행 래퍼
                              ※ 실적·인력 색인 데이터는 이 저장소에 없다 — 위키 「레퍼런스 색인」이 정본(아래 정본 관계)
```

## 게이트 (스킬이 넘어가려면 문서로 증명해야 하는 것)
| 게이트 | 기준 | 미달 시 |
|---|---|---|
| ① 가점 (P2) | 정량 실점 합계 ≤ 5.0 | 정성 비중 ≥ 70%면 사람 판단, 아니면 중단(가점미달). 회복가능 실점은 `차단사항`에 기한과 함께 |
| ② 심사 (P5) | 심사위원 페르소나 채점 총점 ≥ 80 | 재작성 1회(상위 3건만 겨냥) → 그래도 미달이면 중단(심사미달), 사람이 판단 |
80점은 합격선이 아니라 **착수선**이다. 게이트는 느낌으로 통과시키지 않는다.

## 글의 두 가지 기준 (한준 2026-09-04)
- **표현**: 꼭 필요한 전문용어만 그 용어로 쓰고, 나머지는 아무 지식이 없는 제3자에게 알려 주듯 대학생 강의처럼 푼다 → `house-style.md`.
- **색채**: AI로 쓰면 내용과 강조하는 주장이 다 비슷해진다. 이 발주처·이 과업·우리 실적 셋이 다 들어가야만 나오는 문장의 비율을 올린다.
  고유 관찰 3 → 주장마다 우리만의 근거 → 회사명 가림 테스트 → 금지어 0 → 차별점은 범주를 달리 → `distinctiveness.md`.

## 함께 담은 스킬 (skills.tsv)

| 역할 | 스킬 | 출처 | 방식 |
|---|---|---|---|
| 제안 상류 (이 저장소) | `vax-proposal` | 이 저장소 | git |
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

**외부 스킬은 Tools DB(01.WIKI_AI) 보안 검토를 거쳐 「사용중」이 된 것만 넣는다.** 후보·보류는 넣지 않는다
(OpenClaw류 재발 방지 — vax-wiki-gateway 규칙 그대로).

### 검토 대기 (후보 — skills.tsv에는 아직 없음)
| 스킬 | 출처 | 검토 의견 (2026-09-04) |
|---|---|---|
| `axlabs-mckinsey-pptx` | seulee26/mckinsey-pptx (MIT, AX Labs 이승필) | **P6 발표자료용으로 넣을 가치가 있다.** 슬라이드 템플릿 40종 + 요청에 맞는 템플릿을 고르고 근거를 대는 서브에이전트, 한국어 지원, python-pptx 기반, 문서상 외부 네트워크 호출 없음. 다만 ① 맥킨지 스타일이라 **회사 디자인 토큰과 다르다** — 구조·템플릿 선택에 쓰고 색·글꼴은 우리 것으로 다시 입히거나 Figma 단계에서 맞춘다. ② 플러그인 설치 후 Claude Code 재시작 필요. ③ 내장 `pptx` 스킬과 역할이 겹치므로 어느 쪽을 기본으로 할지 정한다. → Tools DB 보안 검토 후 「사용중」이 되면 `skills.tsv`에 `marketplace` 줄로 추가: `/plugin marketplace add seulee26/mckinsey-pptx` → `/plugin install axlabs-mckinsey-pptx@axlabs` |

## 함께 쓰는 오픈소스 (설치 대상 아님 · 참고)

python-pptx(브랜드 pptx 템플릿) · python-hwpx(hwpx 플레이스홀더) · typst(보고서·견적·공문 조판,
`vax-wiki-gateway/templates/typst`) · MinerU(RFP PDF → 마크다운, 서버) · Pretendard · Geist(글꼴) · kiwipiepy(한국어 형태소, 서버).

## 정본 관계

- 디자인 값 정본 = 서버 `ops/ui_tokens.py`. 여기 `scripts/ui_tokens.py`는 사본이며 `server/sync_tokens.sh`로만 갱신한다.
- 회사 팩트·실적·인증 정본 = 위키(회사 팩트 DB). 스킬은 재료 팩으로만 받고, 직접 타이핑하지 않는다.
- 실적 ↔ 기술요소 ↔ 재활용 문구 색인 정본 = 위키 「레퍼런스 색인」(01.WIKI_AI / Company) https://app.notion.com/p/3d16394f4c9981b493e3d4b5dc7884a9 — 실명·재무·신용등급이 있어 git에 두지 않는다(한준 2026-09-04). 재료 팩 §5·§7은 여기서 고른다.
- 재료 팩의 목차(H2 열 개, 0~9) = `references/material-pack.md`. 서버와 스킬이 함께 지키는 계약이라 한쪽만 바꾸지 않는다.
- 인력 데이터(성명·연령·이력) 정본 = 위키(레퍼런스 색인 §I · Members · 「용역수행 조직도 및 보유인력 총괄표」 2026-08-22 최신본). 저장소에는 서식 구조(`staffing-table.md`)만 둔다.
