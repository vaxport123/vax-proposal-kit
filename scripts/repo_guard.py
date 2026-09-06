#!/usr/bin/env python3
"""repo_guard — 회사 사실이 공개 저장소로 새는 것을 막는다. LLM 없음, 정규식만.

이 키트는 GitHub에 공개된다. 실제 발주처 이름·공고번호·계약 금액·임직원 실명이
규칙 문서나 예시에 남으면 그대로 노출된다. 이 스크립트가 git이 추적하는 텍스트 파일을
훑어 네 가지를 찾고, 하나라도 있으면 종료코드 1을 낸다(커밋 훅이 이 값으로 커밋을 막는다).

■ 무엇을 찾나
  ① 나라장터 공고번호      R + 숫자2 + 영문2 + 숫자8 (예: R26BK01711646). 예시용 R26EX00000001 은 허용.
  ② 원 단위 금액           천 단위 콤마가 두 번 이상 붙은 「…,000,000원」. 예시는 「1억 2천만 원」처럼 콤마 없이.
  ③ 실명 + 직함            한국 성씨로 시작하는 이름 뒤에 직함(대표이사·이사·대리·감독·PM 등)이 붙은 것.
                           흔한 낱말 오탐(콘텐츠 PM·총괄 감독·대리수행)을 피하려 성씨로 시작하는 이름만 잡는다.
  ④ 금지 낱말              scripts/repo_guard.deny.txt 의 실제 발주처·현장 이름(부분 문자열).

■ 사용
  python3 scripts/repo_guard.py            # 저장소 루트에서. 걸리면 파일:줄:내용 출력 후 종료코드 1
  python3 scripts/repo_guard.py --selftest # 가짜 문자열로 네 패턴 검증
  python3 scripts/repo_guard.py --list     # 검사 대상 파일만 출력(디버그)

  bids/ 는 검사하지 않는다(로컬 작업 폴더, git에 넣지 않는다). 이진 파일(.png 등)과
  이 스크립트 자신·deny.txt 도 뺀다(자기 예시 문자열에 자기가 걸리지 않게).
"""
import argparse
import os
import re
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DENY_FILE = os.path.join(HERE, "repo_guard.deny.txt")

# ① 공고번호 — R26BK01711646 형식. 예시용 하나는 허용.
BID_NO = re.compile(r"\bR\d{2}[A-Z]{2}\d{8}\b")
BID_NO_ALLOW = {"R26EX00000001"}

# ② 원 단위 금액 — 콤마 묶음이 둘 이상(백만 원 이상). 「1억 2,000만 원」(콤마 하나)은 통과.
MONEY = re.compile(r"\d{1,3}(?:,\d{3}){2,}\s*원")

# ③ 실명 + 직함 — 한국 성씨로 시작하는 이름 + 직함. 성씨 앵커 + 뒤 경계로 오탐을 줄인다.
#   흔한 낱말(콘텐츠 PM·총괄 감독·대리수행·이사회·감독기관)은 걸리지 않고, 「홍길동 대리」「신윤수 대표이사」만 잡는다.
SURNAME = "김이박최정강조윤장임한오서신권황안송전홍고문양손배백허유남심노하곽성차주우구민나지진엄채원천방공현함염추도소석선설마길연위표명기반라왕금옥육인맹제모장남탁국어편용"
# 이름에 딱 붙는 직위(공백 없어도 됨). 조직 직위라 「연출」 같은 역할어와 헷갈리지 않는다.
_TITLES_TIGHT = ["대표이사", "부사장", "이사장", "본부장", "전무", "상무", "이사",
                 "부장", "차장", "과장", "팀장", "실장", "대리", "주임"]
# 역할어와 겹치는 직함(감독·PM)은 이름 뒤 공백이 있을 때만 — 「연출감독·실감콘텐츠 PM」 오탐을 막는다.
_TITLES_LOOSE = ["감독", "PM"]
# 직함 뒤: 낱말 끝이거나(한글 아님), 사람 뒤에 붙는 조사(입니다·가·이·는…)일 때만 인정한다.
_TAIL = r"(?:(?![가-힣])|(?=[입이가은는을를의에도만님께라나]))"
NAME_TITLE = re.compile(
    r"(?<![가-힣])[" + SURNAME + r"][가-힣]{1,2}"
    r"(?:\s?(?:" + "|".join(_TITLES_TIGHT) + r")|\s(?:" + "|".join(_TITLES_LOOSE) + r"))" + _TAIL
)


def load_deny(path=DENY_FILE):
    words = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and not w.startswith("#"):
                    words.append(w)
    return words


def scan_text(text, deny_words, path=""):
    """반환: [(줄번호, 코드, 걸린 문자열)]. 코드: 공고번호·금액·실명직함·금지어."""
    out = []
    for ln, line in enumerate(text.split("\n"), 1):
        for m in BID_NO.finditer(line):
            if m.group(0) not in BID_NO_ALLOW:
                out.append((ln, "공고번호", m.group(0)))
        for m in MONEY.finditer(line):
            out.append((ln, "금액", m.group(0).strip()))
        for m in NAME_TITLE.finditer(line):
            out.append((ln, "실명직함", m.group(0).strip()))
        for w in deny_words:
            if w in line:
                out.append((ln, "금지어", w))
    return out


BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
              ".pdf", ".ttf", ".otf", ".woff", ".woff2", ".eot",
              ".zip", ".gz", ".tar", ".7z", ".mp4", ".mov", ".mp3", ".wav",
              ".hwp", ".hwpx", ".pptx", ".ppt", ".docx", ".doc", ".xlsx", ".xls"}
SELF_FILES = ("repo_guard.py", "repo_guard.deny.txt")


def tracked_files():
    try:
        # -z: 한글·공백이 든 파일명을 8진수로 이스케이프하지 않고 널 구분으로 그대로 준다
        out = subprocess.check_output(["git", "ls-files", "-z"], encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print("git ls-files 실패: %s" % e, file=sys.stderr)
        return []
    files = []
    for p in out.split("\0"):
        if not p:
            continue
        if p.startswith("bids/"):
            continue
        if os.path.splitext(p)[1].lower() in BINARY_EXT:
            continue
        if p.endswith(SELF_FILES):
            continue
        files.append(p)
    return files


def scan_repo(deny_words):
    findings = []
    for p in tracked_files():
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except (OSError, IOError):
            continue
        for ln, code, hit in scan_text(text, deny_words, p):
            findings.append((p, ln, code, hit))
    return findings


def selftest():
    fails, n = [], [0]

    def ok(name, cond):
        n[0] += 1
        if not cond:
            fails.append(name)

    deny = ["금지어테스트"]
    codes = lambda t: {c for _, c, _ in scan_text(t, deny)}  # noqa: E731
    ok("① 공고번호 잡음", "공고번호" in codes("공고 R26BK01711646 제안"))
    ok("① 예시 공고번호는 통과", "공고번호" not in codes("예시 공고번호 R26EX00000001 은 허용"))
    ok("② 원 단위 금액 잡음", "금액" in codes("추정가격 109,090,909원"))
    ok("② 콤마 하나(만 원)는 통과", "금액" not in codes("예산 1억 2,000만 원"))
    ok("② 글자 수는 통과", "금액" not in codes("본문 17,000자를 읽었다"))
    ok("③ 실명+직함 잡음(홍길동 대리)", "실명직함" in codes("담당은 홍길동 대리입니다"))
    ok("③ 실명+직함 잡음(신유진 이사)", "실명직함" in codes("신유진 이사가 총괄한다"))
    ok("③ 실명+감독 잡음(공백)", "실명직함" in codes("촬영은 김도현 감독이 맡는다"))
    ok("③ 콘텐츠 PM 은 통과", "실명직함" not in codes("실감콘텐츠 PM이 맡는다"))
    ok("③ 연출감독 역할어는 통과", "실명직함" not in codes("윤규상 연출감독 · 25년"))
    ok("③ 총괄 감독 은 통과", "실명직함" not in codes("체계는 총괄 감독 아래 다섯입니다"))
    ok("③ 대리수행 은 통과", "실명직함" not in codes("교육 대리수행 실적"))
    ok("④ 금지 낱말 잡음", "금지어" in codes("이번 사업은 금지어테스트 지역이다"))
    ok("④ 없으면 통과", not codes("평범한 문장은 아무것도 걸리지 않는다"))
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — %d건 통과(공고번호·금액·실명·금지어)" % n[0])
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="공개 저장소 유출 검사(공고번호·금액·실명·금지 낱말)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--list", action="store_true", help="검사 대상 파일만 출력")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.list:
        for p in tracked_files():
            print(p)
        return 0
    deny = load_deny()
    if not deny:
        print("ⓘ deny.txt 에 금지 낱말이 없다(%s) — 공고번호·금액·실명만 검사한다" % DENY_FILE, file=sys.stderr)
    findings = scan_repo(deny)
    for p, ln, code, hit in findings:
        print("%s:%d: [%s] %s" % (p, ln, code, hit))
    if findings:
        n_files = len({f[0] for f in findings})
        print("\n✗ 유출 의심 %d건 · 파일 %d개 — 위 자리를 예시(예시문화재단)로 바꾸거나 지운다." % (len(findings), n_files))
        return 1
    print("✓ 공개 범위 검사 통과 — 공고번호·금액·실명·금지 낱말 없음.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
