/* ============================================================================
 * _data.js — שכבת גישה אחידה לנתונים
 * ----------------------------------------------------------------------------
 * מטרה: מקור אמת אחד לכל הדשבורדים, עם נפילה אוטומטית מ-API חי לקבצים סטטיים.
 *
 *   מצב Live  : השרת (Flask) פעיל. קורא מ-/api/* עם מחירים חיים מלאים.
 *   מצב Cloud : השרת כבוי (PC כבוי / מוגש מ-GitHub Pages). קורא קבצי JSON
 *               סטטיים ומשחזר את אותם שדות מחושבים בצד הלקוח.
 *
 * כל פונקציה מחזירה את אותו מבנה שה-API מחזיר, בתוספת דגל _live.
 * שום קובץ קיים לא תלוי בקובץ הזה עד שמחברים אותו במפורש (additive בלבד).
 *
 * תאימות: ES5/var, ללא bundler, נטען כ-<script src="_data.js"> רגיל.
 * ========================================================================== */
(function (global) {
  'use strict';

  /* נתיב הבסיס לקבצים הסטטיים נגזר ממיקום הקובץ הזה (שורש הפרויקט),
     כך שזה עובד זהה משורש האתר וגם מתוך templates/. */
  var BASE = (function () {
    try {
      var src = (document.currentScript && document.currentScript.src) || '';
      if (src) return src.slice(0, src.lastIndexOf('/') + 1);
    } catch (e) {}
    return '';
  })();

  var DataLayer = {
    /* null = עוד לא נבדק, true = Live, false = Cloud/static */
    live: null,
    base: BASE,
  };

  /* ---- עזרי fetch ---- */
  function fetchJSON(url, opts) {
    return fetch(url, opts).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }
  /* fetch עם timeout קצר — כדי שזיהוי המצב לא יתקע כשהשרת כבוי */
  function fetchJSONTimeout(url, ms) {
    return new Promise(function (resolve, reject) {
      var done = false;
      var t = setTimeout(function () { if (!done) { done = true; reject(new Error('timeout')); } }, ms || 2500);
      fetch(url, { cache: 'no-store' }).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      }).then(function (j) { if (!done) { done = true; clearTimeout(t); resolve(j); } })
        .catch(function (e) { if (!done) { done = true; clearTimeout(t); reject(e); } });
    });
  }
  function staticURL(rel) { return DataLayer.base + rel + '?_=' + Date.now(); }

  /* ============================================================
   * שחזור /api/portfolio במצב סטטי
   * משחזר בדיוק את החישובים מ-app.py (market_value, pnl, summary,
   * distance_pct, alert) מתוך portfolio.json + daily_latest.json.
   * ============================================================ */
  function buildStaticPortfolio(raw, daily) {
    var holdings  = raw.holdings || [];
    var watchlist = raw.watchlist || [];
    var trades    = raw.trades || [];
    var cash      = Number(raw.cash || 0);

    /* מפת מחירים לפי טיקר מתוך הדוח היומי */
    var pmap = {};
    if (daily && daily.holdings) {
      daily.holdings.forEach(function (h) { if (h.ticker) pmap[h.ticker] = h; });
    }
    var tmap = {};
    if (daily && daily.watchlist_triggers) {
      daily.watchlist_triggers.forEach(function (t) { if (t.ticker) tmap[t.ticker] = t; });
    }

    var enriched = [], totalValue = 0, totalCost = 0, todayChg = 0;
    holdings.forEach(function (h) {
      var sym = h.symbol;
      var d   = pmap[sym] || {};
      var curr = d.price != null ? d.price : null;
      var chg  = d.chg_pct != null ? d.chg_pct : null;
      var qty  = Number(h.quantity || 0);
      var cost = Number(h.buy_price || 0) * qty;
      var mval = curr != null ? curr * qty : null;
      var pnl  = mval != null ? mval - cost : null;
      var pnlP = (pnl != null && cost > 0) ? pnl / cost * 100 : null;

      if (mval != null) totalValue += mval;
      totalCost += cost;
      if (curr && chg != null) {
        var prev = curr / (1 + chg / 100);
        todayChg += (curr - prev) * qty;
      }
      enriched.push({
        symbol: sym, name: h.name || sym, quantity: qty, buy_price: Number(h.buy_price || 0),
        current_price: curr, day_change_pct: chg,
        price_stale_s: d.price != null ? null : undefined, price_source: d.price != null ? 'daily' : undefined,
        market_value: mval != null ? Math.round(mval * 1e4) / 1e4 : null,
        cost_basis: Math.round(cost * 1e4) / 1e4,
        pnl: pnl != null ? Math.round(pnl * 1e4) / 1e4 : null,
        pnl_pct: pnlP != null ? Math.round(pnlP * 1e4) / 1e4 : null,
        layer: h.layer, sector: h.sector, analyst_score: h.analyst_score,
        risk_score: h.risk_score, notes: h.notes || '',
      });
    });

    var wEnriched = watchlist.map(function (w) {
      var sym = w.symbol;
      var d = tmap[sym] || pmap[sym] || {};
      var curr = d.current_price != null ? d.current_price : (d.price != null ? d.price : null);
      var trig = w.trigger_price != null ? Number(w.trigger_price) : null;
      var direction = w.trigger_direction || 'below';
      var alert = false;
      if (curr != null && trig != null) {
        if (direction === 'below' && curr <= trig) alert = true;
        else if (direction === 'above' && curr >= trig) alert = true;
      }
      var dist = (curr != null && trig != null && trig > 0)
        ? Math.round((curr - trig) / trig * 100 * 100) / 100 : null;
      var out = {}; for (var k in w) out[k] = w[k];
      out.current_price = curr; out.distance_pct = dist; out.alert = alert;
      return out;
    });

    var totalPnl = totalValue - totalCost;
    return {
      holdings: enriched, watchlist: wEnriched, trades: trades, cash: cash,
      summary: {
        total_value: Math.round(totalValue * 1e4) / 1e4,
        total_cost: Math.round(totalCost * 1e4) / 1e4,
        total_pnl: Math.round(totalPnl * 1e4) / 1e4,
        total_pnl_pct: totalCost > 0 ? Math.round(totalPnl / totalCost * 100 * 1e4) / 1e4 : 0,
        today_change: Math.round(todayChg * 1e4) / 1e4,
        grand_total: Math.round((totalValue + cash) * 1e4) / 1e4,
        positions: enriched.length, trades_logged: trades.length,
      },
      timestamp: (daily && daily.generated) || new Date().toISOString(),
      _live: false,
    };
  }

  /* ---- API ציבורי ---- */

  /* תיק מלא: מנסה /api/portfolio, ואם נכשל בונה מצב סטטי */
  DataLayer.getPortfolio = function () {
    return fetchJSONTimeout('/api/portfolio', 2500).then(function (j) {
      DataLayer.live = true; j._live = true; return j;
    }).catch(function () {
      DataLayer.live = false;
      return Promise.all([
        fetchJSON(staticURL('portfolio.json')).catch(function () { return null; }),
        fetchJSON(staticURL('analyses/_daily/daily_latest.json')).catch(function () { return null; }),
      ]).then(function (arr) {
        if (!arr[0]) throw new Error('portfolio.json unavailable');
        return buildStaticPortfolio(arr[0], arr[1]);
      });
    });
  };

  /* דוח יומי */
  DataLayer.getDaily = function () {
    return fetchJSONTimeout('/api/daily/latest', 2500).then(function (j) {
      if (j) j._live = true; return j;
    }).catch(function () {
      return fetchJSON(staticURL('analyses/_daily/daily_latest.json'))
        .then(function (j) { if (j) j._live = false; return j; })
        .catch(function () { return null; });
    });
  };

  /* דוח שבועי */
  DataLayer.getWeekly = function () {
    return fetchJSONTimeout('/api/ceo-weekly/latest', 2500).then(function (j) {
      if (j) j._live = true; return j;
    }).catch(function () {
      return fetchJSON(staticURL('analyses/_weekly/ceo_weekly.json'))
        .then(function (j) { if (j) j._live = false; return j; })
        .catch(function () { return null; });
    });
  };

  /* בריאות התיק */
  DataLayer.getHealth = function () {
    return fetchJSONTimeout('/api/portfolio/health/latest', 2500).then(function (j) {
      if (j) j._live = true; return j;
    }).catch(function () {
      return fetchJSON(staticURL('portfolio-health.json'))
        .then(function (j) { if (j) j._live = false; return j; })
        .catch(function () { return null; });
    });
  };

  /* reviews אחרונים: live מ-/api/latest-reviews, סטטי מאינדקס שמיוצר בשלב 1 */
  DataLayer.getReviews = function () {
    return fetchJSONTimeout('/api/latest-reviews', 2500).then(function (j) {
      DataLayer.live = true; return j;
    }).catch(function () {
      return fetchJSON(staticURL('analyses/_reviews_index.json'))
        .then(function (j) { return (j && j.reviews) ? j.reviews : (Array.isArray(j) ? j : []); })
        .catch(function () { return []; });
    });
  };

  /* זיהוי מצב יזום (לבאנר). מחזיר Promise<boolean> live */
  DataLayer.detectMode = function () {
    if (DataLayer.live !== null) return Promise.resolve(DataLayer.live);
    return fetchJSONTimeout('/api/ping', 1800).then(function () {
      DataLayer.live = true; return true;
    }).catch(function () { DataLayer.live = false; return false; });
  };

  global.DataLayer = DataLayer;
})(window);
