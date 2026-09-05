#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""layout_wireframes.py — references/layouts.json(정본)에서 두 가지를 만든다.
  1) assets/layouts/L01.png … L14.png + catalog.png : 회사 팩트 없는 와이어프레임(문서·README용)
  2) scripts/figma_slides_layouts.js 의 /*LAYOUTS-BEGIN*/ … /*LAYOUTS-END*/ 블록 : Figma에서 쓰는 좌표 사본
사용: python3 layout_wireframes.py            (둘 다)
      python3 layout_wireframes.py --selftest (JSON 무결성 · 겹침 · 경계)
JSON을 고친 뒤 이 스크립트를 돌린다. JS나 PNG를 직접 고치지 않는다.
"""
import json, os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
JSON_PATH = os.path.join(HERE, "..", "references", "layouts.json")
JS_PATH = os.path.join(HERE, "figma_slides_layouts.js")
OUT_DIR = os.path.join(ROOT, "assets", "layouts")

ROLE_COLOR = {"photo": (200, 214, 228), "overlay": None, "logo": (235, 235, 235), "text": None, "card": (244, 245, 247), "card-dark": (11, 31, 51),
              "panel": (244, 245, 247), "panel-tint": (230, 240, 247), "label": (0, 104, 176), "arrow": None, "rows": (250, 250, 250),
              "table": (244, 245, 247), "gantt": (244, 245, 247), "ghost-number": None}


def load():
    with io.open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def expand(layout):
    """repeat 규칙(사진 스트립 등)을 펼쳐 실제 존 목록을 돌려준다."""
    zones = list(layout["zones"])
    rep = layout.get("repeat")
    if not rep:
        return zones
    out = []
    base = {z["id"]: z for z in zones if z["id"] in rep["ids"]}
    others = [z for z in zones if z["id"] not in rep["ids"]]
    w0 = base[rep["ids"][0]]["w"]
    for i in range(rep["count"]):
        dx = i * (w0 + rep["gap"])
        for zid in rep["ids"]:
            z = dict(base[zid]); z["id"] = "%s%d" % (zid, i + 1); z["x"] = z["x"] + dx; out.append(z)
    return out + others


def selftest(data):
    fails = []
    keys = [l["key"] for l in data["layouts"]]
    if len(keys) != len(set(keys)): fails.append("key 중복")
    for l in data["layouts"]:
        zs = expand(l)
        ids = [z["id"] for z in zs]
        if len(ids) != len(set(ids)): fails.append(l["key"] + " zone id 중복")
        for z in zs:
            if z["x"] < 0 or z["y"] < 0 or z["x"] + z["w"] > 1920 + 1 or z["y"] + z["h"] > 1080 + 1:
                fails.append("%s %s 경계 이탈" % (l["key"], z["id"]))
        if l.get("chrome"):
            for z in zs:
                if z["role"] not in ("text",) and z["y"] < 250 and z["role"] not in ("overlay",):
                    fails.append("%s %s 가 헤더·제목 영역(y<250)을 침범" % (l["key"], z["id"]))
                if z["role"] not in ("text",) and z["y"] + z["h"] > 930 and z["role"] not in ("overlay", "photo"):
                    fails.append("%s %s 가 결론 띠(y≥930)를 침범" % (l["key"], z["id"]))
    print("selftest 실패: " + " | ".join(fails) if fails else "selftest OK — 레이아웃 %d개 · 존 %d개" % (len(data["layouts"]), sum(len(expand(l)) for l in data["layouts"])))
    return 1 if fails else 0


def render(data):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("PIL 없음 — PNG는 건너뜀 (pip install pillow)"); return
    os.makedirs(OUT_DIR, exist_ok=True)
    g = data["grid"]; thumbs = []
    for l in data["layouts"]:
        im = Image.new("RGB", (1920, 1080), (255, 255, 255)); d = ImageDraw.Draw(im)
        if l.get("chrome"):
            hb = g["header"]["band"]; d.rectangle([hb[0], hb[1], hb[0] + hb[2], hb[1] + hb[3]], fill=(248, 249, 250)); d.line([0, 90, 1920, 90], fill=(211, 218, 227), width=2)
            d.rectangle([g["header"]["crumb"]["x"], 28, g["header"]["crumb"]["x"] + 260, 60], outline=(150, 150, 150))
            lg = g["header"]["logo"]; d.rectangle([lg["x"], lg["y"], lg["x"] + lg["w"], lg["y"] + lg["h"]], fill=(230, 230, 230))
            t = g["title"]; d.rectangle([t["x"], t["y"], t["x"] + 1100, t["y"] + 58], fill=(20, 20, 20)); d.rectangle([t["x"] + 1110, t["y"], t["x"] + 1400, t["y"] + 58], fill=(0, 104, 176))
            s = g["subtitle"]; d.rectangle([s["x"], s["y"], s["x"] + 700, s["y"] + 24], fill=(180, 186, 194))
            cb = g["closingBar"]; d.rectangle([cb["x"], cb["y"], cb["x"] + cb["w"], cb["y"] + cb["h"]], fill=(230, 240, 247)); d.rectangle([cb["x"], cb["y"], cb["x"] + cb["accentBar"], cb["y"] + cb["h"]], fill=(0, 104, 176))
            d.rectangle([cb["x"] + 30, cb["y"] + 26, cb["x"] + 900, cb["y"] + 50], fill=(20, 20, 20))
            p = g["page"]; d.rectangle([p["x"] + 40, p["y"], p["x"] + 80, p["y"] + 16], fill=(180, 186, 194))
        for z in expand(l):
            x, y, w, h = z["x"], z["y"], z["w"], z["h"]; r = z["role"]
            if r == "overlay": d.rectangle([x, y, x + w, y + h], fill=(11, 31, 51))  # 사진 위 어두운 덮개 = 어두운 면으로 표시
            elif r == "photo": d.rectangle([x, y, x + w, y + h], fill=ROLE_COLOR["photo"]); d.line([x, y, x + w, y + h], fill=(160, 175, 190), width=3); d.line([x + w, y, x, y + h], fill=(160, 175, 190), width=3)
            elif r == "text":
                col = {"paper": (255, 255, 255), "accent": (0, 104, 176), "mid": (150, 156, 165), "ink": (20, 20, 20)}.get(z.get("color", "ink"), (20, 20, 20))
                bh = min(h, int(z.get("size", 20) * 0.9)); d.rectangle([x, y, x + min(w, int(len(z.get("text", "글")) * z.get("size", 20) * 0.9)), y + bh], fill=col)
            elif r == "ghost-number": d.rectangle([x, y, x + w, y + h], outline=(230, 236, 242), width=6)
            elif r == "arrow": d.line([x, y + h // 2, x + w, y + h // 2], fill=(0, 104, 176), width=6); d.polygon([(x + w, y + h // 2), (x + w - 16, y + h // 2 - 10), (x + w - 16, y + h // 2 + 10)], fill=(0, 104, 176))
            elif r == "label": d.rectangle([x, y, x + w, y + h], fill=(0, 104, 176))
            elif r == "logo": d.rectangle([x, y, x + w, y + h], fill=(230, 230, 230))
            elif r in ("card", "panel", "panel-tint", "card-dark", "rows"):
                d.rectangle([x, y, x + w, y + h], fill=ROLE_COLOR[r], outline=(211, 218, 227))
                if r == "card":
                    fy = y + 28
                    for i, f in enumerate(z.get("fields", [])):
                        fh = 34 if i == 0 else 22; d.rectangle([x + 28, fy, x + min(w - 56, 60 + len(f) * 18), fy + fh], fill=(20, 20, 20) if i < 2 else (120, 126, 134)); fy += fh + 18
                if r == "rows":
                    for i in range(z.get("count", 4)):
                        ry = y + i * z.get("rowH", 88); d.ellipse([x, ry, x + 40, ry + 40], fill=(0, 104, 176)); d.rectangle([x + 60, ry + 8, x + w, ry + 30], fill=(60, 60, 60))
            elif r == "table":
                d.rectangle([x, y, x + w, y + z["headH"]], fill=(0, 74, 128)); cx = x
                for i, cw in enumerate(z["cols"]): d.line([cx, y, cx, y + h], fill=(255, 255, 255), width=2); cx += cw
                for i in range(1, (h - z["headH"]) // z["rowH"] + 1):
                    ry = y + z["headH"] + (i - 1) * z["rowH"]; d.rectangle([x, ry, x + w, ry + z["rowH"]], fill=(244, 245, 247) if i % 2 else (255, 255, 255), outline=(230, 234, 238))
            elif r == "gantt":
                d.rectangle([x, y, x + w, y + z["headH"]], fill=(0, 74, 128)); colw = (w - z["labelW"]) // z["cols"]
                for i in range(z["rows"]):
                    ry = y + z["headH"] + i * z["rowH"]; d.rectangle([x, ry, x + w, ry + z["rowH"]], fill=(244, 245, 247) if i % 2 else (255, 255, 255), outline=(230, 234, 238))
                    bx = x + z["labelW"] + (i * colw * 0.6) % (w - z["labelW"] - colw); d.rectangle([bx + 10, ry + 12, bx + colw * 0.9, ry + z["rowH"] - 12], fill=(0, 104, 176))
                for c in range(z["cols"] + 1): d.line([x + z["labelW"] + c * colw, y, x + z["labelW"] + c * colw, y + h], fill=(255, 255, 255), width=2)
        d.rectangle([0, 0, 1919, 1079], outline=(200, 200, 200))
        im.save(os.path.join(OUT_DIR, l["key"] + ".png")); thumbs.append((l["key"] + " " + l["name"], im.resize((640, 360))))
    cols = 4; rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 640, rows * 384), "white"); d = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        fnt = ImageFont.truetype(os.path.join(ROOT, "fonts", "Freesentation", "Freesentation-5Medium.ttf"), 18)
    except Exception:
        fnt = None
    for i, (label, t) in enumerate(thumbs):
        x = (i % cols) * 640; y = (i // cols) * 384; sheet.paste(t, (x, y + 24)); d.text((x + 6, y + 4), label, fill="black", font=fnt); d.rectangle([x, y + 24, x + 639, y + 383], outline=(160, 160, 160))
    sheet.save(os.path.join(OUT_DIR, "catalog.png")); print("PNG %d + catalog.png → %s" % (len(thumbs), os.path.relpath(OUT_DIR, ROOT)))


def emit_js(data):
    with io.open(JS_PATH, encoding="utf-8") as f:
        js = f.read()
    a, b = "/*LAYOUTS-BEGIN*/", "/*LAYOUTS-END*/"
    if a not in js or b not in js:
        sys.exit("JS에 LAYOUTS 마커가 없다")
    payload = {"grid": data["grid"], "layouts": {l["key"]: dict(l, zones=expand(l)) for l in data["layouts"]}}
    for l in payload["layouts"].values(): l.pop("repeat", None)
    block = a + "\nconst LAYOUT_DATA = " + json.dumps(payload, ensure_ascii=False, indent=None) + ";\n" + b
    js = js[:js.index(a)] + block + js[js.index(b) + len(b):]
    with io.open(JS_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(js)
    print("JS LAYOUTS 블록 갱신 → %s" % os.path.relpath(JS_PATH, ROOT))


if __name__ == "__main__":
    data = load()
    if "--selftest" in sys.argv:
        sys.exit(selftest(data))
    if selftest(data):
        sys.exit(1)
    render(data)
    emit_js(data)
