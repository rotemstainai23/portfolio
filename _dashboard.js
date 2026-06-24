/* ============================================================================
 * _dashboard.js — רכיבי UI משותפים לכל הדשבורדים
 * ----------------------------------------------------------------------------
 * מטרה: קוד UI אחד במקום כפילויות בין hub.html ל-portfolio.html.
 *
 * כל הפונקציות נארזות תחת namespace גלובלי Dash.
 * Additive בלבד — שום קובץ קיים לא תלוי בקובץ הזה עד שמחברים אותו.
 *
 * שימוש:
 *   <script src="_dashboard.js"></script>
 *   Dash.buildHeatmap(holdings, { svgEl, tooltipEl, height: 260, linkBase: '/templates' });
 *   Dash.buildTickerCard(card, { linkBase: '/templates' });
 * ========================================================================== */
(function (global) {
  'use strict';

  var Dash = {};

  /* ---- סיגנל: מיפוי verdict → מחלקה (good / warn / bad / neutral) ---- */
  Dash.sigClass = function (verdict) {
    if (!verdict) return 'neutral';
    var v = verdict.toString().toLowerCase();
    if (/buy|strong|חזק|קנ|invest|yes/i.test(v)) return 'good';
    if (/sell|avoid|לא|no|red/i.test(v)) return 'bad';
    if (/hold|wait|watch|yellow|שמור/i.test(v)) return 'warn';
    return 'neutral';
  };

  /* ---- תווית קצרה לסיגנל ---- */
  Dash.sigLabel = function (verdict) {
    if (!verdict) return 'אין נתון';
    var v = verdict.toString();
    return v.length > 18 ? v.slice(0, 18) + '…' : v;
  };

  /* ---- מחלקת שינוי יומי ---- */
  Dash.changeClass = function (n) {
    if (n == null) return 'flat';
    return n > 0 ? 'up' : n < 0 ? 'down' : 'flat';
  };

  /* ---- פורמט אחוז עם סימן ---- */
  Dash.fmtPct = function (n) {
    if (n == null) return '';
    return (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
  };

  /* ---- אנימציית מונה (ease-out cubic) ---- */
  Dash.animateCounter = function (el, target, prefix, suffix, decimals, duration) {
    if (!el) return;
    prefix = prefix || '';
    suffix = suffix || '';
    decimals = decimals == null ? 0 : decimals;
    duration = duration || 1400;
    var start = performance.now();
    function step(now) {
      var t = Math.min((now - start) / duration, 1);
      var ease = 1 - Math.pow(1 - t, 3);
      el.textContent = prefix + (target * ease).toFixed(decimals) + suffix;
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  };

  /* ---- צבע תא הeatmap לפי אחוז P&L ---- */
  Dash.pnlColor = function (pct) {
    if (pct == null) return 'rgba(139,92,246,.4)';
    var c = Math.max(-20, Math.min(20, pct));
    if (c >= 0) {
      var t = c / 20;
      return 'rgba(' + Math.round(59 + (52 - 59) * t) + ',' + Math.round(130 + (211 - 130) * t) + ',' + Math.round(246 + (153 - 246) * t) + ',' + (0.55 + t * 0.35) + ')';
    } else {
      var t2 = Math.abs(c) / 20;
      return 'rgba(' + Math.round(59 + (251 - 59) * t2) + ',' + Math.round(130 + (113 - 130) * t2) + ',' + Math.round(246 + (133 - 246) * t2) + ',' + (0.55 + t2 * 0.35) + ')';
    }
  };

  /* ---- Treemap: חלוקת slice-and-dice ---- */
  Dash.sliceDice = function (items, x, y, w, h, horiz) {
    var total = items.reduce(function (s, d) { return s + d.value; }, 0);
    if (total === 0) return [];
    var rects = [], offset = 0;
    items.forEach(function (d) {
      var ratio = d.value / total;
      if (horiz) {
        rects.push(Object.assign({}, d, { x: x + offset, y: y, w: w * ratio, h: h }));
        offset += w * ratio;
      } else {
        rects.push(Object.assign({}, d, { x: x, y: y + offset, w: w, h: h * ratio }));
        offset += h * ratio;
      }
    });
    return rects;
  };

  /* ---- Stroke-dasharray לטבעת ציון ---- */
  Dash.ringFill = function (sig) {
    var pct = { good: 85, warn: 55, bad: 22, neutral: 0 }[sig] || 0;
    var circ = 2 * Math.PI * 14;
    return (pct / 100) * circ + ' ' + circ;
  };

  /* ---- רוחב סרגל Conviction ---- */
  Dash.convWidth = function (sig) {
    return { good: '82%', warn: '55%', bad: '28%', neutral: '40%' }[sig] || '40%';
  };

  /* ---- Heatmap ----
   * opts:
   *   svgEl      — אלמנט SVG או id מחרוזת
   *   tooltipEl  — אלמנט tooltip או id מחרוזת
   *   height     — גובה SVG (ברירת מחדל 260)
   *   linkBase   — קידומת לקישורי טיקר (ברירת מחדל '')
   *   sectionEl  — אלמנט section להסרת display:none אחרי בנייה (אופציונלי)
   * ------------------------------------------------------------------ */
  Dash.buildHeatmap = function (holdings, opts) {
    opts = opts || {};
    var svg = typeof opts.svgEl === 'string' ? document.getElementById(opts.svgEl) : opts.svgEl;
    var tooltip = typeof opts.tooltipEl === 'string' ? document.getElementById(opts.tooltipEl) : opts.tooltipEl;
    if (!svg) return;

    /* נקה תוכן קודם */
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    var H = opts.height || 260;
    var W = (svg.parentElement && svg.parentElement.getBoundingClientRect().width) || 800;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);

    var data = holdings
      .filter(function (h) { return (h.market_value || 0) > 0; })
      .map(function (h) {
        return {
          sym: h.symbol,
          name: h.name || h.symbol,
          value: h.market_value || 0,
          pnl: h.pnl || 0,
          pnlPct: h.market_value > 0 ? (h.pnl / (h.market_value - h.pnl)) * 100 : 0,
          price: h.current_price || h.buy_price || 0,
          change: h.day_change_pct || null,
        };
      })
      .sort(function (a, b) { return b.value - a.value; });

    if (!data.length) return;

    var linkBase = opts.linkBase != null ? opts.linkBase : '';
    var pad = 2;

    Dash.sliceDice(data, 2, 2, W - 4, H - 4, W >= H).forEach(function (d, i) {
      var ns = 'http://www.w3.org/2000/svg';
      var g = document.createElementNS(ns, 'g');
      g.style.cursor = 'pointer';
      g.style.animation = 'heatCell .4s var(--ease) ' + (i * 55) + 'ms both';

      var rx = Math.max(0, d.x + pad), ry = Math.max(0, d.y + pad);
      var rw = Math.max(0, d.w - pad * 2), rh = Math.max(0, d.h - pad * 2);

      var rect = document.createElementNS(ns, 'rect');
      rect.setAttribute('x', rx); rect.setAttribute('y', ry);
      rect.setAttribute('width', rw); rect.setAttribute('height', rh);
      rect.setAttribute('rx', 10);
      rect.setAttribute('fill', Dash.pnlColor(d.pnlPct));
      rect.setAttribute('stroke', 'rgba(255,255,255,.08)'); rect.setAttribute('stroke-width', '1');
      g.appendChild(rect);

      var labelSize = Math.min(rw / 3.5, rh / 2.2, 22);
      var showLabel = rw > 48 && rh > 30;
      var showPct = rw > 60 && rh > 50;

      if (showLabel) {
        var symEl = document.createElementNS(ns, 'text');
        symEl.setAttribute('x', rx + rw / 2);
        symEl.setAttribute('y', ry + rh / 2 + (showPct ? -6 : labelSize / 3));
        symEl.setAttribute('text-anchor', 'middle'); symEl.setAttribute('dominant-baseline', 'middle');
        symEl.setAttribute('font-family', "'Fira Code',monospace");
        symEl.setAttribute('font-size', Math.max(10, labelSize));
        symEl.setAttribute('font-weight', '900'); symEl.setAttribute('fill', 'rgba(255,255,255,.95)');
        symEl.textContent = d.sym;
        g.appendChild(symEl);

        if (showPct) {
          var pctEl = document.createElementNS(ns, 'text');
          pctEl.setAttribute('x', rx + rw / 2);
          pctEl.setAttribute('y', ry + rh / 2 + labelSize * 0.9);
          pctEl.setAttribute('text-anchor', 'middle'); pctEl.setAttribute('dominant-baseline', 'middle');
          pctEl.setAttribute('font-family', "'Fira Code',monospace");
          pctEl.setAttribute('font-size', Math.max(8, labelSize * 0.58));
          pctEl.setAttribute('font-weight', '700');
          pctEl.setAttribute('fill', d.pnlPct >= 0 ? 'rgba(52,211,153,.9)' : 'rgba(251,113,133,.9)');
          pctEl.textContent = (d.pnlPct >= 0 ? '+' : '') + d.pnlPct.toFixed(1) + '%';
          g.appendChild(pctEl);
        }
      }

      if (tooltip) {
        g.addEventListener('mouseenter', function () {
          tooltip.innerHTML =
            '<div class="hmt-sym">' + d.sym + '</div>' +
            '<div class="hmt-name">' + d.name + '</div>' +
            '<div class="hmt-row"><span class="hmt-lbl">מחיר</span><span class="hmt-val">$' + d.price.toFixed(2) + '</span></div>' +
            '<div class="hmt-row"><span class="hmt-lbl">שווי</span><span class="hmt-val">$' + d.value.toFixed(0) + '</span></div>' +
            '<div class="hmt-row"><span class="hmt-lbl">P&amp;L</span><span class="hmt-val" style="color:' + (d.pnl >= 0 ? 'var(--sig-good)' : 'var(--sig-bad)') + '">' +
            (d.pnl >= 0 ? '+' : '') + '$' + d.pnl.toFixed(0) + ' (' + (d.pnlPct >= 0 ? '+' : '') + d.pnlPct.toFixed(1) + '%)</span></div>' +
            (d.change != null ? '<div class="hmt-row"><span class="hmt-lbl">היום</span><span class="hmt-val" style="color:' + (d.change >= 0 ? 'var(--sig-good)' : 'var(--sig-bad)') + '">' + (d.change >= 0 ? '▲' : '▼') + ' ' + Math.abs(d.change).toFixed(2) + '%</span></div>' : '');
          tooltip.classList.add('visible');
        });
        g.addEventListener('mousemove', function (e) {
          var vw = window.innerWidth;
          var lx = (e.clientX + 16 + 180 > vw) ? e.clientX - 196 : e.clientX + 16;
          tooltip.style.left = lx + 'px';
          tooltip.style.top = (e.clientY - 60) + 'px';
        });
        g.addEventListener('mouseleave', function () { tooltip.classList.remove('visible'); });
      }

      g.addEventListener('click', function () { location.href = linkBase + '/analyst.html?ticker=' + d.sym; });
      svg.appendChild(g);
    });

    if (opts.sectionEl) {
      var sec = typeof opts.sectionEl === 'string' ? document.getElementById(opts.sectionEl) : opts.sectionEl;
      if (sec) sec.style.display = '';
    }
  };

  /* ---- Ticker Card HTML ----
   * card: { ticker, price, change, verdict, name, verdictLabel }
   * opts: { linkBase }
   * ------------------------------------------------------------------ */
  Dash.buildTickerCard = function (card, opts) {
    opts = opts || {};
    var linkBase = opts.linkBase != null ? opts.linkBase : '';
    var ticker = card.ticker;
    var price = card.price;
    var change = card.change;
    var verdict = card.verdict;
    var name = card.name || '';
    var verdictLabel = card.verdictLabel;

    var sig = Dash.sigClass(verdict);
    var chgCls = Dash.changeClass(change);
    var accentCls = sig === 'good' ? 'green' : sig === 'bad' ? 'red' : sig === 'warn' ? 'warn' : 'neutral';
    var dash = Dash.ringFill(sig);
    var convW = Dash.convWidth(sig);
    var label = verdictLabel || Dash.sigLabel(verdict);
    var ringLbl = sig === 'good' ? 'BUY' : sig === 'bad' ? 'SELL' : sig === 'warn' ? 'HOLD' : 'N/A';
    var priceTxt = price != null ? '$' + price.toFixed(2) : '—';
    var chgTxt = change != null ? Dash.fmtPct(change) : '—';
    var chgArrow = chgCls === 'up' ? '▲' : chgCls === 'down' ? '▼' : '—';

    return '<div class="ticker-card" onmousemove="const r=this.getBoundingClientRect();this.style.setProperty(\'--mx\',((event.clientX-r.left)/r.width*100)+\'%\');this.style.setProperty(\'--my\',((event.clientY-r.top)/r.height*100)+\'%\')">' +
      '<div class="tc-accent ' + accentCls + '"></div>' +
      '<div class="tc-body">' +
        '<div class="tc-top">' +
          '<div class="tc-left">' +
            '<div class="tc-symbol">' + ticker + '</div>' +
            '<div class="tc-name">' + name + '</div>' +
            '<span class="tc-ai">⬡ AI</span>' +
          '</div>' +
          '<div class="tc-ring-wrap">' +
            '<div class="tc-ring"><svg viewBox="0 0 32 32">' +
              '<circle class="tc-ring-track" cx="16" cy="16" r="14"/>' +
              '<circle class="tc-ring-fill ' + sig + '" cx="16" cy="16" r="14" style="stroke-dasharray:' + dash + ';stroke-dashoffset:0"/>' +
            '</svg></div>' +
            '<span class="tc-ring-lbl">' + ringLbl + '</span>' +
          '</div>' +
        '</div>' +
        '<span class="tc-signal ' + sig + '">' + label + '</span>' +
        '<div style="margin-top:10px">' +
          '<div class="tc-price">' + priceTxt + '</div>' +
          '<div class="tc-change ' + chgCls + '">' + chgArrow + ' ' + chgTxt + ' היום</div>' +
        '</div>' +
        '<div class="tc-conv-wrap">' +
          '<div class="tc-conv-lbl">Conviction</div>' +
          '<div class="tc-conv-track"><div class="tc-conv-fill ' + sig + '" style="--conv-w:' + convW + '"></div></div>' +
        '</div>' +
        '<div class="tc-links">' +
          '<a class="tc-link analyst" href="' + linkBase + '/analyst.html?ticker=' + ticker + '"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M3 3v18h18"/><rect x="7" y="11" width="3" height="7"/><rect x="12" y="7" width="3" height="11"/><rect x="17" y="4" width="3" height="14"/></svg> אנליסט</a>' +
          '<a class="tc-link devils" href="' + linkBase + '/devils.html?ticker=' + ticker + '"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> Devil</a>' +
          '<a class="tc-link ceo" href="' + linkBase + '/ceo.html?ticker=' + ticker + '"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg> CEO</a>' +
          '<a class="tc-link ic" href="' + linkBase + '/ic.html?ticker=' + ticker + '"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg> IC</a>' +
        '</div>' +
      '</div>' +
    '</div>';
  };

  global.Dash = Dash;
})(window);
