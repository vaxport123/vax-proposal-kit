#!/usr/bin/env python3
"""도식·표를 **글이 아니라 SVG**로 그린다 — 마크다운 초안의 ```fig 블록 → 자립 SVG.

한준 2026-09-04: "텍스트 대신에 svg 기반의 도식화나 표 처리" · 2026-07-30: "도식화나 표 구조 넣고 … 제대로된 걸로".

■ 한 그림, 두 목적지
· HTML 초안(`render_html.py`)에는 인라인 SVG로 들어간다. 색은 `var(--brand)` 같은 토큰 변수라
  회사 토큰·다크모드를 그대로 따른다.
· Figma 덱에는 `--accent <hex>`로 발주처 CI 색을 박아 `.svg` 파일로 뽑고, Figma 플러그인 API
  `figma.createNodeFromSvg(svg)`로 그대로 올린다(도형·텍스트가 편집 가능한 노드가 된다).
  같은 데이터에서 두 결과가 나오므로 문구를 고치면 둘 다 바뀐다.

■ 왜 이미지가 아니라 SVG인가
· 도식은 데이터의 표현이다. 라벨만 있으면 그릴 수 있고, 고치면 따라 바뀐다(그림 파일은 안 바뀐다).
· 자립 SVG라 브라우저·PDF·노션·Figma에서 그대로 나온다. 외부 요청 0, 라이선스 문제 0.
· 서버 `proposal_figures.py`(HTML/CSS 도식 10종)와 **같은 계약**(`type` + 종류별 필드)이다. 거기서 쓰던
  payload를 그대로 붙여도 그려진다. 여기서는 슬라이드 문법(`figma-handoff.md` §4)에 맞춰 `cards`·`stats`·
  `table`·`steps`를 더했다.

■ 계약
```fig
{"type": "flow", "title": "제작 순서", "steps": [{"h": "실측", "b": "이틀"}, …]}
```
마크다운 안의 ```fig 코드 블록에 JSON 하나. `render(fig, palette)` → `<svg …>` 문자열.
모르는 type·깨진 JSON은 **빈칸이 아니라 경고 상자**로 그린다(조용한 유실 금지 · guardrails §4).
값이 비면 `⚠️ 확인필요`로 남긴다(spec·matrix·select) — "고품질" 같은 말로 채우면 그게 감점이다.

■ 사용
  python3 figures_svg.py --selftest
  python3 figures_svg.py 04_제안서_v4.md --out-dir figs/ --accent "#0068B0"   # 블록마다 figs/fig-01.svg …
  python3 figures_svg.py 04_제안서_v4.md --list                               # 블록 목록만(종류·제목·줄)
"""
import argparse
import html as _html
import json
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

NEED = "⚠️ 확인필요"
W = 1200                       # 기본 폭(px). 슬라이드 본문 영역 1728에 맞춰 늘리면 글자도 같이 커진다.
FONT = "Freesentation, 'Pretendard Variable', Pretendard, 'Malgun Gothic', sans-serif"

# 색 팔레트 — HTML용은 토큰 변수, Figma용은 hex. 이 두 개 말고는 만들지 않는다(무채색 원칙).
PALETTE_VAR = {
    "accent": "var(--brand)", "accent_bg": "var(--brand-bg)", "ink": "var(--ink)",
    "ink_soft": "var(--ink-soft)", "mid": "var(--mid)", "surface": "var(--surface-alt)",
    "line": "var(--hairline)", "paper": "var(--paper)", "warn": "var(--warn)", "warn_bg": "var(--warn-bg)",
    "on_accent": "#ffffff",
}


def palette_hex(accent="#0068B0"):
    """Figma·독립 파일용. 강조색 하나만 발주처 CI, 나머지는 실측 3덱의 무채색 단계(figma-handoff §1)."""
    return {
        "accent": accent, "accent_bg": _tint(accent, 0.90), "ink": "#141414", "ink_soft": "#3a3a3a",
        "mid": "#68727f", "surface": "#f4f5f7", "line": "#d3dae3", "paper": "#ffffff",
        "warn": "#b45309", "warn_bg": "#fff4e5", "on_accent": "#ffffff",
    }


def _tint(hex6, k):
    """hex를 흰색 쪽으로 k(0~1)만큼 섞는다 — 옅은 강조면."""
    h = hex6.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: int(c + (255 - c) * k)  # noqa: E731
    return "#%02x%02x%02x" % (f(r), f(g), f(b))


def _e(v):
    return _html.escape(str(v if v is not None else ""), quote=True)


# ── 글자 폭 추정과 줄바꿈 ────────────────────────────────────────────────────────────
# SVG는 자동 줄바꿈이 없다. 한글 1em · 영문/숫자 0.56em · 공백 0.28em(figma-handoff §6과 같은 기준).
def _cw(ch):
    if ch == " ":
        return 0.28
    if "가" <= ch <= "힣" or "㄰" <= ch <= "㆏":
        return 1.0
    if ord(ch) > 0x2e80:                    # 한자·기호·이모지
        return 1.0
    if ch in "ilj.,:;'|!":
        return 0.3
    return 0.56


def text_width(s, size):
    return sum(_cw(c) for c in str(s)) * size


def wrap(s, width_px, size, max_lines=6):
    """폭에 맞춰 줄을 나눈다. 공백에서 먼저 끊고, 긴 낱말은 글자에서 끊는다. 넘치면 마지막 줄에 …"""
    s = str(s or "").strip()
    if not s:
        return [""]
    lines, cur = [], ""
    for word in re.split(r"(\s+)", s):
        if not word:
            continue
        if text_width(cur + word, size) <= width_px:
            cur += word
            continue
        if cur.strip():
            lines.append(cur.rstrip())
            cur = ""
        if word.isspace():
            continue
        while text_width(word, size) > width_px:      # 한 낱말이 한 줄보다 길다
            cut = 1
            while cut < len(word) and text_width(word[:cut + 1], size) <= width_px:
                cut += 1
            lines.append(word[:cut])
            word = word[cut:]
        cur = word
    if cur.strip():
        lines.append(cur.rstrip())
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + "…"
    return lines or [""]


def text(x, y, s, size, fill, weight=400, anchor="start", width=None, max_lines=6, lh=1.35):
    """<text> 하나. width가 있으면 줄바꿈한다. 반환: (svg, 차지한 높이)"""
    lines = wrap(s, width, size, max_lines) if width else [str(s or "")]
    spans = []
    for i, ln in enumerate(lines):
        dy = 0 if i == 0 else size * lh
        spans.append('<tspan x="%g" dy="%g">%s</tspan>' % (x, dy, _e(ln)))
    svg = ('<text x="%g" y="%g" font-size="%g" font-weight="%d" text-anchor="%s" '
           'style="fill:%s;font-family:%s">%s</text>' % (x, y + size * 0.9, size, weight, anchor, fill, FONT, "".join(spans)))
    return svg, size * 0.9 + size * lh * (len(lines) - 1) + size * 0.35


def rect(x, y, w, h, fill, stroke=None, r=0, sw=1):
    st = ';stroke:%s;stroke-width:%g' % (stroke, sw) if stroke else ''
    return '<rect x="%g" y="%g" width="%g" height="%g" rx="%g" style="fill:%s%s"/>' % (x, y, w, h, r, fill, st)


def line(x1, y1, x2, y2, stroke, sw=1.5):
    return '<line x1="%g" y1="%g" x2="%g" y2="%g" style="stroke:%s;stroke-width:%g"/>' % (x1, y1, x2, y2, stroke, sw)


def arrow(x, y, size, fill):
    """오른쪽 화살촉(▶)."""
    return '<path d="M%g %g L%g %g L%g %g Z" style="fill:%s"/>' % (x, y - size / 2, x + size * 0.8, y, x, y + size / 2, fill)


def _svg(w, h, body, title=""):
    t = '<title>%s</title>' % _e(title) if title else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %g %g" width="%g" height="%g" '
            'role="img" data-fig="1">%s%s</svg>' % (w, h, w, h, t, body))


def _title(f, p, w):
    """도식 제목(왼쪽 세로 막대 + 강조색 라벨). 없으면 높이 0."""
    t = str(f.get("title") or "").strip()
    if not t:
        return "", 0
    s, h = text(18, 2, t, 22, p["accent"], 700, width=w - 24, max_lines=1)
    return rect(0, 0, 5, 30, p["accent"]) + s, h + 10


def _note(f, p, w, y):
    n = str(f.get("note") or "").strip()
    if not n:
        return "", 0
    s, h = text(0, y + 6, n, 15, p["mid"], width=w, max_lines=2)
    return s, h + 6


# ── 종류별 렌더러 ────────────────────────────────────────────────────────────────────
def fig_flow(f, p, w):
    """단계 흐름 — steps=[{"h":단계,"b":설명}] · 가로 카드 사이 화살표(공정·파이프라인 유형)."""
    steps = [s for s in (f.get("steps") or []) if s][:6]
    if not steps:
        return ""
    th, top = _title(f, p, w)
    gap, n = 34, len(steps)
    cw = (w - gap * (n - 1)) / n
    body_lines = max(len(wrap(s.get("b"), cw - 28, 16)) for s in steps)
    ch = 16 + 15 + 8 + 24 + 8 + 16 * 1.35 * body_lines + 14
    out = [th]
    for i, s in enumerate(steps):
        x = i * (cw + gap)
        out.append(rect(x, top, cw, ch, p["surface"]))
        out.append(rect(x, top, cw, 4, p["accent"]))
        out.append(text(x + 14, top + 14, "%02d" % (i + 1), 15, p["accent"], 700)[0])
        out.append(text(x + 14, top + 36, s.get("h"), 22, p["ink"], 700, width=cw - 28, max_lines=1)[0])
        out.append(text(x + 14, top + 72, s.get("b"), 16, p["ink_soft"], width=cw - 28, max_lines=4)[0])
        if i < n - 1:
            out.append(arrow(x + cw + 10, top + ch / 2, 16, p["accent"]))
    y = top + ch
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def fig_steps(f, p, w):
    """순서 카드(세로) — steps=[{"h":단계,"b":설명}] · 한 반 운영 5단계처럼 좌 번호·우 설명."""
    steps = [s for s in (f.get("steps") or []) if s][:8]
    if not steps:
        return ""
    th, y = _title(f, p, w)
    out = [th]
    for i, s in enumerate(steps):
        bl = len(wrap(s.get("b"), w - 260, 17))
        rh = max(64, 26 + 17 * 1.35 * bl + 18)
        out.append(rect(0, y, w, rh, p["surface"] if i % 2 == 0 else p["paper"]))
        out.append(rect(0, y, 4, rh, p["accent"]))
        out.append(text(22, y + rh / 2 - 20, "%02d" % (i + 1), 34, p["accent"], 900)[0])
        out.append(text(90, y + 12, s.get("h"), 20, p["ink"], 700, width=130, max_lines=2)[0])
        out.append(text(240, y + 14, s.get("b"), 17, p["ink_soft"], width=w - 260, max_lines=4)[0])
        y += rh + 6
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def fig_cards(f, p, w):
    """카드 3열(원인·전략·원칙·목표) — items=[{"h":제목,"b":본문,"foot":결론 한 줄}] · 2~4장."""
    items = [i for i in (f.get("items") or []) if i][:4]
    if not items:
        return ""
    th, top = _title(f, p, w)
    gap, n = 28, len(items)
    cw = (w - gap * (n - 1)) / n
    bl = max(len(wrap(i.get("b"), cw - 36, 17)) for i in items)
    hl = max(len(wrap(i.get("h"), cw - 36, 24, 2)) for i in items)
    has_foot = any(str(i.get("foot") or "").strip() for i in items)
    ch = 20 + 22 + 10 + 24 * 1.3 * hl + 12 + 17 * 1.4 * bl + (46 if has_foot else 18)
    out = [th]
    for i, it in enumerate(items):
        x = i * (cw + gap)
        out.append(rect(x, top, cw, ch, p["paper"], p["line"], 0, 1.2))
        out.append(rect(x, top, cw, 5, p["accent"]))
        out.append(text(x + 18, top + 18, "%02d" % (i + 1), 20, p["accent"], 700)[0])
        out.append(text(x + 18, top + 48, it.get("h"), 24, p["ink"], 700, width=cw - 36, max_lines=2)[0])
        by = top + 48 + 24 * 1.3 * hl + 12
        out.append(text(x + 18, by, it.get("b"), 17, p["ink_soft"], width=cw - 36, max_lines=6, lh=1.4)[0])
        if has_foot and str(it.get("foot") or "").strip():
            out.append(rect(x + 18, top + ch - 40, cw - 36, 28, p["accent_bg"], None, 14))
            out.append(text(x + cw / 2, top + ch - 35, it.get("foot"), 14, p["accent"], 700, "middle", width=cw - 50, max_lines=1)[0])
    y = top + ch
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def fig_stats(f, p, w):
    """숫자 카드 — items=[{"n":"48곳","label":"애니메이션 기업","src":"출처"}] · 2~4개. 수치가 주인공일 때."""
    items = [i for i in (f.get("items") or []) if i][:4]
    if not items:
        return ""
    th, top = _title(f, p, w)
    gap, n = 28, len(items)
    cw = (w - gap * (n - 1)) / n
    ch = 150
    out = [th]
    for i, it in enumerate(items):
        x = i * (cw + gap)
        out.append(rect(x, top, cw, ch, p["surface"]))
        num = str(it.get("n") or NEED)
        size = 56 if text_width(num, 56) <= cw - 36 else 40
        out.append(text(x + 18, top + 18, num, size, p["accent"] if num != NEED else p["warn"], 900)[0])
        out.append(text(x + 18, top + 88, it.get("label"), 17, p["ink"], 600, width=cw - 36, max_lines=2)[0])
        if it.get("src"):
            out.append(text(x + 18, top + ch - 26, it.get("src"), 12, p["mid"], width=cw - 36, max_lines=1)[0])
    y = top + ch
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def fig_arch(f, p, w):
    """추진 체계 — top=총괄, groups=[{"h":파트,"items":[역할…]}] (조직·인력 유형의 왼쪽 도식)."""
    groups = [g for g in (f.get("groups") or []) if g][:6]
    if not groups:
        return ""
    th, top = _title(f, p, w)
    gap, n = 22, len(groups)
    cw = (w - gap * (n - 1)) / n
    tw = min(360, w * 0.4)
    out = [th, rect((w - tw) / 2, top, tw, 44, p["accent"]),
           text(w / 2, top + 10, f.get("top") or "총괄책임자", 20, p["on_accent"], 700, "middle", width=tw - 20, max_lines=1)[0],
           line(w / 2, top + 44, w / 2, top + 66, p["accent"], 2),
           line(cw / 2, top + 66, w - cw / 2, top + 66, p["accent"], 2)]
    il = max(len(g.get("items") or []) for g in groups)
    ch = 44 + 8 + il * 26 + 14
    for i, g in enumerate(groups):
        x = i * (cw + gap)
        out.append(line(x + cw / 2, top + 66, x + cw / 2, top + 82, p["accent"], 2))
        out.append(rect(x, top + 82, cw, ch, p["surface"]))
        out.append(rect(x, top + 82, cw, 40, p["ink"]))
        out.append(text(x + cw / 2, top + 91, g.get("h"), 17, p["on_accent"], 700, "middle", width=cw - 16, max_lines=1)[0])
        for j, it in enumerate((g.get("items") or [])[:6]):
            out.append(text(x + cw / 2, top + 132 + j * 26, it, 15, p["ink_soft"], 400, "middle", width=cw - 16, max_lines=1)[0])
    y = top + 82 + ch
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def fig_layers(f, p, w):
    """계층도 — layers=[{"h":층,"b":설명}] 위→아래. 시스템 네 덩이·데이터/플랫폼 층."""
    ls = [x for x in (f.get("layers") or []) if x][:6]
    if not ls:
        return ""
    th, y = _title(f, p, w)
    out = [th]
    for i, x in enumerate(ls):
        bl = len(wrap(x.get("b"), w - 330, 17))
        rh = max(58, 20 + 17 * 1.35 * bl + 16)
        out.append(rect(0, y, w, rh, p["surface"]))
        out.append(rect(0, y, 6, rh, p["accent"]))
        out.append(text(22, y + 14, "%d" % (i + 1), 20, p["accent"], 700)[0])
        out.append(text(56, y + 12, x.get("h"), 20, p["ink"], 700, width=240, max_lines=2)[0])
        out.append(text(310, y + 14, x.get("b"), 17, p["ink_soft"], width=w - 330, max_lines=4)[0])
        y += rh + 6
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def fig_gantt(f, p, w):
    """일정 — bars=[{"h":단계,"from":1,"to":3,"out":산출물}] · units=총 칸 수(기본 12) · unit=칸 이름(주·월)."""
    bars = [b for b in (f.get("bars") or []) if b][:12]
    n = int(f.get("units") or f.get("months") or 12) or 12
    unit = str(f.get("unit") or ("주" if f.get("units") else "월"))
    if not bars:
        return ""
    th, top = _title(f, p, w)
    lw, ow, rh, hh = 230, 250, 40, 34
    cw = (w - lw - ow) / n
    out = [th, rect(0, top, w, hh, p["ink"]),
           text(12, top + 8, "단계", 15, p["on_accent"], 700)[0],
           text(w - ow + 12, top + 8, "산출물·확인", 15, p["on_accent"], 700)[0]]
    for i in range(n):
        out.append(text(lw + cw * i + cw / 2, top + 8, "%d%s" % (i + 1, unit), 13, p["on_accent"], 500, "middle")[0])
    y = top + hh
    for i, b in enumerate(bars):
        s = max(1, int(b.get("from") or 1))
        e = min(n, max(s, int(b.get("to") or s)))
        # 단계 이름·산출물은 두 줄까지 — 한 줄에서 「…」로 잘리면 심사위원이 읽을 수 없다(실측 2026-09-04)
        hl = max(len(wrap(b.get("h"), lw - 20, 15, 2)), len(wrap(b.get("out"), ow - 20, 14, 2)))
        rh_i = rh if hl <= 1 else rh + 20
        out.append(rect(0, y, w, rh_i, p["surface"] if i % 2 == 0 else p["paper"]))
        out.append(text(12, y + 10, b.get("h"), 15, p["ink"], 600, width=lw - 20, max_lines=2)[0])
        out.append(rect(lw + cw * (s - 1) + 2, y + 9, cw * (e - s + 1) - 4, rh_i - 18, p["accent"], None, 4))
        out.append(text(w - ow + 12, y + 10, b.get("out"), 14, p["ink_soft"], width=ow - 20, max_lines=2)[0])
        y += rh_i
    for i in range(n + 1):
        out.append(line(lw + cw * i, top + hh, lw + cw * i, y, p["line"], 1))
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def _table(f, p, w, head, rows, first_col_accent=True, need_cols=()):
    """공통 표. head=[열 이름] · rows=[[셀…]] · 열 폭은 head의 `widths`(비율)로, 없으면 균등. 머리 행은 진한 면 + 흰 글자,
    첫 열은 강조색(실측 3덱의 표 문법). need_cols의 빈 셀은 확인필요로 채운다."""
    th, top = _title(f, p, w)
    n = len(head)
    ws = f.get("widths") or [1] * n
    tot = float(sum(ws))
    cws = [w * x / tot for x in ws]
    fs = int(f.get("font") or 15)
    hh = 40
    out = [th, rect(0, top, w, hh, p["ink"])]
    x = 0
    for i, h in enumerate(head):
        out.append(text(x + 12, top + 11, h, fs, p["on_accent"], 700, width=cws[i] - 20, max_lines=1)[0])
        x += cws[i]
    y = top + hh
    for ri, r in enumerate(rows):
        cells = [str(c if c is not None else "") for c in r] + [""] * (n - len(r))
        for ci in need_cols:
            if ci < n and not cells[ci].strip():
                cells[ci] = NEED
        hts = [len(wrap(cells[i], cws[i] - 24, fs)) for i in range(n)]
        rh = max(36, 12 + fs * 1.35 * max(hts) + 10)
        out.append(rect(0, y, w, rh, p["surface"] if ri % 2 == 0 else p["paper"]))
        x = 0
        for i in range(n):
            c = cells[i]
            is_need = NEED in c
            fill = p["warn"] if is_need else (p["accent"] if (i == 0 and first_col_accent) else p["ink_soft"])
            wt = 700 if (i == 0 and first_col_accent) else 400
            if is_need:
                out.append(rect(x + 2, y + 2, cws[i] - 4, rh - 4, p["warn_bg"]))
            out.append(text(x + 12, y + 8, c, fs, fill, wt, width=cws[i] - 24, max_lines=8)[0])
            x += cws[i]
        y += rh
        out.append(line(0, y, w, y, p["line"], 1))
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def fig_table(f, p, w):
    """일반 표 — head=[…], rows=[[…]]. 마크다운 표를 그대로 옮길 때. 첫 열 강조는 `first`(기본 true)."""
    head, rows = f.get("head") or [], f.get("rows") or []
    if not (head and rows):
        return ""
    return _table(f, p, w, head, rows[:14], f.get("first", True))


def fig_matrix(f, p, w):
    """요구 ↔ 대응 ↔ 근거 — rows=[{"req":…,"ans":…,"ev":…}]. 근거가 비면 확인필요(감점 1순위 겨냥)."""
    rows = [r for r in (f.get("rows") or []) if r][:17]
    if not rows:
        return ""
    f = dict(f)
    f.setdefault("widths", [4, 4, 3])
    f.setdefault("title", "요구사항 대응표")
    return _table(f, p, w, ["발주처 요구·평가요소", "우리 대응", "근거"],
                  [[r.get("req"), r.get("ans"), r.get("ev")] for r in rows], True, need_cols=(2,))


def fig_risk(f, p, w):
    """위험 관리표 — rows=[{"risk","cause","effect","plan"}]. 원인·영향이 비면 이 과업 고유 위험이 아니다."""
    rows = [r for r in (f.get("rows") or []) if r][:8]
    if not rows:
        return ""
    f = dict(f)
    f.setdefault("widths", [3, 3, 3, 4])
    f.setdefault("title", "위험 관리 계획")
    return _table(f, p, w, ["위험", "원인", "영향", "대응"],
                  [[r.get("risk"), r.get("cause"), r.get("effect"), r.get("plan")] for r in rows], True, need_cols=(1, 2))


def fig_spec(f, p, w):
    """품질·규격 수치표 — rows=[{"item","value","how"}]. 값이 없으면 확인필요."""
    rows = [r for r in (f.get("rows") or []) if r][:12]
    if not rows:
        return ""
    f = dict(f)
    f.setdefault("widths", [3, 3, 4])
    f.setdefault("title", "품질 기준·검수 방법")
    return _table(f, p, w, ["항목", "기준값", "검수 방법"],
                  [[r.get("item"), r.get("value"), r.get("how")] for r in rows], True, need_cols=(1,))


def fig_select(f, p, w):
    """선정 기준·대상 — criteria=[{"h","b"}] · rows=[{"item","why","grade","note"}]. 선정 배점이 있는 공고의 중심 표."""
    crit = [c for c in (f.get("criteria") or []) if c][:6]
    rows = [r for r in (f.get("rows") or []) if r][:14]
    if not (crit or rows):
        return ""
    parts, y = [], 0
    if crit:
        s = _table({"title": f.get("title") or "선정 기준", "widths": [1, 3]}, p, w, ["선정 기준", "내용·비중"],
                   [[c.get("h"), c.get("b")] for c in crit])
        parts.append((s, _h(s)))
    if rows:
        s = _table({"title": "" if crit else f.get("title"), "widths": [2, 4, 1.5, 2], "note": f.get("note")}, p, w,
                   ["선정 대상", "선정 근거", "등급·LOD", "비고"],
                   [[r.get("item"), r.get("why"), r.get("grade"), r.get("note")] for r in rows], True, need_cols=(1,))
        parts.append((s, _h(s)))
    return _stack(parts, w, f.get("title"))


def fig_system(f, p, w):
    """운용 시스템 구성도 — rows=[{"h":구성요소,"b":역할,"spec":사양,"fail":고장 대응}] · 상자 → 화살표 + 고장 대응 줄."""
    rows = [r for r in (f.get("rows") or []) if str((r or {}).get("h") or "").strip()][:6]
    if not rows:
        return ""
    th, top = _title(f, p, w)
    gap, n = 34, len(rows)
    cw = (w - gap * (n - 1)) / n
    bl = max(len(wrap(r.get("b"), cw - 28, 15)) for r in rows)
    has_spec = any(r.get("spec") for r in rows)
    ch = 16 + 26 + 8 + 15 * 1.35 * bl + (28 if has_spec else 0) + 16
    out = [th]
    for i, r in enumerate(rows):
        x = i * (cw + gap)
        out.append(rect(x, top, cw, ch, p["surface"]))
        out.append(rect(x, top, cw, 4, p["accent"]))
        out.append(text(x + 14, top + 14, r.get("h"), 20, p["ink"], 700, width=cw - 28, max_lines=1)[0])
        out.append(text(x + 14, top + 48, r.get("b"), 15, p["ink_soft"], width=cw - 28, max_lines=4)[0])
        if r.get("spec"):
            out.append(text(x + 14, top + ch - 30, r.get("spec"), 13, p["mid"], width=cw - 28, max_lines=1)[0])
        if i < n - 1:
            out.append(arrow(x + cw + 10, top + ch / 2, 16, p["accent"]))
    y = top + ch + 12
    fails = [r for r in rows if str(r.get("fail") or "").strip()]
    if fails:
        out.append(line(0, y, w, y, p["line"], 1))
        out.append(text(0, y + 8, "고장 대응", 15, p["accent"], 700)[0])
        y += 34
        for r in fails:
            s, h = text(0, y, "%s — %s" % (r.get("h"), r.get("fail")), 15, p["ink_soft"], width=w, max_lines=2)
            out.append(s)
            y += h
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def fig_layout(f, p, w):
    """배치 개념도 — space=공간 · zones=[{"h","pos":"북|중앙|남동…","b"}] · path=[동선]. 도면이 없어도 그린다(개념도라고 note에 박는다)."""
    POS = {"북서": (0, 0), "북": (0, 1), "북동": (0, 2), "서": (1, 0), "중앙": (1, 1), "동": (1, 2),
           "남서": (2, 0), "남": (2, 1), "남동": (2, 2)}
    zones = [z for z in (f.get("zones") or []) if str((z or {}).get("h") or "").strip()][:6]
    if not zones:
        return ""
    th, top = _title(f, p, w)
    out = [th]
    if f.get("space"):
        s, h = text(0, top, f.get("space"), 16, p["accent"], 700, width=w, max_lines=1)
        out.append(s)
        top += h + 4
    gw, gh = w, 300
    cw, ch = gw / 3, gh / 3
    out.append(rect(0, top, gw, gh, p["paper"], p["accent"], 0, 2))
    for i in (1, 2):
        out.append(line(cw * i, top, cw * i, top + gh, p["line"], 1))
        out.append(line(0, top + ch * i, gw, top + ch * i, p["line"], 1))
    at = {}
    for z in zones:
        at.setdefault(POS.get(str(z.get("pos") or "").strip(), (1, 1)), []).append(z)
    for (r, c), zs in at.items():
        yy = top + ch * r + 8
        for z in zs[:2]:
            out.append(rect(cw * c + 8, yy, cw - 16, 40, p["surface"]))
            out.append(rect(cw * c + 8, yy, 3, 40, p["accent"]))
            out.append(text(cw * c + 18, yy + 4, z.get("h"), 15, p["ink"], 700, width=cw - 34, max_lines=1)[0])
            if z.get("b"):
                out.append(text(cw * c + 18, yy + 22, z.get("b"), 12, p["ink_soft"], width=cw - 34, max_lines=1)[0])
            yy += 46
    y = top + gh + 10
    path = [str(x) for x in (f.get("path") or []) if str(x).strip()][:6]
    if path:
        s, h = text(0, y, "동선  " + "  ▶  ".join(path), 15, p["accent"], 700, width=w, max_lines=2)
        out.append(s)
        y += h
    n_svg, nh = _note(f, p, w, y)
    return _svg(w, y + nh + 4, "".join(out) + n_svg, f.get("title"))


def _h(svg):
    m = re.search(r'height="([\d.]+)"', svg or "")
    return float(m.group(1)) if m else 0


def _stack(parts, w, title=""):
    """SVG 여러 장을 세로로 쌓아 한 장으로."""
    body, y = [], 0
    for s, h in parts:
        inner = re.sub(r"^<svg[^>]*>|</svg>$", "", s.strip())
        inner = re.sub(r"<title>.*?</title>", "", inner, count=1)
        body.append('<g transform="translate(0,%g)">%s</g>' % (y, inner))
        y += h + 14
    return _svg(w, y, "".join(body), title)


def fig_warn(msg, p, w, title=""):
    th, top = _title({"title": title}, p, w)
    s, h = text(16, top + 12, "%s — %s" % (NEED, msg), 16, p["warn"], 600, width=w - 32, max_lines=3)
    return _svg(w, top + h + 28, th + rect(0, top, w, h + 24, p["warn_bg"]) + s, title)


TYPES = {"flow": fig_flow, "steps": fig_steps, "cards": fig_cards, "stats": fig_stats, "arch": fig_arch,
         "layers": fig_layers, "gantt": fig_gantt, "table": fig_table, "matrix": fig_matrix, "risk": fig_risk,
         "spec": fig_spec, "select": fig_select, "system": fig_system, "layout": fig_layout}


def render(fig, palette=None, width=W):
    """도식 하나 → SVG 문자열. 모르는 종류·예외는 경고 상자(조용히 버리지 않는다)."""
    p = palette or PALETTE_VAR
    if not isinstance(fig, dict):
        return fig_warn("도식 데이터가 JSON 객체가 아니다", p, width)
    t = str(fig.get("type") or "").strip()
    fn = TYPES.get(t)
    if not fn:
        return fig_warn("알 수 없는 도식 종류 「%s」 (가능: %s)" % (t, " ".join(TYPES)), p, width, fig.get("title"))
    try:
        return fn(fig, p, width) or fig_warn("데이터가 비어 있다", p, width, fig.get("title"))
    except Exception as ex:                       # 도식 하나가 문서를 막지 않는다
        return fig_warn("도식 생성 실패: %s" % str(ex)[:80], p, width, fig.get("title"))


# ── 마크다운 안의 ```fig 블록 ─────────────────────────────────────────────────────────
FENCE = re.compile(r"^```fig[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)


def parse_block(src):
    """```fig 안의 JSON. 깨졌으면 (None, 오류문)."""
    try:
        return json.loads(src), ""
    except Exception as ex:                        # noqa: BLE001
        return None, "JSON 오류: %s" % str(ex)[:80]


def find_blocks(md):
    """[(시작 줄 번호, 원문, dict 또는 None, 오류)]"""
    out = []
    for m in FENCE.finditer(md):
        ln = md.count("\n", 0, m.start()) + 1
        fig, err = parse_block(m.group(1))
        out.append((ln, m.group(1), fig, err))
    return out


def render_block(src, palette=None, width=W):
    fig, err = parse_block(src)
    if fig is None:
        return fig_warn(err, palette or PALETTE_VAR, width)
    return render(fig, palette, width)


def export(md_path, out_dir, accent="#0068B0", width=W):
    md = open(md_path, encoding="utf-8").read()
    os.makedirs(out_dir, exist_ok=True)
    p = palette_hex(accent)
    rows = []
    for i, (ln, src, fig, err) in enumerate(find_blocks(md), 1):
        svg = fig_warn(err, p, width) if fig is None else render(fig, p, width)
        t = (fig or {}).get("type", "?")
        name = "fig-%02d-%s.svg" % (i, t)
        open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="").write(svg)
        rows.append((name, ln, t, (fig or {}).get("title", ""), err))
    return rows


def selftest():
    fails, n = [], [0]

    def ok(name, cond):
        n[0] += 1
        if not cond:
            fails.append(name)

    p = palette_hex("#0068B0")
    ok("줄바꿈: 한글 폭", wrap("가나다라마바사아자차", 100, 20) == ["가나다라마", "바사아자차"])
    ok("줄바꿈: 공백 우선", wrap("hello world foo", 80, 16)[0] == "hello")
    ok("줄바꿈: 넘치면 말줄임", wrap("가" * 40, 100, 20, 2)[-1].endswith("…"))
    ok("flow 그림", "<svg" in render({"type": "flow", "steps": [{"h": "실측", "b": "이틀"}]}, p) and "실측" in render({"type": "flow", "steps": [{"h": "실측"}]}, p))
    ok("flow 화살표 n-1", render({"type": "flow", "steps": [{"h": "a"}, {"h": "b"}, {"h": "c"}]}, p).count("<path") == 2)
    ok("cards 셋", render({"type": "cards", "items": [{"h": "a", "b": "b"}] * 3}, p).count("<rect") >= 6)
    ok("stats 큰 숫자", 'font-size="56"' in render({"type": "stats", "items": [{"n": "48곳", "label": "기업"}]}, p))
    ok("stats 값 없으면 확인필요", NEED in render({"type": "stats", "items": [{"label": "기업"}]}, p))
    g = render({"type": "gantt", "units": 13, "unit": "주", "bars": [{"h": "실측", "from": 1, "to": 1, "out": "스캔"}]}, p)
    ok("gantt 13주 머리", "13주" in g and "스캔" in g)
    mx = render({"type": "matrix", "rows": [{"req": "5분 이상", "ans": "5분 30초", "ev": ""}]}, p)
    ok("matrix 근거 비면 확인필요", NEED in mx)
    ok("matrix 경고면 색", p["warn_bg"] in mx)
    ok("spec 값 없으면 확인필요", NEED in render({"type": "spec", "rows": [{"item": "폴리곤", "value": "", "how": "검수"}]}, p))
    ok("table 일반", "머리" in render({"type": "table", "head": ["머리", "b"], "rows": [["1", "2"]]}, p))
    ok("arch 총괄 상자", "총괄책임자" in render({"type": "arch", "groups": [{"h": "기획", "items": ["A", "B"]}]}, p))
    ok("layers 넷", render({"type": "layers", "layers": [{"h": "a", "b": "b"}] * 4}, p).count(">4<") == 1)
    ok("steps 번호", ">05<" in render({"type": "steps", "steps": [{"h": "a", "b": "b"}] * 5}, p))
    sy = render({"type": "system", "rows": [{"h": "재생", "b": "콘텐츠", "fail": "예비기"}, {"h": "표시", "b": "출력"}]}, p)
    ok("system 고장 대응", "고장 대응" in sy and "예비기" in sy)
    lo = render({"type": "layout", "space": "3층 232㎡", "zones": [{"h": "강의실", "pos": "북"}], "path": ["입구", "강의실"]}, p)
    ok("layout 동선", "동선" in lo and "강의실" in lo)
    sel = render({"type": "select", "criteria": [{"h": "수요", "b": "20%"}], "rows": [{"item": "무등산", "why": ""}]}, p)
    ok("select 두 표 쌓임", sel.count("<g transform") == 2 and NEED in sel)
    ok("모르는 종류는 경고", NEED in render({"type": "nope"}, p))
    ok("빈 데이터도 경고", NEED in render({"type": "flow", "steps": []}, p))
    ok("예외도 경고", NEED in render({"type": "gantt", "bars": [{"from": "x"}]}, p))
    ok("HTML용은 토큰 변수", "var(--brand)" in render({"type": "cards", "items": [{"h": "a"}]}))
    ok("Figma용은 hex", "#0068B0" in render({"type": "cards", "items": [{"h": "a"}]}, p) and "var(" not in render({"type": "cards", "items": [{"h": "a"}]}, p))
    ok("이스케이프", "&lt;b&gt;" in render({"type": "cards", "items": [{"h": "<b>"}]}, p))
    md = "본문\n\n```fig\n{\"type\": \"flow\", \"steps\": [{\"h\": \"a\"}]}\n```\n\n```fig\n{깨짐\n```\n"
    bl = find_blocks(md)
    ok("블록 둘 찾음", len(bl) == 2 and bl[0][2] and bl[1][2] is None)
    ok("깨진 JSON은 경고 SVG", NEED in render_block(bl[1][1], p))
    ok("종류 14", len(TYPES) == 14)
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — %d건 통과(도식 %d종·줄바꿈·확인필요·경고·팔레트·블록)" % (n[0], len(TYPES)))
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="마크다운 ```fig 블록 → SVG")
    ap.add_argument("src", nargs="?")
    ap.add_argument("--out-dir", default="figs")
    ap.add_argument("--accent", default="#0068B0", help="발주처 CI 강조색(hex). HTML은 토큰 변수를 쓰므로 여기 값은 파일 내보내기에만")
    ap.add_argument("--width", type=int, default=W)
    ap.add_argument("--list", action="store_true", help="블록 목록만")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.src:
        ap.error("src 가 필요하다")
    if a.list:
        for ln, src, fig, err in find_blocks(open(a.src, encoding="utf-8").read()):
            print("%4d줄  %-8s %s %s" % (ln, (fig or {}).get("type", "?"), (fig or {}).get("title", ""), err))
        return 0
    rows = export(a.src, a.out_dir, a.accent, a.width)
    for name, ln, t, title, err in rows:
        print("%s  (%d줄 · %s · %s)%s" % (name, ln, t, title, "  ⚠ " + err if err else ""))
    print("%d장 → %s" % (len(rows), a.out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
