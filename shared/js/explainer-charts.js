/* ==========================================================================
   Bitcoin Data Labs — Deep Dives: small SVG chart kit for the paper explainer pages.
   No dependencies. Every chart: thin marks, hairline grid, hover + keyboard tooltip,
   and a "Table view" twin so no value is reachable only by hovering.
   Usage: BDLCharts.hbars(el, {...}) etc. Labels are set with textContent only.
   ========================================================================== */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function text(parent, x, y, s, cls, extra) {
    const t = el('text', Object.assign({ x, y, class: cls }, extra || {}), parent);
    t.textContent = s;
    return t;
  }
  const measureCtx = document.createElement('canvas').getContext('2d');
  function textW(s, size, weight) {
    measureCtx.font = `${weight || 400} ${size || 12}px Inter, -apple-system, "Segoe UI", sans-serif`;
    return measureCtx.measureText(String(s)).width;
  }

  /* ---------- tooltip ---------- */
  let tipEl;
  function tipNode() {
    if (!tipEl) {
      tipEl = document.createElement('div');
      tipEl.className = 'tooltip';
      tipEl.hidden = true;
      tipEl.setAttribute('role', 'status');
      document.body.appendChild(tipEl);
    }
    return tipEl;
  }
  function showTip(x, y, content) {
    const t = tipNode();
    t.replaceChildren();
    for (const r of content.rows || []) {
      const d = document.createElement('div');
      if (r.color) {
        const k = document.createElement('span');
        k.className = 'tk';
        k.style.background = r.color;
        d.appendChild(k);
      }
      const v = document.createElement('span');
      v.className = 'tv';
      v.textContent = r.value;
      d.appendChild(v);
      if (r.label) {
        const l = document.createElement('span');
        l.className = 'tl';
        l.textContent = ' ' + r.label;
        d.appendChild(l);
      }
      t.appendChild(d);
    }
    if (content.title) {
      const d = document.createElement('div');
      d.className = 'tl';
      d.textContent = content.title;
      t.insertBefore(d, t.firstChild);
    }
    if (content.note) {
      const d = document.createElement('div');
      d.className = 'tl';
      d.style.marginTop = '4px';
      d.textContent = content.note;
      t.appendChild(d);
    }
    t.hidden = false;
    const w = t.offsetWidth, h = t.offsetHeight;
    let left = x + 14, top = y + 14;
    if (left + w > window.innerWidth - 8) left = x - w - 14;
    if (top + h > window.innerHeight - 8) top = y - h - 14;
    t.style.left = Math.max(8, left) + 'px';
    t.style.top = Math.max(8, top) + 'px';
  }
  function hideTip() { if (tipEl) tipEl.hidden = true; }
  function hover(node, contentFn, aria) {
    node.setAttribute('tabindex', '0');
    if (aria) node.setAttribute('aria-label', aria);
    node.addEventListener('pointermove', (e) => showTip(e.clientX, e.clientY, contentFn()));
    node.addEventListener('pointerleave', hideTip);
    node.addEventListener('focus', () => {
      const b = node.getBoundingClientRect();
      showTip(b.left + Math.min(b.width, 260) / 2, b.top + b.height / 2, contentFn());
    });
    node.addEventListener('blur', hideTip);
  }
  window.addEventListener('scroll', hideTip, { passive: true });

  /* ---------- geometry ---------- */
  function hbarPath(x0, x1, y, h, r) {
    const w = x1 - x0;
    if (w <= 0.5) return '';
    r = Math.min(r, w, h / 2);
    return `M${x0},${y}H${x1 - r}Q${x1},${y} ${x1},${y + r}V${y + h - r}Q${x1},${y + h} ${x1 - r},${y + h}H${x0}Z`;
  }
  function niceStep(span, count) {
    const raw = span / count;
    const p = Math.pow(10, Math.floor(Math.log10(raw)));
    const f = raw / p;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
  }
  function ticks(min, max, count) {
    const s = niceStep(max - min, count);
    const out = [];
    for (let v = Math.ceil(min / s - 1e-9) * s; v <= max + 1e-9; v += s) out.push(+v.toFixed(10));
    return out;
  }
  const dayMs = 86400000;
  function parseDay(s) {
    if (s instanceof Date) return s.getTime();
    if (/T/.test(s)) return Date.parse(s);
    const [y, m, d] = s.split('-').map(Number);
    return Date.UTC(y, m - 1, d);
  }
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function fmtDay(t) {
    const d = new Date(t);
    return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
  }
  function fmtMonth(t) {
    const d = new Date(t);
    return `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
  }

  /* ---------- mounting ---------- */
  function mount(container, draw) {
    let lastW = 0;
    const render = () => {
      const w = Math.round(container.clientWidth);
      if (!w || w === lastW) return;
      lastW = w;
      container.replaceChildren();
      draw(w);
    };
    render();
    if ('ResizeObserver' in window) new ResizeObserver(render).observe(container);
  }
  function root(container, w, h, label) {
    return el('svg', { viewBox: `0 0 ${w} ${h}`, width: w, height: h, role: 'group', 'aria-label': label || '' }, container);
  }
  function tableView(host, headers, rows) {
    const d = document.createElement('details');
    d.className = 'tableview';
    const s = document.createElement('summary');
    s.textContent = 'Table view';
    d.appendChild(s);
    const wrap = document.createElement('div');
    wrap.className = 'tablewrap';
    const t = document.createElement('table');
    t.className = 'data';
    const hr = t.createTHead().insertRow();
    headers.forEach((h) => { const th = document.createElement('th'); th.textContent = h; hr.appendChild(th); });
    const tb = t.createTBody();
    rows.forEach((r) => { const tr = tb.insertRow(); r.forEach((c) => { tr.insertCell().textContent = c; }); });
    wrap.appendChild(t);
    d.appendChild(wrap);
    if (host.nodeType === 1 && host.classList && host.classList.contains('chart')) host.insertAdjacentElement('afterend', d);
    else host.appendChild(d);
  }
  function gridX(svg, xs, scale, y0, y1, fmt, showLabels) {
    const g = el('g', { class: 'tick' }, svg);
    xs.forEach((v) => {
      const x = scale(v);
      el('line', { x1: x, x2: x, y1: y0, y2: y1, stroke: css('--grid'), 'stroke-width': 1 }, g);
      if (showLabels !== false) text(g, x, y1 + 15, fmt(v), '', { 'text-anchor': 'middle' });
    });
  }

  /* ---------- horizontal bars ----------
     rows: [{label, value, color, valueText, note, strong}] ; opts.max, opts.tickFmt, opts.aria
     When the labels would take more than ~40% of the width, each label sits above its bar. */
  function hbars(container, o) {
    mount(container, (w) => {
      const barH = Math.min(o.barH || 20, 24);
      const maxLab = Math.max(...o.rows.map((r) => textW(r.label, 12, r.strong ? 600 : 400)));
      const stacked = maxLab + 14 > w * 0.4;
      const rowH = stacked ? barH + 26 : (o.rowH || 34);
      const valW = Math.max(...o.rows.map((r) => textW(r.valueText, 12, 600))) + 12;
      const x0 = stacked ? 0 : maxLab + 14, x1 = w - valW;
      const max = o.max || Math.max(...o.rows.map((r) => r.value));
      const sx = (v) => x0 + (v / max) * (x1 - x0);
      const h = o.rows.length * rowH + 26;
      const svg = root(container, w, h, o.aria);
      gridX(svg, ticks(0, max, Math.max(2, Math.floor((x1 - x0) / 90))), sx, 0, o.rows.length * rowH, o.tickFmt || ((v) => v));
      o.rows.forEach((r, i) => {
        const g = el('g', { class: 'row' }, svg);
        const y = stacked ? i * rowH + 20 : i * rowH + (rowH - barH) / 2;
        text(g, 0, stacked ? i * rowH + 14 : y + barH / 2 + 4, r.label, r.strong ? 'lbl-strong' : 'lbl');
        el('path', { d: hbarPath(x0, sx(r.value), y, barH, 4), fill: r.color, class: 'mark' }, g);
        text(g, sx(r.value) + 6, y + barH / 2 + 4, r.valueText, 'val');
        const hit = el('rect', { x: 0, y: i * rowH, width: w, height: rowH, class: 'hit' }, g);
        hover(hit, () => ({ title: r.label, rows: [{ value: r.valueText, color: r.color }], note: r.note }), `${r.label}: ${r.valueText}`);
      });
      el('line', { x1: x0, x2: x0, y1: 0, y2: o.rows.length * rowH, stroke: css('--axis'), 'stroke-width': 1 }, svg);
    });
    if (o.table !== false) tableView(o.tableHost || container, o.tableHeaders || ['', 'Value'], o.rows.map((r) => [r.label, r.valueText]));
  }

  /* ---------- grouped horizontal bars ----------
     groups: [{label, values:[..], texts:[..]}], series: [{name, color}] */
  function groupedH(container, o) {
    mount(container, (w) => {
      const n = o.series.length, barH = 16, gap = 4, pad = 14;
      const groupH = n * barH + (n - 1) * gap + pad;
      const labelW = Math.min(w * 0.4, Math.max(...o.groups.map((g) => textW(g.label, 12, 600))) + 14);
      const valW = Math.max(...o.groups.flatMap((g) => g.texts.map((t) => textW(t, 12, 600)))) + 12;
      const x0 = labelW, x1 = w - valW;
      const max = o.max;
      const sx = (v) => x0 + (v / max) * (x1 - x0);
      const h = o.groups.length * groupH + 26;
      const svg = root(container, w, h, o.aria);
      gridX(svg, ticks(0, max, Math.max(2, Math.floor((x1 - x0) / 90))), sx, 0, o.groups.length * groupH, o.tickFmt || ((v) => v));
      o.groups.forEach((gr, i) => {
        const g = el('g', { class: 'row' }, svg);
        const top = i * groupH + pad / 2;
        text(g, 0, top + (n * barH + (n - 1) * gap) / 2 + 4, gr.label, 'lbl-strong');
        gr.values.forEach((v, j) => {
          const y = top + j * (barH + gap);
          el('path', { d: hbarPath(x0, sx(v), y, barH, 4), fill: o.series[j].color, class: 'mark' }, g);
          text(g, sx(v) + 6, y + barH / 2 + 4, gr.texts[j], 'val');
        });
        const hit = el('rect', { x: 0, y: i * groupH, width: w, height: groupH, class: 'hit' }, g);
        hover(hit, () => ({ title: gr.label, rows: gr.values.map((v, j) => ({ value: gr.texts[j], label: o.series[j].name, color: o.series[j].color })) }),
          `${gr.label}: ` + gr.values.map((v, j) => `${o.series[j].name} ${gr.texts[j]}`).join(', '));
      });
      el('line', { x1: x0, x2: x0, y1: 0, y2: o.groups.length * groupH, stroke: css('--axis'), 'stroke-width': 1 }, svg);
    });
    if (o.table !== false) tableView(o.tableHost || container, [''].concat(o.series.map((s) => s.name)), o.groups.map((g) => [g.label].concat(g.texts)));
  }

  /* ---------- dumbbell: from (hollow ring) -> to (filled) ----------
     rows: [{label, from, to, color, text, fromText, toText, marker:{v, text, label}}] */
  function dumbbell(container, o) {
    mount(container, (w) => {
      const maxLab = Math.max(...o.rows.map((r) => textW(r.label, 12)));
      const stacked = maxLab + 16 > w * 0.4;
      const rowH = stacked ? 48 : (o.rowH || 38);
      const valW = Math.max(...o.rows.map((r) => textW(r.text, 12, 600))) + 16;
      const x0 = stacked ? 8 : maxLab + 16, x1 = w - valW;
      const max = o.max;
      const sx = (v) => x0 + (v / max) * (x1 - x0);
      const h = o.rows.length * rowH + 26;
      const svg = root(container, w, h, o.aria);
      gridX(svg, ticks(0, max, Math.max(2, Math.floor((x1 - x0) / 90))), sx, 0, o.rows.length * rowH, o.tickFmt || ((v) => v));
      o.rows.forEach((r, i) => {
        const g = el('g', { class: 'row' }, svg);
        const cy = stacked ? i * rowH + 32 : i * rowH + rowH / 2;
        text(g, 0, stacked ? i * rowH + 13 : cy + 4, r.label, 'lbl');
        el('line', { x1: sx(r.from), x2: sx(r.to), y1: cy, y2: cy, stroke: css('--ink-mark-light'), 'stroke-width': 2, 'stroke-linecap': 'round' }, g);
        if (r.marker) {
          el('line', { x1: sx(r.marker.v), x2: sx(r.marker.v), y1: cy - 8, y2: cy + 8, stroke: css('--ink-mid'), 'stroke-width': 2 }, g);
        }
        el('circle', { cx: sx(r.from), cy, r: 5, fill: '#fff', stroke: css('--ink-mid'), 'stroke-width': 2, class: 'mark' }, g);
        el('circle', { cx: sx(r.to), cy, r: 6, fill: r.color, stroke: '#fff', 'stroke-width': 2, class: 'mark' }, g);
        text(g, sx(Math.max(r.from, r.to, r.marker ? r.marker.v : 0)) + 12, cy + 4, r.text, 'val');
        const hit = el('rect', { x: 0, y: i * rowH, width: w, height: rowH, class: 'hit' }, g);
        hover(hit, () => ({
          title: r.label,
          rows: [{ value: r.fromText, label: o.fromName }, { value: r.toText, label: o.toName, color: r.color }]
            .concat(r.marker ? [{ value: r.marker.text, label: r.marker.label }] : []),
        }), `${r.label}: ${o.fromName} ${r.fromText}, ${o.toName} ${r.toText}`);
      });
    });
    if (o.table !== false) {
      const hasMarker = o.rows.some((r) => r.marker);
      tableView(o.tableHost || container, [''].concat([o.fromName, o.toName], hasMarker ? [o.markerName] : []),
        o.rows.map((r) => [r.label, r.fromText, r.toText].concat(hasMarker ? [r.marker ? r.marker.text : ''] : [])));
    }
  }

  /* ---------- strip (one dot per point, dodged into a beeswarm) ----------
     rows: [{label, points:[{v, kind, title, valueText}]}]; kinds: {k:{color, r, name, on_top}};
     callouts: [{row, v, text}] */
  function strip(container, o) {
    mount(container, (w) => {
      const narrow = w < 600;
      const k = narrow ? 0.7 : 1, step = narrow ? 6.5 : 9, cap = narrow ? 9 : 12;
      const x0 = narrow ? 6 : Math.min(w * 0.3, Math.max(...o.rows.map((r) => textW(r.label, 12, 600))) + 16), x1 = w - 10;
      const max = o.max;
      const sx = (v) => x0 + (v / max) * (x1 - x0);
      const layouts = o.rows.map((row) => {
        const placed = [];
        const pts = row.points.slice().sort((a, b) => (o.kinds[a.kind].on_top ? 1 : 0) - (o.kinds[b.kind].on_top ? 1 : 0) || a.v - b.v);
        let maxLevel = 0;
        pts.forEach((p) => {
          const x = sx(p.v), r = o.kinds[p.kind].r * k;
          let best = 0, bestClash = Infinity;
          for (let j = 0; j <= 2 * cap; j++) {
            const lvl = j === 0 ? 0 : (j % 2 ? (j + 1) / 2 : -j / 2);
            const clash = placed.filter((q) => q.lvl === lvl && Math.abs(q.x - x) < q.r + r + 1.5).length;
            if (clash === 0) { best = lvl; bestClash = 0; break; }
            if (clash < bestClash) { bestClash = clash; best = lvl; }
          }
          placed.push({ x, lvl: best, r, p });
          maxLevel = Math.max(maxLevel, Math.abs(best));
        });
        return { placed, maxLevel };
      });
      // Callout labels stay inside the chart; labels that would collide go on a second line.
      const callouts = (o.callouts || []).map((c) => {
        const x = sx(c.v), tw = textW(c.text, 11) * 1.08;
        const left = Math.max(0, Math.min(x - 4, w - tw - 4));
        return Object.assign({}, c, { x, tw, left, right: left + tw, line: 0 });
      });
      o.rows.forEach((_, row) => {
        const cs = callouts.filter((c) => c.row === row).sort((a, b) => a.left - b.left);
        cs.forEach((c, i) => { if (i && c.left < cs[i - 1].right + 8) c.line = cs[i - 1].line + 1; });
      });
      const linesAbove = (row) => {
        const cs = callouts.filter((c) => c.row === row);
        return cs.length ? 1 + Math.max(...cs.map((c) => c.line)) : 0;
      };
      let y = 0;
      const bands = layouts.map((l, i) => {
        const labelH = narrow ? 18 : 0;
        const top = y + labelH + linesAbove(i) * 14 + 6;
        const hh = Math.max(40, (2 * l.maxLevel + 1) * step + 16);
        const band = { top: y, labelY: y + 13, cy: top + hh / 2, hh, calloutTop: y + labelH };
        y = top + hh + 4;
        return band;
      });
      const h = y + 26;
      const svg = root(container, w, h, o.aria);
      gridX(svg, ticks(0, max, Math.max(2, Math.floor((x1 - x0) / 80))), sx, 0, y, o.tickFmt || ((v) => v));
      layouts.forEach((l, i) => {
        const b = bands[i];
        const g = el('g', {}, svg);
        if (i > 0) el('line', { x1: 0, x2: w, y1: b.top, y2: b.top, stroke: css('--border-subtle'), 'stroke-width': 1 }, g);
        text(g, 0, narrow ? b.labelY : b.cy + 4, o.rows[i].label, 'lbl-strong');
        l.placed.forEach((q) => {
          const kk = o.kinds[q.p.kind];
          const py = b.cy - q.lvl * step;
          const c = el('circle', { cx: q.x, cy: py, r: q.r, fill: kk.color, stroke: '#fff', 'stroke-width': narrow ? 1.5 : 2 }, g);
          c.setAttribute('aria-hidden', 'true');
          const hit = el('circle', { cx: q.x, cy: py, r: Math.max(q.r + 4, 8), class: 'hit' }, g);
          hover(hit, () => ({ title: q.p.title, rows: [{ value: q.p.valueText, label: kk.name, color: kk.color }] }), `${q.p.title}: ${q.p.valueText}`);
        });
      });
      callouts.forEach((c) => {
        const b = bands[c.row];
        const ty = b.calloutTop + 11 + c.line * 14;
        el('line', { x1: c.x, x2: c.x, y1: ty + 4, y2: b.cy - 8, stroke: css('--ink-mid'), 'stroke-width': 1 }, svg);
        text(svg, c.left, ty, c.text, 'annot');
      });
    });
    if (o.table !== false) {
      const rows = [];
      o.rows.forEach((r) => r.points.forEach((p) => rows.push([p.title, r.label, o.kinds[p.kind].name, p.valueText])));
      tableView(o.tableHost || container, o.tableHeaders || ['Window', 'Pairs', 'Kind', 'Loss'], rows);
    }
  }

  /* ---------- line chart with crosshair ----------
     series: [{name, color, width, points:[{t, y}], endLabel}] ; yMin, yMax ; bands: [{from, to, label}] */
  function lines(container, o) {
    mount(container, (w) => {
      const endW = Math.max(...o.series.map((s) => textW(s.endLabel || '', 12, 600))) + 14;
      const x0 = 36, x1 = w - endW, y0 = 14, plotH = o.height || 230, y1 = y0 + plotH;
      const ts = o.series[0].points.map((p) => parseDay(p.t));
      const tMin = ts[0], tMax = ts[ts.length - 1];
      const sx = (t) => x0 + ((t - tMin) / (tMax - tMin)) * (x1 - x0);
      const sy = (v) => y1 - ((v - o.yMin) / (o.yMax - o.yMin)) * plotH;
      const h = y1 + 30;
      const svg = root(container, w, h, o.aria);
      (o.bands || []).forEach((b) => {
        const bx0 = sx(Math.max(tMin, parseDay(b.from))), bx1 = sx(Math.min(tMax, parseDay(b.to)));
        el('rect', { x: bx0, y: y0, width: bx1 - bx0, height: plotH, fill: css('--gap-band') }, svg);
        text(svg, bx0 + 6, y0 + 13, b.label, 'annot');
      });
      const gy = el('g', { class: 'tick' }, svg);
      ticks(o.yMin, o.yMax, 5).forEach((v) => {
        el('line', { x1: x0, x2: x1, y1: sy(v), y2: sy(v), stroke: css('--grid'), 'stroke-width': 1 }, gy);
        text(gy, x0 - 6, sy(v) + 4, (o.yFmt || ((x) => x))(v), '', { 'text-anchor': 'end' });
      });
      const gx = el('g', { class: 'tick' }, svg);
      const startYear = new Date(tMin).getUTCFullYear();
      for (let yr = startYear; yr <= new Date(tMax).getUTCFullYear(); yr++) {
        [0, 6].forEach((mo) => {
          const t = Date.UTC(yr, mo, 1);
          if (t < tMin || t > tMax) return;
          el('line', { x1: sx(t), x2: sx(t), y1: y1, y2: y1 + 4, stroke: css('--axis') }, gx);
          text(gx, sx(t), y1 + 18, mo === 0 ? String(yr) : 'Jul', '', { 'text-anchor': 'middle' });
        });
      }
      el('line', { x1: x0, x2: x1, y1: y1, y2: y1, stroke: css('--axis'), 'stroke-width': 1 }, svg);
      o.series.forEach((s) => {
        const d = s.points.map((p, i) => `${i ? 'L' : 'M'}${sx(parseDay(p.t)).toFixed(1)},${sy(p.y).toFixed(1)}`).join('');
        el('path', { d, fill: 'none', stroke: s.color, 'stroke-width': s.width || 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
        const last = s.points[s.points.length - 1];
        el('circle', { cx: sx(parseDay(last.t)), cy: sy(last.y), r: 4, fill: s.color, stroke: '#fff', 'stroke-width': 2 }, svg);
      });
      // end labels, nudged apart only when they would overlap
      const ends = o.series.map((s) => ({ s, y: sy(s.points[s.points.length - 1].y) })).sort((a, b) => a.y - b.y);
      for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 15) ends[i].y = ends[i - 1].y + 15;
      ends.forEach((e) => text(svg, x1 + 8, e.y + 4, e.s.endLabel, 'val'));
      // crosshair
      const cross = el('line', { y1: y0, y2: y1, stroke: css('--ink-mid'), 'stroke-width': 1, visibility: 'hidden' }, svg);
      const dots = o.series.map((s) => el('circle', { r: 4, fill: s.color, stroke: '#fff', 'stroke-width': 2, visibility: 'hidden' }, svg));
      const overlay = el('rect', { x: x0, y: y0, width: x1 - x0, height: plotH, class: 'hit' }, svg);
      let idx = ts.length - 1;
      const showAt = (i, cx, cy) => {
        idx = i;
        const x = sx(ts[i]);
        cross.setAttribute('x1', x); cross.setAttribute('x2', x); cross.setAttribute('visibility', 'visible');
        o.series.forEach((s, j) => { dots[j].setAttribute('cx', x); dots[j].setAttribute('cy', sy(s.points[i].y)); dots[j].setAttribute('visibility', 'visible'); });
        showTip(cx, cy, { title: (o.tipDate || fmtMonth)(ts[i]), rows: o.series.map((s) => ({ value: o.valueFmt(s.points[i].y), label: s.name, color: s.color })) });
      };
      const hide = () => { cross.setAttribute('visibility', 'hidden'); dots.forEach((d) => d.setAttribute('visibility', 'hidden')); hideTip(); };
      overlay.setAttribute('tabindex', '0');
      overlay.setAttribute('aria-label', (o.aria || 'Chart') + '. Use the left and right arrow keys to read values.');
      overlay.addEventListener('pointermove', (e) => {
        const r = svg.getBoundingClientRect(), px = ((e.clientX - r.left) / r.width) * w;
        let best = 0;
        ts.forEach((t, i) => { if (Math.abs(sx(t) - px) < Math.abs(sx(ts[best]) - px)) best = i; });
        showAt(best, e.clientX, e.clientY);
      });
      overlay.addEventListener('pointerleave', hide);
      overlay.addEventListener('blur', hide);
      const keyShow = () => { const r = svg.getBoundingClientRect(); showAt(idx, r.left + (sx(ts[idx]) / w) * r.width, r.top + 40); };
      overlay.addEventListener('focus', keyShow);
      overlay.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
          e.preventDefault();
          idx = Math.max(0, Math.min(ts.length - 1, idx + (e.key === 'ArrowLeft' ? -1 : 1)));
          keyShow();
        }
      });
    });
    if (o.table !== false) {
      tableView(o.tableHost || container, ['Month'].concat(o.series.map((s) => s.name)),
        o.series[0].points.map((p, i) => [fmtMonth(parseDay(p.t))].concat(o.series.map((s) => o.valueFmt(s.points[i].y)))));
    }
  }

  /* ---------- daily columns with release markers ----------
     days: [{d, n}] (snapshot days only; missing days are shaded as gaps);
     vlines: [{t, label}] ; markers: [{t, label, color}] */
  function columns(container, o) {
    mount(container, (w) => {
      const x0 = 40, x1 = w - 10, y0 = 30, plotH = o.height || 220, y1 = y0 + plotH;
      const ts = o.days.map((d) => parseDay(d.d));
      const tMin = ts[0], tMax = ts[ts.length - 1] + dayMs;
      const sx = (t) => x0 + ((t - tMin) / (tMax - tMin)) * (x1 - x0);
      const max = o.max || Math.max(...o.days.map((d) => d.n));
      const sy = (v) => y1 - (v / max) * plotH;
      const svg = root(container, w, y1 + 44, o.aria);
      for (let i = 1; i < ts.length; i++) {
        if (ts[i] - ts[i - 1] > dayMs * 1.5) {
          el('rect', { x: sx(ts[i - 1] + dayMs), y: y0, width: sx(ts[i]) - sx(ts[i - 1] + dayMs), height: plotH, fill: css('--gap-band') }, svg);
        }
      }
      const gy = el('g', { class: 'tick' }, svg);
      ticks(0, max, 4).forEach((v) => {
        el('line', { x1: x0, x2: x1, y1: sy(v), y2: sy(v), stroke: css('--grid'), 'stroke-width': 1 }, gy);
        text(gy, x0 - 6, sy(v) + 4, String(v), '', { 'text-anchor': 'end' });
      });
      (o.vlines || []).forEach((v) => {
        const x = sx(parseDay(v.t));
        el('line', { x1: x, x2: x, y1: y0 - 4, y2: y1, stroke: css('--ink-mark-light'), 'stroke-width': 1 }, svg);
        text(svg, x, y0 - 10, v.label, 'annot', { 'text-anchor': 'middle' });
      });
      const bw = Math.max(1, ((x1 - x0) / ((tMax - tMin) / dayMs)) * 0.85);
      const bars = el('g', {}, svg);
      o.days.forEach((d, i) => {
        if (d.n <= 0) return;
        el('rect', { x: sx(ts[i]), y: sy(d.n), width: bw, height: y1 - sy(d.n), fill: o.color }, bars);
      });
      el('line', { x1: x0, x2: x1, y1: y1, y2: y1, stroke: css('--axis'), 'stroke-width': 1 }, svg);
      (o.markers || []).forEach((m) => {
        const x = sx(parseDay(m.t));
        el('path', { d: `M${x},${y1 + 4}l6,10h-12z`, fill: m.color, stroke: '#fff', 'stroke-width': 1.5 }, svg);
      });
      const gx = el('g', { class: 'tick' }, svg);
      for (let yr = new Date(tMin).getUTCFullYear(); yr <= new Date(tMax).getUTCFullYear(); yr++) {
        [0, 6].forEach((mo) => {
          const t = Date.UTC(yr, mo, 1);
          if (t < tMin || t > tMax) return;
          text(gx, sx(t), y1 + 32, mo === 0 ? String(yr) : 'Jul', '', { 'text-anchor': 'middle' });
        });
      }
      const cross = el('line', { y1: y0, y2: y1, stroke: css('--ink-mark'), 'stroke-width': 1, visibility: 'hidden' }, svg);
      const overlay = el('rect', { x: x0, y: y0 - 16, width: x1 - x0, height: plotH + 34, class: 'hit' }, svg);
      let idx = o.days.reduce((b, d, i) => (d.n > o.days[b].n ? i : b), 0);
      const showAt = (i, cx, cy) => {
        idx = i;
        const x = sx(ts[i]) + bw / 2;
        cross.setAttribute('x1', x); cross.setAttribute('x2', x); cross.setAttribute('visibility', 'visible');
        const near = (o.markers || []).concat(o.vlines || []).filter((m) => Math.abs(parseDay(m.t) - ts[i]) < dayMs * 1.5);
        showTip(cx, cy, { title: fmtDay(ts[i]), rows: [{ value: String(o.days[i].n), label: o.valueLabel, color: o.color }], note: near.map((m) => m.tip || m.label).join(' · ') || undefined });
      };
      const hide = () => { cross.setAttribute('visibility', 'hidden'); hideTip(); };
      overlay.setAttribute('tabindex', '0');
      overlay.setAttribute('aria-label', (o.aria || 'Chart') + '. Use the left and right arrow keys to read each day.');
      overlay.addEventListener('pointermove', (e) => {
        const r = svg.getBoundingClientRect(), px = ((e.clientX - r.left) / r.width) * w;
        const t = tMin + ((px - x0) / (x1 - x0)) * (tMax - tMin);
        let best = 0;
        ts.forEach((tt, i) => { if (Math.abs(tt - t) < Math.abs(ts[best] - t)) best = i; });
        showAt(best, e.clientX, e.clientY);
      });
      overlay.addEventListener('pointerleave', hide);
      overlay.addEventListener('blur', hide);
      const keyShow = () => { const r = svg.getBoundingClientRect(); showAt(idx, r.left + (sx(ts[idx]) / w) * r.width, r.top + 60); };
      overlay.addEventListener('focus', keyShow);
      overlay.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
          e.preventDefault();
          idx = Math.max(0, Math.min(ts.length - 1, idx + (e.key === 'ArrowLeft' ? -1 : 1)));
          keyShow();
        }
      });
    });
    if (o.table !== false) {
      tableView(o.tableHost || container, ['Day', o.valueLabel],
        o.days.filter((d) => d.n >= (o.tableMin || 1)).map((d) => [fmtDay(parseDay(d.d)), String(d.n)]));
    }
  }

  /* ---------- forest plot (log scale) ----------
     rows: [{label, est, lo, hi, color, sub, strong, valueText, note, tableRow}] */
  function forest(container, o) {
    mount(container, (w) => {
      const top = 26;
      const maxLab = Math.max(...o.rows.map((r) => textW(r.label, 12, r.strong ? 600 : 400) + (r.sub ? 14 : 0)));
      const stacked = maxLab + 16 > w * 0.42;
      const rowH = stacked ? 40 : 30;
      const valW = Math.max(...o.rows.map((r) => textW(r.valueText, 12, 600))) + 14;
      const x0 = stacked ? 8 : maxLab + 16, x1 = w - valW;
      const lmin = Math.log(o.min), lmax = Math.log(o.max);
      const sx = (v) => x0 + ((Math.log(Math.max(o.min, Math.min(o.max, v))) - lmin) / (lmax - lmin)) * (x1 - x0);
      const h = top + o.rows.length * rowH + 26;
      const svg = root(container, w, h, o.aria);
      const g0 = el('g', { class: 'tick' }, svg);
      const tk = (o.ticks || [0.1, 0.3, 1, 3, 10]).filter((v) => (x1 - x0) > 260 || [0.1, 1, 10].includes(v));
      tk.forEach((v) => {
        el('line', { x1: sx(v), x2: sx(v), y1: top - 4, y2: top + o.rows.length * rowH, stroke: v === 1 ? css('--ink-mid') : css('--grid'), 'stroke-width': 1 }, g0);
        text(g0, sx(v), top + o.rows.length * rowH + 15, String(v), '', { 'text-anchor': 'middle' });
      });
      text(svg, sx(1) - 6, 12, o.leftNote || '← slower after', 'annot', { 'text-anchor': 'end' });
      text(svg, sx(1) + 6, 12, o.rightNote || 'faster after →', 'annot');
      o.rows.forEach((r, i) => {
        const g = el('g', { class: 'row' }, svg);
        const cy = stacked ? top + i * rowH + 27 : top + i * rowH + rowH / 2;
        if (r.strong) el('rect', { x: 0, y: top + i * rowH + 2, width: w, height: rowH - 4, rx: 6, fill: css('--primary-light') }, g);
        text(g, r.sub ? 14 : 4, stacked ? top + i * rowH + 14 : cy + 4, r.label, r.strong ? 'lbl-strong' : 'lbl', r.sub ? { 'font-style': 'italic' } : null);
        el('line', { x1: sx(r.lo), x2: sx(r.hi), y1: cy, y2: cy, stroke: r.color, 'stroke-width': 2, 'stroke-linecap': 'round', class: 'mark' }, g);
        el('circle', { cx: sx(r.est), cy, r: 5, fill: r.color, stroke: '#fff', 'stroke-width': 2, class: 'mark' }, g);
        text(g, x1 + 8, cy + 4, r.valueText, 'val');
        const hit = el('rect', { x: 0, y: top + i * rowH, width: w, height: rowH, class: 'hit' }, g);
        hover(hit, () => ({ title: r.label, rows: [{ value: r.valueText, label: 'rate ratio', color: r.color }], note: r.note }), `${r.label}: ${r.valueText}. ${r.note || ''}`);
      });
    });
    if (o.table !== false) tableView(o.tableHost || container, o.tableHeaders, o.rows.map((r) => r.tableRow));
  }

  /* ---------- 100% stacked bars ----------
     rows: [{label, parts:[{name, value, color, textClass}]}] */
  function stack100(container, o) {
    mount(container, (w) => {
      const barH = 24, gapPx = 2;
      // A label too wide for the chart breaks after its colon onto a second line.
      const wrap = o.rows.some((r) => textW(r.label, 12, 600) * 1.08 > w && r.label.includes(': '));
      const labelH = wrap ? 36 : 20, rowH = labelH + barH + 18;
      const h = o.rows.length * rowH;
      const svg = root(container, w, h, o.aria);
      o.rows.forEach((r, i) => {
        const g = el('g', { class: 'row' }, svg);
        const y = i * rowH + labelH;
        if (wrap && r.label.includes(': ')) {
          const k = r.label.indexOf(': ');
          text(g, 0, y - 23, r.label.slice(0, k), 'lbl-strong');
          text(g, 0, y - 7, r.label.slice(k + 2), 'lbl');
        } else {
          text(g, 0, y - 7, r.label, 'lbl-strong');
        }
        const total = r.parts.reduce((s, p) => s + p.value, 0);
        let x = 0;
        r.parts.forEach((p, j) => {
          const pw = (p.value / total) * w;
          const last = j === r.parts.length - 1;
          const segW = Math.max(0, pw - (last ? 0 : gapPx));
          const rx = 4;
          el('rect', { x, y, width: segW, height: barH, rx: (j === 0 || last) ? rx : 0, fill: p.color, class: 'mark' }, g);
          if (j > 0 && !last) { /* square inner corners via rx 0 */ }
          const share = Math.round((p.value / total) * 100) + '%';
          const label = `${share} ${p.short || ''}`.trim();
          if (textW(label, 11.5, 600) + 12 < segW) text(g, x + 8, y + barH / 2 + 4, label, p.textClass || 'val-in');
          else if (textW(share, 11.5, 600) + 10 < segW) text(g, x + 6, y + barH / 2 + 4, share, p.textClass || 'val-in');
          const hit = el('rect', { x, y: y - 2, width: Math.max(segW, 8), height: barH + 4, class: 'hit' }, g);
          hover(hit, () => ({ title: r.label, rows: [{ value: `${share} (${p.value.toLocaleString('en-US')} nodes)`, label: p.name, color: p.color }] }), `${r.label}, ${p.name}: ${share}`);
          x += pw;
        });
      });
    });
    if (o.table !== false) {
      const names = o.rows[0].parts.map((p) => p.name);
      tableView(o.tableHost || container, ['Cohort'].concat(names), o.rows.map((r) => {
        const total = r.parts.reduce((s, p) => s + p.value, 0);
        return [r.label].concat(r.parts.map((p) => `${Math.round((p.value / total) * 100)}% (${p.value.toLocaleString('en-US')})`));
      }));
    }
  }

  window.BDLCharts = { hbars, groupedH, dumbbell, strip, lines, columns, forest, stack100, tableView, fmtDay, parseDay, css };
})();
