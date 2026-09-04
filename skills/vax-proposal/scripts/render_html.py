#!/usr/bin/env python3
"""마크다운 초안 → 회사 디자인 HTML 1장.

서버 `ops/render_md_page.py`의 마크다운 엔진과 공개 금지 검사를 그대로 가져오고, 스타일만
정본 디자인 토큰(`ui_tokens.py`, ERP와 같은 값)으로 바꿨다. **원본은 md 하나**, HTML은 렌더 결과다.

사용:
    python3 render_html.py <초안.md> <출력.html> "<제목>" [--md-link 파일명] [--kick 머리글]

⚠️ 공개 금지 정보(서버 주소·포트·모델명·채널 ID·내부 경로·토큰)가 본문에 있으면 **렌더를 거부한다.**
   사람이 잊어도 기계가 막는다. 임직원 실명은 자동으로 못 잡으므로 사람이 확인한다.

지원 문법은 우리가 실제로 쓰는 것만: 제목 · 표 · 목록 · 인용 · 굵게 · 코드 · 구분선.
"""
import argparse
import html
import os
import re
import sys

# 윈도우 콘솔(cp949)에서 한글·기호(—, ⚠️) 출력이 깨지지 않게. 리눅스에서는 그대로다.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ui_tokens  # noqa: E402  — 정본 사본. 색·간격은 여기서 온다.
import figures_svg  # noqa: E402  — ```fig 블록 → 인라인 SVG(도식·표). 색은 토큰 변수로 그린다.

# 공개 페이지에 있으면 안 되는 것 — references/guardrails.md §1 의 기계 판정판 (서버와 같은 목록)
FORBIDDEN = (
    (r"\b100\.\d+\.\d+\.\d+\b", "사설망 IP"),
    (r":8787\b", "내부 포트"),
    (r"\b(gemini|gpt-4|claude-[a-z]+-\d)", "모델명"),
    (r"\bC0[A-Z0-9]{8,}\b", "슬랙 채널·유저 ID"),
    (r"/opt/vax|/var/lib/vax|/var/www", "서버 경로"),
    (r"xox[bp]-|xapp-", "토큰"),
)

NUM = re.compile(r"^\d+\. ")
TABLE_SEP = set("-:")

# 토큰 다음에 오는 본문 규칙. 색·모서리·간격은 전부 var(--…)만 쓴다 — hex 를 새로 적지 않는다.
BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
b,strong{font-weight:600}
html{scroll-behavior:smooth}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{background:var(--paper);color:var(--ink);
font-family:'Geist','Pretendard Variable',Pretendard,'Inter',ui-sans-serif,system-ui,-apple-system,
BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic","맑은 고딕",sans-serif;
font-size:15px;line-height:1.75;-webkit-print-color-adjust:exact;print-color-adjust:exact}
a{color:var(--brand)}
a:focus-visible,button:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
.wrap{max-width:880px;margin:0 auto;padding:28px 28px 96px}
[data-embed] .dhead{display:none}
.dhead{border-bottom:1px solid var(--hairline);padding-bottom:16px;margin-bottom:8px}
.dhead .kick{color:var(--brand);font-size:11px;font-weight:600;letter-spacing:3px;margin-bottom:7px}
h1{font-size:26px;font-weight:600;letter-spacing:-.5px;line-height:1.32}
.dmeta{color:var(--mid);font-size:12.5px;margin-top:8px}
h2{font-size:20px;font-weight:600;letter-spacing:-.3px;margin:56px 0 0;padding-bottom:12px;
border-bottom:1px solid var(--hairline);scroll-margin-top:16px}
h3{font-size:16px;font-weight:600;margin:28px 0 8px}
h4{font-size:13px;font-weight:600;color:var(--ink-soft);margin:20px 0 6px}
p{margin:10px 0}
ul,ol{margin:10px 0 10px 22px}li{margin:6px 0}
.sub{margin:3px 0 3px 4px;color:var(--ink-soft);font-size:14px}
hr{border:0;border-top:1px solid var(--hairline);margin:32px 0}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}
th,td{border:1px solid var(--hairline);padding:9px 12px;text-align:left;vertical-align:top}
th{background:var(--surface-alt);color:var(--mid);font-weight:500;font-size:12px}
code{background:var(--surface-alt);border:1px solid var(--hairline);border-radius:var(--r-sm);
padding:1px 6px;font-size:13px;font-family:ui-monospace,Menlo,Consolas,monospace}
pre{background:var(--surface-alt);border:1px solid var(--hairline);border-radius:var(--r-nested);
padding:13px 15px;margin:13px 0;overflow-x:auto}
pre code{background:none;border:0;padding:0;font-size:13px;line-height:1.6}
blockquote{border-left:3px solid var(--brand);background:var(--brand-bg);padding:12px 16px;margin:14px 0;
color:var(--ink-soft);border-radius:0 var(--r-sm) var(--r-sm) 0}
.todo{background:var(--warn-bg);color:var(--warn);border:1px solid var(--warn);border-radius:var(--r-sm);
padding:1px 6px;font-weight:600}
.fig{margin:18px 0}.fig svg{width:100%;height:auto;display:block}
.foot{margin-top:52px;padding-top:16px;border-top:1px solid var(--hairline);color:var(--mid);font-size:13px}
@media print{.wrap{padding:0}h2{page-break-after:avoid}table{page-break-inside:avoid}}
"""

# 테마 — **칠하기 전에** 정한다(나중에 정하면 흰 화면이 번쩍인다). ERP와 같은 localStorage 키.
THEME_JS = """<script>(function(){try{
var q=(location.search.match(/[?&]theme=(light|dark)/)||[])[1];
if(/[?&]embed=1/.test(location.search)){document.documentElement.dataset.embed='1'}
var t=q||localStorage.getItem('vaxtheme');
if(t!=='light'&&t!=='dark'){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}
document.documentElement.dataset.theme=t}catch(e){}})();</script>"""


def inline(t):
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    # ⚠️ 확인필요 는 눈에 띄게 — 조용한 누락 금지(guardrails §4)
    t = re.sub(r"(⚠️\s*확인필요[^<]*)", r'<span class="todo">\1</span>', t)
    return t


def render(md):
    lines, out, i = md.split("\n"), [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|") and i + 1 < len(lines) and \
                set(lines[i + 1].replace("|", "").replace(" ", "")) <= TABLE_SEP:
            head = [c.strip() for c in ln.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            out.append("<table><tr>" + "".join("<th>%s</th>" % inline(c) for c in head) + "</tr>")
            for r in rows:
                out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            out.append("</table>")
            continue
        if ln.startswith("```"):
            is_fig = ln.strip().startswith("```fig")
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i] if is_fig else html.escape(lines[i]))
                i += 1
            i += 1
            if is_fig:
                # 도식·표는 글이 아니라 SVG로(figures_svg). 깨진 JSON도 경고 상자로 나온다 — 조용히 사라지지 않는다.
                out.append('<div class="fig">' + figures_svg.render_block("\n".join(buf)) + "</div>")
            else:
                out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue
        if ln.startswith("#"):
            n = len(ln) - len(ln.lstrip("#"))
            out.append("<h%d>%s</h%d>" % (n, inline(ln[n:].strip()), n))
        elif ln.strip() in ("---", "***"):
            out.append("<hr>")
        elif ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(inline(lines[i].lstrip(">").strip()))
                i += 1
            out.append("<blockquote>%s</blockquote>" % "<br>".join(x for x in buf if x))
            continue
        elif NUM.match(ln):
            buf = []
            while i < len(lines) and (NUM.match(lines[i]) or (buf and lines[i].startswith("   "))):
                if lines[i].startswith("   "):
                    buf.append('<div class="sub">%s</div>' % inline(lines[i].strip().lstrip("- ")))
                else:
                    buf.append("<li>%s</li>" % inline(NUM.sub("", lines[i])))
                i += 1
            out.append("<ol>" + "".join(buf) + "</ol>")
            continue
        elif ln.startswith("- "):
            buf = []
            while i < len(lines) and lines[i].startswith("- "):
                buf.append("<li>%s</li>" % inline(lines[i][2:]))
                i += 1
            out.append("<ul>" + "".join(buf) + "</ul>")
            continue
        elif ln.strip():
            out.append("<p>%s</p>" % inline(ln))
        i += 1
    return "\n".join(out)


def check_forbidden(md):
    """공개 금지 정보 목록(빈 리스트면 통과)."""
    return [why for pat, why in FORBIDDEN if re.search(pat, md, re.I)]


def build(md, title, kick="제안서 초안", md_link=""):
    foot = ""
    if md_link:
        foot = '원본(마크다운): <a href="%s">%s</a> · ' % (html.escape(md_link), html.escape(md_link))
    todo = md.count("확인필요")
    meta = "초안 · 확인필요 %d건" % todo if todo else "초안"
    return (
        '<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>%s</title>\n" % html.escape(title) +
        '<meta name="color-scheme" content="light dark">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap" rel="stylesheet">\n'
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">\n'
        + THEME_JS + "\n<style>\n" + ui_tokens.css() + BASE_CSS + "</style>\n</head>\n"
        '<body><div class="wrap">\n'
        '<div class="dhead"><div class="kick">%s</div><h1>%s</h1><div class="dmeta">%s</div></div>\n'
        % (html.escape(kick), html.escape(title), meta)
        + render(md) +
        '\n<div class="foot">%s이 문서는 초안이다 — 사람이 Figma·노션에서 고친 값이 정답이다.</div>\n'
        "</div></body></html>" % foot
    )


def selftest():
    """LLM 없이 결정론 검사. 렌더 규칙과 금지 검사가 살아 있는지."""
    fails = []

    def ok(name, cond):
        if not cond:
            fails.append(name)

    ok("금지: 사설망 IP", check_forbidden("서버는 100.64.0.1 에 있다") == ["사설망 IP"])
    ok("금지: 내부 경로", "서버 경로" in check_forbidden("파일은 /var/www/x 에"))
    ok("통과: 보통 문장", check_forbidden("발주처 요구 과업 3건") == [])
    h = build("# 제목\n\n본문 **강조** 와 `코드`\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n⚠️ 확인필요 — 금액", "T")
    ok("토큰이 들어간다", "--brand:" in h and "--r-card:" in h)
    ok("표가 만들어진다", "<table>" in h and "<th>a</th>" in h)
    ok("확인필요가 표시된다", 'class="todo"' in h)
    ok("hex 를 새로 적지 않는다", not re.search(r"#[0-9a-fA-F]{6}", BASE_CSS))
    ok("메타에 확인필요 건수", "확인필요 1건" in h)
    f = build("본문\n\n```fig\n{\"type\": \"flow\", \"steps\": [{\"h\": \"실측\", \"b\": \"이틀\"}]}\n```\n\n```fig\n{깨짐\n```\n", "T")
    ok("fig 블록이 SVG로", f.count('<div class="fig"><svg') == 2 and "실측" in f)
    ok("fig 색은 토큰 변수", "var(--brand)" in f)
    ok("깨진 fig도 경고로 남는다", "확인필요" in f and "JSON 오류" in f)
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — %d건 통과" % 11)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="마크다운 초안 → 회사 디자인 HTML 1장")
    ap.add_argument("src", nargs="?")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("title", nargs="?")
    ap.add_argument("--md-link", default="", help="하단에 걸 원본 md 파일명(같은 폴더)")
    ap.add_argument("--kick", default="제안서 초안", help="제목 위 작은 머리글")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.src and a.dst and a.title):
        ap.error("src dst title 이 필요하다")

    md = open(a.src, encoding="utf-8").read()
    bad = check_forbidden(md)
    if bad:
        print("공개 금지 정보가 있어 렌더하지 않는다: " + " · ".join(bad), file=sys.stderr)
        return 1
    page = build(md, a.title, a.kick, a.md_link)
    os.makedirs(os.path.dirname(a.dst) or ".", exist_ok=True)
    open(a.dst, "w", encoding="utf-8", newline="").write(page)
    print("%s → %s (%d bytes · 표 %d개 · 확인필요 %d건)"
          % (a.src, a.dst, len(page), page.count("<table>"), md.count("확인필요")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
