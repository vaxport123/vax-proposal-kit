#!/usr/bin/env python3
"""웹에서 찾은 이미지를 사업 폴더에 **출처와 함께** 내려받는다 — `bids/<사업>/img/` + `MANIFEST.md`.

한준 2026-09-04: "필요한 건 웹 크롤링 통한 이미지 넣기".
찾는 일(검색·페이지 열기)은 Claude가 WebSearch·WebFetch로 한다. 이 스크립트는 **정한 URL을 받아**
내려받고, 크기를 확인하고, 출처를 적고, 슬라이드 폭에 맞춰 줄이는 일만 한다. 규칙은 `references/images.md`.

■ 왜 출처를 기계로 남기나
· 제안서는 발주처에 가고 Figma 링크는 밖으로 나간다. 어디서 가져왔는지 모르는 그림은 못 쓴다.
· MANIFEST에 URL·페이지·내려받은 날·용도·사용권 판단이 한 줄로 남으면 사람이 5초에 검토한다.
· 같은 URL을 다시 받지 않는다(파일명 = URL 해시 앞 8자 + 지정 이름).

■ 사용
  python3 img_fetch.py <사업폴더> <URL> --name suncheon-campus-3f --use "Ⅰ-1 캠퍼스 사진" --page <출처 페이지 URL> --license "발주처 공식 홈페이지 보도자료"
  python3 img_fetch.py <사업폴더> --list "urls.tsv"      # 탭 구분: url  name  use  page  license
  python3 img_fetch.py --selftest

■ 거부하는 것
· 600px 미만(짧은 변) — 1920 슬라이드에서 흐려진다.
· 이미지가 아닌 응답(HTML·리다이렉트 페이지).
· `--license` 비움 — 사용권 판단 없이 받지 않는다(빈칸은 나중에 아무도 안 채운다).
"""
import argparse
import hashlib
import io
import os
import re
import sys
import urllib.request
from datetime import date

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

MIN_SHORT = 600           # 짧은 변 최소 px
MAX_LONG = 1920           # 이보다 크면 줄여 저장(슬라이드 폭)
UA = "Mozilla/5.0 (proposal-kit img_fetch; contact: proposal team)"
HEAD = "| 파일 | 크기(px) | 용도(슬라이드) | 출처 페이지 | 원본 URL | 사용권 판단 | 받은 날 |\n|---|---|---|---|---|---|---|\n"


def _slug(s):
    s = re.sub(r"[^A-Za-z0-9가-힣_-]+", "-", str(s or "")).strip("-")
    return s[:40] or "img"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    return data, ctype


def check_and_shrink(data):
    """(bytes, (w,h), ext) — PIL이 있으면 크기 검사·축소, 없으면 그대로 두고 크기는 (0,0)."""
    try:
        from PIL import Image
    except ImportError:
        return data, (0, 0), _sniff_ext(data)
    im = Image.open(io.BytesIO(data))
    w, h = im.size
    if min(w, h) < MIN_SHORT:
        raise ValueError("너무 작다 %dx%d (짧은 변 %d 미만)" % (w, h, MIN_SHORT))
    ext = "png" if (im.mode in ("RGBA", "LA", "P") and _sniff_ext(data) == "png") else "jpg"
    if max(w, h) > MAX_LONG:
        k = MAX_LONG / float(max(w, h))
        im = im.resize((int(w * k), int(h * k)))
        w, h = im.size
    buf = io.BytesIO()
    if ext == "jpg":
        im.convert("RGB").save(buf, "JPEG", quality=86, optimize=True)
    else:
        im.save(buf, "PNG", optimize=True)
    return buf.getvalue(), (w, h), ext


def _sniff_ext(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if b"<svg" in data[:2000].lower():
        return "svg"
    raise ValueError("이미지가 아니다(HTML·리다이렉트 페이지일 수 있다)")


def save(bid_dir, url, name, use, page, license_note, data=None):
    if not str(license_note or "").strip():
        raise ValueError("--license 가 비어 있다. 사용권 판단 없이 받지 않는다(references/images.md §2)")
    img_dir = os.path.join(bid_dir, "img")
    os.makedirs(img_dir, exist_ok=True)
    h8 = hashlib.sha1(url.encode()).hexdigest()[:8]
    for f in os.listdir(img_dir):
        if f.startswith(h8 + "-"):
            return os.path.join(img_dir, f), "이미 있음"
    if data is None:
        data, _ = fetch(url)
    data, (w, hgt), ext = check_and_shrink(data)
    fn = "%s-%s.%s" % (h8, _slug(name), ext)
    path = os.path.join(img_dir, fn)
    open(path, "wb").write(data)
    man = os.path.join(img_dir, "MANIFEST.md")
    if not os.path.exists(man):
        open(man, "w", encoding="utf-8").write("# img — 웹에서 확보한 이미지(출처 필수)\n\n규칙: `references/images.md`. 이 표에 없는 그림은 덱에 넣지 않는다.\n\n" + HEAD)
    row = "| `%s` | %dx%d | %s | %s | %s | %s | %s |\n" % (fn, w, hgt, use or "", page or "", url, license_note, date.today().isoformat())
    open(man, "a", encoding="utf-8").write(row)
    return path, "%dx%d" % (w, hgt)


def selftest():
    import tempfile
    fails = []

    def ok(n, c):
        if not c:
            fails.append(n)

    ok("슬러그", _slug("순천 캠퍼스/3층!") == "순천-캠퍼스-3층")
    ok("PNG 판별", _sniff_ext(b"\x89PNG\r\n\x1a\n" + b"0" * 10) == "png")
    try:
        _sniff_ext(b"<html><body>hi</body></html>")
        ok("HTML은 거부", False)
    except ValueError:
        pass
    try:
        from PIL import Image
        im = Image.new("RGB", (300, 300), "white")
        b = io.BytesIO()
        im.save(b, "PNG")
        try:
            check_and_shrink(b.getvalue())
            ok("작은 그림 거부", False)
        except ValueError:
            pass
        im = Image.new("RGB", (4000, 2000), "white")
        b = io.BytesIO()
        im.save(b, "JPEG")
        _, (w, h), ext = check_and_shrink(b.getvalue())
        ok("큰 그림은 1920으로", w == 1920 and h == 960 and ext == "jpg")
        with tempfile.TemporaryDirectory() as td:
            try:
                save(td, "http://x/a.jpg", "a", "u", "p", "", data=b.getvalue())
                ok("사용권 비면 거부", False)
            except ValueError:
                pass
            p, info = save(td, "http://x/a.jpg", "a", "Ⅰ-1", "http://x", "공식 보도자료", data=b.getvalue())
            ok("저장·MANIFEST", os.path.exists(p) and "1920x960" in open(os.path.join(td, "img", "MANIFEST.md"), encoding="utf-8").read())
            p2, info2 = save(td, "http://x/a.jpg", "a", "Ⅰ-1", "http://x", "공식 보도자료", data=b.getvalue())
            ok("같은 URL은 다시 받지 않음", info2 == "이미 있음" and p2 == p)
    except ImportError:
        print("(PIL 없음 — 크기 검사는 건너뜀)")
    print(("selftest 실패 " + " | ".join(fails)) if fails else "selftest OK — 이미지 판별·크기·사용권·중복 검사")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="웹 이미지 내려받기 + 출처 MANIFEST")
    ap.add_argument("bid_dir", nargs="?")
    ap.add_argument("url", nargs="?")
    ap.add_argument("--name", default="")
    ap.add_argument("--use", default="", help="어느 슬라이드에 쓰나 (예: Ⅰ-1 캠퍼스 사진)")
    ap.add_argument("--page", default="", help="이미지가 실린 출처 페이지 URL")
    ap.add_argument("--license", default="", help="사용권 판단 한 줄(필수). 예: 발주처 공식 홈페이지 보도자료 / 제조사 제품 페이지 / CC BY")
    ap.add_argument("--list", default="", help="탭 구분 목록 파일: url name use page license")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.bid_dir:
        ap.error("bid_dir 가 필요하다")
    jobs = []
    if a.list:
        for ln in open(a.list, encoding="utf-8"):
            if ln.strip() and not ln.startswith("#"):
                c = (ln.rstrip("\n").split("\t") + [""] * 5)[:5]
                jobs.append(c)
    elif a.url:
        jobs.append([a.url, a.name, a.use, a.page, a.license])
    else:
        ap.error("url 또는 --list 가 필요하다")
    rc = 0
    for url, name, use, page, lic in jobs:
        try:
            p, info = save(a.bid_dir, url, name, use, page, lic)
            print("OK  %s  %s" % (info, p))
        except Exception as ex:                    # noqa: BLE001
            rc = 1
            print("거부  %s  — %s" % (url, str(ex)[:120]))
    return rc


if __name__ == "__main__":
    sys.exit(main())
