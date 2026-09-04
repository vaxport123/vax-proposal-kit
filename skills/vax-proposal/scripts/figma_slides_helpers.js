// figma_slides_helpers.js — Figma Slides 덱을 `use_figma` 스크립트로 만들 때 쓰는 공통 헬퍼.
// 실측 3덱 문법(figma-handoff.md §3~4)과 구성 규칙(slide-rules.md §5)을 코드로 고정한 것.
// 2026-09-04 순천캠퍼스 VR 덱(24장)을 만들며 알게 된 요령(figma-handoff.md §6)이 들어 있다.
//
// 쓰는 법: use_figma 스크립트 맨 앞에 이 파일 내용을 붙이고(모듈 import 없음), 아래처럼 부른다.
//   const P = { accent: "#0068B0", ink: "#141414", soft: "#3a3a3a", mid: "#68727f", line: "#d3dae3", face: "#f4f5f7", tint: "#e6f0f7" };
//   await loadFonts();
//   const row = figma.createSlideRow(); row.name = "Ⅱ. 사업수행 부문";
//   const s = figma.createSlide(row, 0);
//   chrome(s, P, { crumbChapter: "Ⅱ. 사업수행 부문", crumbSection: "3. 장비 납품", title: "장비는 제안요청서 9품목 전부 …", emph: ["9품목 전부"], sub: "…", page: "Ⅱ-13" });
//   const fig = await placeSvg(s, svgString, 96, 300, 1728);   // figures_svg.py가 뽑은 SVG
//   bar(s, P, "9품목 전부, 그 위에 예비 커버 5·여분 케이블 5", ["9품목 전부"]);
//   const logo = logoBox(s, 1824 - 180, 40, 180, 48);           // 뒤에 upload_assets(nodeIds, FIT)로 시그니처 PNG 채움
//
// 규칙: 색은 P에 있는 것만(강조 하나 + 무채색). 글꼴은 Freesentation 한 가족. 좌표는 전 장 동일 — 여기 상수 밖에서 좌표를 새로 만들지 않는다.

const W = 1920, H = 1080;
const X0 = 96, X1 = 1824, CONTENT_W = 1728;            // 좌우 여백 96
const Y_CRUMB = 48, Y_RULE = 112, Y_TITLE = 150, Y_BODY = 300, Y_BAR = 960, Y_PAGE = 1040;
const FONT = "Freesentation";
const F = { black: "9 Black", bold: "7 Bold", medium: "5 Medium", regular: "4 Regular", light: "3 Light" };

function hex(h) { const n = parseInt(h.slice(1), 16); return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 }; }
function fill(h) { return [{ type: "SOLID", color: hex(h) }]; }

async function loadFonts() {
  // 글꼴이 없으면 대체하지 않고 멈춘다(figma-handoff §2). install.sh가 fonts/를 설치한다.
  const avail = await figma.listAvailableFontsAsync();
  for (const style of Object.values(F)) {
    if (!avail.some(f => f.fontName.family === FONT && f.fontName.style === style)) throw new Error(`글꼴 없음: ${FONT} ${style} — bash fonts/install-fonts.sh --force 후 Figma 재시작`);
    await figma.loadFontAsync({ family: FONT, style });
  }
}

// 글자 폭 추정(한글 1em · 영문 0.56 · 공백 0.28). textAutoResize=HEIGHT의 height가 스크립트 안에서 갱신되지 않아(10으로 읽힘) 줄 수를 이걸로 센다.
function estWidth(s, size) { let w = 0; for (const ch of s) { const c = ch.charCodeAt(0); w += ch === " " ? 0.28 : (c >= 0xac00 && c <= 0xd7a3) || c > 0x2e80 ? 1 : 0.56; } return w * size; }
function estLines(s, size, width) { return Math.max(1, Math.ceil(estWidth(s, size) / width)); }
function estHeight(s, size, width, lh = 1.35) { return estLines(s, size, width) * size * lh; }

function text(parent, s, x, y, size, style, color, opts = {}) {
  const t = figma.createText();
  parent.appendChild(t);
  t.fontName = { family: FONT, style };
  t.characters = s;
  t.fontSize = size;
  t.fills = fill(color);
  t.lineHeight = { value: (opts.lh || 1.35) * 100, unit: "PERCENT" };
  if (opts.width) { t.resize(opts.width, 10); t.textAutoResize = "HEIGHT"; } else { t.textAutoResize = "WIDTH_AND_HEIGHT"; }
  if (opts.align) t.textAlignHorizontal = opts.align;
  t.x = x; t.y = y;
  // 강조 낱말: 같은 텍스트 노드 안에서 범위 색만 바꾼다(제목 안 1~2개 · figma-handoff §1)
  for (const e of (opts.emph || [])) { const i = s.indexOf(e); if (i >= 0) { t.setRangeFills(i, i + e.length, fill(opts.emphColor)); if (opts.emphBold) t.setRangeFontName(i, i + e.length, { family: FONT, style: F.bold }); } }
  return t;
}
function rect(parent, x, y, w, h, color, r = 0) { const n = figma.createRectangle(); parent.appendChild(n); n.x = x; n.y = y; n.resize(w, h); n.fills = fill(color); n.cornerRadius = r; return n; }
function line(parent, x, y, w, color) { return rect(parent, x, y, w, 1, color); }

// 헤더(브레드크럼·실선) · 제목·부제 · 쪽번호. 시그니처 자리는 logoBox()로 따로(PNG는 upload_assets로 채운다).
// 반환: 부제 아래 y (본문 시작 y로 쓴다. Y_BODY보다 아래면 그 값을 쓴다)
function chrome(slide, P, o) {
  slide.fills = fill("#ffffff");
  const ch = text(slide, o.crumbChapter, X0, Y_CRUMB, 22, F.bold, P.ink);
  text(slide, "  ›  " + (o.crumbSection || ""), X0 + estWidth(o.crumbChapter, 22), Y_CRUMB, 22, F.light, P.mid);
  line(slide, X0, Y_RULE, CONTENT_W, P.line);
  const tl = estLines(o.title, 48, CONTENT_W);
  text(slide, o.title, X0, Y_TITLE, 48, F.bold, P.ink, { width: CONTENT_W, emph: o.emph, emphColor: P.accent, lh: 1.3 });
  let y = Y_TITLE + tl * 48 * 1.3 + 16;
  if (o.sub) { text(slide, o.sub, X0, y, 22, F.regular, P.mid, { width: CONTENT_W }); y += estHeight(o.sub, 22, CONTENT_W) + 12; }
  if (o.page) text(slide, o.page, W / 2 - 40, Y_PAGE, 15, F.light, P.mid, { width: 80, align: "CENTER" });   // 장별 번호 「Ⅱ-3」 — 표지·목차·약어표만 생략
  return Math.max(y, Y_BODY);
}

// 하단 결론 바 — 제목을 되풀이하지 않는 「그래서 발주처에 무엇이 좋은가」
function bar(slide, P, s, emph = []) {
  rect(slide, X0, Y_BAR, CONTENT_W, 60, P.tint, 6);
  text(slide, s, X0 + 28, Y_BAR + 17, 22, F.bold, P.ink, { width: CONTENT_W - 56, emph, emphColor: P.accent });
}

// 시그니처·사진 자리: 빈 사각형을 만들고 id를 모아 두면, 스크립트 뒤 `upload_assets(nodeIds, scaleMode)`로 PNG를 채운다(시그니처 FIT · 사진 FILL).
function logoBox(slide, x = X1 - 180, y = 40, w = 180, h = 48) { const n = rect(slide, x, y, w, h, "#ffffff"); n.name = "signature"; return n.id; }
function photoBox(slide, x, y, w, h, caption, P) {
  const n = rect(slide, x, y, w, h, P.face, 4); n.name = "photo";
  if (caption) text(slide, caption, x, y + h + 6, 13, F.light, P.mid, { width: w });   // 출처 캡션(images.md §3-5)
  return n.id;
}

// figures_svg.py가 뽑은 SVG를 편집 가능한 노드로. 폭에 맞춰 비율 유지 축소. 반환: 배치된 프레임(높이는 .height로 읽힌다 — SVG는 갱신된다)
async function placeSvg(slide, svgString, x, y, width) {
  const n = figma.createNodeFromSvg(svgString);
  slide.appendChild(n);
  const k = width / n.width;
  n.rescale(k);
  n.x = x; n.y = y;
  return n;
}

// 본문 텍스트 블록(18~20px, 3~6줄). 도식 옆 오른쪽 열에 초안 문단을 그대로 놓는다(slide-rules §4 — 요약하지 않는다).
function body(slide, P, paragraphs, x, y, width, size = 19) {
  let yy = y;
  for (const p of paragraphs) { text(slide, p, x, yy, size, F.regular, P.soft, { width, lh: 1.5 }); yy += estHeight(p, size, width, 1.5) + 18; }
  return yy;
}

// PART 구분 슬라이드: 옅은 바탕 · 거대 로마숫자 · 강조 세로선 · 장 제목 · 절 목록. 쪽번호는 장 첫 번호(예 Ⅱ-1).
function part(slide, P, o) {
  slide.fills = fill("#f4f5f7");
  text(slide, o.roman, 1100, 120, 420, F.black, "#e4e8ee");
  rect(slide, X0, 380, 6, 220, P.accent);
  text(slide, "PART " + o.roman, X0 + 40, 380, 24, F.bold, P.accent);
  text(slide, o.title, X0 + 40, 430, 76, F.bold, P.ink, { width: 1200 });
  let y = 560; for (const s of (o.sections || [])) { text(slide, s, X0 + 40, y, 24, F.regular, P.soft); y += 40; }
  if (o.page) text(slide, o.page, W / 2 - 40, Y_PAGE, 15, F.light, P.mid, { width: 80, align: "CENTER" });
}

// 목차: 장 로마숫자(강조색)·장 제목·절 목록만. **쪽번호를 적지 않는다**(한준 2026-09-04).
function toc(slide, P, chapters) {
  slide.fills = fill("#ffffff");
  text(slide, "제안 목차", X0, Y_TITLE, 48, F.bold, P.ink);
  line(slide, X0, Y_TITLE + 80, CONTENT_W, P.line);
  let y = Y_TITLE + 120;
  for (const c of chapters) {
    text(slide, c.roman, X0, y, 30, F.black, P.accent);
    text(slide, c.title, X0 + 90, y + 2, 28, F.bold, P.ink);
    text(slide, (c.sections || []).join("   ·   "), X0 + 90, y + 44, 20, F.regular, P.mid, { width: CONTENT_W - 90 });
    y += 44 + estHeight((c.sections || []).join("   ·   "), 20, CONTENT_W - 90) + 36;
  }
}

// 마지막 검사: 덱 전체 텍스트에서 내부 표기가 남았는지. 남으면 이름을 돌려준다 — 사람이 발표자 노트로 옮긴다.
function leftovers(pattern = /근거:|⚠️|확인필요|재료 팩/) {
  return figma.root.findAllWithCriteria({ types: ["TEXT"] }).filter(t => pattern.test(t.characters)).map(t => `${t.parent && t.parent.name}: ${t.characters.slice(0, 40)}`);
}
