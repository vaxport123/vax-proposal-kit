#!/usr/bin/env python3
"""회사소개서 마스터 HTML 안의 사진(base64 data URI)을 파일로 뽑아 assets/photos/ 에 둔다 (한준 2026-09-04 "그렇게 해").

왜: 슬라이드에는 실사가 들어가는데 직원 PC에는 사진이 한 장도 없었다. 정본 사진은 이 HTML(templates/company-intro)에
81장이 base64로 박혀 있다 — 그것을 이름 붙여 꺼내 두면 Figma·pptx에서 바로 쓴다.

사용:  python3 scripts/extract_assets.py            # templates/company-intro/*.html → assets/photos/
       python3 scripts/extract_assets.py --dry      # 무엇이 나오는지만
출력:  assets/photos/<키>.<확장자> + assets/photos/MANIFEST.md (키 · 크기 · HTML 안에서 쓰인 캡션)
"""
import argparse
import base64
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = glob.glob(os.path.join(ROOT, "templates", "company-intro", "*.html"))
OUT = os.path.join(ROOT, "assets", "photos")
EXT = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "webp": "webp", "gif": "gif", "svg+xml": "svg", "avif": "avif"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if not SRC:
        print("templates/company-intro/*.html 없음"); return 1
    html = io.open(SRC[0], encoding="utf-8", errors="replace").read()
    # 1) IMG 객체: 키 → data URI  (const IMG={kbs:"data:image/jpeg;base64,...", ...})
    # 키는 "jeongjo": 처럼 따옴표로 감싸져 있다(실측). 따옴표 유무 모두 받는다.
    pairs = re.findall(r"""["']?([A-Za-z_][A-Za-z0-9_]*)["']?\s*:\s*"(data:image/([a-z+]+);base64,([A-Za-z0-9+/=]+))\"""", html)
    # 2) 캡션: bg("kbs") 가 쓰인 곳 근처의 <span>…</span> 또는 배열 ["kbs","제목",…]
    caps = {}
    for m in re.finditer(r'\["([a-z0-9_]+)"\s*,\s*"([^"]{2,80})"', html):
        caps.setdefault(m.group(1), m.group(2))
    for m in re.finditer(r'bg\("([a-z0-9_]+)"\)\}?>\s*<span>([^<]{2,120})</span>', html):
        caps.setdefault(m.group(1), m.group(2))
    seen, rows = set(), []
    os.makedirs(OUT, exist_ok=True)
    for key, uri, mime, b64 in pairs:
        if key in seen:
            continue
        seen.add(key)
        ext = EXT.get(mime, mime)
        data = base64.b64decode(b64)
        path = os.path.join(OUT, f"{key}.{ext}")
        rows.append((key, ext, len(data), caps.get(key, "")))
        if not a.dry:
            with open(path, "wb") as f:
                f.write(data)
    rows.sort(key=lambda r: r[0])
    total = sum(r[2] for r in rows)
    if not a.dry:
        with io.open(os.path.join(OUT, "MANIFEST.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("# assets/photos — 회사 사진 자산 (회사소개서 마스터 v3에서 추출)\n\n")
            f.write(f"원본: `templates/company-intro/` HTML의 IMG 객체 {len(rows)}장 · 합계 {total/1e6:.1f}MB · `scripts/extract_assets.py`로 다시 만든다(손으로 고치지 않는다).\n")
            f.write("캡션은 HTML 안에서 그 사진이 쓰인 자리의 문구다 — 어느 사업 사진인지 판별용. 제안서에 넣을 때는 재료 팩 §5 실적명과 맞춰 쓴다.\n")
            f.write("대외 공개된 회사소개서의 사진이므로 제안서·발표자료에 쓸 수 있다. 발주처 로고·타사 사진은 여기 없다(발주처 CI는 figma-howto.md 절차로 따로 구한다).\n\n")
            f.write("| 파일 | 크기 | HTML 안 캡션(사업 힌트) |\n|---|---|---|\n")
            for key, ext, n, cap in rows:
                f.write(f"| `{key}.{ext}` | {n/1024:.0f}KB | {cap} |\n")
    print(f"{'[dry] ' if a.dry else ''}사진 {len(rows)}장 · {total/1e6:.1f}MB → {OUT}")
    for key, ext, n, cap in rows[:12]:
        print(f"  {key}.{ext:<4} {n/1024:5.0f}KB  {cap}")
    if len(rows) > 12:
        print(f"  … 외 {len(rows)-12}장 (MANIFEST.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
