# agents/ — 대표가 만든 agent.md 들

여기에 놓는 파일은 Claude Code 서브에이전트 정의다. `~/.claude/agents/`(개인) 또는 프로젝트
`.claude/agents/`에 복사해 쓴다. `install.sh`는 이 폴더를 `~/.claude/agents/vax/`로 통째로 복사한다(예정).

## 파일 규약
- 파일 하나 = 에이전트 하나. 이름은 kebab-case (`proposal-section-writer.md`).
- 맨 위 frontmatter에 `name` · `description`(언제 부르는지 트리거 문구 포함) · `tools`(허용 도구)를 둔다.
- 본문에는 **무엇을 받고 무엇을 내는지**, 그리고 지키는 원칙(단일 출처 · ⚠️ 확인필요 · 공개 금지)을 적는다.
- 회사 팩트·서버 주소·내부 경로를 본문에 박지 않는다 — 재료 팩과 `guardrails.md`를 가리킨다.

## 이 스킬셋과 어울리는 자리
| 자리 | 에이전트 예 | 하는 일 |
|---|---|---|
| 3단계 절별 초안 | `proposal-section-writer` | 절 하나를 받아 문단+요점을 쓴다(병렬로 여러 절) |
| 검토 | `proposal-fact-checker` | 초안의 모든 숫자·고유명사가 재료 팩에 있는지 대조 |
| 문체 | (`humanize-korean` 스킬의 에이전트들) | AI 티 진단·윤문·마무리 |

## 지금 들어 있는 것
| 파일 | 자리 | 하는 일 |
|---|---|---|
| `proposal-critic.md` | P4 검토 ④ · P6 덱 계획 검토 | **비판자.** 한글 표현(A1 번역투 · A2 공문투 · A3 말은 되는데 뜻이 불분명한 문장 · A4 기계적 병렬 · A5 빈 수사 · A6 어려운 말 · A7 낭독 실패 · A8 회사명 가림)과 AI 디자인(B1 같은 틀 반복 · B2 명사형 제목 · B3 제목 사슬 끊김 · B4 결론 바 되풀이 · B5 글로 채운 장 · B6 장식 남용 · B7 헤더/쪽번호/목차 위반 · B8 빈 사진 자리 · B9 밀도 붕괴)을 잡는다. 표현은 직접 고쳐 새 판본을, 디자인은 슬라이드별 지시를 낸다. 사실·숫자는 바꾸지 않는다 (한준 2026-09-04) |

`install.sh`가 이 폴더의 `*.md`(README 제외)를 `~/.claude/agents/`로 복사한다. 새 세션에서 `subagent_type: proposal-critic`으로 부른다.
부를 때 넘기는 것: `draft_path` · `rules_dir`(스킬 `references/` 절대 경로) · `mode`(text | deck | both) · `out_dir`.
