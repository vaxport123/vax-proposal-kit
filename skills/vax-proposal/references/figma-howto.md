# Figma MCP 실측 요령 — 덱을 만들 때 알아 두면 시간이 준다 (규칙이 아니라 메모)

> **한 장에 한 호출로 만든다. 장 하나가 끝나면 `_BUILD_STATE.md`를 갱신한다. Figma 토큰이 끊기면(30분마다) 이 상태 파일부터 읽고 이어 간다.**
> 상태 파일의 「장별 노드 ID」 표는 `snapshotIds()`(figma_slides_helpers.js)를 돌려 채운다. 반쯤 만든 덱을 기억으로 이어 붙이지 않는다.

`deck.md`가 「무엇이어야 하는가」라면 이 파일은 「어떻게 하면 되더라」다. 2026-09-04 순천캠퍼스 VR 덱 두 개(24장·46장)를 만들며 확인한 것이고,
틀린 것이 발견되면 고친다. 여기 적힌 좌표·크기는 **기본값**이다. 장의 내용에 따라 바꿔도 된다. 전 장 같아야 하는 것은 헤더와 쪽번호만(`deck.md` §4).

## 전제
- Figma 공식 MCP 커넥터. 부르기 전에 **공식 스킬 셋을 읽는다**: `figma-use`(기본) + **`figma-use-slides`(Slides 전용 — 이걸 안 읽어 어제 겪은 문제의 절반이 거기 답이 있었다)** + 새 파일이면 `figma-create-new-file`.
  MCP 자원 주소: `skill://figma/figma-use-slides/SKILL.md` · `references/slide-gotchas.md`(좌표 어긋남·검증 스크립트) · `references/slide-design.md`(안티패턴). `use_figma` 호출 때 `skillNames`에 `resource:figma-use-slides`를 넣는다.
- 공식 스킬의 두 단계 워크플로를 그대로 따른다: **1단계 계획**(우리 `07_슬라이드계획` + 디자인 브리프가 그것이다 · 좌표 계산은 하지 않는다 · 레이아웃 반복 검사) → **2단계 제작**(3~5장씩 한 호출 · 배치마다 `validate()` · 화면은 첫 배치와 마지막 배치만).
- `generate_deck` 도구가 보여도 쓰지 않는다. 템플릿 고정이라 발주처 CI·브리프를 못 따르고, 뒤에 고칠 수 없다.
- **헤드리스(`claude -p` · bid-loop)에서는 Figma MCP가 붙지 않는다.** P6-시안부터는 사람이 앉은 세션(데스크톱 Claude 또는 Claude Code 대화형)에서 한다.
- HTML 초안은 초안이다. Figma에 들어간 뒤로는 Figma가 정본이고, HTML을 다시 렌더해 덮어쓰지 않는다. Figma에서 문장을 고치면 노션 초안에도 같은 수정을 남긴다.
- Slides 파일은 `get_metadata`가 안 된다. `use_figma` 읽기 스크립트(`findAllWithCriteria({types:['SLIDE']})`)로 구조를, `get_screenshot`(슬라이드 node-id)으로 화면을 본다.
- 팀 라이브러리가 있으면 `get_libraries`로 확인해 그 컴포넌트를 우선 쓴다. 회사 토큰 변수가 Figma에 없으면 만들지 말고 알린다.

## 만들기
- **틀에서 시작한다.** 레이아웃 라이브러리 https://www.figma.com/slides/jnsArJT6nEoWKVZKW3c1Fz (틀 14종, 자리표시 글)를 복제해 시작하거나, 스크립트로 만들 때는 `figma_slides_helpers.js` + `figma_slides_layouts.js`를 붙여 `houseChrome(s, P, {...})` → `applyLayout(s, layoutFor(증거유형), P, content)` 순서로 깐다. 좌표를 손으로 계산하지 않는다(v5의 실패).
- **새로 만든 Slides 파일에서는 같은 스크립트 안에서 `getSlideGrid()`가 `[]`를 돌려준다**(2026-09-06 실측 — 만든 뒤에도 빈 배열). 만든 슬라이드 id를 변수에 모아 쓰고, 다음 호출에서 `figma.currentPage.findAllWithCriteria({types:["SLIDE"]})`로 찾는다.
- 행(SLIDE_ROW) 노드를 `get_screenshot`하면 그 행의 슬라이드가 한 줄로 찍힌다(장 하나씩 찍지 않아도 된다 · 26장 행은 두 줄로 접힌다). 원본 폭 = n×1960 + (n-1)×200(Slides 파일) — 이 값으로 잘라 모음판을 만든다.
- **`appendChild`를 먼저, `x`·`y`는 그 뒤에** — 모든 노드, 모든 깊이에서. 순서를 바꾸면 노드가 (−240, −240) 어긋나고, 간헐적이라 한 번 잘 됐다고 안전하지 않다. 헬퍼의 프리미티브는 이 순서를 지킨다. 어긋난 노드를 240 더해 보정하지 말고 순서를 고친다.
- 새 Slides 파일은 기본 밝은 테마가 깔린다. 그 테마 색·글자 스타일에 끌려가지 말고 브리프 값으로 덮어쓴다.
- 새 파일 `create_new_file(editorType: slides)` → PART마다 `figma.createSlideRow(r)` + `row.name` → `figma.createSlide(r, c)`(둘 다 숫자 인덱스).
  빈 슬라이드를 먼저 전부 만들고 이름·id 표를 받아 둔다. 같은 스크립트 안의 `getSlideGrid()`는 갱신 전 값을 준다.
- 행(장)별 스크립트를 병렬로 보내도 된다(5개 동시까지 안전했다). 중간에 죽으면 그 슬라이드에 부분 생성물이 남는다 → 다시 돌리기 전에 자식을 지운다.
- `scripts/figma_slides_helpers.js`를 스크립트 맨 앞에 붙인다(`loadFonts` · `header` · `actionTitle` · `logoBox` · `photoBox` · `placeSvg` · `notes` · `retitle` · 그림 프리미티브 · `validate` · `evidenceCheck` · `leftovers`). 2026-09-06에 `chrome`·`bar`·`body`·`part`·`toc`(위에서 아래로 쌓는 조합 함수)는 지웠다 — 레이아웃은 증거 유형별로 고른다(deck.md §5). 글자 단계 기본값은 `T`.
- **Paperlogy는 로컬에 설치돼 있어도 Figma 글꼴 목록에 안 뜰 수 있다**(2026-09-05 v5 실측). 그러면 표지·PART·큰 숫자도 Freesentation 9 Black으로 간다 — 대체 글꼴을 다른 가족에서 고르지 않는다.
- 글꼴은 `listAvailableFontsAsync`로 「Freesentation / 7 Bold」식 스타일 이름을 확인하고 전부 `loadFontAsync`한 뒤 쓴다. 로컬에 설치돼 있으면 데스크톱 Figma가 바로 본다.
- `textAutoResize = "HEIGHT"` 텍스트의 `height`는 스크립트 안에서 갱신되지 않는다(10으로 읽힘). 헬퍼 `estLines`(한글 1em · 영문 0.56 · 공백 0.28)로 줄 수를
  추정해 다음 요소의 y를 잡는다. 46px · 폭 1728이면 한 줄 약 37자.
- 큰 숫자는 카드 폭 290에 56px이면 6자부터 줄바꿈된다 → 44px.

## SVG 도식 넣기 (`figures_svg.py`)
- `python3 scripts/figures_svg.py 04_제안서_vN.md --out-dir figs/ --accent "#발주처CI" --no-title`
- 코드에 SVG 문자열을 붙이지 말고 `upload_assets`(count N)로 올린다: `curl -F "file=@fig.svg;filename=이름.svg;type=image/svg+xml"`.
  페이지 루트에 파일명 그대로 FRAME(편집 가능한 벡터·텍스트)이 생긴다. 그다음 `slide.appendChild(node)` → `rescale(1728 / node.width)` → x·y.
  30장을 한 번에 올리고 한 스크립트로 옮기면 끝난다(코드 50,000자 제한 회피).
- SVG에서 온 TEXT 노드를 고칠 때는 `getStyledTextSegments(["fontName"])`로 글꼴을 먼저 로드한 뒤 `characters`를 바꾼다.
- SVG는 `placeSvg`가 만든 프레임의 `.height`가 갱신된다. 그 아래에 본문·결론 바를 붙인다.

## 시그니처·사진
- 빈 사각형을 만들고 `upload_assets(nodeIds, scaleMode)`로 채운다: 시그니처 FIT(46곳 한 번에), 사진 FILL. URL마다 `curl -F file=@…` 한 번, 10분 안에.
- 발주처 CI 구하기(5분): 기관 홈페이지 로고를 저장하고 주색 hex를 딴다. 「CI·BI 안내」 페이지가 있으면 그 값을 우선한다. 없으면 로고 주색 하나만 쓰고 보조색은 만들지 않는다.
  로고 파일과 hex는 `bids/<사업>/ci/`에 두고 `_STATE.md`에 적는다. 예: 한국청년기업가정신재단 `#1b4fc4` · 한국자살예방협회 `#e8202a` · KITECH `#0047bb` · 국립순천대 `#0068B0`.
- 웹에서 딴 이미지 URL이 제품 컷이 아닐 수 있다(메타 페이지의 lookaside URL은 세로 1080×1920이었다). 넣기 전 `screenshot`으로 한 번 본다. 아니면 빼고 MANIFEST에 「미확인 → 제외」.

## 그림 그리기 (2026-09-05 도식 10장 실측)
- 레시피는 `scripts/figma_slides_diagrams.js`에 넷만 남겼다(헬퍼 다음에 붙인다): `routeMap` 동선 지도 · `systemConnect` 연결도 · `roomPlan` 배치도 · `approvalTimeline` 타임라인. 스토리보드·판·공정도·층도·반경 지도·와이어프레임은 지웠다 — 도형으로 그린 개념도는 증거가 아니었다(사진·렌더·수치가 증거다). 표가 증거인 장은 `fitTable`.
- 벡터(`createVector`)는 `vectorPaths`를 넣은 뒤 **x·y를 경로 최소점으로 다시 놓는다.** 안 놓으면 (0,0)으로 튄다. 헬퍼 `arrow`·`curvePath`가 처리한다.
- 곡선 경로는 정거장 원 **아래 층**에 둔다: `slide.insertChild(구역 띠 다음 index, path)`.
- 텍스트 속성(정렬·글자)을 바꿀 때도 그 글꼴을 `loadFontAsync`해야 한다(안 하면 「unloaded font」).
- 한 장을 그림으로 바꾸는 순서: `clearBody(slide)`(본문→노트) → 구역/바탕 → 경로·화살표 → 요소(원·헤드셋·상자) → 라벨 → 결론 y → 화면 한 장 확인. 장 하나에 한 호출.

## 고칠 때 (2026-09-05 v5 2차 손질 실측)
- **노드 이름은 역할마다 하나**: 간트 막대와 결론 문장 배경에 같은 이름(`bg-bar`)을 썼더니 「결론을 본문 아래로」 스크립트가 간트 첫 막대를 끌고 갔다. 헬퍼는 결론 배경을 `bg-closing`으로 쓴다. 이름 규약: title · closing · bg-closing · crumb · crumb-sec · page · caption · src · signature · photo-* · bg-th · bg-tr · bg-rule · bg-dot · bg-stepdot · bg-stepline · bg-cardline · bg-block · bg-gantt.
- **여러 열 장은 한 줄로 재적재하지 않는다.** 열마다 y가 다른 장(단계·타임라인·사진+표)을 y 순서 한 줄로 다시 쌓으면 열이 흩어진다. 표는 `bg-tr` 행을 머리 행 아래 이어 붙이고, 단계·카드는 `bg-stepdot`·`bg-cardline` x로 열을 나눠 열마다 쌓는다.
- **옮기기 전에 배정을 끝낸다.** 행을 위에서부터 옮기면서 「이 행 범위에 든 글자」를 고르면, 앞 행에서 이미 옮긴 글자가 다음 행 범위에 들어가 두 번 밀린다. 행↔글자 배정을 먼저 전부 만들고 그다음 한 번에 옮긴다. 순서가 흐트러졌으면 첫 열 이름으로 원래 순서를 되돌린다.
- **수정 스크립트와 `get_screenshot`을 같은 호출 묶음에 넣지 않는다.** 나란히 보내면 화면이 수정 전 상태로 찍힌다(빈 행·겹침이 보여 헛수고했다). 수정 결과를 받은 뒤 다음 차례에 찍는다.
- 46장을 한 장씩 보지 말고 PIL로 3열 모음판(축소 640px)을 만들어 4장으로 본다. 겹침·빈 면적·행 누락이 한눈에 보인다.

## 마무리
- 행(장)을 만들 때마다 헬퍼 `validate(slideIds)`를 돌린다(공식 스킬의 배치 검증을 옮긴 것 + 본문 18px 하한 + 빈 면적 추정). `clean`이면 화면을 안 찍고 다음 행. 아니면 그 장만 찍어 고친다.
- `slide.speakerNotes`(마크다운 불릿)에 요점과 ⚠️ 확인필요를 넣는다. 본문에는 내부 표기를 남기지 않는다(`leftovers()`로 검색).
- 기존 덱을 고칠 때는 장을 지우고 다시 만들지 않는다. 그 자리에서 고친다(사용자가 「처음부터」라고 한 때만 삭제). 제목 사슬을 다시 썼으면 `retitle({ "14": "새 제목", … })`로 `title` 노드 글만 바꾼다.
- 초안 문단은 `notes(slide, [문단…], skipInTalk)`로 발표자 노트에 넣는다. 발표에서 건너뛸 장(별지·회사 소개)은 `skipInTalk = true`.
- **pptx 제출이 요구되면** Figma 내보내기(pdf)나 `doc-gen`(pptx) 경로를 쓰되, Freesentation은 오피스 기본 글꼴이 아니라 받는 쪽 PC에서 깨진다. pptx는 글꼴을 심거나 pdf로 낸다. hwp는 `claw-hwp`.
- 그다음 `deck.md` §6대로 전 장 화면을 찍어 `bids/<사업>/shots/`에 받고 비판자에 넘긴다. 내보내기는 pdf면 Figma에서, hwp·pptx면 하류 스킬(`vax-exit-kit` · `doc-gen` · `claw-hwp`).

## 참고 덱
- 순천캠퍼스 VR 24장(네이티브 노드 · 내용 누락) https://www.figma.com/slides/X1gbJJ0suIxbIeT75bkNzC ·
  46장(SVG 도식 · 디자인 무너짐) https://www.figma.com/slides/8uXlvJ6fp2Z2DC1LHZL41n — 둘을 나란히 보면 `deck.md` §5가 왜 있는지 보인다.
- 회사가 손으로 완성한 3덱(44~54장): 재도전 인식개선 https://www.figma.com/slides/BN80Dl0GVyKdoucXKPpsFg ·
  생명지킴이 영상 https://www.figma.com/slides/rNBq9cTJOZeg7wtDiPyjmB · 공정자동화 3D https://www.figma.com/slides/tmZb7iG9WhrrkHWrT5I5kc
