// figma_slides_helpers.js — Figma Slides 덱을 `use_figma` 스크립트로 만들 때 쓰는 공통 프리미티브.
// 2026-09-06: 위에서 아래로 쌓는 조합 함수(chrome·bar·body·part·toc)를 지웠다. AI가 좌표를 계산해 흘려 쌓은 화면은 문서를 늘려 붙인 것이 됐고 재배치가 끝나지 않았다(순천 v5 실측).
// 레이아웃은 증거 유형별 컴포넌트에서 고른다(deck.md §5 — 회사 손 덱 3개에서 뽑는 것이 다음 일). 이 파일은 그 컴포넌트를 채우거나, 지도·연결도·배치도·타임라인(figma_slides_diagrams.js)을 그릴 때 필요한 원자 함수만 둔다.
// 모든 프리미티브는 appendChild 뒤에 x·y를 준다(Figma 공식 figma-use-slides 스킬의 「(-240,-240) 어긋남」 회피 — 순서를 바꾸지 말 것).
// 노드 이름 규약(validate·retitle·leftovers가 이름으로 찾는다): title · closing · crumb · crumb-sec · page · caption · src · signature · photo-* · bg-*(rule·dot·th·tr·zone·path·arrow·stop·hmd…). 역할마다 이름 하나 — 간트 막대와 결론 배경에 같은 이름을 쓰면 재배치 스크립트가 막대를 끌고 간다.
//
// 쓰는 법: use_figma 스크립트 맨 앞에 이 파일을 붙이고(모듈 import 없음) 필요하면 figma_slides_diagrams.js 를 이어 붙인다.
//   const P = { accent: "#0068B0", deep: "#004A80", tint: "#E6F0F7", ink: "#141414", soft: "#4C4C4C", mid: "#6B7480", line: "#D3DAE3", face: "#F4F5F7", paper: "#FFFFFF" };
//   await loadFonts();
//   const s = figma.getSlideGrid().flat().find(x => x.name === "20");
//   text(s, "액션 타이틀 한 문장", 96, 150, T.title, F.bold, P.ink, { width: 1728, name: "title" });
//   notes(s, ["초안 문단 …"]);                                   // 문단은 화면이 아니라 노트
//   const r = await validate([s.id]);                            // 겹침·경계·작은 글자
// 규칙: 색은 P에 있는 것만(강조 하나 + 무채색). 글꼴은 Freesentation 한 가족. 헤더·쪽번호 좌표만 전 장 동일(deck.md §4).

const W = 1920, H = 1080;
const X0 = 96, X1 = 1824, CONTENT_W = 1728;            // 좌우 여백 96
const Y_CRUMB = 48, Y_RULE = 112, Y_TITLE = 150, Y_PAGE = 1040;
const FONT = "Freesentation";
const F = { black: "9 Black", bold: "7 Bold", medium: "5 Medium", regular: "4 Regular", light: "3 Light" };
// 글자 단계 기본값(deck.md §4 기준선). 브리프가 다르면 덮어쓴다: Object.assign(T, { title: 60 }).
const T = { title: 54, sub: 24, key: 28, cardTitle: 36, body: 22, number: 150, table: 20, caption: 13, crumb: 22, page: 15, part: 84 };

function hex(h) { const n = parseInt(h.slice(1), 16); return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 }; }
function fill(h, op) { return [{ type: "SOLID", color: hex(h), ...(op !== undefined ? { opacity: op } : {}) }]; }

async function loadFonts() {
  // 글꼴이 없으면 대체하지 않고 멈춘다(deck.md §4). install.sh가 fonts/를 설치한다. Paperlogy는 로컬에 있어도 Figma 목록에 안 뜰 수 있다 → Freesentation 9 Black.
  const avail = await figma.listAvailableFontsAsync();
  for (const style of Object.values(F)) {
    if (!avail.some(f => f.fontName.family === FONT && f.fontName.style === style)) throw new Error(`글꼴 없음: ${FONT} ${style} — bash fonts/install-fonts.sh --force 후 Figma 재시작`);
    await figma.loadFontAsync({ family: FONT, style });
  }
}

// 글자 폭 추정(한글 1em · 영문 0.56 · 공백 0.28). 새로 만든 textAutoResize=HEIGHT 텍스트의 height는 같은 스크립트 안에서 갱신되지 않아(10으로 읽힘) 줄 수를 이걸로 센다. 이미 있는 노드의 height는 믿어도 된다.
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
  if (opts.name) t.name = opts.name;
  t.x = x; t.y = y;
  // 강조 낱말: 같은 텍스트 노드 안에서 범위 색만 바꾼다(제목 안 1~2개)
  for (const e of (opts.emph || [])) { if (!opts.emphColor) break; const i = s.indexOf(e); if (i >= 0) { t.setRangeFills(i, i + e.length, fill(opts.emphColor)); if (opts.emphBold) t.setRangeFontName(i, i + e.length, { family: FONT, style: F.bold }); } }
  return t;
}
function rect(parent, x, y, w, h, color, r = 0) { const n = figma.createRectangle(); parent.appendChild(n); n.x = x; n.y = y; n.resize(w, h); n.fills = fill(color); n.cornerRadius = r; return n; }
function line(parent, x, y, w, color) { return rect(parent, x, y, w, 1, color); }

// 헤더·쪽번호(전 장 같아야 하는 것만 — deck.md §4-3·4). 본문 배치는 여기서 하지 않는다.
function header(slide, P, o) {
  slide.fills = fill("#ffffff");
  text(slide, o.crumbChapter, X0, Y_CRUMB, T.crumb, F.bold, P.ink, { name: "crumb" });
  text(slide, "  ›  " + (o.crumbSection || ""), X0 + estWidth(o.crumbChapter, T.crumb), Y_CRUMB, T.crumb, F.light, P.mid, { name: "crumb-sec" });
  line(slide, X0, Y_RULE, CONTENT_W, P.line).name = "bg-rule";
  if (o.page) text(slide, o.page, W / 2 - 40, Y_PAGE, T.page, F.light, P.mid, { width: 80, align: "CENTER", name: "page" });   // 장별 번호 「Ⅱ-3」 — 표지·목차·약어표만 생략
  return Y_RULE;
}
// 액션 타이틀(deck.md §2-1). 반환: 제목 아래 y(증거가 시작할 자리). 두 줄이면 자동으로 내려온다.
function actionTitle(slide, P, s, o = {}) {
  const size = o.size || T.title, lines = estLines(s, size, CONTENT_W);
  text(slide, s, X0, Y_TITLE, size, F.bold, P.ink, { width: CONTENT_W, emph: o.emph, emphColor: P.accent, lh: 1.3, name: "title" });
  return Y_TITLE + lines * size * 1.3 + 44;
}

// 시그니처·사진 자리: 빈 사각형을 만들고 id를 모아 두면, 스크립트 뒤 `upload_assets(nodeIds, scaleMode)`로 PNG를 채운다(시그니처 FIT · 사진 FILL).
function logoBox(slide, x = X1 - 180, y = 40, w = 180, h = 48) { const n = rect(slide, x, y, w, h, "#ffffff"); n.name = "signature"; return n.id; }
function photoBox(slide, x, y, w, h, caption, P) {
  const n = rect(slide, x, y, w, h, P.face, 4); n.name = "photo";
  if (caption) text(slide, caption, x, y + h + 6, T.caption, F.light, P.mid, { width: w, name: "caption" });   // 출처 캡션(images.md §3-5)
  return n.id;
}

// figures_svg.py가 뽑은 SVG(표·간트)를 편집 가능한 노드로. 폭은 본문 전폭(1728)으로만. 반환: 배치된 프레임(.height가 갱신된다)
async function placeSvg(slide, svgString, x, y, width) {
  const n = figma.createNodeFromSvg(svgString);
  slide.appendChild(n);
  const k = width / n.width;
  n.rescale(k);
  n.x = x; n.y = y;
  return n;
}

// 발표자 노트 — 초안 문단·⚠️ 확인필요·「발표에서 건너뜀」 표시가 여기로 간다(마크다운 불릿). 화면에는 올리지 않는다(deck.md §2).
function notes(slide, items, skipInTalk = false) {
  const lines = (skipInTalk ? ["- (발표에서 건너뜀)"] : []).concat(items.map(p => "- " + p));
  slide.speakerNotes = lines.join("\n");
}

// 제목 교체 — 고스트 덱의 액션 타이틀을 고친 뒤 name "title" 노드의 글만 바꾼다. map: { "슬라이드 이름": "새 제목" }
async function retitle(map) {
  await loadFonts();
  const done = [];
  for (const s of figma.getSlideGrid().flat()) { const t = map[s.name]; if (!t) continue; const n = s.children.find(c => c.name === "title" && c.type === "TEXT"); if (!n) { done.push(s.name + ": title 없음"); continue; } n.characters = t; done.push(s.name); }
  return done;
}

// ── 그림 프리미티브(지도·연결도·배치도·타임라인용 — figma_slides_diagrams.js가 쓴다) ──
// 화살표: 선 + 삼각 머리. dash면 점선. 벡터는 vectorPaths를 넣은 뒤 x·y를 최소점으로 다시 놓아야 한다(안 놓으면 원점으로 튄다).
function arrow(p, x1, y1, x2, y2, color, o = {}) {
  const w = o.w || 4, v = figma.createVector(); p.appendChild(v); v.name = "bg-arrow";
  v.vectorPaths = [{ windingRule: "NONE", data: `M ${x1} ${y1} L ${x2} ${y2}` }]; v.strokes = fill(color); v.strokeWeight = w; v.strokeCap = "ROUND"; v.fills = []; if (o.dash) v.dashPattern = [12, 10];
  v.x = Math.min(x1, x2) - w / 2; v.y = Math.min(y1, y2) - w / 2;
  const a = Math.atan2(y2 - y1, x2 - x1), L = o.head || 18, p1 = [x2 - L * Math.cos(a - 0.5), y2 - L * Math.sin(a - 0.5)], p2 = [x2 - L * Math.cos(a + 0.5), y2 - L * Math.sin(a + 0.5)];
  const h = figma.createVector(); p.appendChild(h); h.name = "bg-arrowhead"; h.vectorPaths = [{ windingRule: "NONZERO", data: `M ${x2} ${y2} L ${p1[0]} ${p1[1]} L ${p2[0]} ${p2[1]} Z` }]; h.fills = fill(color); h.strokes = [];
  h.x = Math.min(x2, p1[0], p2[0]); h.y = Math.min(y2, p1[1], p2[1]); return v;
}
// 원 테두리(반경·강조). dash면 점선.
function ring(p, cx, cy, r, color, w = 3, dash = false) { const e = figma.createEllipse(); p.appendChild(e); e.resize(r * 2, r * 2); e.fills = []; e.strokes = fill(color); e.strokeWeight = w; if (dash) e.dashPattern = [12, 10]; e.name = "bg-ring"; e.x = cx - r; e.y = cy - r; return e; }
// 점들을 지나는 부드러운 곡선(동선). pts = [[x,y],...]. 정거장 아래 층에 두려면 p.insertChild(index, v).
function curvePath(p, pts, color, w = 6) {
  let d = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) { const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2; const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6], c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6]; d += ` C ${c1[0]} ${c1[1]} ${c2[0]} ${c2[1]} ${p2[0]} ${p2[1]}`; }
  const v = figma.createVector(); p.appendChild(v); v.name = "bg-path"; v.vectorPaths = [{ windingRule: "NONE", data: d }]; v.strokes = fill(color); v.strokeWeight = w; v.strokeCap = "ROUND"; v.strokeJoin = "ROUND"; v.fills = [];
  const xs = pts.map(q => q[0]), ys = pts.map(q => q[1]); const exX = (v.width - w - (Math.max(...xs) - Math.min(...xs))) / 2, exY = (v.height - w - (Math.max(...ys) - Math.min(...ys))) / 2;
  v.x = Math.min(...xs) - w / 2 - Math.max(0, exX); v.y = Math.min(...ys) - w / 2 - Math.max(0, exY); return v;
}
// 구역 띠(지도·배치도의 바탕 영역). outline이면 점선 테두리만.
function zone(p, x, y, w, h, color, label, sub, P, outline = false) { const r = rect(p, x, y, w, h, outline ? "#ffffff" : color, 16); r.name = "bg-zone"; if (outline) { r.strokes = fill(P.line); r.strokeWeight = 2; r.dashPattern = [10, 8]; } if (label) text(p, label, x + 28, y + 22, 24, F.bold, P.deep, { name: "zone-h" }); if (sub) text(p, sub, x + 28, y + 56, 20, F.regular, P.mid, { name: "zone-sub" }); return r; }
// 헤드셋 픽토그램(기기 여러 대를 격자로). 사각형 둘이라 이모지·아이콘 금지 규칙에 걸리지 않는다.
function headset(p, x, y, w, h, color) { const b = rect(p, x, y, w, h, color, h / 3); b.name = "bg-hmd"; const vz = rect(p, x + w * 0.18, y + h * 0.32, w * 0.64, h * 0.3, "#ffffff", 4); vz.name = "bg-hmd-visor"; return b; }
// 장을 다시 그릴 때: 헤더·제목·쪽번호·결론(·사진)만 남기고 본문을 노트로 보낸 뒤 지운다. 반환: 노트로 간 문단 수.
function clearBody(slide, keepPhotos = false) { const keep = keepPhotos ? /^(crumb|crumb-sec|bg-rule|bg-dot|signature|bg-sig|page|title|closing|photo|caption|src)/ : /^(crumb|crumb-sec|bg-rule|bg-dot|signature|bg-sig|page|title|closing)$/; const gone = slide.children.filter(c => !keep.test(c.name)); const bodies = gone.filter(c => c.type === "TEXT" && c.fontSize >= 20 && c.characters.length > 14).map(c => c.characters); if (bodies.length) slide.speakerNotes = ((slide.speakerNotes || "") ? slide.speakerNotes + "\n" : "") + "- (화면에서 노트로) " + bodies.join("\n- "); for (const c of gone) c.remove(); return bodies.length; }

// ── 검사 ──
// 배치 검사(Figma 공식 figma-use-slides 스킬의 batch validation을 옮긴 것): 형제 겹침·글자 잘림·경계 이탈·18px 미만. 「틀리지 않음」 검사다 — 「증거가 있음」은 evidenceCheck가 센다.
// 겹침 예외: 배경·사진·시그니처처럼 겹치도록 만든 것은 name에 bg·photo·signature·overlay가 있으면 뺀다.
async function validate(slideIds, opts = {}) {
  const OVERLAP = opts.overlap || 4, OVERFLOW = 1, ignore = opts.ignore || /^bg|photo|signature|overlay/i;
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
      if (c.type === "TEXT" && typeof c.n.fontSize === "number" && c.n.fontSize < 18 && !/caption|page|crumb|src/i.test(c.name)) issues.push({ slide: slide.name, type: "smallText", node: c.name, size: c.n.fontSize });
    }
  }
  return { clean: issues.length === 0, issues };
}

// 증거 검사(deck.md §6-1~3): 장마다 「글 말고 무엇이 있나」를 센다. 사진(photo-*·이미지 fill)·벡터·SVG 프레임·표(bg-th)·격자(bg-hmd)·큰 숫자(fontSize ≥ 96)를 증거로 본다.
// 반환: 증거 없는 장 목록 · PART별 사진 수 · 발주처 시점이 없는 제목 목록(휴리스틱: 발주처·학생·담당자·심사·선생님·드립·하실 이 없음).
function evidenceCheck(opts = {}) {
  const who = opts.who || /발주처|학생|담당자|심사|선생님|학부모|대학|드립|하실|하셔|보실|받으/;
  const noEvidence = [], noWho = [], photosByPart = {}; let part = "표지";
  for (const s of figma.getSlideGrid().flat()) {
    const title = s.children.find(c => c.name === "title");
    if (title && /^PART/.test(title.characters)) { part = title.characters; photosByPart[part] = photosByPart[part] || 0; continue; }
    const photos = s.children.filter(c => /^photo/.test(c.name) || (c.fills && Array.isArray(c.fills) && c.fills.some(f => f.type === "IMAGE")));
    photosByPart[part] = (photosByPart[part] || 0) + photos.length;
    const ev = photos.length || s.children.some(c => c.type === "VECTOR" || c.type === "FRAME" || c.name === "bg-th" || c.name === "bg-hmd" || (c.type === "TEXT" && c.fontSize >= 96));
    if (!ev && title) noEvidence.push(s.name + " " + title.characters.slice(0, 20));
    if (title && !who.test(title.characters) && !/^(PART|표지|목차|약어|참고)/.test(title.characters)) noWho.push(s.name + " " + title.characters.slice(0, 24));
  }
  return { noEvidence, photosByPart, noWho, noWhoRatio: noWho.length };
}

// 마지막 검사: 덱 전체 텍스트에서 내부 표기·조어가 남았는지. 남으면 이름을 돌려준다 — 사람이 발표자 노트로 옮긴다.
function leftovers(pattern = /근거:|⚠️|확인필요|재료 팩|덩이|제목 사슬|색채 카드|걷는 점/) {
  return figma.root.findAllWithCriteria({ types: ["TEXT"] }).filter(t => pattern.test(t.characters)).map(t => `${t.parent && t.parent.name}: ${t.characters.slice(0, 40)}`);
}

// 재개용 스냅샷(토큰이 끊기기 전에 상태 파일을 채운다) — 현재 페이지의 슬라이드를 「장 이름 · 노드 id · 자식 수」 마크다운 표로 돌려준다.
// 이 문자열을 _BUILD_STATE.md 의 「장별 노드 ID」 표에 그대로 붙이면, 다음 세션이 어느 장까지 만들었는지 id로 바로 찾는다.
// 새로 만든 Slides 파일에서는 getSlideGrid()가 빈 배열이라(figma-howto.md 실측) currentPage 를 직접 훑는다.
function snapshotIds() {
  const slides = figma.currentPage.findAllWithCriteria({ types: ["SLIDE"] });
  const rows = slides.map(s => `| ${s.name} | \`${s.id}\` | ${s.children.length} |`);
  return ["| 장(이름) | 노드 ID | 자식 수 |", "|---|---|---|"].concat(rows).join("\n");
}
