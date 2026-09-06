// figma_slides_diagrams.js — 덱 증거 유형 중 「지도·연결도·배치도·타임라인」 네 가지의 뼈대 + 표 채우기(2026-09-06).
// 2026-09-05 대학 캠퍼스 VR 건 v5에서 열 가지를 그렸고, 그중 실제로 통한 넷만 남겼다(스토리보드·판·공정도·층도·반경 지도·와이어프레임·열 재적재는 지움 — 도형으로 그린 개념도는 증거가 아니었다).
// 사진·렌더·큰 숫자·표·비교는 레시피가 아니라 재료(§0)와 레이아웃 컴포넌트(다음 일)로 해결한다.
// 쓰는 법: use_figma 스크립트 맨 앞에 figma_slides_helpers.js 를 붙이고, 그 뒤에 이 파일을 붙인다.
//   await loadFonts(); const P = { accent:"#0068B0", deep:"#004A80", tint:"#E6F0F7", ink:"#141414", soft:"#4C4C4C", mid:"#6B7480", line:"#D3DAE3", face:"#F4F5F7", paper:"#FFFFFF" };
//   const s = figma.getSlideGrid().flat().find(x => x.name === "20"); clearBody(s); routeMap(s, P, { zones: [...], stops: [...] });
// 실측 요령(figma-howto.md): 벡터는 vectorPaths 뒤 x·y를 다시 놓는다(arrow·curvePath가 처리) · 수정과 get_screenshot은 다른 호출에 · 한 장에 한 호출.

function R(p, x, y, w, h, color, r = 0, name = "bg-shape", op) { const n = rect(p, x, y, w, h, color, r); n.name = name; if (op !== undefined) n.fills = fill(color, op); return n; }
function E(p, x, y, w, h, color, name = "bg-shape") { const e = figma.createEllipse(); p.appendChild(e); e.resize(w, h); e.fills = fill(color); e.name = name; e.x = x; e.y = y; return e; }
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

// 2) 연결도 — 상자(번호·제목·한 줄) + 가운데 기기 격자 + 화살표. boxes:[{x,y,w,h,n,h1,b}] grid:{x,y,rows,cols,label,sub} arrows:[{x1,y1,x2,y2,label,dash,color,lx,ly}]
function systemConnect(slide, P, o) {
  const box = (x, y, w, h, n, h1, b) => { R(slide, x, y, w, h, P.face, 14, "bg-box"); R(slide, x, y, 8, h, P.accent, 4, "bg-boxbar"); text(slide, n, x + 28, y + 20, 44, F.black, P.accent, { name: "box-n" }); text(slide, h1, x + 28, y + 80, 30, F.bold, P.ink, { width: w - 56, name: "box-h" }); if (b) text(slide, b, x + 28, y + 124, 22, F.regular, P.soft, { width: w - 56, name: "box-b" }); };
  o.boxes.forEach(b => box(b.x, b.y, b.w, b.h, b.n, b.h1, b.b));
  if (o.grid) { const g = o.grid; for (let r = 0; r < g.rows; r++) for (let c = 0; c < g.cols; c++) headset(slide, g.x + c * 96, g.y + r * 120, 80, 56, P.accent);
    const gw = g.cols * 96 - 16; if (g.label) text(slide, g.label, g.x, g.y + g.rows * 120 - 20, 24, F.bold, P.deep, { width: gw, align: "CENTER", name: "grid-h" }); if (g.sub) text(slide, g.sub, g.x, g.y + g.rows * 120 + 14, 20, F.regular, P.mid, { width: gw, align: "CENTER", name: "grid-b" }); }
  (o.arrows || []).forEach(a => { arrow(slide, a.x1, a.y1, a.x2, a.y2, a.color || P.accent, { dash: a.dash }); if (a.label) text(slide, a.label, a.lx !== undefined ? a.lx : Math.min(a.x1, a.x2) + 24, a.ly !== undefined ? a.ly : Math.min(a.y1, a.y2) - 36, 20, F.medium, a.color || P.accent, { name: "arrow-l" }); });
  closingBelow(slide, o.closingY || 870);
}

// 3) 배치도 — 교사 자리·좌석 격자·보관함·순환 화살표 + 오른쪽 단계 목록. o:{seats:{rows,cols}, roomLabel, deskLabel, cabinet:{label,sub,slots}, steps:[[n,h,b]], loop:[l1,l2,l3]}
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

// 4) 타임라인 — 주 축·구간 띠·마름모 지점·아래 도구 칩. o:{weeks, spans:[[a,b,l]], ms:[[w,n,h,b]], tools:[[h,b]], toolsTitle}
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

// 표 장을 가용 높이에 맞춘다(표가 증거인 장에서만): 행 높이를 결론 위 880까지 늘리고, 많이 늘면 글자 +2. **배정 먼저, 이동 나중**.
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
