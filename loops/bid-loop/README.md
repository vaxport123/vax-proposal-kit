# loops/bid-loop — 입찰 제안 파이프라인 하네스 (유한준, 2026-07)

`/bid-loop` 한 번 호출 = 한 스텝. `_STATE.md`가 진실의 원천이고, 게이트(가점 ①·심사 ②)를 문서로 증명해야 넘어간다.
`skills/vax-proposal/SKILL.md`는 각 단계의 **내용**을, 이 폴더는 **운행 규칙과 실행 장치**를 맡는다.

## 파일
| 파일 | 역할 | 어디에 두나 |
|---|---|---|
| `bid-loop.md` | `/bid-loop` 슬래시 커맨드 본문 — 절대 규칙 · P0~P6 · 스텝 종료 규칙 | `.claude/commands/bid-loop.md` (**이 이름 그대로.** `loop.md`로 저장하면 내장 `/loop`를 덮어쓴다) |
| `_STATE.template.md` | 사업별 상태 기계 템플릿 | 새 사업 시작 시 `bids/{사업명}/_STATE.md`로 복사 |
| `_REVIEW_RUBRIC.md` | P5 심사위원 채점 절차(페르소나·역순 채점·근거 인용 의무) | `bids/_REVIEW_RUBRIC.md` (스킬 `references/review-rubric.md`와 같은 내용) |
| `run-loop.sh` | 야간 헤드리스 실행 래퍼 — 시간대(21~08시)·중복 실행·예산 상한·타임아웃·로그 | 프로젝트 루트. cron이 매시 정각에 부른다 |
| `settings.json` | 루프 실행 권한 — `rm`·`git push`·`curl`·`ssh` 금지, `company/` 쓰기 금지 | 프로젝트 `.claude/settings.json` |
| `bid-loop_절차서.html` | 설치·실행 따라하기 문서(대표 작성) | 읽기용 |

## 이 스킬셋에 맞춘 조정 세 가지
1. **회사 상수는 재료 팩에서 온다.** 원본 `bid-loop.md` P2에는 신용등급·등록 업종코드·직접생산확인·설립일이 직접 적혀 있다(2026-07-24 기준).
   이 스킬셋에서는 그 값을 **재료 팩 §5**가 공급한다 — 위키가 갱신되면 재료 팩이 먼저 바뀌므로 두 곳이 어긋나지 않는다.
   `bid-loop.md`의 상수는 **참고값**으로 읽고, 판정에는 재료 팩 값을 쓴다.
2. **레퍼런스 색인도 재료 팩에서 온다.** 원본은 `bids/_REFERENCE_INDEX.md`(실적·인력·재무 전체)를 P3가 읽었다.
   여기서는 재료 팩 §5·§7 + `references/reference-index.template.md`(구조)를 쓴다. 데이터 원본은 `server/seed/`에 있고 직원 PC에는 깔리지 않는다.
3. **초안은 마크다운이 원본.** 원본 절차는 P4를 `.docx`로 썼다. 이 스킬셋은 `04_제안서_vN.md`로 쓰고, HTML(P6)·docx(`doc-gen`)·pptx는 그것을 렌더한다.
   RFP가 docx/hwp 제출을 요구하면 마지막에 변환한다.

## 헤드리스 실행 (선택)
```bash
# macOS/Linux — 매시 정각, 21:00~08:59 에만 실제 실행
0 * * * * /path/to/project/run-loop.sh <사업폴더명>
```
윈도우는 작업 스케줄러에서 `bash run-loop.sh <사업폴더명>`을 매시 정각에 건다.
`MAX_BUDGET_USD`(기본 3) · `MAX_TURNS`(60) · `TIMEOUT_SEC`(1800)로 한 스텝의 상한을 잡는다.
실패해도 되돌리지 않는다 — 재시작은 cron이, 재개 지점은 `_STATE.md`가 맡는다.

## 서버 자동화와의 관계
서버 `vax-bid-*` 타이머는 **재료**(레이더·채점·학습·시장)를 만들고, 이 루프는 **초안**(판단·작성)을 만든다. 같은 일을 두 곳에서 하지 않는다.
