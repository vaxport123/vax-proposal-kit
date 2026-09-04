# loops/bid-loop — 입찰 제안 파이프라인 하네스 (유한준, 2026-07)

`/bid-loop` 한 번 호출 = 한 스텝. `_STATE.md`가 진실의 원천이고, 게이트(가점 ①·심사 ②)를 문서로 증명해야 넘어간다.
`skills/vax-proposal/SKILL.md`는 각 단계의 **내용**을, 이 폴더는 **운행 규칙과 실행 장치**를 맡는다. 2026-09-05에 겹치던 단계 설명과 회사 상수를 이 폴더에서 뺐다.

## 파일
| 파일 | 역할 | 어디에 두나 |
|---|---|---|
| `bid-loop.md` | `/bid-loop` 슬래시 커맨드 본문 — 절대 규칙 · 부팅 · 스텝 표 · 종료 규칙 | `.claude/commands/bid-loop.md` (**이 이름 그대로.** `loop.md`로 저장하면 내장 `/loop`를 덮어쓴다) |
| `_STATE.template.md` | 사업별 상태 기계 템플릿 | 새 사업 시작 시 `bids/{사업명}/_STATE.md`로 복사 |
| `run-loop.sh` | 야간 헤드리스 실행 래퍼 — 시간대(21~08시)·중복 실행·예산 상한·타임아웃·로그 | 프로젝트 루트. cron이 매시 정각에 부른다 |
| `settings.json` | 루프 실행 권한 — `rm`·`git push`·`curl`·`ssh` 금지, `company/` 쓰기 금지 | 프로젝트 `.claude/settings.json` |
| `bid-loop_절차서.html` | 설치·실행 따라하기 문서(대표 작성, 2026-07 원본 기준) | 읽기용 |

P5 채점 절차는 스킬 `references/review-rubric.md` 한 곳에만 둔다(옛 `_REVIEW_RUBRIC.md` 사본은 09-05에 지웠다).
회사 상수와 레퍼런스 색인은 재료 팩(§5·§7)이 공급한다. 데이터 정본은 위키 「레퍼런스 색인」이고 git에는 두지 않는다.
초안은 마크다운(`04_제안서_vN.md`)이 원본이고 HTML·docx·pptx·hwp는 그것을 렌더한다.

## 헤드리스 실행 (선택)
```bash
# macOS/Linux — 매시 정각, 21:00~08:59 에만 실제 실행
0 * * * * /path/to/project/run-loop.sh <사업폴더명>
```
윈도우는 작업 스케줄러에서 `bash run-loop.sh <사업폴더명>`을 매시 정각에 건다.
`MAX_BUDGET_USD`(기본 3) · `MAX_TURNS`(60) · `TIMEOUT_SEC`(1800)로 한 스텝의 상한을 잡는다.
실패해도 되돌리지 않는다 — 재시작은 cron이, 재개 지점은 `_STATE.md`가 맡는다.

## 서버 자동화와의 관계
서버 `vax-bid-*` 타이머는 **재료**(레이더·채점·학습·시장·재료 팩)를 만들고, 이 루프는 **초안**(판단·작성)을 만든다. 같은 일을 두 곳에서 하지 않는다.
