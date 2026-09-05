// figma_slides_helpers.js — Figma Slides 덱을 `use_figma` 스크립트로 만들 때 쓰는 공통 헬퍼.
// 슬라이드 규칙(deck.md §4 헤더·쪽번호·글꼴)과 실측 요령(figma-howto.md)을 코드로 옮긴 것.
// 2026-09-05: 아래 좌표 상수는 **기본값**이다. 전 장 같아야 하는 것은 헤더(브레드크럼·실선·시그니처)와 쪽번호만이고(deck.md §4),
// 본문·결론 바 위치는 장의 내용에 따라 바꾼다(46장 덱에서 y=960 고정 결론 바가 하단 1/3 공백을 만들었다).
// 모든 프리미티브는 appendChild 뒤에 x·y를 준다(Figma 공식 figma-use-slides 스킬의 「(-240,-240) 어긋남」 회피 — 순서를 바꾸지 말 것).
// 프리미티브(text·rect·line·loadFonts·logoBox·photoBox·placeSvg·notes·retitle·validate·leftovers)는 그대로 쓰고, 조합 함수(chrome·bar·part·toc·body)는 **예시**다 —
// 덱의 디자인 브리프(deck.md §5)에 맞는 레이아웃 가족을 새로 짜는 쪽이 맞다(한준 2026-09-05 "디자인·레이아웃 자율").
//
// 쓰는 법: use_figma 스크립트 맨 앞에 이 파일 내용을 붙이고(모듈 import 없음), 아래처럼 부른다.
//   const P = { accent: "#0068B0", ink: "#141414", soft: "#3a3a3a", mid: "#68727f", line: "#d3dae3", face: "#f4f5f7", tint: "#e6f0f7" };
//   await loadFonts();
//   const row = figma.createSlideRow(); row.name = "Ⅱ. 사업수행 부문";
//   const s = figma.createSlide(row, 0);
//   chrome(s, P, { crumbChapter: "Ⅱ. 사업수행 부문", crumbSection: "3. 장비 납품", title: "장비는 제안요청서 9품목 전부 …", emph: ["9품목 전부"], sub: "…", page: "Ⅱ-13" });
//   const fig = await placeSvg(s, svgString, 96, 300, 1728);   // figures_svg.py가 뽑은 SVG
//   bar(s, P, "9품목 전부, 그 위에 예비 커버 5·여분 케이블 5", ["9품목 전부"], fig.y + fig.height + 24);   // 본문 바로 아래. 없어도 된다
//   const logo = logoBox(s, 1824 - 180, 40, 180, 48);           // 뒤에 upload_assets(nodeIds, FIT)로 시그니처 PNG 채움
//
// 규칙: 색은 P에 있는 것만(강조 하나 + 무채색). 글꼴은 Freesentation 한 가족. 헤더·쪽번호 좌표만 전 장 동일.

const W = 1920, H = 1080;
const X0 = 96, X1 = 1824, CONTENT_W = 1728;            // 좌우 여백 96
const Y_CRUMB = 48, Y_RULE = 112, Y_TITLE = 150, Y_BODY = 300, Y_BAR = 960, Y_PAGE = 1040;
const FONT = "Freesentation";
const F = { black: "9 Black", bold: "7 Bold", medium: "5 Medium", regular: "4 Regular", light: "3 Light" };
// 글자 단계 기본값(deck.md §4 기준선 · 2026-09-05 한준 "폰트가 작다" 뒤 한 단계 올림). 브리프가 다르면 T를 덮어쓴다: Object.assign(T, { title: 60 }).
const T = { title: 54, sub: 24, key: 28, cardTitle: 36, body: 22, number: 150, table: 20, caption: 13, crumb: 22, page: 15, part: 84 };

function hex(h) { const n = parseInt(h.slice(1), 16); return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 }; }
function fill(h) { return [{ type: "SOLID", color: hex(h) }]; }

async function loadFonts() {
  // 글꼴이 없으면 대체하지 않고 멈춘다(deck.md §4). install.sh가 fonts/를 설치한다.
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
  if (opts.name) t.name = opts.name;   // validate()·retitle()·leftovers()가 이름으로 찾는다: title · closing · crumb · page · caption · src · bg-*
  t.x = x; t.y = y;
  // 강조 낱말: 같은 텍스트 노드 안에서 범위 색만 바꾼다(제목 안 1~2개 · deck.md §4)
  for (const e of (opts.emph || [])) { if (!opts.emphColor) break; const i = s.indexOf(e); if (i >= 0) { t.setRangeFills(i, i + e.length, fill(opts.emphColor)); if (opts.emphBold) t.setRangeFontName(i, i + e.length, { family: FONT, style: F.bold }); } }
  return t;
}
function rect(parent, x, y, w, h, color, r = 0) { const n = figma.createRectangle(); parent.appendChild(n); n.x = x; n.y = y; n.resize(w, h); n.fills = fill(color); n.cornerRadius = r; return n; }
function line(parent, x, y, w, color) { return rect(parent, x, y, w, 1, color); }

// 헤더(브레드크럼·실선) · 제목·부제 · 쪽번호. 시그니처 자리는 logoBox()로 따로(PNG는 upload_assets로 채운다).
// 반환: 부제 아래 y (본문 시작 y로 쓴다. Y_BODY보다 아래면 그 값을 쓴다)
function chrome(slide, P, o) {
  slide.fills = fill("#ffffff");
  const ch = text(slide, o.crumbChapter, X0, Y_CRUMB, T.crumb, F.bold, P.ink, { name: "crumb" });
  text(slide, "  ›  " + (o.crumbSection || ""), X0 + estWidth(o.crumbChapter, T.crumb), Y_CRUMB, T.crumb, F.light, P.mid, { name: "crumb-sec" });
  line(slide, X0, Y_RULE, CONTENT_W, P.line).name = "bg-rule";
  const ts = o.titleSize || T.title, tl = estLines(o.title, ts, CONTENT_W);
  text(slide, o.title, X0, Y_TITLE, ts, F.bold, P.ink, { width: CONTENT_W, emph: o.emph, emphColor: P.accent, lh: 1.3, name: "title" });
  let y = Y_TITLE + tl * ts * 1.3 + 16;
  if (o.sub) { text(slide, o.sub, X0, y, T.sub, F.regular, P.mid, { width: CONTENT_W }); y += estHeight(o.sub, T.sub, CONTENT_W) + 12; }
  if (o.page) text(slide, o.page, W / 2 - 40, Y_PAGE, T.page, F.light, P.mid, { width: 80, align: "CENTER", name: "page" });   // 장별 번호 「Ⅱ-3」 — 표지·목차·약어표만 생략
  return Math.max(y, Y_BODY);
}

// 결론 바 — 있어도 되고 없어도 된다(deck.md §4). 있으면 제목을 되풀이하지 않는 「그래서 발주처에 무엇이 좋은가」를,
// 본문 바로 아래(y = 마지막 요소 아래 + 24)에 둔다. y를 안 주면 옛 기본값(바닥 고정) — 본문이 짧은 장에서는 쓰지 않는다.
function bar(slide, P, s, emph = [], y = Y_BAR) {
  y = Math.min(y, Y_BAR);
  rect(slide, X0, y, CONTENT_W, 64, P.tint, 6).name = "bg-bar";
  text(slide, s, X0 + 28, y + 14, T.key, F.bold, P.ink, { width: CONTENT_W - 56, emph, emphColor: P.accent, name: "closing" });
  return y + 64;
}

// 시그니처·사진 자리: 빈 사각형을 만들고 id를 모아 두면, 스크립트 뒤 `upload_assets(nodeIds, scaleMode)`로 PNG를 채운다(시그니처 FIT · 사진 FILL).
function logoBox(slide, x = X1 - 180, y = 40, w = 180, h = 48) { const n = rect(slide, x, y, w, h, "#ffffff"); n.name = "signature"; return n.id; }
function photoBox(slide, x, y, w, h, caption, P) {
  const n = rect(slide, x, y, w, h, P.face, 4); n.name = "photo";
  if (caption) text(slide, caption, x, y + h + 6, 13, F.light, P.mid, { width: w });   // 출처 캡션(images.md §3-5)
  return n.id;
}

// figures_svg.py가 뽑은 SVG를 편집 가능한 노드로. 폭은 본문 전폭(1728)으로만 — 좁히면 글자가 18px 아래로 내려간다(deck.md §3). 반환: 배치된 프레임(.height가 갱신된다)
async function placeSvg(slide, svgString, x, y, width) {
  const n = figma.createNodeFromSvg(svgString);
  slide.appendChild(n);
  const k = width / n.width;
  n.rescale(k);
  n.x = x; n.y = y;
  return n;
}

// 화면에 남기는 핵심 문장 1~2개(22px 기준선). 초안 문단 전체는 화면이 아니라 notes()로 보낸다(deck.md §2-2 · 한준 2026-09-05 "글자만 많고 도식이 적다").
// 문단이 화면에 꼭 있어야 하는 장(회사 소개·서술이 곧 내용인 절)에만 문단을 넣는다. 반환: 마지막 줄 아래 y.
function body(slide, P, paragraphs, x, y, width, size = T.body) {
  let yy = y;
  for (const p of paragraphs) { text(slide, p, x, yy, size, F.regular, P.soft, { width, lh: 1.5 }); yy += estHeight(p, size, width, 1.5) + 18; }
  return yy;
}

// 발표자 노트 — 초안 문단·⚠️ 확인필요·「발표에서 건너뜀」 표시가 여기로 간다(마크다운 불릿). 계획의 「초안 문단 번호」 열이 「있음」이 되는 자리.
function notes(slide, items, skipInTalk = false) {
  const lines = (skipInTalk ? ["- (발표에서 건너뜀)"] : []).concat(items.map(p => "- " + p));
  slide.speakerNotes = lines.join("\n");
}

// 제목 교체 — 계획서의 제목 사슬을 고친 뒤(deck.md §2-1) name "title" 노드의 글만 바꾼다. 장을 다시 만들지 않는다. map: { "슬라이드 이름": "새 제목" }
async function retitle(map) {
  await loadFonts();
  const done = [];
  for (const s of figma.getSlideGrid().flat()) { const t = map[s.name]; if (!t) continue; const n = s.children.find(c => c.name === "title" && c.type === "TEXT"); if (!n) { done.push(s.name + ": title 없음"); continue; } n.characters = t; done.push(s.name); }
  return done;
}

// PART 구분 슬라이드: 옅은 바탕 · 거대 로마숫자 · 강조 세로선 · 장 제목 · 절 목록. 쪽번호는 장 첫 번호(예 Ⅱ-1).
function part(slide, P, o) {
  slide.fills = fill("#f4f5f7");
  text(slide, o.roman, 1100, 120, 420, F.black, "#e4e8ee");
  rect(slide, X0, 380, 6, 220, P.accent);
  text(slide, "PART " + o.roman, X0 + 40, 380, 24, F.bold, P.accent);
  text(slide, o.title, X0 + 40, 430, T.part, F.bold, P.ink, { width: 1200, name: "title" });
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

// 배치 검사(Figma 공식 figma-use-slides 스킬의 batch validation을 옮긴 것 · 2026-09-05): 형제 겹침·글자 잘림·경계 이탈을 3초에 본다.
// 행(장)을 하나 만들 때마다 돌리고, clean이면 화면을 안 찍고 다음 행으로. 아니면 그 장만 찍어 고친다.
// 겹침 예외: 사진 위 덮개·시그니처·결론 바 배경처럼 겹치도록 만든 것은 name에 "bg" 또는 "photo"를 넣어 두면 뺀다.
async function validate(slideIds, opts = {}) {
  const OVERLAP = opts.overlap || 4, OVERFLOW = 1, ignore = opts.ignore || /bg|photo|signature|overlay/i;
  const issues = [];
  const slides = await Promise.all(slideIds.map(id => figma.getNodeByIdAsync(id)));
  for (const slide of slides) {
    if (!slide) continue;
    const ch = slide.children.map(c => ({ id: c.id, name: c.name, type: c.type, x: c.x, y: c.y, w: c.width, h: c.height, n: c }));
    for (let i = 0; i < ch.length; i++) for (let j = i + 1; j < ch.length; j++) {
      const a = ch[i], b = ch[j];
      if (ignore.test(a.name) || ignore.test(b.name)) continue;
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x), oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ox >= OVERLAP && oy >= OVERLAP) issues.push({ slide: slide.name, type: "overlap", nodes: [a.name, b.name] });
    }
    for (const c of ch) {
      if (c.type === "FRAME") for (const t of c.n.findAllWithCriteria({ types: ["TEXT"] })) {
        const ab = t.absoluteBoundingBox, pb = c.n.absoluteBoundingBox;
        if (ab && pb && (ab.x + ab.width > pb.x + pb.width + OVERFLOW || ab.y + ab.height > pb.y + pb.height + OVERFLOW)) issues.push({ slide: slide.name, type: "textClip", node: t.name });
      }
      if (c.x + c.w < -OVERLAP || c.y + c.h < -OVERLAP || c.x > W + OVERLAP || c.y > H + OVERLAP) issues.push({ slide: slide.name, type: "outOfBounds", node: c.name });
      if (c.type === "TEXT" && typeof c.n.fontSize === "number" && c.n.fontSize < 18 && !/caption|page|crumb|src/i.test(c.name)) issues.push({ slide: slide.name, type: "smallText", node: c.name, size: c.n.fontSize });   // deck.md §4 본문 18px 하한
    }
    // 빈 면적: 헤더 아래(140)~쪽번호 위(1020) 본문 영역에서 자식 상자들이 덮는 비율(대략)
    const body = { y0: 140, y1: 1020 }; let covered = 0;
    for (const c of ch) { const y0 = Math.max(c.y, body.y0), y1 = Math.min(c.y + c.h, body.y1); if (y1 > y0) covered += (y1 - y0) * Math.min(c.w, CONTENT_W); }
    const ratio = covered / ((body.y1 - body.y0) * CONTENT_W);
    if (ratio < 0.66 && ch.length > 3) issues.push({ slide: slide.name, type: "emptyArea", filled: Math.round(ratio * 100) + "%" });   // deck.md §5 빈 면적 1/3 상한(추정치 — 화면으로 확인)
  }
  return { clean: issues.length === 0, issues };
}

// 마지막 검사: 덱 전체 텍스트에서 내부 표기가 남았는지. 남으면 이름을 돌려준다 — 사람이 발표자 노트로 옮긴다.
function leftovers(pattern = /근거:|⚠️|확인필요|재료 팩/) {
  return figma.root.findAllWithCriteria({ types: ["TEXT"] }).filter(t => pattern.test(t.characters)).map(t => `${t.parent && t.parent.name}: ${t.characters.slice(0, 40)}`);
}
