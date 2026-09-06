#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_check.py — 사업 폴더(bids/<사업>)를 읽어 **자료가 얇은 곳**을 기계로 찾고, Claude가 사용자에게 물을 질문서 초안을 만든다.
`references/asking.md` §2 카탈로그의 「결손 신호(기계)」 열을 구현한다. 문장·판단은 Claude가 한다 — 이 스크립트는 빈칸을 세기만 한다.

사용:  python3 gap_check.py bids/<사업> [--phase P0|P3.5|P4|P6|P7|auto] [--out logs/질문_P6.md]
       종료코드 0=질문 없음 · 1=질문 있음 · 2=오류.   --selftest 오프라인 자체 검사.
--phase auto(기본)는 `_STATE.md`의 현재단계·상태로 단계를 고른다. 폴더에 없는 문서는 건너뛴다(그 단계가 아직이면 결손이 아니다).
"""
import io, os, re, sys, tempfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

WARN = "⚠️ 확인필요"


def rd(p):
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return None


def latest(folder, prefix):
    """04_제안서_v3.md 처럼 판이 여러 개면 가장 큰 N."""
    best, bn = None, -1
    for f in os.listdir(folder):
        m = re.match(re.escape(prefix) + r"_?v?(\d+)\.md$", f) or (re.match(re.escape(prefix) + r"\.md$", f) and re.match(r"()", ""))
        if m:
            n = int(m.group(1)) if m.group(1) else 0
            if n > bn:
                best, bn = os.path.join(folder, f), n
    return best


def table_rows(md, header_word):
    """header_word 를 포함한 표 머리 아래의 데이터 행(구분선 제외)을 돌려준다."""
    rows, on = [], False
    for line in md.splitlines():
        if line.startswith("|") and header_word in line and not on:
            on = True
            continue
        if on:
            if not line.startswith("|"):
                break
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


def q(qs, phase, what, why, form, tried=None, blocking=False):
    qs.append({"phase": phase, "what": what, "why": why, "form": form, "tried": tried or "", "blocking": blocking})


# ---------- 단계별 검사 ----------
def check_p0(folder, qs):
    md = rd(os.path.join(folder, "00_재료팩.md"))
    if md is None:
        return
    heads = re.findall(r"^## (\d)\.\s*(.+)$", md, re.M)
    if len(heads) < 10:
        q(qs, "P0", "재료 팩에 절이 %d개뿐입니다(열 개 필요). 빠진 절: %s" % (len(heads), ", ".join(str(i) for i in range(10) if str(i) not in [h[0] for h in heads])),
          "열 절이 다 있어야 P1 평가표를 원문 그대로 옮길 수 있습니다", "붙여넣기", "재료 팩 페이지·RFP 원문(추출)", blocking=True)
    # 절별 내용 길이
    parts = re.split(r"^## (\d)\.\s*(.+)$", md, flags=re.M)
    for i in range(1, len(parts) - 2, 3):
        num, title, body = parts[i], parts[i + 1].strip(), parts[i + 2]
        body_clean = re.sub(r"^>.*$", "", body, flags=re.M)               # 「어디서 채우나」 안내 제거
        body_clean = re.sub(r"[|\-:\s\[\]]", "", body_clean)
        if len(body_clean) < 12:
            q(qs, "P0", "재료 팩 §%s 「%s」이 비어 있습니다" % (num, title), "이 절 없이는 그 항목을 「[RFP에 명시 없음]」으로 둬야 합니다", "값·붙여넣기", "재료 팩 페이지", blocking=True)
    n_warn = md.count(WARN)
    if n_warn:
        items = re.findall(re.escape(WARN) + r"\s*[—:-]?\s*([^\n|]+)", md)
        q(qs, "P0", "재료 팩에 「확인필요」가 %d곳 있습니다: %s" % (n_warn, " · ".join(x.strip() for x in items[:6])), "값을 채워야 초안에서 빈칸이 안 남습니다", "값", "재료 팩 §8")
    stamps = re.findall(r"판본:\s*(\S+)", md)
    rfp = rd(os.path.join(folder, "00_RFP원문_추출.md"))
    if rfp:
        s2 = re.findall(r"판본:\s*(\S+)", rfp)
        if stamps and s2 and stamps[0] != s2[0]:
            q(qs, "P0", "재료 팩 판본(%s)과 RFP 원문 판본(%s)이 다릅니다" % (stamps[0], s2[0]), "다른 판을 섞으면 배점·요구 ID가 어긋납니다", "어느 판이 맞는지 택일", "두 페이지의 판본 도장", blocking=True)
    allmd = " ".join(filter(None, (rd(os.path.join(folder, f)) for f in os.listdir(folder) if f.endswith(".md"))))
    for word, ask, why in (
        ("이전 제안서", "이 발주처나 유사 과업에 우리가 낸 **이전 제안서**가 있습니까", "있으면 색채 카드와 실적 사진을 바로 얻고, 그때 안 통한 것을 피할 수 있습니다"),
        ("담당자", "발주처 **담당자와 통화·현장 설명회** 메모가 있습니까", "담당자가 한 말은 페인포인트 중 가장 센 출처입니다"),
        ("경쟁사", "이번에 붙을 **경쟁사**로 누가 예상됩니까", "경쟁사 표준 답을 예측해야 다른 축을 잡습니다(writing.md §3 ③)"),
    ):
        if word not in allmd:
            q(qs, "P0", ask, why, "예/아니오 · 파일 · 이름", "사업 폴더 전체")


def check_p35(folder, qs):
    a = rd(os.path.join(folder, "03a_페인포인트.md"))
    if a is not None:
        rows = table_rows(a, "출처")
        with_src = [r for r in rows if len(r) >= 3 and re.search(r"https?://|\d{4}|링크|회의록|보도|공고|평가|계획|홈페이지", r[2])]
        if len(with_src) < 5:
            q(qs, "P3.5", "출처가 붙은 발주처 사실이 %d행입니다(5 이상 필요)" % len(with_src),
              "출처 없는 관찰은 심사위원 앞에서 주장이 됩니다. 발주처를 **만난 사람**·담당자가 한 말·현장에 가 본 사람이 있으면 그 메모가 가장 센 출처입니다",
              "사람 이름(내부)·메모·링크", "probe_web 검색 결과(03a_raw)·재료 팩 §5")
    b = rd(os.path.join(folder, "03b_방향전략.md"))
    if b is not None:
        cards = table_rows(b, "경쟁사가")
        empty = [r for r in cards if len(r) < 4 or len(r[3]) < 4]
        if len(cards) < 8:
            q(qs, "P3.5", "색채 카드가 %d장입니다(8 이상 필요)" % len(cards), "위키에 아직 안 올라간 우리 실물·등록(특허·저작권 번호)·사람이 있으면 카드가 됩니다", "항목·사진·번호", "재료 팩 §5·§7 · 위키 실적 색인")
        if empty:
            q(qs, "P3.5", "「경쟁사가 못 쓰는 이유」가 빈 카드가 %d장입니다" % len(empty), "이유를 못 붙이면 카드가 아닙니다(writing.md §3)", "한 줄씩", "03b 카드 표")
        if not re.search(r"이름 후보|후보 셋|컨셉 이름", b):
            q(qs, "P3.5", "컨셉 이름 후보 셋이 없습니다", "이름이 덱의 모티프가 됩니다(writing.md §3)", "후보 셋 중 택일 — 제가 셋을 내겠습니다", "03b")
        if not re.search(r"동의|합의", b):
            q(qs, "P3.5", "방향에 사용자 동의 표시가 없습니다", "방향 동의 후 전략으로 갑니다(SKILL 원칙 6)", "동의 / 수정 한 줄", "03b §3")


def check_p4(folder, qs):
    p = latest(folder, "04_제안서")
    md = rd(p) if p else None
    if not md:
        return
    items = re.findall(re.escape(WARN) + r"\s*[—:-]?\s*([^\n|]+)", md)
    if items:
        q(qs, "P4", "초안 %s에 「확인필요」가 %d곳입니다: %s" % (os.path.basename(p), len(items), " · ".join(x.strip() for x in items[:7])),
          "값이 들어와야 다음 회차 검토가 의미 있습니다", "값 (한 번에)", "재료 팩·위키")


def check_p6(folder, qs):
    md = rd(os.path.join(folder, "06_재료점검.md"))
    if md is None:
        p = latest(folder, "07_슬라이드계획")
        md = rd(p) if p else None
        if md is None:
            return
        m = re.search(r"## 재료 점검.*?(?=\n## |\Z)", md, re.S)
        md = m.group(0) if m else ""
    rules = [
        (r"결정", 1, "심사위원이 내릴 결정 한 문장"),
        (r"반대", 3, "가장 큰 반대 의견 셋"),
        (r"현장 사진|발주처.*사진", 6, "발주처 현장 사진 6장"),
        (r"우리 실물|실물", 6, "우리 실물 6장"),
        (r"숫자", 5, "출처 있는 숫자 5개"),
        (r"색채 카드|카드", 8, "색채 카드 8장"),
    ]
    for pat, need, label in rules:
        line = next((l for l in md.splitlines() if re.search(pat, l)), None)
        if line is None:
            q(qs, "P6", "재료점검에 「%s」 항목이 없습니다" % label, "빈 칸이면 덱을 만들지 않습니다(deck.md §0)", "값·파일", "06_재료점검 · 07 재료 점검 절", blocking=True)
            continue
        body = re.sub(r"^[^:：]*[:：]", "", line).strip()
        if len(re.sub(r"[\s\-—·]", "", body)) < 4:
            q(qs, "P6", "재료점검 「%s」이 비었습니다" % label, "빈 칸이면 덱을 만들지 않습니다(deck.md §0)", "값·파일", "재료 팩·images.md 절차·03a·03b", blocking=True)
            continue
        if need > 1:
            nums = [int(x) for x in re.findall(r"(\d+)\s*(?:장|개|건)", line)]
            n = max(nums) if nums else None
            if n is None:
                n = len([c for c in re.split(r"[·,]", body) if c.strip()])
            if n < need:
                who = "현장에 다녀온 분·발주처 담당자(요청 문안 가능)" if "현장" in label else ("실적 담당·장비 담당" if "실물" in label else "03a·재료 팩 §3")
                q(qs, "P6", "「%s」이 %d입니다(%d 필요)" % (label, n, need), "부족하면 그 재료를 쓰는 장을 만들 수 없습니다", "파일·링크 — 누가: %s" % who, "img/MANIFEST · 03a · 03b", blocking=True)
    plan = latest(folder, "07_슬라이드계획")
    pm = rd(plan) if plan else None
    if pm and "## 승인" in pm:
        sec = pm.split("## 승인", 1)[1]
        if not re.search(r"승인자\s*[:：]\s*\S{2,}", sec) or re.search(r"승인자\s*[:：]\s*[-—]", sec):
            q(qs, "P6", "고스트 덱 계획(%s)에 승인이 없습니다" % os.path.basename(plan), "승인 전에는 Figma를 열지 않습니다", "「승인」 또는 고칠 장 번호", "07 ## 승인", blocking=True)


def check_p7(folder, qs):
    st = rd(os.path.join(folder, "_STATE.md"))
    if not st:
        return
    m = re.search(r"^상태:\s*(\S+)", st, re.M)
    status = m.group(1) if m else ""
    done = status in ("완료", "낙찰", "유찰", "미제출", "종료")
    has_retro = re.search(r"^회고:\s*\{?\s*결과\s*[:：]\s*[^-\s}][^\n}]*", st, re.M) or re.search(r"^회고:\s*\n(\s+결과\s*[:：]\s*[^-\s][^\n]*)", st, re.M)
    if done and not has_retro:
        for i, (what, why, form) in enumerate([
            ("결과가 어떻게 됐습니까(낙찰·유찰·미개찰·미제출) — 순위·기술점수·가격점수가 나왔으면 숫자로", "결과가 있어야 통한 것과 안 통한 것을 가를 수 있습니다", "택일·숫자"),
            ("심사위원·담당자가 한 말이 있습니까(개인 이름 없이 그대로)", "가장 비싼 피드백입니다", "한두 줄"),
            ("우리 제안 중 발주처가 반응한 장·문장·카드 하나", "다음 같은 유형에서 먼저 꺼낼 것", "하나"),
            ("헛돈 것 하나(페인포인트가 틀렸나 · 카드가 약했나 · 발표가 길었나)", "다음에 뺄 것", "하나"),
            ("누가 이겼거나 붙었나, 그쪽 제안의 특징 한 줄", "경쟁사 표준 답 예측을 갱신합니다", "한 줄"),
            ("이번에 없어서 아쉬웠던 재료(사진·숫자·사람·이전 제안서) 하나", "재료 게이트를 현실에 맞춥니다", "하나"),
            ("같은 기관 유형·과업 유형이 또 나오면 처음부터 다르게 할 것 하나", "절차 교훈 → ROADMAP 또는 이슈", "한 줄"),
        ], 1):
            q(qs, "P7", "회고 %d/7 · %s" % (i, what), why, form, "_STATE.md 회고 칸 비어 있음")


def pick_phase(folder):
    st = rd(os.path.join(folder, "_STATE.md")) or ""
    m = re.search(r"^상태:\s*(\S+)", st, re.M)
    if m and m.group(1) in ("완료", "낙찰", "유찰", "미제출", "종료"):
        return "P7"
    m = re.search(r"^현재단계:\s*(P[\d.]+)", st, re.M)
    cur = m.group(1) if m else ""
    if cur.startswith("P6"): return "P6"
    if cur.startswith("P4") or cur.startswith("P5"): return "P4"
    if cur.startswith("P3"): return "P3.5"
    return "P0"


def render(qs, phase, folder):
    L = ["# 질문서 초안 — %s (`gap_check.py` · %s)" % (phase, os.path.basename(os.path.abspath(folder))), ""]
    if not qs:
        L += ["빠진 것이 없습니다. 이 단계에서 물을 것 없이 진행합니다.", ""]
        return "\n".join(L)
    block = [x for x in qs if x["blocking"]]
    later = [x for x in qs if not x["blocking"]]
    L.append("Claude는 이 초안을 `asking.md` §1·§5에 맞춰 다듬어 **한 메시지**로 묻는다(일곱 넘으면 「지금 답하지 않아도 진행되는 것」으로 내린다). 헤드리스면 `_STATE.md` 차단사항에 적고 종료.")
    L.append("")
    if block:
        L.append("## 답이 있어야 다음으로 가는 것 (%d)" % len(block))
        for i, x in enumerate(block, 1):
            L.append("%d. **%s** — 왜: %s. 답 형태: %s. 제가 찾아본 곳: %s" % (i, x["what"], x["why"], x["form"], x["tried"] or "-"))
        L.append("")
    if later:
        L.append("## 지금 답하지 않아도 진행되는 것 (%d · 답 없으면 ⚠️ 확인필요로 두고 진행)" % len(later))
        for i, x in enumerate(later, len(block) + 1):
            L.append("%d. %s — 왜: %s. 답 형태: %s. 제가 찾아본 곳: %s" % (i, x["what"], x["why"], x["form"], x["tried"] or "-"))
        L.append("")
    return "\n".join(L)


def run(folder, phase="auto"):
    if not os.path.isdir(folder):
        raise SystemExit("폴더가 없습니다: %s" % folder)
    if phase == "auto":
        phase = pick_phase(folder)
    qs = []
    {"P0": check_p0, "P3.5": check_p35, "P4": check_p4, "P6": check_p6, "P7": check_p7}[phase](folder, qs)
    if phase == "P0":
        pass
    return phase, qs


# ---------- 셀프테스트 ----------
def selftest():
    fails = []
    d = tempfile.mkdtemp(prefix="gap_")
    def w(name, s): io.open(os.path.join(d, name), "w", encoding="utf-8").write(s)
    # P0: 절 8개 · 확인필요 · 경쟁사 없음
    w("00_재료팩.md", "판본: A#1#1\n" + "".join("## %d. 절%d\n\n%s\n\n" % (i, i, "" if i == 3 else "- 값: 어떤 내용이 충분히 길게 들어 있다") for i in range(8)) + "## 8. 확인필요\n- ⚠️ 확인필요 — 신용등급 원문\n\n## 9. 끝\n- 이전 제안서 있음 · 담당자 메모 있음 · 충분한 내용\n")
    w("_STATE.md", "상태: 진행중\n현재단계: P1\n")
    ph, qs = run(d)
    if ph != "P0": fails.append("phase P0")
    texts = " ".join(x["what"] for x in qs)
    if "확인필요」가 1곳" not in texts: fails.append("P0 warn")
    if "경쟁사" not in texts or "이전 제안서" in texts: fails.append("P0 words")
    if "§3 「절3」이 비어 있습니다" not in texts: fails.append("P0 sections")
    if any("개뿐" in x["what"] for x in qs): fails.append("P0 count false positive")
    # P3.5: 출처 3행 · 카드 5장(이유 빈칸 1)
    w("_STATE.md", "상태: 진행중\n현재단계: P3.5\n")
    w("03a_페인포인트.md", "| # | 사실 | 출처(링크 · 날짜) | RFP |\n|---|---|---|---|\n" + "".join("| %d | 사실 | 홈페이지 2026 | x |\n" % i for i in range(3)) + "| 9 | 사실 | | x |\n")
    w("03b_방향전략.md", "| # | 종류 | 카드 | 경쟁사가 못 쓰는 이유 |\n|---|---|---|---|\n" + "".join("| C%d | 실물 | 카드 | 이유가 있다 |\n" % i for i in range(4)) + "| C5 | 실물 | 카드 | |\n\n## 3. 방향 (사용자 동의)\n이름 후보 셋: a·b·c\n")
    ph, qs = run(d)
    texts = " ".join(x["what"] for x in qs)
    if ph != "P3.5" or "3행" not in texts or "5장입니다" not in texts or "빈 카드가 1장" not in texts: fails.append("P3.5: " + texts[:120])
    if "이름 후보" in texts or "동의 표시" in texts: fails.append("P3.5 false positive")
    # P6: 07 재료 점검 절 — 사진 2장 · 승인 없음
    w("_STATE.md", "상태: 진행중\n현재단계: P6-계획\n")
    w("07_슬라이드계획_v1.md", "## 재료 점검\n- 심사위원이 내릴 결정: 「1순위로 올린다」\n- 가장 큰 반대 셋: ① a → 3장 ② b → 4장 ③ c → 5장\n- 발주처 현장 사진 2장: 외관·입구\n- 우리 실물 6장: a · b · c · d · e · f\n- 출처 있는 숫자 5개: 1·2·3·4·5\n- 색채 카드 8장: 03b 1~8\n\n## 승인\n- 승인자: -\n- 일시: -\n")
    ph, qs = run(d)
    texts = " ".join(x["what"] for x in qs)
    if ph != "P6" or "사진 6장」이 2입니다" not in texts or "승인이 없습니다" not in texts: fails.append("P6: " + texts[:160])
    if "실물" in texts or "숫자" in texts: fails.append("P6 false positive")
    if not all(x["blocking"] for x in qs): fails.append("P6 blocking")
    # P7: 완료·회고 없음 → 7문
    w("_STATE.md", "상태: 완료\n현재단계: P7\n회고: {결과: -, 통한것: -}\n")
    ph, qs = run(d)
    if ph != "P7" or len(qs) != 7: fails.append("P7 count %d" % len(qs))
    w("_STATE.md", "상태: 완료\n현재단계: P7\n회고: {결과: 유찰 2위, 통한것: 9장}\n")
    ph, qs = run(d)
    if qs: fails.append("P7 done false positive")
    md = render([], "P0", d)
    if "빠진 것이 없습니다" not in md: fails.append("render empty")
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — P0·P3.5·P6·P7 결손 검출 · 서식")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(2)
    phase = sys.argv[sys.argv.index("--phase") + 1] if "--phase" in sys.argv else "auto"
    try:
        ph, qs = run(args[0], phase)
    except SystemExit as e:
        print(e); sys.exit(2)
    md = render(qs, ph, args[0])
    print(md)
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        io.open(out, "w", encoding="utf-8").write(md)
    sys.exit(1 if qs else 0)
