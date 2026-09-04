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

비어 있는 상태로 시작한다. 대표가 만든 agent.md를 그대로 넣으면 된다.
