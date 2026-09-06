#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""readiness.py — 「모든 자료·아이디어가 갖춰졌나」를 기계로 판정한다. 통과 전에는 초안(P4)도 피그마(P6 ⑨)도 시작하지 않는다.
`references/intake.md`의 게이트 둘을 구현한다. 인테이크(00_인테이크.md)의 체크·값과 폴더의 산출물, `_STATE.md`를 함께 본다.

사용:  python3 readiness.py bids/<사업> --gate draft|deck [--out logs/게이트_draft.md]
       종료코드 0=통과 · 1=미통과(남은 것을 사용자에게 요구할 문장으로 출력) · 2=오류.   --selftest 오프라인.
게이트 항목:
  draft  RFP 원문 · 연결(노션 또는 팩 직접) · 01·02·03 산출물 · 03a 출처 5 · 03b 카드 8 · 방향(사용자 말) · 방향 동의 · 확인 「이대로 시작」 · 확인필요 0(건너뜀 허용)
  deck   draft 전부 · 05 심사 80점 · 피그마 연결 · 재료점검 여섯 · 07 계획 · 승인
"""
import io, os, re, sys, tempfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import gap_check as G
except Exception:  # 셀프테스트 격리 등
    G = None

NEVER_SKIP = ("RFP", "피그마", "승인")   # 「그냥 진행해」로도 건너뛸 수 없는 것


def rd(p):
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return None


def checked(md, label):
    """'- [x] 라벨: 값' 줄이 체크됐고 값이 비어 있지 않은가. 값이 없어도 체크면 True."""
    m = re.search(r"^- \[([ xX])\]\s*" + re.escape(label) + r"[^:\n]*:?\s*(.*)$", md, re.M)
    if not m:
        return False, ""
    return m.group(1).lower() == "x", m.group(2).strip()


def field(md, label):
    m = re.search(r"^-\s*(?:\[[ xX]\]\s*)?" + re.escape(label) + r"[^:\n]*:\s*(.*)$", md, re.M)
    return m.group(1).strip() if m else ""


def skipped(md, label):
    return bool(re.search(re.escape(label) + r".*건너뜀", md)) and not any(k in label for k in NEVER_SKIP)


def latest(folder, prefix):
    if G:
        return G.latest(folder, prefix)
    best, bn = None, -1
    for f in os.listdir(folder):
        m = re.match(re.escape(prefix) + r"_?v?(\d+)\.md$", f)
        if m and int(m.group(1)) > bn:
            best, bn = os.path.join(folder, f), int(m.group(1))
    return best


def nonempty(folder, name, minlen=200):
    s = rd(os.path.join(folder, name))
    return bool(s) and len(s.strip()) >= minlen


def evaluate(folder, gate):
    """항목 목록: {id, ok, label, ask, hard}. hard=사용자 결정으로도 못 건너뜀."""
    items = []
    def add(id_, ok, label, ask, hard=False):
        items.append({"id": id_, "ok": bool(ok), "label": label, "ask": ask, "hard": hard})

    intake = rd(os.path.join(folder, "00_인테이크.md"))
    if intake is None:
        add("intake", False, "접수 파일(00_인테이크.md) 없음", "접수를 먼저 합니다 — RFP · 연결 · 방향 · 재료 · 확인 다섯 묶음을 차례로 묻겠습니다(`intake.md` §1)", hard=True)
        intake = ""
    st = rd(os.path.join(folder, "_STATE.md")) or ""

    # ① RFP
    ok_rfp, v = checked(intake, "RFP 원문 받음")
    has_rfp = nonempty(folder, "00_RFP원문_추출.md")
    add("rfp", ok_rfp and has_rfp, "RFP 원문", "제안요청서 원문을 주십시오 — 노션 「RFP 원문(추출)」 링크 · 파일 경로(pdf/hwp/docx) · 본문 붙여넣기 중 편한 것으로. 없으면 어떤 단계도 시작할 수 없습니다", hard=True)

    # ② 연결
    notion_line = field(intake, "노션")
    notion_ok = checked(intake, "노션")[0] and (("열림" in notion_line) or ("직접" in notion_line)) or bool(re.search(r"노션:\s*(열림|통과|ok|OK|재료팩 열림)", st))
    add("notion", notion_ok, "노션 연결(또는 재료 팩 직접 제공)", "노션 커넥터를 회사 계정으로 연결해 주십시오(재료 팩·위키를 읽습니다). 연결이 어려우면 재료 팩을 빈 서식(`material-pack.template.md`)에 채워 붙여 주십시오")

    # 산출물
    add("p1", nonempty(folder, "01_평가표.md"), "P1 평가표", "P1 평가표를 제가 만듭니다(RFP가 있으면 바로)")
    add("p2", nonempty(folder, "02_가점진단.md", 100), "P2 가점 진단", "P2 가점 진단을 제가 만듭니다")
    add("p3", nonempty(folder, "03_레퍼런스매핑.md", 100), "P3 레퍼런스", "P3 레퍼런스 매핑을 제가 만듭니다(위키 연결 필요)")
    a = rd(os.path.join(folder, "03a_페인포인트.md"))
    n_src = 0
    if a and G:
        rows = G.table_rows(a, "출처")
        n_src = len([r for r in rows if len(r) >= 3 and re.search(r"https?://|\d{4}|링크|회의록|보도|공고|평가|계획|홈페이지", r[2])])
    add("p3a", n_src >= 5, "페인포인트(출처 있는 사실 %d/5)" % n_src, "출처 있는 발주처 사실이 %d행입니다. 발주처를 만난 분·담당자가 한 말·현장 메모가 있으면 주십시오(웹 수집은 제가 합니다)" % n_src)
    b = rd(os.path.join(folder, "03b_방향전략.md"))
    n_cards = len(G.table_rows(b, "경쟁사가")) if (b and G) else 0
    add("p3b", n_cards >= 8, "색채 카드(%d/8)" % n_cards, "색채 카드가 %d장입니다. 위키에 없는 우리 실물·등록(특허·저작권 번호)·사람이 있으면 알려 주십시오" % n_cards)

    # ③ 방향 — 사용자가 말로 준 것
    ok_dir, dir_v = checked(intake, "주요 방향 한두 문장")
    add("direction", ok_dir and len(dir_v) >= 6, "주요 방향(사용자가 말로)", "이 제안의 **주요 방향**을 한두 문장으로 주십시오(예: 「운영 부담 없는 전시관」처럼 발주처가 얻는 것으로). 없으면 제가 후보 셋을 내고 고르시게 하겠습니다")
    add("agree", bool(b and re.search(r"동의|합의", b)), "방향 동의(03b)", "03b 방향 절을 읽고 「동의」 또는 고칠 점을 한 줄로 주십시오")

    # ⑤ 확인
    ok_conf, _ = checked(intake, "사용자 확인")
    add("confirm", ok_conf, "접수 확인 「이대로 시작」", "받은 것을 요약해 드렸습니다. 「이대로 시작」이라고 답해 주시면 초안에 들어갑니다")

    # 확인필요
    allmd = " ".join(filter(None, (rd(os.path.join(folder, f)) for f in os.listdir(folder) if f.endswith(".md") and not f.startswith("logs"))))
    n_warn = allmd.count("⚠️ 확인필요")
    add("warn", n_warn == 0, "확인필요 %d곳" % n_warn, "「확인필요」가 %d곳 남았습니다. 값을 주시거나 「그대로 진행」이라고 답해 주십시오(그러면 표시를 남기고 갑니다)" % n_warn)

    if gate == "deck":
        s5 = latest(folder, "05_심사결과") or (os.path.join(folder, "05_심사결과_1회.md") if os.path.exists(os.path.join(folder, "05_심사결과_1회.md")) else None)
        score = None
        if s5:
            m = re.search(r"총점\D{0,10}(\d{2,3})", rd(s5) or "")
            score = int(m.group(1)) if m else None
        if score is None:
            m = re.search(r"총점:\s*(\d+)", st)
            score = int(m.group(1)) if m else None
        add("score", score is not None and score >= 80, "심사 %s점(80 이상)" % (score if score is not None else "-"), "심사위원 채점(P5)이 80점 이상이어야 덱으로 갑니다. 지금 %s점 — 개선 상위 3건을 먼저 반영합니다" % (score if score is not None else "미채점"))
        fig_line = field(intake, "피그마")
        fig_ok = (checked(intake, "피그마")[0] and "열림" in fig_line) or bool(re.search(r"피그마:\s*[^,}\n]*(열림|통과|ok|OK)", st))
        add("figma", fig_ok, "피그마 연결(회사 계정 · 라이브러리 열림)", "피그마를 회사 계정으로 연결하고 레이아웃 라이브러리 파일이 열리는지 확인해 주십시오(`references/layouts.md` 링크). 안 열리면 관리자에게 팀 프로젝트 이동·공유를 요청해 주십시오. 이것 없이는 덱을 만들 수 없습니다", hard=True)
        if G:
            qs = []
            G.check_p6(folder, qs)
            mats = [x for x in qs if "승인" not in x["what"]]
            appr = [x for x in qs if "승인" in x["what"]]
            has_plan = bool(latest(folder, "07_슬라이드계획"))
            add("materials", not mats and (has_plan or os.path.exists(os.path.join(folder, "06_재료점검.md"))), "재료점검 여섯(결정·반대 셋·사진 6·실물 6·숫자 5·카드 8)", "재료 요청서: " + " / ".join(x["what"] for x in mats) if mats else "재료점검(06 또는 07 「재료 점검」 절)을 제가 채웁니다")
            add("plan", has_plan, "고스트 덱 계획(07)", "고스트 덱 계획을 제가 만듭니다(재료점검 통과 뒤)")
            add("approval", has_plan and not appr, "고스트 덱 승인", "07 고스트 덱 표를 보시고 「승인」 또는 고칠 장 번호를 주십시오. 승인 전에는 피그마를 열지 않습니다", hard=True)

    # 건너뜀 반영
    for it in items:
        if not it["ok"] and not it["hard"] and skipped(intake, it["label"].split("(")[0].strip()):
            it["ok"] = True
            it["label"] += " · 건너뜀(사용자 결정)"
    return items


def render(items, gate, folder):
    name = "초안 게이트(P4 앞)" if gate == "draft" else "덱 게이트(피그마 앞)"
    left = [x for x in items if not x["ok"]]
    L = ["# %s — %s" % (name, os.path.basename(os.path.abspath(folder))), ""]
    for x in items:
        L.append("- %s %s" % ("✓" if x["ok"] else ("✗" if x["hard"] else "△"), x["label"]))
    L.append("")
    if not left:
        L.append("**통과 — %s.**" % ("초안(P4)을 시작한다" if gate == "draft" else "피그마를 연다(P6 ⑨)"))
        return "\n".join(L) + "\n", 0
    hard = [x for x in left if x["hard"]]
    L.append("**미통과 %d건 — %s 시작하지 않는다.** 아래를 한 메시지로 요구한다(`asking.md` §5). ✗는 사용자 결정으로도 건너뛸 수 없다." % (len(left), "초안을" if gate == "draft" else "피그마를"))
    L.append("")
    L.append("## 사용자에게 요구할 것")
    for i, x in enumerate(left, 1):
        L.append("%d. %s%s" % (i, x["ask"], " (필수 · 건너뛸 수 없음)" if x["hard"] else ""))
    L.append("")
    if hard:
        L.append("## 헤드리스면 `차단사항`에")
        L.append("- " + " · ".join(x["label"] for x in hard))
    return "\n".join(L) + "\n", 1


def selftest():
    fails = []
    d = tempfile.mkdtemp(prefix="ready_")
    def w(name, s): io.open(os.path.join(d, name), "w", encoding="utf-8").write(s)
    # 빈 폴더 → 접수 없음(hard) · RFP(hard)
    w("_STATE.md", "상태: 진행중\n현재단계: P0\n")
    items = evaluate(d, "draft"); md, rc = render(items, "draft", d)
    if rc != 1 or "접수를 먼저" not in md or "제안요청서 원문을" not in md or "건너뛸 수 없음" not in md: fails.append("empty draft")
    # 접수 다 채움 + 산출물
    intake = ("# 00_인테이크\n## ① RFP\n- [x] RFP 원문 받음: 노션 링크\n- [x] `00_RFP원문_추출.md` 저장됨\n"
              "## ② 연결\n- [x] 노션: 회사 커넥터 열림\n- [ ] 피그마: 미연결(덱 게이트에서 다시)\n"
              "## ③ 방향\n- [x] 주요 방향 한두 문장: 담당 두 명이 손대지 않아도 되는 전시관\n"
              "## ⑤ 확인\n- [x] 사용자 확인 「이대로 시작」: 2026-09-20\n")
    w("00_인테이크.md", intake)
    w("00_RFP원문_추출.md", "판본: A\n" + "과업 내용 " * 60)
    w("01_평가표.md", "x" * 250); w("02_가점진단.md", "x" * 120); w("03_레퍼런스매핑.md", "x" * 120)
    w("03a_페인포인트.md", "| # | 사실 | 출처(링크 · 날짜) | RFP |\n|---|---|---|---|\n" + "".join("| %d | 사실 | 홈페이지 2026 | x |\n" % i for i in range(5)))
    w("03b_방향전략.md", "| # | 종류 | 카드 | 경쟁사가 못 쓰는 이유 |\n|---|---|---|---|\n" + "".join("| C%d | 실물 | 카드 | 이유 |\n" % i for i in range(8)) + "\n## 3. 방향 (사용자 동의 2026-09-19)\n")
    items = evaluate(d, "draft"); md, rc = render(items, "draft", d)
    if rc != 0: fails.append("full draft: " + " | ".join(x["label"] for x in items if not x["ok"]))
    # 방향 빠짐 → 미통과(soft) · 건너뜀 허용
    w("00_인테이크.md", intake.replace("- [x] 주요 방향 한두 문장: 담당 두 명이 손대지 않아도 되는 전시관", "- [ ] 주요 방향 한두 문장: "))
    items = evaluate(d, "draft"); md, rc = render(items, "draft", d)
    if rc != 1 or "주요 방향**을" not in md: fails.append("direction missing")
    w("00_인테이크.md", intake.replace("- [x] 주요 방향 한두 문장: 담당 두 명이 손대지 않아도 되는 전시관", "- [ ] 주요 방향 한두 문장: 건너뜀(2026-09-20, 사용자 결정)"))
    items = evaluate(d, "draft"); md, rc = render(items, "draft", d)
    if rc != 0 or "건너뜀(사용자 결정)" not in md: fails.append("direction skip")
    # 확인필요 있으면 미통과
    w("00_인테이크.md", intake); w("04_제안서_v1.md", "본문 ⚠️ 확인필요 — 신용등급\n" + "x" * 200)
    items = evaluate(d, "draft"); md, rc = render(items, "draft", d)
    if rc != 1 or "1곳 남았습니다" not in md: fails.append("warn")
    os.remove(os.path.join(d, "04_제안서_v1.md"))
    # deck: 피그마 미연결(hard) · 점수 없음 · 재료 없음 · 승인 없음
    items = evaluate(d, "deck"); md, rc = render(items, "deck", d)
    if rc != 1 or "피그마를 회사 계정으로" not in md or "80점 이상" not in md: fails.append("deck missing: " + md[:200])
    # deck 전부 채움
    w("00_인테이크.md", intake.replace("- [ ] 피그마: 미연결(덱 게이트에서 다시)", "- [x] 피그마: 회사 계정 · 라이브러리 열림"))
    w("05_심사결과_1회.md", "## 총점: 83 / 100\n" + "x" * 100)
    w("07_슬라이드계획_v1.md", "## 재료 점검\n- 심사위원이 내릴 결정: 「1순위」\n- 가장 큰 반대 셋: ① a → 3장 ② b → 4장 ③ c → 5장\n- 발주처 현장 사진 6장: a·b·c·d·e·f\n- 우리 실물 6장: a · b · c · d · e · f\n- 출처 있는 숫자 5개: 1·2·3·4·5\n- 색채 카드 8장: 03b 1~8\n\n## 승인\n- 승인자: 사업총괄\n- 일시: 2026-09-21\n")
    items = evaluate(d, "deck"); md, rc = render(items, "deck", d)
    if rc != 0: fails.append("full deck: " + " | ".join(x["label"] for x in items if not x["ok"]))
    # 승인만 빠짐 → hard
    w("07_슬라이드계획_v1.md", rd(os.path.join(d, "07_슬라이드계획_v1.md")).replace("- 승인자: 사업총괄", "- 승인자: -"))
    items = evaluate(d, "deck"); md, rc = render(items, "deck", d)
    if rc != 1 or "「승인」 또는 고칠 장 번호" not in md or "건너뛸 수 없음" not in md: fails.append("approval hard")
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — 초안 게이트·덱 게이트 · 건너뜀 · 필수 항목")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    gate = sys.argv[sys.argv.index("--gate") + 1] if "--gate" in sys.argv else "draft"
    if not args or gate not in ("draft", "deck") or not os.path.isdir(args[0]):
        print(__doc__); sys.exit(2)
    items = evaluate(args[0], gate)
    md, rc = render(items, gate, args[0])
    print(md)
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        io.open(out, "w", encoding="utf-8").write(md)
    sys.exit(rc)
