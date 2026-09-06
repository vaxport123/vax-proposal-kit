# 제3자 반복 사용을 위한 수정 계획 (2026-09-06 · 한준 "싹 다 고치기 위한 계획을 짜고 Opus 4.8로 고쳐")

리뷰에서 나온 15개 문제를 세 묶음으로 나눠 Opus 4.8 에이전트 셋이 서로 다른 작업 트리(브랜치)에서 고친다. 파일이 겹치지 않게 나눴다. 검토·병합·푸시는 Fable(이 세션)이 한다.
공통 규칙: 한국어 문서는 CLAUDE.md 한국어 원칙(번역투·공문투 금지, 짧게) · 회사 팩트·실명·공고번호·금액을 저장소에 넣지 않는다(예시는 「예시문화재단」) · 셀프테스트가 있는 스크립트는 고친 뒤 `--selftest` 통과 · `bash doctor.sh` 통과 · 커밋 메시지는 한국어로 무엇을 왜.

## 묶음 A — 설치·환경·운영 (브랜치 fix/a-install-ops · 트리 wt-a)
소유 파일: `install.sh` `doctor.sh` `README.md` `START.md`(새) `CHANGELOG.md`(새) `VERSION`(새) `.githooks/pre-commit`(새) `.github/ISSUE_TEMPLATE/*.md`(새) `scripts/figures_svg.py` `scripts/render_html.py` `scripts/img_fetch.py` `scripts/layout_wireframes.py` `scripts/ui_tokens.py` `fonts/install-fonts.sh`
- [2] 첫 실행 점검 절차: `START.md` 한 쪽 — 읽는 순서(START → SKILL.md → writing/deck/layouts 순), 커넥터 점검(노션: 어느 열쇠로 무엇이 열려야 정상 · 피그마: 회사 계정으로 회사 파일이 열려야 정상 · 실패 시 누구에게), 첫 사업 30분 코스.
- [4] 윈도우 콘솔 한글: 소유한 파이썬 스크립트 맨 위에 `sys.stdout/stderr.reconfigure(encoding="utf-8")` 방어 코드(예외 무시). README·START의 명령 예시에 `PYTHONIOENCODING=utf-8` 필요 없게.
- [6] 규칙 문서 길이: START.md가 「처음 한 번은 이 순서로」를 맡고, README 첫 화면 60초 시작 아래에 START 링크.
- [12] 버전: `VERSION` 파일(0.6.0부터) · `CHANGELOG.md`(오늘까지의 큰 변경을 날짜별 5~10줄) · doctor가 VERSION과 원격 태그를 비교해 「새 판 있음」 안내. 태그는 사람이 `git tag v0.6.0`.
- [13] 커밋 훅: `.githooks/pre-commit`가 셀프테스트 5종(ui_tokens·render_html·figures_svg·proposal_lint·layout_wireframes·probe_web) + `scripts/repo_guard.py`(묶음 B가 만든다 — 없으면 건너뜀)를 돌리고 실패면 커밋 거부. `install.sh`가 `git config core.hooksPath .githooks` 설정. doctor가 hooksPath 확인.
- [14] 외부 의존 점검: doctor에 「ddgs 실제 검색 1회(결과 0이면 경고)」「Figma 공식 스킬 문서 URL 목록은 figma-howto에 있음」 안내. 네트워크 없으면 info로.
- [15] 문의 창구: `.github/ISSUE_TEMPLATE/bug.md`·`request.md`(한국어), README·START에 「문제가 생기면 이슈 또는 #제안서 채널(자리표시)」.
- [3] 문서에 걸린 Figma 링크(라이브러리·손 덱 3개)에 「팀 프로젝트로 옮겨야 다른 직원이 열 수 있다 — 옮긴 뒤 링크 갱신」 주석과 START 점검 항목. 실제 이동은 사람.

## 묶음 B — 절차 게이트 기계화·공개 범위 (브랜치 fix/b-gates · 트리 wt-b)
소유 파일: `skills/vax-proposal/scripts/proposal_lint.py` `scripts/repo_guard.py`(새) `loops/bid-loop/_STATE.template.md` `loops/bid-loop/bid-loop.md` `skills/vax-proposal/references/deck.md` `skills/vax-proposal/references/writing.md` `skills/vax-proposal/references/material-pack.template.md`(새) `agents/proposal-critic.md` `examples/**`
- [1] 재료 팩 빈 서식: `references/material-pack.template.md` — 열 개 절(material-pack.md 계약 그대로) 빈 칸 + 어디서 채우나 한 줄씩. SKILL P0 「팩이 없으면 이 서식을 사람이 채운다」는 묶음 C가 SKILL에 적는다(파일 소유 분리) — B는 서식만.
- [5] 승인 게이트 기계화: 계획서(07)에 `## 승인` 절(승인자 · 일시 · 「고스트 덱 승인」 문구)이 없으면 lint P9 「상」. `_STATE.template.md`에 `승인: {고스트덱: -, 승인자: -, 일시: -}` 칸. bid-loop P6-계획 출구에 「승인 절 있음」 조건. deck.md §2-6에 서식.
- [7] 웹 재료를 사실로 옮기는 실수: lint L14 — `03a_페인포인트.md` 계열 문서에서 출처 열이 비었거나 `03a_raw` 파일명·`duckduckgo`·`검색 결과`를 출처로 적었으면 「상」. 표 열 이름 「출처」 감지. writing.md §2에 한 줄.
- [8] 공개 범위 검사: `scripts/repo_guard.py` — git 추적 파일(bids/ 제외) 전체에서 공고번호 패턴(`R\d{2}[A-Z]{2}\d{8}` 등 나라장터 형식), 원 단위 금액(`\d{1,3}(,\d{3}){2,}원`), 실명+직함 패턴, 실제 발주처 이름 목록(`repo_guard.deny.txt`에 한 줄씩 — 초기값: 순천·순천캠퍼스·국립순천대) 을 찾아 보고. `--selftest`. 지금 저장소에서 걸리는 곳(writing.md·deck.md·layouts.md·figma-howto.md·README 실전 기록 등)을 **예시문화재단 예시로 바꾸거나 일반화**해 통과시킨다. 단 README 「실전 기록」과 CHANGELOG는 사업명 없이 「대학 캠퍼스 VR 건」처럼.
- 예시 세트(`examples/`)를 새 서식(승인 절·출처 열)에 맞춰 갱신하고 lint 통과 유지. 비판자 A9에 「출처가 03a_raw」 지적 추가.

## 묶음 C — 재사용·재개·수집 견고성 (브랜치 fix/c-reuse · 트리 wt-c)
소유 파일: `skills/vax-proposal/SKILL.md` `skills/vax-proposal/references/figma-howto.md` `skills/vax-proposal/references/layouts.md` `skills/vax-proposal/references/images.md` `skills/vax-proposal/scripts/probe_web.py` `skills/vax-proposal/scripts/figma_slides_helpers.js` `skills/vax-proposal/scripts/figma_slides_layouts.js` `skills/vax-proposal/scripts/figma_slides_diagrams.js` `loops/bid-loop/_BUILD_STATE.template.md`(새) `loops/bid-loop/run-loop.sh` `docs/ROADMAP.md`(새)
- [9] 마감 단계 P7: SKILL에 「사업이 끝나면(낙찰/유찰 상관없이) 03a·03b·07·비판 로그 요약을 노션 레퍼런스 색인에 올린다 — 회사 사실은 위키가 정본, bids는 로컬」 절차 + 체크리스트. bid-loop 표에 P7 행. 어떤 것을 올리고(페인포인트·카드·이름·틀 선택) 무엇은 안 올리나(원고 전체·개인 이름).
- [10] 재개 절차: `_BUILD_STATE.template.md`(피그마 파일 키 · 장별 노드 ID 표 · 진행 · 교훈) + SKILL P6·figma-howto 첫 줄에 「한 장에 한 호출 · 끝나면 상태 파일 갱신 · 토큰 끊기면 상태 파일부터」 굵게. helpers.js에 `snapshotIds()`(현재 슬라이드 이름→id 표를 마크다운으로 돌려줌) 추가.
- [1] SKILL P0에 「재료 팩이 없으면 `material-pack.template.md`를 사람이 채워 붙여넣기」 경로(묶음 B가 서식 파일을 만든다 — 파일명만 참조).
- [14] probe_web 견고성: 검색 전부 0건이면 종료코드 2와 원인 후보(네트워크·차단·검색어) 출력, 재시도 1회(지역 kr-kr→wt-wt), 뉴스 날짜에 「검색엔진 값 · 원문 확인」 표시, `--dry-run`(검색어만 출력). 파이썬 표준 출력 utf-8 방어 코드.
- [11] `docs/ROADMAP.md`: 「새 절차로 실제 공고 1건 완주 → 걸리는 곳 고치기」를 첫 줄에, 이번 15개 중 사람이 할 일(3·9·11) 표시.
- SKILL.md 「파일」 목록에 START·CHANGELOG·repo_guard·템플릿 둘 반영(이름만 — 내용은 다른 묶음).

## 병합 순서
B → A → C (A의 훅이 B의 repo_guard를 부른다 · C의 SKILL이 A·B 파일명을 참조). 각 병합 뒤 `bash doctor.sh`와 셀프테스트 전부, `python scripts/repo_guard.py`, 예시 lint. 마지막에 태그 v0.6.0.
