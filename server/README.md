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

## proposal_material.py — 재료 팩 생성기
- 트리거: 입찰레이더 `진행상태=도전` (+ 우리담당 지정). 이미 팩이 있고 RFP 판본(ingest_stamp)이 같으면 다시 쓰지 않는다.
- 출처(모두 이미 서버에 있는 것): RFP 읽기 캐시(`rfp_read.json`) · go/no-go 캐시(`gonogo_req.json`) · 채점 결과(bid_grade/bid_score) · 범위·리서치 캐시(`bid_scope.json`·`bid_research.json`) · 회사 팩트 DB · bid_learn 결과 · 서식 manifest.
- 출력: `skills/vax-proposal/references/material-pack.md` 의 H2 아홉 개 목차를 **그대로** 따르는 마크다운. 전략·컨셉·서술은 넣지 않는다.
- 쓰기 전 공개 금지 검사(서버 주소·포트·토큰·내부 경로)를 통과해야 위키에 쓴다.
- 1차 배포는 `--dry-run`(stdout 출력)만. 위키 쓰기(`--commit`)는 사람이 결과를 보고 켠다 — 이 저장소의 「자동은 제안/dry-run, 확정은 사람」 원칙.
- 새 systemd 유닛 `vax-proposal-material.timer`(업무시간 30분마다)로 돈다. 기존 sweep 타이머의 자리를 대신한다.

## sync_tokens.sh — 디자인 토큰 동기화
서버 `ops/ui_tokens.py` → 이 저장소 `skills/vax-proposal/scripts/ui_tokens.py`. 반대로 하지 않는다.
동기화 후 `python3 ui_tokens.py --selftest`가 통과해야 커밋한다.

## 배포 순서 (서버에서, 사람이)
1. `proposal_material.py`를 pipeline 폴더에 두고 `--selftest` → `--dry-run --no <공고>`로 출력 확인.
2. 출력이 material-pack.md 목차와 맞으면 `--commit`으로 위키에 한 건 써 보고 스킬로 읽어 본다(왕복 검증).
3. 그다음 `vax-proposal-sweep.timer` 비활성 + `vax-proposal-material.timer` 활성. 순서를 바꾸지 않는다 — 재료가 먼저 나와야 초안 자동 생성을 끊어도 팀이 비지 않는다.
