#!/usr/bin/env python3
"""proposal_lint — 글 규칙(writing.md)과 슬라이드 계획 규칙(deck.md §2·§5)을 **정규식으로** 검사한다. LLM 없음.

한준 2026-09-05: "상용 반복 사용 가능한 키트"가 되려면 어느 기계에서 누가 돌려도 같은 답이 나와야 한다.
비판자 에이전트(proposal-critic)는 사람처럼 읽고 판단하지만, 낱말·길이·빈도처럼 셀 수 있는 것은 여기서 먼저 센다.
비판자는 이 결과를 받아 「왜 그런가·어떻게 고치나」에 집중한다.

■ 사용
  python3 proposal_lint.py bids/<사업>/04_제안서_v3.md              # 초안(text 모드 자동)
  python3 proposal_lint.py bids/<사업>/07_슬라이드계획_v1.md --plan  # 슬라이드 계획
  python3 proposal_lint.py 04_제안서_v3.md --json                   # 기계용
  python3 proposal_lint.py --selftest
  종료코드: 심각도 「상」이 하나라도 있으면 1, 아니면 0. (bid-loop P4-검토·P6-계획의 출구 조건으로 쓴다)

■ 검사 코드 (writing.md 「AI 티 세 층」과 deck.md §2·§5에 대응)
  낱말  L1 번역투 · L2 공문투·명사형 종결 · L3 빈 수사 · L4 RFP 금지 표현(~할 수도 있다·~이 가능하다·~을 고려하고 있다)
  리듬  L5 문장 40자 초과(절 첫 문단 · 60자 초과는 어디서나) · L6 같은 길이 문장 5연속 · 「세 가지」 강박 · L7 문단마다 반복 동사
  구조  L8 문두 접속사·담화표지·되풀이 결론
  형식  L9 마크다운 표(fig 블록으로 바꿔야) · L10 출처 번호 [n]·03a 파일 · L11 공개 금지·내부 표기 · L12 fig JSON 깨짐
  L13 내부 조어(덩이·색채 카드·걷는 점·제목 사슬·레이아웃 가족·그 셋/넷) — 화면·본문에 새면 「중」
  L14 페인포인트(03a)의 출처(재료 파일·검색엔진을 출처로 적었거나 출처 열이 비었거나 없으면 「상」 · writing.md §2)
  계획  P1 디자인 브리프 · P2 제목 사슬(명사형·가리키기·40자) · P3 같은 증거 유형 연속 3장 · P4 고스트 덱 표(증거 유형·증거 출처 열, 증거 빈칸) · P5 RFP 대응표 빈칸 · P7 재료 점검 절 · P8 반대 의견 대응표 · P9 승인 절(승인자·일시·고스트 덱 승인)
  게이트(상)는 RFP·증거 관련(L4 금지 표현 · L11 공개 금지 · L12 fig 깨짐 · L14 페인포인트 출처 · P5 대응표 빈칸 · P4 증거 열 없음/증거 빈칸 · P7 재료 점검 없음 · P9 승인 없음)만. 디자인 항목(P1·P3)은 「중」 — 경향 조절용(한준 2026-09-05 "하드게이트로 하면 글 문서가 된다")
"""
import argparse
import json
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import figures_svg  # fig 블록 파싱
except Exception:  # noqa: BLE001
    figures_svg = None
try:
    import render_html  # 공개 금지 패턴
except Exception:  # noqa: BLE001
    render_html = None

SEV_ORDER = {"상": 0, "중": 1, "하": 2}

# ── 낱말 ─────────────────────────────────────────────────────────────────────────
L1_TRANSLATIONESE = [
    (r"[을를] 통해", "~을 통해 → ~로/~해서/~함으로써"),
    (r"통하여", "통하여 → ~로"),
    (r"에 대(한|하여|해)\b", "~에 대한 → 목적격으로 바로"),
    (r"에 있어(서)?\b", "~에 있어 → ~에서/~할 때"),
    (r"라는 점에서", "~라는 점에서 → ~라서"),
    (r"(되어진|지게 된|되어지)", "이중 피동 → 능동이나 단일 피동"),
    (r"가지고 있", "가지고 있다 → ~이 있다"),
    (r"에 의(해|하여)\b", "~에 의해 → 행위자를 주어로"),
    (r"적인 측면에서", "~적인 측면에서 → ~에서"),
    (r"하는 것이 가능", "~하는 것이 가능하다 → ~할 수 있다"),
]
L2_BUREAU = [
    (r"진행하였습니다|진행하였다", "진행하였습니다 → 했습니다"),
    (r"반영이 필요", "반영이 필요합니다 → 고쳐야 합니다"),
    (r"할 필요가 있", "~할 필요가 있다 → ~해야 한다"),
    (r"[을를] 통한 .{1,12}의 (극대화|제고|강화|향상)", "명사 사슬 → 동사로 푼다"),
]
# 명사형 종결: 문장이 이런 낱말로 끝나면(마침표 유무 무관) 개조식이다. 표 안·제목·코드는 검사에서 뺀다.
L2_NOUN_END = re.compile(r"(구축|제공|마련|확보|수행|추진|강화|지원|실시|도입|적용|운영|관리|개발|제작|납품|확대|개선|제고|향상|극대화)\s*[.。]?\s*$")
L3_EMPTY = ["최적의", "최고의", "차별화된", "혁신적인", "선도적인", "체계적인", "전문적인", "고품질", "완벽한", "원스톱", "시너지",
            "토탈 솔루션", "풍부한 경험", "다년간의 노하우", "만족도 극대화", "성공적으로 수행", "효과적으로", "적극적으로", "다양한"]
L4_RFP_FORBID = [
    (r"할 수도 있", "「~할 수도 있다」는 RFP가 불가능으로 간주"),
    (r"가능(하다|합니다|함)\b", "「~이 가능하다」는 RFP가 불가능으로 간주 → ~합니다"),
    (r"고려하고 있", "「~을 고려하고 있다」는 RFP가 불가능으로 간주"),
]
# ── 구조 ─────────────────────────────────────────────────────────────────────────
L8_CONJ = re.compile(r"^(또한|그리고|따라서|특히|이를 통해|그러므로|아울러|더불어|한편|즉)[,\s]")
L8_MARKER = re.compile(r"(중요한 것은|핵심은|무엇보다|주목할 점은)")
L8_RECAP = re.compile(r"^(결국|요컨대|정리하면|결론적으로|이처럼)")
L7_VERBS = re.compile(r"(제공합니다|지원합니다|구현합니다|확보합니다|수행합니다|추진합니다|강화합니다)")

SENT_SPLIT = re.compile(r"(?<=[.!?。])\s+|(?<=다\.)|(?<=요\.)")


def _is_table(line):
    return line.lstrip().startswith("|")


def _is_heading(line):
    return line.lstrip().startswith("#")


def _strip_md(s):
    s = re.sub(r"`[^`]*`", "", s)
    s = re.sub(r"\*\*|__|\*|~~", "", s)
    s = re.sub(r"\[(\d+)\]", "", s)          # 출처 번호는 길이에서 뺀다
    s = re.sub(r"\(근거:[^)]*\)", "", s)       # 근거 표기도
    return s.strip()


def _sentences(text):
    out = []
    for raw in SENT_SPLIT.split(text):
        s = raw.strip()
        if len(s) >= 4:
            out.append(s)
    return out


def _blocks(md):
    """(줄 번호, 종류, 원문) — 종류: fig · code · table · heading · text · blank. fig/code 안은 검사에서 뺀다."""
    out, i, lines = [], 0, md.split("\n")
    in_code, code_kind = False, None
    for ln, line in enumerate(lines, 1):
        st = line.strip()
        if st.startswith("```"):
            if not in_code:
                in_code, code_kind = True, ("fig" if st.startswith("```fig") else "code")
                out.append((ln, code_kind, line))
            else:
                in_code, code_kind = False, None
                out.append((ln, "code_end", line))
            continue
        if in_code:
            out.append((ln, code_kind, line))
            continue
        kind = "blank" if not st else "heading" if _is_heading(line) else "table" if _is_table(line) else "text"
        out.append((ln, kind, line))
    return out


def lint_text(md, path=""):
    """초안 검사. 반환: [{"line", "sev", "code", "msg", "src"}]"""
    F = []

    def add(line, sev, code, msg, src=""):
        F.append({"line": line, "sev": sev, "code": code, "msg": msg, "src": _strip_md(src)[:70]})

    blocks = _blocks(md)
    # L13 내부 조어 — 줄 단위(코드 블록 제외)
    JARGON = re.compile(r"덩이|색채 카드|걷는 점|제목 사슬|레이아웃 가족|그 (셋|넷|다섯)(은|이|을|도)")
    in_code = False
    for ln, line in enumerate(md.split("\n"), 1):
        if line.strip().startswith("```"): in_code = not in_code; continue
        if in_code or line.startswith("#"): continue
        m13 = JARGON.search(line)
        if m13: add(ln, "중", "L13", "내부 조어 「%s」 — 발주처 앞에서 쓰는 말이 아니다(writing.md §4)" % m13.group(0), line)
    # 문단 묶기(text 줄이 연속되면 한 문단) · 절(heading) 경계
    paras, cur, cur_ln = [], [], None
    after_heading, skip_sec = False, False
    SKIP_SEC = re.compile(r"참고문헌|확인필요 목록|목차|약어")
    for ln, kind, line in blocks:
        if kind == "heading":
            after_heading = True
            skip_sec = bool(SKIP_SEC.search(line))
        if kind == "text" and skip_sec:
            continue                                   # 출처 목록·확인필요 목록은 문장이 아니다
        if kind == "text":
            if not cur:
                cur_ln = ln
            cur.append(_strip_md(line))
        elif cur:
            paras.append((cur_ln, " ".join(cur), after_heading))
            cur, after_heading = [], False
    if cur:
        paras.append((cur_ln, " ".join(cur), after_heading))

    # L1~L4 · L2 명사형 종결 — text 줄만
    for ln, kind, line in blocks:
        if kind != "text":
            continue
        s = _strip_md(line)
        for pat, msg in L1_TRANSLATIONESE:
            if re.search(pat, s):
                add(ln, "중", "L1", "번역투: " + msg, s)
        for pat, msg in L2_BUREAU:
            if re.search(pat, s):
                add(ln, "중", "L2", "공문투: " + msg, s)
        body = re.sub(r"^[-*•·]\s*|^\d+[.)]\s*", "", s)       # 불릿 기호 제거 후 끝을 본다
        if L2_NOUN_END.search(body) and not body.endswith(("다.", "다", "요.", "까?", "니다.")):
            add(ln, "중", "L2", "명사형 종결(개조식) → 「~합니다」 완전한 문장으로", s)
        for w in L3_EMPTY:
            if w in s:
                add(ln, "중", "L3", "빈 수사 「%s」 → 수치·사례·번호로" % w, s)
        for pat, msg in L4_RFP_FORBID:
            if re.search(pat, s):
                add(ln, "상", "L4", msg, s)
        if L8_MARKER.search(s):
            add(ln, "하", "L8", "담화표지 → 지우고 근거로", s)
        if L8_RECAP.match(body):
            add(ln, "하", "L8", "되풀이 결론 문두(결국·요컨대…) → 지우고 그 자리에 숫자·사례", s)

    # L5~L8 — 문단 단위
    three_cnt = len(re.findall(r"세 가지|세 문장|셋입니다|3가지", md))
    if three_cnt > 3:
        add(0, "중", "L6", "「세 가지」 강박: %d회 — 둘이나 넷으로 바꾸거나 나열을 푼다" % three_cnt)
    ordinal_secs = len(re.findall(r"첫째", md))
    if ordinal_secs > 2:
        add(0, "하", "L6", "「첫째·둘째」 나열이 %d곳 — 절마다 같은 틀" % ordinal_secs)
    for ln, text, first in paras:
        sents = _sentences(text)
        for s in sents:
            n = len(s)
            if first and n > 40:
                add(ln, "중", "L5", "절 첫 문단 문장 %d자(40자 상한) — 낭독 검사" % n, s)
            elif n > 60:
                add(ln, "하", "L5", "문장 %d자 — 둘로 나눈다" % n, s)
        lens = [len(s) for s in sents]
        for i in range(len(lens) - 4):
            w = lens[i:i + 5]
            if max(w) - min(w) <= 6:
                add(ln, "중", "L6", "같은 길이 문장 5연속(%s자) — 짧은 문장 하나를 긴 문장 뒤에" % "·".join(map(str, w)))
                break
        verbs = L7_VERBS.findall(text)
        for v in set(verbs):
            if verbs.count(v) >= 2:
                add(ln, "중", "L7", "한 문단에 「%s」 %d회 — 그 일을 실제로 하는 동사로(만듭니다·잽니다·짭니다)" % (v, verbs.count(v)))
        conj = sum(1 for s in sents if L8_CONJ.match(s))
        if conj > 1:
            add(ln, "하", "L8", "문두 접속사 %d개(문단당 1 이하) — 지우고 문장 순서로 관계를 보인다" % conj)

    # L9 마크다운 표 (fig 밖)
    seen_tbl = set()
    for ln, kind, line in blocks:
        if kind == "table" and re.search(r"\|\s*-{3,}", line):
            if ln not in seen_tbl:
                add(ln - 1, "중", "L9", "마크다운 표 → ```fig table(또는 matrix·spec·gantt)로 (deck.md §3)")
                seen_tbl.add(ln)

    # L10 출처
    cites = len(set(re.findall(r"\[(\d+)\]", md)))
    if cites == 0:
        add(0, "하", "L10", "출처 번호 [n]이 하나도 없다 — 발주처 사실에는 03a_페인포인트.md 번호를 단다")
    if path:
        d = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(os.path.join(d, "03a_페인포인트.md")):
            add(0, "중", "L10", "같은 폴더에 03a_페인포인트.md가 없다 — 페인포인트 없이 쓴 초안은 색채가 나오지 않는다(writing.md §2)")
    if not re.search(r"확인필요 목록", md):
        add(0, "하", "L10", "「확인필요 목록」 절이 없다 — ⚠️ 확인필요를 끝에 모아야 담당자가 채운다")

    # L14 재료 파일을 출처로 적은 페인포인트(03a) — 웹에서 긁어 온 재료를 확인 없이 사실로 옮기는 실수
    if path and "페인포인트" in os.path.basename(path):
        BADSRC = re.compile(r"03a_raw|duckduckgo|ddgs|검색\s*결과|검색결과", re.I)
        src_seen = False
        for tln, head, rows in _tables(md):
            si = _col(head, "출처")
            if si is None:
                continue
            src_seen = True
            for r_i, r in enumerate(rows):
                cell = _strip_md(r[si]).strip() if si < len(r) else ""
                if not cell or cell in ("-", "—"):
                    add(tln + 2 + r_i, "상", "L14", "발주처 사실에 출처가 비었다 — 원 페이지 주소와 날짜를 적는다(writing.md §2). 재료(03a_raw)는 출처가 아니다")
                elif BADSRC.search(cell):
                    add(tln + 2 + r_i, "상", "L14", "출처에 재료 파일·검색엔진(%s)이 적혔다 — 그 페이지를 열어 확인한 원 주소·날짜로 바꾼다(writing.md §2)" % cell[:30], cell)
        if not src_seen:
            add(0, "상", "L14", "페인포인트 표에 「출처」 열이 없다 — 발주처 사실마다 원 페이지 주소·날짜 열이 있어야 한다(writing.md §2)")

    # L11 공개 금지 · 내부 표기 수
    if render_html is not None:
        for why in render_html.check_forbidden(md):
            add(0, "상", "L11", "공개 금지 정보: " + why)
    need = md.count("⚠️")
    if need:
        add(0, "하", "L11", "⚠️ 확인필요 %d곳 — 제출 전 0이어야 한다(목록에 모여 있으면 정상)" % need)

    # L12 fig JSON
    if figures_svg is not None:
        for ln, src, fig, err in figures_svg.find_blocks(md):
            if fig is None:
                add(ln, "상", "L12", "fig 블록 JSON 깨짐: " + err)
            elif not fig.get("type"):
                add(ln, "상", "L12", "fig 블록에 type이 없다")
    return F


# ── 슬라이드 계획 ─────────────────────────────────────────────────────────────────
def _tables(md):
    """마크다운 표를 [(시작줄, 머리[], 행[[셀]])]로."""
    out, lines = [], md.split("\n")
    i = 0
    while i < len(lines):
        if _is_table(lines[i]) and i + 1 < len(lines) and re.search(r"\|\s*:?-{3,}", lines[i + 1]):
            head = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and _is_table(lines[j]):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            out.append((i + 1, head, rows))
            i = j
        else:
            i += 1
    return out


def _col(head, *keys):
    for k in keys:
        for i, h in enumerate(head):
            if k in h:
                return i
    return None


def lint_plan(md, path=""):
    F = []

    def add(line, sev, code, msg, src=""):
        F.append({"line": line, "sev": sev, "code": code, "msg": msg, "src": _strip_md(src)[:70]})

    # P1 브리프
    m = re.search(r"^#+.*브리프.*$", md, re.M)
    if not m:
        add(0, "중", "P1", "디자인 브리프 절이 없다(deck.md §5) — 시각 컨셉·팔레트·글자 단계·레이아웃 가족·여백 장·헤더 좌표")
    else:
        start = m.end()
        nxt = re.search(r"^#+ ", md[start:], re.M)
        brief = md[start:start + nxt.start()] if nxt else md[start:]
        for k in ("컨셉", "팔레트", "글자", "레이아웃", "여백", "헤더"):
            if k not in brief:
                add(md[:start].count("\n") + 1, "중", "P1", "브리프에 「%s」 항목이 없다" % k)
        if re.search(r"(볼류메트릭|ICVFX|디지털휴먼|메타버스|AI)\s*(기반|컨셉|중심)", brief):
            add(md[:start].count("\n") + 1, "중", "P1", "시각 컨셉이 기술 이름에서 나왔다 — 발주처·과업의 모티프로")

    # P2 제목 사슬
    m = re.search(r"^#+.*제목 사슬.*$", md, re.M)
    if not m:
        add(0, "상", "P2", "「제목 사슬」 절이 없다(deck.md §2) — 제목만 읽어 발표가 되게 먼저 쓴다")
    else:
        start = m.end()
        nxt = re.search(r"^#+ ", md[start:], re.M)
        sec = md[start:start + nxt.start()] if nxt else md[start:]
        titles = [re.sub(r"^\s*(\d+[.)]|[-*])\s*", "", t) for t in sec.split("\n") if re.match(r"^\s*(\d+[.)]|[-*])\s+", t)]
        for k, t in enumerate(titles, 1):
            tt = _strip_md(t)
            if len(tt) > 40:
                add(0, "하", "P2", "제목 %d이 %d자(40자 상한) — 근거 한 줄을 부제로" % (k, len(tt)), tt)
            if not re.search(r"(다|요|까|니다)\s*[.?!]?\s*$", tt) and not re.search(r"^(PART|Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|표지|목차)", tt):
                add(0, "중", "P2", "제목 %d이 명사형 — 한 문장 주장(~합니다)으로" % k, tt)
            if re.search(r"(장|절|뒤|아래|별지|부록)에서\s*(답|다룹|설명|말|보)", tt) or re.search(r"후술|참고하", tt):
                add(0, "중", "P2", "제목 %d이 다른 장을 가리킨다 — 그 장의 근거를 통합한 주장으로(deck.md §2-1 ①)" % k, tt)
        if len(titles) < 5:
            add(0, "중", "P2", "제목 사슬이 %d줄 — 본문 장 전부의 제목을 순서대로" % len(titles))

    # P3·P4 — 고스트 덱 표(deck.md §2-6): | 장 | 쪽번호 | 액션 타이틀 | 증거 유형 | 증거 출처 | 사진 | 노트 |
    tbls = _tables(md)
    plan_tbl = None
    for ln, head, rows in tbls:
        if _col(head, "제목", "타이틀", "슬라이드") is not None and (_col(head, "증거") is not None or _col(head, "유형", "레이아웃") is not None):
            plan_tbl = (ln, head, rows)
            break
    if plan_tbl is None:
        add(0, "상", "P3", "고스트 덱 표가 없다(열: 장 · 쪽번호 · 액션 타이틀 · 증거 유형 · 증거 출처 · 사진 · 노트 — deck.md §2-6)")
    else:
        ln, head, rows = plan_tbl
        ci = _col(head, "증거 유형")
        if ci is None:
            ci = _col(head, "증거")
        if ci is None:
            add(ln, "상", "P4", "「증거 유형」 열이 없다 — 장마다 주장 한 문장 + 증거 하나(deck.md §2-2). 문단을 배치하는 옛 서식이다")
            ci = _col(head, "유형", "레이아웃")
        else:
            si = _col(head, "출처")
            if si is None:
                add(ln, "중", "P4", "「증거 출처」 열이 없다 — 출처 없는 증거는 만들지 않는다(deck.md §2-2)")
            ti0 = _col(head, "제목", "타이틀")
            empty = []
            kinds = []
            for r_i, r in enumerate(rows):
                t = _strip_md(r[ti0]) if ti0 is not None and ti0 < len(r) else ""
                if re.search(r"^(PART|표지|목차|약어|참고문헌)", t) or re.search(r"(표지|목차|PART|약어|참고)", r[ci] if ci < len(r) else ""):
                    continue
                v = _strip_md(r[ci]).strip() if ci < len(r) else ""
                if not v or v in ("-", "—"):
                    empty.append(str(r_i + 1))
                kinds.append(v)
                if si is not None and si < len(r) and not _strip_md(r[si]).strip().strip("-—"):
                    add(ln + 2 + r_i, "중", "P4", "증거 출처가 비었다 — 사진 파일·재료 팩 §·페인포인트 #·03b 카드 #", t)
            if empty:
                add(ln, "상", "P4", "증거가 없는 본문 장 %d개(표 행 %s) — 그 장은 아직 장이 아니다(deck.md §2-2)" % (len(empty), ",".join(empty[:10])))
            tables = sum(1 for k in kinds if k.startswith("표"))
            if kinds and tables > len(kinds) / 2:
                add(ln, "중", "P3", "증거의 절반 넘게 표(%d/%d) — 표 몇 개를 사진·지도·연결도·큰 숫자로(deck.md §2-4)" % (tables, len(kinds)))
        if ci is not None:
            run, prev = 1, None
            for r_i, r in enumerate(rows):
                v = _strip_md(r[ci]).strip() if ci < len(r) else ""
                if v and v == prev:
                    run += 1
                    if run == 3:
                        add(ln + 2 + r_i, "중", "P3", "같은 증거 유형 「%s」 연속 3장 — 순서를 바꾸거나 다른 증거로(deck.md §2-4 경향)" % v)
                else:
                    run = 1
                prev = v or prev
        ti = _col(head, "제목", "타이틀")
        for r_i, r in enumerate(rows):
            if ti is not None and ti < len(r):
                t = _strip_md(r[ti])
                if t and not re.search(r"(다|요|까|니다)\s*[.?!]?\s*$", t) and not re.search(r"^(PART|표지|목차|약어|참고문헌|마무리)", t) and not re.search(r"(표지|목차|PART|구분|약어|참고)", r[ci] if (ci is not None and ci < len(r)) else ""):
                    add(ln + 2 + r_i, "중", "P2", "본문 장 제목이 명사형", t)
    # P7 재료 점검 · P8 반대 의견 대응표 (deck.md §0 · §2-5)
    if not re.search(r"^#+.*재료 점검", md, re.M):
        add(0, "상", "P7", "「재료 점검」 절이 없다 — 결정 한 문장·반대 셋·발주처 사진 6·우리 실물 6·숫자 5·색채 카드 8(deck.md §0). 없으면 덱을 만들지 않는다")
    if not re.search(r"^#+.*반대 의견", md, re.M):
        add(0, "중", "P8", "「반대 의견 대응표」가 없다 — 반대 셋이 각각 어느 장에서 답해지는지(deck.md §2-5)")
    rfp_tbl = None
    for ln, head, rows in tbls:
        if _col(head, "요구", "ID", "품목") is not None and _col(head, "슬라이드", "대응") is not None:
            rfp_tbl = (ln, head, rows)
    if rfp_tbl is None:
        add(0, "상", "P5", "RFP 요구 ID 대응표가 없다(deck.md §2-3) — 요구 ID·품목 전부에 슬라이드 번호")
    else:
        ln, head, rows = rfp_tbl
        si = _col(head, "슬라이드", "대응")
        empty = [ln + 2 + i for i, r in enumerate(rows) if si >= len(r) or not r[si].strip() or r[si].strip() in ("-", "—", "")]
        if empty:
            add(empty[0], "상", "P5", "대응 슬라이드가 빈 요구 항목 %d개(줄 %s) — 장을 추가하거나 「해당사항 없음」 장에" % (len(empty), ",".join(map(str, empty[:8]))))
    # P9 승인 절 — 고스트 덱은 사람 승인 뒤에만 Figma로 간다(deck.md §2-6)
    # 제목이 「승인」으로 시작하는 절만 본다(「고스트 덱(…승인되기 전에는…)」 같은 제목은 아니다)
    m = re.search(r"^#+\s*승인", md, re.M)
    if not m:
        add(0, "상", "P9", "「승인」 절이 없다(deck.md §2-6) — 승인자·일시·「고스트 덱 승인」 문구가 있어야 P6-시안으로 간다")
    else:
        start = m.end()
        nxt = re.search(r"^#+ ", md[start:], re.M)
        sec = md[start:start + nxt.start()] if nxt else md[start:]
        line_no = md[:m.start()].count("\n") + 1
        if "고스트 덱 승인" not in sec:
            add(line_no, "상", "P9", "승인 절에 「고스트 덱 승인」 문구가 없다 — 무엇을 승인했는지 한 줄로 남긴다")
        if not re.search(r"승인자", sec):
            add(line_no, "상", "P9", "승인 절에 승인자가 없다 — 승인한 사람을 적는다")
        if not re.search(r"일시|날짜|\d{4}-\d{2}-\d{2}", sec):
            add(line_no, "상", "P9", "승인 절에 일시가 없다 — 승인 날짜를 적는다")

    # 목차 쪽번호
    for ln, kind, line in _blocks(md):
        if kind in ("text", "table") and "목차" in line and re.search(r"[Pp]\.\s*\d|\d+\s*~\s*\d+\s*(쪽|p)", line):
            add(ln, "중", "P6", "목차에 쪽번호가 적혔다 — 한준 2026-09-04 「목차에는 페이지 번호를 넣지 마」", line)
    # 내부 표기
    if render_html is not None:
        for why in render_html.check_forbidden(md):
            add(0, "상", "L11", "공개 금지 정보: " + why)
    return F


# ── 출력 ─────────────────────────────────────────────────────────────────────────
def report(F, path, as_json=False):
    F = sorted(F, key=lambda f: (SEV_ORDER[f["sev"]], f["line"]))
    if as_json:
        print(json.dumps({"file": path, "findings": F, "counts": _counts(F)}, ensure_ascii=False, indent=1))
        return
    for f in F:
        where = "%4d줄" % f["line"] if f["line"] else "  문서"
        print("%s [%s] %s %s%s" % (where, f["sev"], f["code"], f["msg"], ("  ← " + f["src"]) if f["src"] else ""))
    c = _counts(F)
    print("— %s: 상 %d · 중 %d · 하 %d%s" % (os.path.basename(path) if path else "", c["상"], c["중"], c["하"],
                                          "  (상이 있으면 다음 스텝으로 못 간다)" if c["상"] else "  ✓ 통과"))


def _counts(F):
    return {k: sum(1 for f in F if f["sev"] == k) for k in ("상", "중", "하")}


def selftest():
    fails, n = [], [0]

    def ok(name, cond):
        n[0] += 1
        if not cond:
            fails.append(name)

    codes = lambda F: {f["code"] for f in F}  # noqa: E731
    bad = ("# 1. 개요\n\n저희는 최적의 솔루션을 통해 고객에 대한 만족도 극대화를 진행하였습니다. 이는 시스템 구축.\n"
           "기능 확장이 가능합니다.\n\n| 항목 | 값 |\n|---|---|\n| a | b |\n\n```fig\n{깨짐\n```\n")
    F = lint_text(bad)
    ok("L1 번역투", "L1" in codes(F))
    ok("L2 공문투·명사형", "L2" in codes(F))
    ok("L3 빈 수사", "L3" in codes(F))
    ok("L4 RFP 금지(상)", any(f["code"] == "L4" and f["sev"] == "상" for f in F))
    ok("L9 표", "L9" in codes(F))
    ok("L12 fig 깨짐", "L12" in codes(F))
    ok("L10 출처 없음", "L10" in codes(F))
    ok("L13 내부 조어", "L13" in codes(lint_text("# a\n\n시스템 네 덩이가 다 있어야 합니다. 그 셋은 실적입니다.\n")))
    good = ("# Ⅰ. 제안개요\n\n전시관에는 지금 다시 보여 줄 장면이 없습니다[1]. 2025년 3월에 문을 열었습니다.\n\n"
            "```fig\n{\"type\": \"stats\", \"items\": [{\"n\": \"3층\", \"label\": \"강의실\"}]}\n```\n\n## 확인필요 목록\n- 없음\n")
    G = lint_text(good)
    ok("좋은 글은 상·중 없음", not any(f["sev"] in ("상", "중") for f in G))
    rhythm = "# a\n\n첫 문장은 열두 자입니다. 둘째 문장도 열두 자입니다. 셋째 문장도 열두 자입니다. 넷째 문장도 열두 자입니다. 다섯 문장도 열두 자입니다.\n"
    ok("L6 같은 길이 5연속", "L6" in codes(lint_text(rhythm)))
    verbs = "# a\n\n저희는 화면을 제공합니다. 그리고 매뉴얼도 제공합니다. 또한 교육을 제공합니다.\n"
    Fv = lint_text(verbs)
    ok("L7 반복 동사", "L7" in codes(Fv))
    ok("L8 문두 접속사", "L8" in codes(Fv))
    longf = "# 절\n\n이 문장은 절의 첫 문단에 있는데 마흔 자를 훌쩍 넘겨서 심사장에서 소리 내어 읽으면 숨이 차게 되는 문장입니다.\n"
    ok("L5 첫 문단 40자", any(f["code"] == "L5" and f["sev"] == "중" for f in lint_text(longf)))
    ok("공개 금지(상)", render_html is None or any(f["code"] == "L11" and f["sev"] == "상" for f in lint_text("# a\n\n서버는 100.64.0.1 입니다.\n")))
    plan_bad = ("# 계획\n\n## 제목 사슬\n1. 사업 개요\n2. 추진 전략\n\n| 장 | 제목 | 유형 | 문단 |\n|---|---|---|---|\n| 1 | 사업 개요 | 카드 | 1 |\n| 2 | 추진 전략 | 카드 | 2 |\n| 3 | 기대 효과 | 카드 | 4 |\n")
    plan_bad2 = ("# 계획\n\n## 재료 점검\n- 결정: x\n\n## 제목 사슬\n1. 전시관은 한 곳이 아니라 세 곳입니다\n\n| 장 | 액션 타이틀 | 증거 유형 | 증거 출처 |\n|---|---|---|---|\n| 1 | 전시관은 한 곳이 아니라 세 곳입니다 | | |\n| 2 | 장비는 6품목 다 맞춥니다 | 표 | 재료 팩 §3 |\n| 3 | 일정은 13주입니다 | 표 | 재료 팩 §3 |\n| 4 | 검수는 전시관에서 합니다 | 표 | 03a #2 |\n")
    P = lint_plan(plan_bad)
    ok("P1 브리프 없음", "P1" in codes(P))
    ok("P2 명사형 제목", "P2" in codes(P))
    ok("P3 연속 3장", any(f["code"] == "P3" and f["sev"] == "중" for f in lint_plan(plan_bad2)))
    ok("P4 증거 열 없음(상)", any(f["code"] == "P4" and f["sev"] == "상" for f in P))
    ok("P4 증거 빈칸(상)", any(f["code"] == "P4" and f["sev"] == "상" and "증거가 없는" in f["msg"] for f in lint_plan(plan_bad2)))
    ok("P7 재료 점검 없음(상)", any(f["code"] == "P7" and f["sev"] == "상" for f in P))
    ok("P8 반대 의견 없음", "P8" in codes(P))
    ok("P5 대응표 없음", "P5" in codes(P))
    plan_good = ("# 계획\n\n## 재료 점검\n- 결정: 협상 1순위\n- 반대 셋: a→3 b→4 c→2\n\n## 디자인 브리프\n- 시각 컨셉: 강의실에서 골목으로 걸어 나가는 동선\n- 팔레트: #0068B0 · 진한 · 옅은\n- 글자 단계: 48/22/19/13\n"
                 "- 레이아웃 가족: 전면 사진 / 좌 도식 / 표 전폭\n- 여백 장: Ⅰ-2 · Ⅱ-5\n- 헤더 좌표: x96 y48\n\n## 제목 사슬\n"
                 "1. 전시관에는 지금 다시 보여 줄 장면이 없습니다\n2. 그런데 전시관은 한 곳이 아니라 세 곳 전체입니다\n3. 그래서 손대지 않아도 맞아 있는 전시관을 만듭니다\n4. 장비는 6품목 전부 맞춥니다\n5. 13주에 검수합니다\n\n"
                 "| 장 | 쪽번호 | 액션 타이틀 | 증거 유형 | 증거 출처 | 사진 | 노트 |\n|---|---|---|---|---|---|---|\n| 1 | — | 표지 | 사진 | MANIFEST 1 | 외관 | — |\n| 2 | Ⅰ-1 | 전시관에는 지금 다시 보여 줄 장면이 없습니다 | 사진 | MANIFEST 2 | 간판 | 1-2 |\n| 3 | Ⅰ-2 | 그런데 전시관은 세 곳 전체입니다 | 큰 숫자 | 03a #1 | — | 3 |\n| 4 | Ⅰ-3 | 그래서 손대지 않아도 맞아 있는 전시관을 만듭니다 | 지도 | 03b 카드 2 | — | 4-5 |\n\n## 반대 의견 대응표\n| 반대 | 답하는 장 |\n|---|---|\n| a | 3 |\n\n"
                 "## RFP 요구 대응표\n| 요구 ID | 대응 슬라이드 |\n|---|---|\n| 기획-001 | 3 |\n| 기능-001 | 4 |\n\n"
                 "## 승인\n- 고스트 덱 승인\n- 승인자: 사업총괄\n- 일시: 2026-09-20\n")
    G = lint_plan(plan_good)
    ok("좋은 계획은 상 없음", not any(f["sev"] == "상" for f in G))
    ok("P2 가리키기 제목", any("가리킨다" in f["msg"] for f in lint_plan(plan_good.replace("5. 13주에 검수합니다", "5. 품질 여섯 항목은 Ⅲ장에서 답합니다"))))
    ok("P6 목차 쪽번호", "P6" in codes(lint_plan(plan_good + "\n목차: Ⅰ 제안개요 P.03~09\n")))
    ok("P9 승인 절 없음(상)", any(f["code"] == "P9" and f["sev"] == "상" for f in P))
    ok("P9 승인 있으면 없음", "P9" not in codes(G))
    ok("P9 문구·승인자·일시 빠짐(상)", any(f["code"] == "P9" and f["sev"] == "상" for f in lint_plan(plan_good.replace("- 고스트 덱 승인\n- 승인자: 사업총괄\n- 일시: 2026-09-20\n", "- 얼른 넘어가기\n"))))
    # L14 페인포인트 출처
    l14_bad = "# 03a\n\n| # | 발주처 사실 | 출처 | RFP 연결 |\n|---|---|---|---|\n| 1 | 관람객이 줄었다 | 03a_raw #3 | 기획 25 |\n| 2 | 담당이 둘이다 | | 운영 15 |\n"
    L14b = lint_text(l14_bad, "bids/x/03a_페인포인트.md")
    ok("L14 재료 파일을 출처로(상)", any(f["code"] == "L14" and f["sev"] == "상" for f in L14b))
    ok("L14 출처 빈칸(상)", sum(1 for f in L14b if f["code"] == "L14" and f["sev"] == "상") >= 2)
    l14_nocol = "# 03a\n\n| # | 발주처 사실 | RFP 연결 |\n|---|---|---|\n| 1 | 관람객이 줄었다 | 기획 25 |\n"
    ok("L14 출처 열 없음(상)", any(f["code"] == "L14" and f["sev"] == "상" for f in lint_text(l14_nocol, "bids/x/03a_페인포인트.md")))
    l14_good = "# 03a\n\n| # | 발주처 사실 | 출처(링크·날짜) | RFP 연결 |\n|---|---|---|---|\n| 1 | 관람객이 줄었다 | 시의회 회의록 2025-11(링크) | 기획 25 |\n"
    ok("L14 좋은 출처는 없음", "L14" not in codes(lint_text(l14_good, "bids/x/03a_페인포인트.md")))
    ok("L14 페인포인트 아닌 파일은 검사 안 함", "L14" not in codes(lint_text(l14_bad, "bids/x/04_제안서_v1.md")))
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — %d건 통과(낱말·리듬·구조·형식·계획)" % n[0])
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="제안서 초안·슬라이드 계획 정규식 검사(LLM 없음)")
    ap.add_argument("src", nargs="?")
    ap.add_argument("--plan", action="store_true", help="07_슬라이드계획 모드(파일명에 「계획」이 있으면 자동)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.src:
        ap.error("src 가 필요하다")
    md = open(a.src, encoding="utf-8").read()
    plan = a.plan or "계획" in os.path.basename(a.src)
    F = lint_plan(md, a.src) if plan else lint_text(md, a.src)
    report(F, a.src, a.json)
    return 1 if any(f["sev"] == "상" for f in F) else 0


if __name__ == "__main__":
    sys.exit(main())
