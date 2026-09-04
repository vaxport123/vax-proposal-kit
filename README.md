# vax-proposal-kit — 제안서 작성 스킬셋 (개인 Claude용)

공고가 「도전」으로 확정되면 서버가 **재료 팩**(정량 지표·회사 자료·RFP 추출)을 위키에 써 두고,
직원은 자기 Claude에 이 스킬셋을 넣어 **제안 전략 → 초안 → HTML 디자인 → Figma**까지 진행한다.

서버는 더 이상 최종 문서·HTML을 자동으로 만들지 않는다. **판단·작성·렌더는 사람이 Claude와
함께 하고, 데이터·학습·추출은 서버가 맡는다.** (한준 2026-09-04 결정)

## 흐름

```
[서버]  입찰레이더 진행상태=도전
          → proposal_material.py 가 위키 정보를 모아 「📦 제안 재료 팩」 페이지를 그 공고 밑에 쓴다
[개인]  Claude + vax-proposal 스킬
          ① 재료 팩을 Notion에서 당겨온다 (직원은 이미 Notion 접근이 있다 — SSH 키 불필요)
          ② 방향(돈 → 안 할 것 → 할 것 → 강점) → 전략 → 절별 서술 초안
          ③ 회사 디자인 토큰으로 HTML 디자인 1장 렌더 (scripts/render_html.py)
          ④ HTML을 Figma에 넣고, 세부 디자인은 Claude-Figma로 조정
```

## 설치 (직원 PC)

```bash
git clone https://github.com/vaxport123/vax-proposal-kit
cd vax-proposal-kit && bash install.sh          # skills.tsv 의 스킬을 ~/.claude/skills 에 설치
bash install.sh --list                          # 무엇이 깔리는지 미리보기
```

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
  references/house-style.md    디자인 토큰 요약 + 「쉬운판」 문체
  references/guardrails.md     공개 금지 정보·근거 없는 문장 금지·⚠️ 확인필요
  references/figma-handoff.md  HTML → Figma 삽입·조정 절차
  scripts/ui_tokens.py         디자인 정본 사본 (서버 ops/ui_tokens.py 에서 동기화)
  scripts/render_html.py       마크다운 → 회사 디자인 HTML 1장 (+ 공개 금지 검사)
server/                       서버에 둘 것 (여기서는 초안·명세만 관리, 배포는 서버에서)
  proposal_material.py         도전 공고 → 재료 팩 문서 생성
  sync_tokens.sh               ui_tokens.py 정본 → 스킬 사본 동기화
agents/                       대표가 만든 agent.md 들 (규약은 agents/README.md)
loops/                        대표가 만든 루프·반복 절차 (규약은 loops/README.md)
  bid-loop/                    ★ /bid-loop 하네스 — P1~P6 게이트 · _STATE 상태 기계 · 심사 루브릭 · 야간 실행 래퍼
server/seed/                  서버가 재료 팩을 채울 때 쓰는 seed 데이터(실명·재무 포함 — 직원 PC에 깔리지 않음)
```

## 게이트 (스킬이 넘어가려면 문서로 증명해야 하는 것)
| 게이트 | 기준 | 미달 시 |
|---|---|---|
| ① 가점 (P2) | 정량 실점 합계 ≤ 5.0 | 정성 비중 ≥ 70%면 사람 판단, 아니면 중단(가점미달). 회복가능 실점은 `차단사항`에 기한과 함께 |
| ② 심사 (P5) | 심사위원 페르소나 채점 총점 ≥ 80 | 재작성 1회(상위 3건만 겨냥) → 그래도 미달이면 중단(심사미달), 사람이 판단 |
80점은 합격선이 아니라 **착수선**이다. 게이트는 느낌으로 통과시키지 않는다.

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
- 재료 팩의 목차 = `references/material-pack.md`. 서버와 스킬이 함께 지키는 계약이라 한쪽만 바꾸지 않는다.
