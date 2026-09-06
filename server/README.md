# server/ — 서버(vax-gateway)에 두는 것의 초안·명세

이 폴더의 파일은 **직원 PC에 설치되지 않는다.** 서버에서 돌 코드의 초안과 명세를 여기서 버전 관리하고,
배포는 서버 저장소(`vax-wiki-gateway`)의 규칙대로 한다. 실제 정본 코드는 서버 pipeline 에 있다.

## 2026-09-04 결정 (한준)
- 도전 공고에 대해 서버가 **HTML 디자인·문서를 자동 생성하던 것을 멈춘다.**
  → `vax-proposal-sweep.timer` 비활성(`systemctl disable --now`). 파일은 지우지 않는다(되돌리기 가능).
  → 이 타이머가 유일한 자동 live-run 경로였고, 수동 CLI 생성은 이미 `draft_locked`로 잠겨 있다.
- 대신 **정량 지표와 회사 자료만** 모아 「📦 제안 재료 팩」을 위키에 쓴다. → `proposal_material.py`
- 재료를 만드는 타이머(`vax-bid-doc` · `radar` · `grade` · `learn` · `market` · `bidprc` · `refresh`)는 **그대로 둔다.**
- `vax-bid-task.timer`(담당자 업무요청)는 초안 존재를 조건으로 보므로, 재료 팩 기준으로 조건을 고칠 때까지 **보류**(한준 결정 대기).
  고칠 방향: 조건을 「재료 팩이 생성됐을 때」로 바꾸면 "재료 팩 준비됨, Claude에서 시작하세요"라는 새 흐름의 출발 신호가 된다.

## proposal_material.py — 재료 팩 생성기 (작성 완료 · 2026-09-04)
**LLM 호출 0회.** 있는 데이터를 `material-pack.md` 계약(H2 열 개, 0~9)에 맞춰 모으기만 한다. 셀프테스트 39건.
서버 임시 폴더에서 도전 공고 `R26EX00000001`로 dry-run 확인(6.7초 · 17,000자 · 블록 135개 · 공개 금지 검사 통과).

- **게이트**: 레이더 `진행상태=도전` + `우리담당` 지정 + `입찰마감일` 전(없으면 통과). `proposal_build._gate_reason`과 같은 판정.
  `--all`로 게이트를 무시할 수 있다(담당 미지정 공고를 미리 보고 싶을 때).
- **판본 도장**: `<공고번호>#<제안요청서 도장(bid_doc_ingest)>#<RFP 읽기버전>#<스크립트 버전>`을 팩 첫 문단 「판본:」에 쓴다.
  같은 도장의 팩이 이미 있으면 건너뛴다(`--force`면 다시 쓴다). 도장이 다르면 옛 팩을 보관(archived) 처리하고 새로 만든다.
- **출처(전부 서버에 이미 있는 것)**
  - RFP 읽기 캐시 `rfp_read.json` — 키가 `공고번호` · `공고번호#도장` · `공고번호#도장#읽기버전` 세 형태로 섞여 있어, 도장 일치 → 읽기버전 늦은 것 → 내용 많은 것 순으로 고른다. 불일치면 §8에 적는다.
  - 자격 캐시 `gonogo_req.json`(참가자격·필수·산출물·일정) · 제안요청서 수집 `bid_scope.json`(과업 범위·작성요령·판본 도장)
  - 레이더 속성: 판정·판정메모·사업등급·등급근거·GoNoGo 브리핑(■ 가점·정량점수·내정 정황·수익률 / ■ 걸리는 것·되는 것·사업 조건)·요구업종코드·참가제한지역·첨부문서
  - Notion 덤프(`notion-dump/datasources`): 회사 팩트 · Certifications(만료·90일 임박 ⚠️) · Projects(대외인용금지 제외) · 입찰결과 아카이브
  - 개찰·학습 DB: `bid_market.analyse/lines`(부가세 제외 환산) · `bid_learn.market_lines`
  - 위키 「레퍼런스 색인」(Notion API로 표·인용 읽기): 열쇳말 겹침 상위 군집 3개 · §I 인력 카드 · §J 공백(→ §8)
  - 등록 업종 `bid_quals.json` ↔ 요구업종코드 → 보유/미보유
- **열쇳말**: 강한 것(RFP 읽기의 keywords + 공고명 낱말)과 약한 것(과업·산출물 낱말)을 나눈다. 실적·군집은 **강한 열쇳말이 하나는 겹쳐야** 고른다.
  실측: 「기획·관리·데이터」 같은 낱말만으로 고르면 사내 문서까지 걸렸다. 범용 낱말 목록(`STOP`)은 코드에 있다.
- **RFP 원문 자식 페이지(v2, 한준 "1번 해결해")**: 읽기 캐시의 본문(`_body`)을 「📄 RFP 원문(추출) — <공고번호>」로 재료 팩 옆에 함께 쓴다. 같은 판본 도장, 같은 skip·보관 규칙. 직원은 hwp를 열지 않고 P1·P4를 한다.
- **§2 원문 배점표(v2, 한준 "2번 해결해 — rfp에 있어")**: 원문의 마크다운 표 중 배점·평점·평가기준이 든 표를 그대로 §2 끝에 싣는다(최대 8개). 기술:가격은 "90%의 기술평가"·"기술평가점수(90점)" 두 어순을 다 읽고(v3 — "기술평가와 10%의 가격평가"에서 뒤 숫자를 잡던 오판 수정), 협상적격 「배점한도의 N%」를 점수로 환산해 적는다. 배점이 "20"처럼 단위 없는 숫자여도 합산한다(v2·v3 — 실측 R26EX00000001에서 합계 0으로 나오던 결함).
- **쓰기 전 검사**: 공개 금지 패턴(`ops/render_md_page.py FORBIDDEN`의 사본) + 계약 H2 열 개 존재. 하나라도 걸리면 `⛔`를 찍고 쓰지 않는다.
- **Notion 쓰기**: `bid_radar.notion`/`notion_patch`(토큰을 읽는 곳은 한 군데). 자식 페이지 생성(첫 배치) → 나머지 블록 append(50개·400KB 단위).
  마크다운 → 블록 변환기는 이 스크립트 안에 있다(제목·표·목록·인용·코드·구분선·굵게·링크). 파이프라인에 기존 변환기가 없어서 새로 썼다.
- **CLI**
  ```
  proposal_material.py --selftest
  proposal_material.py --list                          # 게이트 통과 목록
  proposal_material.py --no R26BK… [--out DIR]         # 한 건 dry(stdout 또는 파일)
  proposal_material.py --no R26BK… --commit [--force]  # 위키에 쓴다 (env BID_MATERIAL_COMMIT=1 도 같음)
  proposal_material.py --commit                        # 도전 전건(같은 판본은 건너뜀)
  proposal_material.py --no-ref                        # 레퍼런스 색인을 읽지 않음(빠른 확인)
  ```
  기본은 dry다 — 이 저장소의 「자동은 제안/dry, 확정은 사람」 원칙. 로그 기호는 파이프라인 관례(`#` 요약 · `==` 공고 · `[dry]` · `[skip]` · `⛔` · `⚠️`).
- **의존**: 같은 폴더의 `bid_radar`(Notion 헬퍼) · `bid_bidprc`·`bid_market`·`bid_learn`(시장 지표, 실패하면 `[warn]` 후 그 절만 비움). LLM 모듈은 import하지 않는다.
- **systemd**: `vax-proposal-material.timer`(업무시간 30분마다, `--commit`)로 돈다. 유닛 파일은 서버 배포 때 sweep 유닛을 본떠 만든다. 기존 sweep 타이머의 자리를 대신한다.

## sync_tokens.sh — 디자인 토큰 동기화
서버 `ops/ui_tokens.py` → 이 저장소 `skills/vax-proposal/scripts/ui_tokens.py`. 반대로 하지 않는다.
동기화 후 `python3 ui_tokens.py --selftest`가 통과해야 커밋한다.

## 배포 순서 (서버에서, 사람이 — 한 단계씩 승인)
1. `proposal_material.py`를 pipeline 폴더에 두고 `--selftest` → `--no <공고> --out /tmp/…`로 출력 확인. ✅ 2026-09-04 pipeline 폴더에 배치, 셀프테스트 39건 통과
2. `--commit`으로 위키에 **한 건** 써 보고 `vax-proposal` 스킬로 읽어 본다(왕복 검증). ✅ 2026-09-04 R26EX00000001 → 공고 페이지 자식 「📦 제안 재료 팩 — R26EX00000001」 생성, Notion MCP로 열 개 절 읽기 확인, 같은 판본 재실행은 `[skip]`
3. `vax-proposal-material.timer` 활성 → 그다음 `vax-proposal-sweep.timer` 비활성. ✅ 2026-09-04 17:00 한준 승인으로 실행. 유닛 사본은 `server/systemd/`.
   즉시 1회 실행에서 도전 4건 중 3건 새로 씀(R26EX00000001 · R26EX00000001 · R26EX00000001), 1건은 같은 판본이라 skip. 30초 · LLM 0회.
   sweep 타이머는 `disable --now`(파일은 남김 — `systemctl enable --now vax-proposal-sweep.timer`로 되돌릴 수 있다).
   ⚠️ 유닛은 서버에 직접 썼다. 서버 저장소(vax-wiki-gateway `systemd/`·`pipeline/`)에는 아직 없으니, 그쪽 deploy.sh 배포 체계에 넣는 작업이 남아 있다(deploy.sh는 있는 파일만 덮어쓰므로 지금 유닛이 지워지지는 않는다).
4. `vax-bid-task` 조건을 「재료 팩 존재」로 바꾼다(별도 결정). ← **다음 단계, 승인 대기**
