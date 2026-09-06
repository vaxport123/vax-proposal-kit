#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""preflight.py — Claude가 사업을 시작하기 전에 돌리는 준비 점검(SKILL.md P-1). 사람이 doctor.sh를 읽는 대신, 이 스크립트가
「필수/권장」으로 나눠 판정하고, **Claude가 사용자에게 요구할 문장**을 그대로 만들어 준다. 한준 2026-09-06 "어차피 클로드 통해서 설치하고 돌릴테니 에이전트가 점검하고 요구하도록".

사용:  python3 scripts/preflight.py [--online] [--json out.json]     종료코드 0=필수 전부 통과 · 1=필수 미통과 · 2=스크립트 오류
       python3 scripts/preflight.py --selftest                        오프라인 자체 검사
--online 이면 웹 검색 1회·원격 태그 확인까지 한다(5~10초). 커넥터(노션·피그마)는 셸에서 볼 수 없어 여기서는 안 본다 — SKILL P-1이 Claude 도구로 확인한다.

판정 항목(필수 = 없으면 P0로 못 간다):
  필수  파이썬 3.10+ · 스킬 설치본이 저장소와 같음 · 비판자 에이전트 설치 · 파이썬 의존성(ddgs·requests·bs4·PIL) · 셀프테스트 7종
  권장  커밋 훅(개발자만) · 글꼴 18종(피그마 제작 때) · /bid-loop 명령(루프형만) · 저장소 최신 · 판 최신(--online) · 웹 검색 통함(--online)
"""
import hashlib, io, json, os, platform, re, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HOME = os.path.expanduser("~")
SKILL = os.path.join(ROOT, "skills", "vax-proposal")
SCRIPTS = os.path.join(SKILL, "scripts")


def sha(p):
    try:
        with open(p, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()
    except Exception:
        return None


def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT, encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 99, str(e)


def font_count():
    s = platform.system()
    if s == "Windows":
        d = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
    elif s == "Darwin":
        d = os.path.join(HOME, "Library", "Fonts")
    else:
        d = os.path.join(HOME, ".local", "share", "fonts", "vax-proposal-kit")
    try:
        return len([f for f in os.listdir(d) if f.startswith(("Freesentation-", "Paperlogy-")) and f.endswith(".ttf")])
    except Exception:
        return 0


def checks(online=False):
    """항목 목록. 각 항목: id · 필수 여부 · 통과 여부 · 상태 한 줄 · 사용자에게 요구할 행동(없으면 None) · Claude가 대신 할 수 있나."""
    C = []
    def add(id_, must, ok, status, ask=None, claude_can=False):
        C.append({"id": id_, "must": must, "ok": bool(ok), "status": status, "ask": ask, "claude_can": claude_can})

    v = sys.version_info
    add("python", True, v >= (3, 10), "파이썬 %d.%d" % (v.major, v.minor), None if v >= (3, 10) else "파이썬 3.10 이상을 설치하십시오(python.org). 지금 %d.%d" % (v.major, v.minor))

    inst = os.path.join(HOME, ".claude", "skills", "vax-proposal", "SKILL.md")
    same = os.path.exists(inst) and sha(inst) == sha(os.path.join(SKILL, "SKILL.md"))
    add("skill", True, same, "스킬 설치본 " + ("최신" if same else ("낡음" if os.path.exists(inst) else "없음")),
        None if same else "저장소 폴더에서 `bash install.sh --force`를 돌리십시오(스킬·에이전트·명령·훅·글꼴을 한 번에 깝니다).", claude_can=True)

    critic = os.path.exists(os.path.join(HOME, ".claude", "agents", "proposal-critic.md"))
    add("critic", True, critic, "비판자 에이전트 " + ("설치됨" if critic else "없음"), None if critic else "`bash install.sh --force` (비판자 proposal-critic이 ~/.claude/agents 에 없습니다)", claude_can=True)

    missing = []
    for mod in ("ddgs", "requests", "bs4", "PIL"):
        try:
            __import__(mod)
        except Exception:
            missing.append(mod)
    add("deps", True, not missing, "파이썬 의존성 " + ("있음" if not missing else "없음: " + ",".join(missing)),
        None if not missing else "`pip install -r skills/vax-proposal/scripts/requirements.txt` (없는 것: %s)" % ",".join(missing), claude_can=True)

    fails = []
    for f in ("ui_tokens", "render_html", "figures_svg", "proposal_lint", "layout_wireframes", "probe_web", "gap_check"):
        rc, _ = run([sys.executable, os.path.join(SCRIPTS, f + ".py"), "--selftest"], timeout=90)
        if rc != 0:
            fails.append(f)
    add("selftest", True, not fails, "셀프테스트 7종 " + ("통과" if not fails else "실패: " + ",".join(fails)),
        None if not fails else "셀프테스트가 실패했습니다(%s). `git pull` 뒤 다시 돌리고, 그래도 실패하면 이슈로 올리십시오." % ",".join(fails))

    rc, out = run(["git", "config", "--get", "core.hooksPath"])
    hook = out.strip() == ".githooks"
    add("hook", False, hook, "커밋 훅 " + ("켜짐" if hook else "꺼짐"), None if hook else "저장소에 커밋할 사람만: `git config core.hooksPath .githooks` (install.sh가 켭니다)", claude_can=True)

    fc = font_count()
    add("fonts", False, fc >= 18, "글꼴 %d/18" % fc, None if fc >= 18 else "피그마 제작 전에 `bash fonts/install-fonts.sh` 를 돌리고 피그마를 다시 여십시오(글꼴 %d/18)." % fc, claude_can=True)

    cmd = os.path.exists(os.path.join(HOME, ".claude", "commands", "bid-loop.md"))
    add("bidloop", False, cmd, "/bid-loop 명령 " + ("있음" if cmd else "없음"), None if cmd else "루프형(야간 자동)으로 쓸 때만: `bash install.sh --force`", claude_can=True)

    rc, out = run(["git", "fetch", "-q", "origin"], timeout=30) if online else (0, "")
    rc2, behind = run(["git", "rev-list", "--count", "HEAD..origin/main"])
    behind = behind.strip() if rc2 == 0 and behind.strip().isdigit() else "?"
    add("uptodate", False, behind == "0", "저장소 " + ("최신" if behind == "0" else "원격보다 %s 커밋 뒤" % behind), None if behind == "0" else "`git pull && bash install.sh --force`", claude_can=True)

    if online:
        try:
            ver = io.open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
        except Exception:
            ver = "?"
        rc, tags = run(["git", "ls-remote", "--tags", "--refs", "origin"], timeout=30)
        latest = sorted([t.split("/v")[-1] for t in tags.split() if "/v" in t], key=lambda s: [int(x) if x.isdigit() else 0 for x in s.split(".")])[-1:] if rc == 0 else []
        latest = latest[0] if latest else "?"
        def _key(x): return [int(t) if t.isdigit() else 0 for t in x.split(".")]
        newer = latest != "?" and ver != "?" and _key(latest) > _key(ver)   # 로컬이 앞서면(개발 중) 통과
        add("version", False, not newer, "판 v%s (원격 최신 v%s)" % (ver, latest), None if not newer else "새 판 v%s: `git pull && bash install.sh --force`" % latest, claude_can=True)
        rc, out = run([sys.executable, "-c", "from ddgs import DDGS; print(len(list(DDGS().text('나라장터 입찰공고', region='kr-kr', max_results=3))))"], timeout=25)
        n = out.strip().splitlines()[-1] if rc == 0 and out.strip() else "0"
        add("search", False, n.isdigit() and int(n) > 0, "웹 검색 %s건" % n, None if (n.isdigit() and int(n) > 0) else "웹 검색이 0건입니다 — 네트워크·차단을 확인하십시오. probe_web은 못 쓰지만 P0~P2는 진행할 수 있습니다.")
    return C


def report(C):
    must_fail = [c for c in C if c["must"] and not c["ok"]]
    rec_fail = [c for c in C if not c["must"] and not c["ok"]]
    L = ["# 준비 점검 (preflight)", ""]
    for c in C:
        L.append("- %s %s%s" % ("✓" if c["ok"] else ("✗" if c["must"] else "△"), c["status"], "" if c["ok"] else "  ← " + ("필수" if c["must"] else "권장")))
    L.append("")
    if not must_fail:
        L.append("**필수 항목 전부 통과 — P0로 간다.**" + (" 권장 %d건은 아래에 적어 두고 진행한다." % len(rec_fail) if rec_fail else ""))
    else:
        L.append("**필수 %d건 미통과 — P0로 가지 않는다.** 아래를 사용자에게 **한 번에** 요구한다(Claude가 대신 할 수 있는 것은 사용자 확인 1회 뒤 Claude가 한다)." % len(must_fail))
    L.append("")
    L.append("## Claude가 사용자에게 요구할 것")
    for c in must_fail + rec_fail:
        if c["ask"]:
            L.append("- [%s] %s%s" % ("필수" if c["must"] else "권장", c["ask"], " — Claude가 대신 실행 가능(확인 1회)" if c["claude_can"] else " — 사람만 할 수 있음"))
    if not (must_fail or rec_fail):
        L.append("- 없음")
    L.append("")
    L.append("## 셸에서 볼 수 없어 Claude 도구로 확인할 것 (SKILL P-1 ②)")
    L.append("- 피그마: `whoami` 계정이 회사 계정인가 · 레이아웃 라이브러리 파일이 열리는가(안 열리면 「팀 프로젝트로 이동·접근 권한」을 요구)")
    L.append("- 노션: 「제안 재료 팩」 검색이 되는가 · 기밀 절이 보이는가(안 보이면 회사 커넥터로 다시 연결을 요구)")
    return "\n".join(L) + "\n", (1 if must_fail else 0)


def selftest():
    fails = []
    C = [{"id": "a", "must": True, "ok": False, "status": "x", "ask": "A를 하십시오", "claude_can": True},
         {"id": "b", "must": False, "ok": False, "status": "y", "ask": "B", "claude_can": False},
         {"id": "c", "must": True, "ok": True, "status": "z", "ask": None, "claude_can": False}]
    md, rc = report(C)
    if rc != 1: fails.append("종료코드")
    for m in ["필수 1건 미통과", "[필수] A를", "대신 실행 가능", "[권장] B", "사람만", "피그마", "노션"]:
        if m not in md: fails.append(m)
    md2, rc2 = report([{"id": "c", "must": True, "ok": True, "status": "z", "ask": None, "claude_can": False}])
    if rc2 != 0 or "전부 통과" not in md2: fails.append("통과 서식")
    if not callable(font_count) or not isinstance(font_count(), int): fails.append("font_count")
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — 판정·요구 문장·종료코드")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    try:
        C = checks(online="--online" in sys.argv)
        md, rc = report(C)
        print(md)
        if "--json" in sys.argv:
            out = sys.argv[sys.argv.index("--json") + 1]
            io.open(out, "w", encoding="utf-8").write(json.dumps(C, ensure_ascii=False, indent=1))
        sys.exit(rc)
    except Exception as e:
        print("preflight 오류: %s" % e)
        sys.exit(2)
