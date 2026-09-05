// figma_slides_diagrams.js — 「그림」 레시피 열 가지 + 표·열 채우기(2026-09-05 순천캠퍼스 VR v5에서 실제로 그린 것을 함수로 옮김).
// 쓰는 법: use_figma 스크립트 맨 앞에 figma_slides_helpers.js 를 붙이고(text·rect·arrow·ring·curvePath·zone·headset·clearBody 를 쓴다), 그 뒤에 이 파일을 붙인다.
//   await loadFonts();
//   const P = { accent:"#0068B0", deep:"#004A80", tint:"#E6F0F7", ink:"#141414", soft:"#4C4C4C", mid:"#6B7480", line:"#D3DAE3", face:"#F4F5F7", paper:"#FFFFFF", dark:"#0B1F33", sky:"#DCEAF5" };
//   const s = figma.getSlideGrid().flat().find(x => x.name === "20");
//   clearBody(s);                     // 본문 → 발표자 노트, 헤더·제목·쪽번호·결론은 남긴다
//   routeMap(s, P, { zones: [...], stops: [...] });
// 원칙(deck.md §3): 장마다 「어떤 그림 한 장이면 설명되나」를 먼저 정한다. 아래 함수는 그 그림의 뼈대다 — 좌표·개수는 장의 내용에 맞춰 바꾼다.
// 규칙(deck.md §4): 색은 P에 있는 것만, 글꼴은 Freesentation, 이모지·기호 아이콘 없음(픽토그램은 도형으로 그린다). 결론 문장(closing)은 그림 아래 60px.
// 실측 요령(figma-howto.md): 벡터는 vectorPaths 뒤 x·y를 다시 놓는다(arrow·curvePath가 처리) · 수정과 get_screenshot은 다른 호출에 · 한 장에 한 호출.

// ── 작은 도우미 ──
function R(p, x, y, w, h, color, r = 0, name = "bg-shape", op) { const n = rect(p, x, y, w, h, color, r); n.name = name; if (op !== undefined) n.fills = fill(color, op); return n; }
function E(p, x, y, w, h, color, name = "bg-shape") { const e = figma.createEllipse(); p.appendChild(e); e.resize(w, h); e.fills = fill(color); e.name = name; e.x = x; e.y = y; return e; }
function strokePath(p, d, color, w, x, y, name = "bg-stroke") { const v = figma.createVector(); p.appendChild(v); v.name = name; v.vectorPaths = [{ windingRule: "NONE", data: d }]; v.strokes = fill(color); v.strokeWeight = w; v.strokeCap = "ROUND"; v.strokeJoin = "ROUND"; v.fills = []; v.x = x; v.y = y; return v; }
function person(p, x, y, h, color) { const hd = h * 0.22; E(p, x + h * 0.12, y, hd, hd, color, "bg-person"); R(p, x, y + hd + 4, h * 0.46, h * 0.62, color, h * 0.12, "bg-person"); }
function closingBelow(slide, y) { const c = slide.children.find(n => n.name === "closing"); if (c) c.y = Math.min(y, 940); return c; }

// 1) 동선 지도 — 구역 띠 위를 지나는 곡선 경로와 정거장. zones:[{x,w,h,sub,outline}] stops:[{n,name,t,x,y}] (x·y는 정거장 원 좌상단, 원 지름 64)
function routeMap(slide, P, o) {
  const Y0 = o.y0 || 300, Y1 = o.y1 || 900;
  o.zones.forEach(z => zone(slide, z.x, Y0, z.w, Y1 - Y0, P.face, z.h, z.sub, P, !!z.outline));
  const pts = o.stops.map(p => [p.x + 32, p.y + 32]);
  const path = curvePath(slide, pts, P.accent, 6);
  const zones = slide.children.filter(c => c.name === "bg-zone"); slide.insertChild(Math.max(...zones.map(z => slide.children.indexOf(z))) + 1, path);
  o.stops.forEach((p, i) => { E(slide, p.x, p.y, 64, 64, P.paper, "bg-stopring"); E(slide, p.x + 6, p.y + 6, 52, 52, (i === 0 || i === o.stops.length - 1) ? P.deep : P.accent, "bg-stop");
    text(slide, p.n, p.x + 6, p.y + 16, 24, F.bold, P.paper, { width: 52, align: "CENTER", name: "stop-n" });
    const up = p.y < (Y0 + Y1) / 2, ly = up ? p.y - 78 : p.y + 78;
    text(slide, p.name, p.x + 32 - 150, ly, 26, F.bold, P.ink, { width: 300, align: "CENTER", name: "stop-name" });
    text(slide, p.t, p.x + 32 - 150, ly + 34, 20, F.regular, P.accent, { width: 300, align: "CENTER", name: "stop-time" }); });
  if (o.caption) text(slide, o.caption, o.captionX || 860, Y1 - 48, 20, F.medium, P.mid, { name: "caption" });
  closingBelow(slide, Y1 + 36);
}

// 2) 시스템 연결도 — 상자(번호·제목·한 줄) + 가운데 기기 격자 + 화살표. boxes:[{x,y,w,h,n,h1,b}] grid:{x,y,rows,cols,label,sub} arrows:[{x1,y1,x2,y2,label,dash,color}]
function systemConnect(slide, P, o) {
  const box = (x, y, w, h, n, h1, b) => { R(slide, x, y, w, h, P.face, 14, "bg-box"); R(slide, x, y, 8, h, P.accent, 4, "bg-boxbar"); text(slide, n, x + 28, y + 20, 44, F.black, P.accent, { name: "box-n" }); text(slide, h1, x + 28, y + 80, 30, F.bold, P.ink, { width: w - 56, name: "box-h" }); if (b) text(slide, b, x + 28, y + 124, 22, F.regular, P.soft, { width: w - 56, name: "box-b" }); };
  o.boxes.forEach(b => box(b.x, b.y, b.w, b.h, b.n, b.h1, b.b));
  if (o.grid) { const g = o.grid; for (let r = 0; r < g.rows; r++) for (let c = 0; c < g.cols; c++) headset(slide, g.x + c * 96, g.y + r * 120, 80, 56, P.accent);
    const gw = g.cols * 96 - 16; if (g.label) text(slide, g.label, g.x, g.y + g.rows * 120 - 20, 24, F.bold, P.deep, { width: gw, align: "CENTER", name: "grid-h" }); if (g.sub) text(slide, g.sub, g.x, g.y + g.rows * 120 + 14, 20, F.regular, P.mid, { width: gw, align: "CENTER", name: "grid-b" }); }
  (o.arrows || []).forEach(a => { arrow(slide, a.x1, a.y1, a.x2, a.y2, a.color || P.accent, { dash: a.dash }); if (a.label) text(slide, a.label, a.lx !== undefined ? a.lx : Math.min(a.x1, a.x2) + 24, a.ly !== undefined ? a.ly : Math.min(a.y1, a.y2) - 36, 20, F.medium, a.color || P.accent, { name: "arrow-l" }); });
  closingBelow(slide, o.closingY || 870);
}

// 3) 스토리보드 — 컷마다 장면 스케치(draw 콜백) + 이름 + 대사. cuts:[{n,h,say,draw(x,y)}] 3열, 컷 540×250
function storyboard(slide, P, cuts, o = {}) {
  const FW = o.fw || 540, FH = o.fh || 250, GX = o.gx || 54, GY = o.gy || 90, X0 = 96, Y0 = o.y0 || 290, cols = o.cols || 3;
  cuts.forEach((c, i) => { const x = X0 + (i % cols) * (FW + GX), y = Y0 + Math.floor(i / cols) * (FH + GY);
    R(slide, x, y, FW, FH, P.face, 12, "bg-frame"); R(slide, x, y + FH - 44, FW, 44, P.tint, 0, "bg-floor"); if (c.draw) c.draw(x, y, slide);
    text(slide, c.n, x + 16, y + 12, 22, F.bold, P.accent, { name: "cut-n" }); text(slide, c.h, x, y + FH + 10, 24, F.bold, P.ink, { width: FW, name: "cut-h" }); if (c.say) text(slide, c.say, x, y + FH + 42, 20, F.regular, P.soft, { width: FW, name: "cut-say", lh: 1.35 }); });
  const rows = Math.ceil(cuts.length / cols); closingBelow(slide, Y0 + rows * (FH + GY) + 10);
}

// 4) 판 세 개(손동작·장면 등) — 위는 그림, 아래 150px는 글. panels:[{n,h,b,draw(x,y)}]
function pictoPanels(slide, P, panels, o = {}) {
  const PW = o.pw || 540, PH = o.ph || 440, GX = o.gx || 54, Y = o.y || 300;
  panels.forEach((p, i) => { const x = 96 + i * (PW + GX); R(slide, x, Y, PW, PH, P.face, 14, "bg-panel"); R(slide, x, Y + PH - 150, PW, 150, P.paper, 0, "bg-panelbase"); if (p.draw) p.draw(x, Y, slide);
    text(slide, p.n, x + 28, Y + PH - 130, 20, F.medium, P.accent, { name: "panel-n" }); text(slide, p.h, x + 28, Y + PH - 104, 34, F.bold, P.ink, { name: "panel-h" }); text(slide, p.b, x + 28, Y + PH - 56, 20, F.regular, P.soft, { width: PW - 56, name: "panel-b", lh: 1.35 }); });
  if (o.caption) text(slide, o.caption, 96, Y + PH + 24, 22, F.medium, P.mid, { name: "caption" });
  closingBelow(slide, Y + PH + (o.caption ? 80 : 60));
}

// 5) 교실 배치도 — 교사 자리·좌석 격자·보관함·순환 화살표 + 오른쪽 단계 목록. o:{seats:{rows,cols}, roomLabel, deskLabel, cabinet:{label,sub,slots}, steps:[[n,h,b]], loop:[label1,label2,label3]}
function roomPlan(slide, P, o) {
  const rx = 96, ry = 290, rw = o.rw || 1080, rh = o.rh || 620; R(slide, rx, ry, rw, rh, P.face, 20, "bg-room"); text(slide, o.roomLabel || "", rx + 28, ry + 20, 22, F.bold, P.deep, { name: "room-h" });
  R(slide, rx + 380, ry + 70, 320, 70, P.deep, 12, "bg-desk"); text(slide, o.deskLabel || "", rx + 380, ry + 92, 22, F.bold, P.paper, { width: 320, align: "CENTER", name: "desk-l" });
  const sx = rx + 120, sy = ry + 190, rows = o.seats.rows, cols = o.seats.cols; for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) { R(slide, sx + c * 150, sy + r * 120, 110, 80, P.paper, 12, "bg-seat"); headset(slide, sx + c * 150 + 25, sy + r * 120 + 16, 60, 42, P.accent); }
  if (o.cabinet) { R(slide, rx + rw - 140, ry + 190, 100, 340, P.paper, 12, "bg-cab"); for (let i = 0; i < (o.cabinet.slots || 15); i++) R(slide, rx + rw - 124, ry + 206 + i * 21, 68, 14, P.accent, 3, "bg-slot"); text(slide, o.cabinet.label, rx + rw - 140, ry + 540, 20, F.bold, P.deep, { width: 100, align: "CENTER", name: "cab-l" }); if (o.cabinet.sub) text(slide, o.cabinet.sub, rx + rw - 140, ry + 566, 18, F.regular, P.mid, { width: 100, align: "CENTER", name: "caption" }); }
  const lastCol = sx + (cols - 1) * 150 + 120; const L = o.loop || [];
  arrow(slide, rx + rw - 150, ry + 240, lastCol, ry + 240, P.deep); if (L[0]) text(slide, L[0], lastCol - 80, ry + 150, 20, F.medium, P.deep, { name: "arrow-l" });
  arrow(slide, lastCol, ry + 500, rx + rw - 150, ry + 500, P.deep); if (L[2]) text(slide, L[2], lastCol - 80, ry + 512, 20, F.medium, P.deep, { name: "arrow-l" });
  arrow(slide, rx + 540, ry + 140, rx + 540, ry + 186, P.accent); if (L[1]) text(slide, L[1], rx + 560, ry + 146, 20, F.medium, P.accent, { name: "arrow-l" });
  let y = 300; const lx = rx + rw + 64; (o.steps || []).forEach(([n, h, b]) => { E(slide, lx, y, 44, 44, P.accent, "bg-stepdot"); text(slide, n, lx, y + 9, 20, F.bold, P.paper, { width: 44, align: "CENTER", name: "step-n" }); text(slide, h, lx + 60, y + 4, 28, F.bold, P.ink, { name: "step-h" }); text(slide, b, lx + 60, y + 44, 20, F.regular, P.soft, { width: 1824 - lx - 60, name: "step-b" }); y += 124; });
  closingBelow(slide, 940);
}

// 6) 공정도 — 단계 상자 띠 + 화살표, 아래에 사진·큰 숫자 카드. stages:[[n,h,b]] photos: 기존 photo-* 노드를 다시 놓는다. stat:{n,l}
function processStrip(slide, P, stages, o = {}) {
  const n = stages.length, gap = 37, w = Math.floor((1728 - gap * (n - 1)) / n), x0 = 96, y0 = o.y0 || 290, h = o.h || 190;
  stages.forEach(([num, h1, b], i) => { const x = x0 + i * (w + gap); R(slide, x, y0, w, h, i === 0 ? P.deep : P.face, 14, "bg-stage"); text(slide, num, x + 22, y0 + 18, 34, F.black, i === 0 ? P.paper : P.accent, { name: "stage-n" }); text(slide, h1, x + 22, y0 + 66, 28, F.bold, i === 0 ? P.paper : P.ink, { name: "stage-h" }); text(slide, b, x + 22, y0 + 106, 19, F.regular, i === 0 ? P.paper : P.soft, { width: w - 44, name: "stage-b", lh: 1.4 }); if (i < n - 1) arrow(slide, x + w + 4, y0 + h / 2, x + w + gap - 4, y0 + h / 2, P.accent, { w: 3 }); });
  const py = y0 + h + 50, ph = o.ph || 330, pw = o.pw || 560;
  const photos = slide.children.filter(c => /^photo/.test(c.name)).sort((a, b) => a.x - b.x), caps = slide.children.filter(c => c.type === "TEXT" && /^(caption|src)/.test(c.name)).sort((a, b) => a.x - b.x);
  photos.forEach((p, i) => { p.x = 96 + i * (pw + 40); p.y = py; p.resize(pw, ph); if (caps[i]) { caps[i].x = p.x; caps[i].y = py + ph + 8; } });
  if (o.stat) { const kx = 96 + photos.length * (pw + 40), kw = 1824 - kx; R(slide, kx, py, kw, ph, P.tint, 14, "bg-box"); text(slide, o.stat.n, kx, py + 70, 110, F.black, P.accent, { width: kw, align: "CENTER", name: "stat-n" }); text(slide, o.stat.l, kx + 24, py + 220, 20, F.regular, P.soft, { width: kw - 48, align: "CENTER", name: "stat-l" }); }
  closingBelow(slide, py + ph + 60);
}

// 7) 층도 — 층 세 개와 가운데 층의 기기 열, 위·아래 연결선, 오른쪽 고장 대응 판. layers:[[h,b,y]] o:{devices, checks:[t,t,t], fault:{h, before, after, note}}
function layerDiagram(slide, P, layers, o = {}) {
  const LX = 96, LW = o.lw || 1300, mid = Math.floor(layers.length / 2);
  layers.forEach(([h1, b, y], i) => { const r = R(slide, LX, y, LW, 140, i === mid ? P.paper : P.face, 14, "bg-layer"); if (i === mid) { r.strokes = fill(P.accent); r.strokeWeight = 2; } text(slide, h1, LX + 24, y + 18, 26, F.bold, P.deep, { name: "layer-h" }); text(slide, b, LX + 24, y + 56, 19, F.regular, P.soft, { width: 360, name: "layer-b", lh: 1.4 }); });
  const my = layers[mid][2], hx = LX + 420, n = o.devices || 15; for (let i = 0; i < n; i++) { const x = hx + i * 58; headset(slide, x, my + 44, 48, 34, P.accent); if (mid > 0) arrow(slide, x + 24, layers[mid - 1][2] + 140, x + 24, my + 40, P.line, { w: 2 }); if (mid < layers.length - 1) arrow(slide, x + 24, my + 140, x + 24, layers[mid + 1][2] - 4, P.line, { w: 2 }); }
  (o.checks || []).forEach((t, i) => { if (!t) return; const y = layers[i][2]; text(slide, t, LX + LW - 190, i === mid ? y + 98 : y + 18, 24, F.bold, P.accent, { name: "chk" }); });
  if (o.fault) { const f = o.fault, gx = LX + LW + 40, gw = 1824 - gx, top = layers[0][2], bot = layers[layers.length - 1][2] + 140; R(slide, gx, top, gw, bot - top, P.tint, 14, "bg-box"); text(slide, f.h, gx + 24, top + 24, 26, F.bold, P.deep, { name: "box-h" }); headset(slide, gx + 40, top + 100, 80, 56, P.mid); text(slide, f.before, gx + 24, top + 170, 20, F.medium, P.ink, { width: gw - 48, name: "box-b" }); arrow(slide, gx + gw / 2, top + 210, gx + gw / 2, top + 270, P.accent); headset(slide, gx + 40, top + 290, 80, 56, P.accent); text(slide, f.after, gx + 24, top + 360, 20, F.medium, P.ink, { width: gw - 48, name: "box-b" }); if (f.note) text(slide, f.note, gx + 24, top + 460, 18, F.regular, P.soft, { width: gw - 48, name: "box-b", lh: 1.4 }); }
  closingBelow(slide, layers[layers.length - 1][2] + 190);
}

// 8) 반경 지도 — 가운데 건물, 안·밖 원, 점 N개, 오른쪽 큰 숫자. o:{cx,cy,center:{label,desc}, ringLabel, dots, dotLabel, stats:[[n,l,src]]}
function radiusMap(slide, P, o) {
  const cx = o.cx || 560, cy = o.cy || 640; ring(slide, cx, cy, 300, P.accent, 3, true); ring(slide, cx, cy, 150, P.line, 2, false);
  let seed = 7; const rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
  for (let i = 0; i < (o.dots || 48); i++) { const a = -0.4 + rnd() * 2.2, r = 160 + rnd() * 125; E(slide, cx + Math.cos(a) * r - 7, cy + Math.sin(a) * r * 0.75 - 7, 14, 14, P.accent, "bg-firm"); }
  R(slide, cx - 70, cy - 60, 140, 120, P.deep, 10, "bg-bldg"); for (let f = 0; f < 3; f++) R(slide, cx - 54, cy - 46 + f * 36, 108, 24, P.paper, 3, "bg-floor", f === 2 ? 1 : 0.35);
  text(slide, o.center.label, cx - 70, cy - 104, 24, F.bold, P.deep, { width: 140, align: "CENTER", name: "map-l" });
  const d = text(slide, o.center.desc, cx - 70 - 24 - 320, cy - 34, 20, F.regular, P.soft, { width: 320, name: "map-b" }); d.textAlignHorizontal = "RIGHT";
  text(slide, o.ringLabel, cx + 170, cy - 330, 22, F.bold, P.accent, { name: "map-l" }); if (o.dotLabel) text(slide, o.dotLabel, cx + 230, cy + 150, 22, F.bold, P.deep, { name: "map-l" });
  let y = 300; (o.stats || []).forEach(([n, l, src]) => { text(slide, n, 1180, y, 96, F.black, P.accent, { name: "stat-n" }); text(slide, l, 1180, y + 134, 22, F.regular, P.ink, { width: 640, name: "stat-l" }); if (src) text(slide, src, 1180, y + 168, 16, F.light, P.mid, { name: "src" }); y += 210; });
  closingBelow(slide, 960);
}

// 9) VR 시야 와이어프레임 — 어두운 프레임 안에 응시점·버튼 하나·상태 칩, 아래 주석 셋. o:{x,y,w,h, chipL, chipR, btn, ann:[[t,color]]}
function wireframeVR(slide, P, o) {
  const X = o.x || 96, Y = o.y || 300, W = o.w || 800, H = o.h || 450; R(slide, X, Y, W, H, P.dark, 24, "bg-vr");
  R(slide, X + 40, Y + 300, W - 80, 4, P.mid, 0, "bg-shape", 0.6); R(slide, X + 120, Y + 90, 180, 210, P.deep, 4, "bg-shape", 0.7); R(slide, X + 520, Y + 120, 160, 180, P.deep, 4, "bg-shape", 0.7);
  ring(slide, X + W / 2, Y + H / 2 - 20, 18, P.paper, 3); ring(slide, X + W / 2, Y + H / 2 - 20, 4, P.accent, 4);
  R(slide, X + W / 2 - 110, Y + H - 90, 220, 54, P.accent, 27, "bg-btn"); text(slide, o.btn || "선택", X + W / 2 - 110, Y + H - 76, 22, F.bold, P.paper, { width: 220, align: "CENTER", name: "ui-l" });
  if (o.chipL) { R(slide, X + 28, Y + 28, 260, 40, P.paper, 20, "bg-chip", 0.9); text(slide, o.chipL, X + 28, Y + 38, 17, F.medium, P.ink, { width: 260, align: "CENTER", name: "ui-l" }); }
  if (o.chipR) { R(slide, X + W - 140, Y + 28, 112, 32, P.paper, 16, "bg-chip", 0.9); text(slide, o.chipR, X + W - 140, Y + 35, 16, F.medium, P.ink, { width: 112, align: "CENTER", name: "ui-l" }); }
  let y = Y + H + 22; (o.ann || []).forEach(([t, c]) => { text(slide, t, X, y, 20, F.medium, c || P.ink, { width: W, name: "ann" }); y += 32; });
  if (o.title) text(slide, o.title, X, Y - 40, 24, F.bold, P.deep, { name: "sec-h" });
  closingBelow(slide, Y + H + 140);
}

// 10) 승인 타임라인 — 주 축·구간 띠·마름모 지점·아래 도구 칩. o:{weeks, spans:[[a,b,l]], ms:[[w,n,h,b]], tools:[[h,b]], toolsTitle}
function approvalTimeline(slide, P, o) {
  const X0 = 136, X1 = 1784, AY = o.ay || 560, N = o.weeks || 13; const wx = w => X0 + (w - 1) / (N - 1) * (X1 - X0);
  R(slide, X0 - 40, AY - 3, X1 - X0 + 80, 6, P.line, 3, "bg-axis");
  for (let w = 1; w <= N; w++) { R(slide, wx(w) - 1, AY - 14, 2, 28, P.mid, 0, "bg-tick"); text(slide, w + "주", wx(w) - 30, AY + 22, 18, F.regular, P.mid, { width: 60, align: "CENTER", name: "tick-l" }); }
  (o.spans || []).forEach(([a, b, l], i) => { const x = wx(a) - 26, w = wx(b) - wx(a) + 52; R(slide, x, AY - 70, w, 34, i % 2 ? P.tint : P.face, 17, "bg-span"); text(slide, l, x, AY - 64, 18, F.medium, P.deep, { width: w, align: "CENTER", name: "span-l" }); });
  (o.ms || []).forEach(([w, n, h, b], i) => { const x = wx(w); const d = R(slide, x - 16, AY - 16, 32, 32, P.accent, 4, "bg-ms"); d.rotation = 45; const up = i % 2 === 0, ly = up ? AY - 190 : AY + 70; R(slide, x - 1, up ? AY - 100 : AY + 20, 2, up ? 70 : 50, P.accent, 0, "bg-msline");
    text(slide, n + " 승인", x - 150, ly, 20, F.medium, P.accent, { width: 300, align: "CENTER", name: "ms-n" }); text(slide, h, x - 150, ly + 26, 28, F.bold, P.ink, { width: 300, align: "CENTER", name: "ms-h" }); text(slide, b, x - 150, ly + 62, 19, F.regular, P.soft, { width: 300, align: "CENTER", name: "ms-b" }); });
  if (o.tools) { text(slide, o.toolsTitle || "", 96, 760, 24, F.bold, P.deep, { name: "sec-h" }); const n = o.tools.length, w = Math.floor((1728 - 24 * (n - 1)) / n); o.tools.forEach(([h, b], i) => { const x = 96 + i * (w + 24); R(slide, x, 800, w, 90, P.face, 12, "bg-tool"); R(slide, x, 800, 8, 90, P.accent, 4, "bg-toolbar"); text(slide, h, x + 28, 814, 24, F.bold, P.ink, { name: "tool-h" }); text(slide, b, x + 28, 848, 19, F.regular, P.soft, { name: "tool-b" }); }); }
  closingBelow(slide, 930);
}

// ── 채우기 ──
// 표 장을 가용 높이에 맞춘다: 행 높이를 (결론 위 880까지) 늘리고, 많이 늘면 글자 +2. **배정 먼저, 이동 나중**(옮기면서 범위를 재면 앞 행 글자가 다음 행에 잡힌다 — 09-05 실측).
function fitTable(slide, o = {}) {
  const title = slide.children.find(c => c.name === "title"), closing = slide.children.find(c => c.name === "closing");
  const th = slide.children.find(c => c.name === "bg-th"), trs = slide.children.filter(c => c.name === "bg-tr").sort((a, b) => a.y - b.y); if (!th || !trs.length) return null;
  const top = Math.max(th.y, title ? title.y + estHeight(title.characters, title.fontSize, title.width, 1.3) + 40 : th.y), dTop = top - th.y;
  const limit = o.bottom || (closing ? 880 : 940), sum = trs.reduce((a, t) => a + t.height, 0); let k = Math.min(o.maxK || 1.8, (limit - (top + th.height)) / sum); if (k < 1) k = 1;
  const texts = slide.children.filter(c => c.type === "TEXT" && c.y >= th.y - 2 && c.name !== "closing" && c.name !== "page");
  const head = texts.filter(t => t.y < th.y + th.height - 2), rows = trs.map(tr => ({ tr, items: texts.filter(t => t.y >= tr.y - 2 && t.y < tr.y + tr.height - 2) }));
  const rules = slide.children.filter(c => c.type === "RECTANGLE" && c.height <= 2 && c.width >= th.width - 4 && c.name !== "bg-rule" && c.y > th.y);
  th.y += dTop; head.forEach(t => t.y += dTop);
  let y = th.y + th.height, bump = k > 1.35 ? 2 : 0;
  for (const r of rows) { const nh = r.tr.height * k; r.tr.y = y; r.tr.resize(r.tr.width, nh); for (const t of r.items) { if (bump && t.fontSize <= 21) t.fontSize += bump; t.y = y + Math.max(8, (nh - Math.max(t.height, estHeight(t.characters, t.fontSize, t.width))) / 2); } y += nh; }
  rules.forEach(g => g.y = y); if (closing) closing.y = Math.min(y + 40, 940);
  return { k: +k.toFixed(2), bump, bottom: Math.round(y) };
}

// 열별 재적재: 단계·카드 장(bg-stepdot 또는 bg-cardline 이 열의 기준)에서 열마다 위→아래로 다시 쌓는다. 여러 열 장을 한 줄로 재적재하면 열이 흩어진다.
function restackColumns(slide, o = {}) {
  const closing = slide.children.find(c => c.name === "closing");
  const dots = slide.children.filter(c => c.name === "bg-stepdot").sort((a, b) => a.x - b.x), lines = slide.children.filter(c => c.name === "bg-cardline").sort((a, b) => a.x - b.x);
  const anchors = dots.length >= 2 ? dots : lines; if (anchors.length < 2) return null;
  const colW = anchors[1].x - anchors[0].x, x0 = anchors[0].x, aB = anchors[0].y + anchors[0].height;
  const below = slide.children.filter(c => c.type === "TEXT" && c !== closing && c.name !== "page" && c.y > aB - 2 && c.x >= x0 - 6);
  const cols = anchors.map(() => []); for (const c of below) { const k = Math.floor((c.x - x0 + 6) / colW); if (k >= 0 && k < cols.length) cols[k].push(c); }
  let maxB = aB; cols.forEach(col => { col.sort((a, b) => a.y - b.y); let y = aB + (dots.length >= 2 ? 28 : 22); col.forEach((c, i) => { c.y = y; y += Math.max(c.height, estHeight(c.characters, c.fontSize, c.width)) + (i === 0 ? 12 : 14); }); maxB = Math.max(maxB, y); });
  if (closing) closing.y = Math.min(maxB + 60, 940); return { bottom: Math.round(maxB) };
}
