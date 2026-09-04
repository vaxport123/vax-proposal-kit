# Figma 핸드오프 — HTML 디자인을 Figma에 넣고 Claude-Figma로 다듬기

렌더한 HTML은 **초안**이다. Figma에 들어간 순간부터 Figma가 정본이고, 세부 디자인은
Claude-Figma(Figma MCP)로 조정한다. HTML을 다시 렌더해 Figma 위를 덮어쓰지 않는다.

## 전제
- Figma 공식 MCP 커넥터가 Claude에 연결돼 있어야 한다.
- Figma를 부르기 전에 **반드시** `/figma-use` 스킬(또는 `skill://figma/figma-use/SKILL.md`)을 먼저 읽는다 — Figma MCP 규칙이다.

## 절차
1. **파일 준비**: 대상 Figma 파일(또는 새 파일)을 정한다. 팀 디자인 라이브러리가 있으면 `get_libraries`로 확인해 그 컴포넌트를 우선 쓴다.
2. **HTML → Figma**: `render_html.py`가 만든 HTML(또는 그 소스)을 Figma 생성 도구로 넣는다.
   페이지 단위 레이아웃이면 `/figma-generate-design` 절차를 따른다. 한 장짜리 제안서는 아트보드 하나로, 슬라이드형이면 절별로 프레임을 나눈다.
3. **토큰 맞추기**: 들어간 뒤 색·모서리·글꼴이 `house-style.md`의 토큰과 같은지 본다. Figma 변수(`get_variable_defs`)에 회사 토큰이 있으면 그것에 연결한다. 없으면 만들지 말고 사용자에게 알린다.
4. **세부 조정은 Claude-Figma로**: 여백·정렬·강조·이미지 배치는 Figma 안에서 `use_figma`로 고친다. 이 단계에서 문장을 고치면 **노션 초안에도 같은 수정을 남긴다**(사본이 어긋나지 않게).
5. **내보내기**: 제출 형식이 pdf면 Figma에서 내보내고, hwp/pptx가 필요하면 하류 스킬(`vax-exit-kit`·`doc-gen`·`claw-hwp`)로 넘긴다.

## 하지 않는 것
- Figma에 들어간 디자인을 HTML로 역변환해 다시 정본으로 삼지 않는다.
- 회사 토큰 밖의 색·글꼴을 Figma에서 새로 만들지 않는다. 필요하면 서버 정본(`ops/ui_tokens.py`)부터 고친다.
- 공개 금지 정보(`guardrails.md`)는 Figma 파일에도 넣지 않는다 — Figma 링크는 쉽게 밖으로 나간다.
