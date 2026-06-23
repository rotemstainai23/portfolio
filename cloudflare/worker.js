// Cloudflare Worker - proxy ל-Yahoo Finance עם כותרות CORS.
// משחזר את מה ש-serve.ps1 עשה במחשב (v8 chart API, בלי auth/crumb), כדי שה-PWA בנייד
// יקבל מחירים חיים ישירות מהדפדפן בלי שרת מקומי.
//
// פריסה (חד-פעמית, חינם):
//   1. cloudflare.com -> הרשמה -> Workers & Pages -> Create Worker
//   2. הדבק את הקובץ הזה, Deploy. תקבל כתובת כמו https://portfolio-proxy.<user>.workers.dev
//   3. הזן את הכתובת ב-PWA: הגדרות -> "כתובת proxy מחירים" (נשמר ב-localStorage)
//
// שני מצבים:
//   GET /?quotes=AAPL,MSFT,NVDA   -> מפת מחירים חיים: {AAPL:{price,prev,chg_pct,...}, ...}
//   GET /?symbol=AAPL&interval=1d&range=6mo -> passthrough גולמי של chart (לגרפי OHLC)

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const YF_HEADERS = {
  "User-Agent": "Mozilla/5.0 (compatible; PortfolioPWA/1.0)",
  "Accept": "application/json",
};

// מושך chart בודד מ-Yahoo, עם fallback query1 -> query2.
async function fetchChart(symbol, interval, range) {
  const sym = encodeURIComponent(symbol);
  for (const apiHost of ["query1", "query2"]) {
    try {
      const url = `https://${apiHost}.finance.yahoo.com/v8/finance/chart/${sym}` +
                  `?interval=${interval}&range=${range}&includePrePost=false`;
      const r = await fetch(url, { headers: YF_HEADERS, cf: { cacheTtl: 30 } });
      if (r.ok) return await r.json();
    } catch (_) { /* נסה את ה-host הבא */ }
  }
  return null;
}

// מחלץ מחיר חי + שינוי יומי מתוך meta של chart.
function quoteFromChart(j) {
  const meta = j && j.chart && j.chart.result && j.chart.result[0] && j.chart.result[0].meta;
  if (!meta) return null;
  const price = meta.regularMarketPrice;
  const prev = meta.chartPreviousClose != null ? meta.chartPreviousClose
             : meta.previousClose;
  const chg_pct = (price != null && prev) ? ((price / prev - 1) * 100) : null;
  return {
    price: price != null ? +price.toFixed(2) : null,
    prev: prev != null ? +prev.toFixed(2) : null,
    chg_pct: chg_pct != null ? +chg_pct.toFixed(2) : null,
    currency: meta.currency || "USD",
    time: meta.regularMarketTime || null,
  };
}

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    const url = new URL(request.url);
    const interval = url.searchParams.get("interval") || "1d";
    const range = url.searchParams.get("range") || "2d";

    // מצב passthrough לגרף בודד
    const symbol = url.searchParams.get("symbol");
    if (symbol) {
      const j = await fetchChart(symbol, interval, range);
      if (!j) return json({ error: "fetch failed", symbol }, 502);
      return json(j);
    }

    // מצב batch quotes
    const quotes = url.searchParams.get("quotes");
    if (quotes) {
      const syms = quotes.split(",").map(s => s.trim().toUpperCase()).filter(Boolean).slice(0, 60);
      const out = {};
      // מקבילי - Yahoo עומד בזה בקלות עבור עד 60 סימבולים
      await Promise.all(syms.map(async sym => {
        const j = await fetchChart(sym, "1d", "2d");
        const q = j ? quoteFromChart(j) : null;
        if (q) out[sym] = q;
      }));
      return json(out);
    }

    return json({ ok: true, usage: "?quotes=AAPL,MSFT or ?symbol=AAPL&interval=1d&range=6mo" });
  },
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
