// Cloudflare Worker — portfolio-proxy
//
// מצבים:
//   GET  /?quotes=AAPL,MSFT,NVDA      → מפת מחירים חיים
//   GET  /?symbol=AAPL&interval=1d... → passthrough גולמי chart
//   POST /oracle                        → Oracle AI chat (env: GROQ_API_KEY)
//   POST /chain                         → הרצת שרשרת via GitHub Actions (env: GH_TOKEN)
//
// הגדרת secrets ב-Cloudflare Dashboard → Worker → Settings → Variables:
//   GROQ_API_KEY   ← מפתח Groq (מאותו key שב-GitHub secrets)
//   GH_TOKEN       ← GitHub token עם repo+workflow permissions (אופציונלי)

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

const YF_HEADERS = {
  "User-Agent": "Mozilla/5.0 (compatible; PortfolioPWA/1.0)",
  "Accept": "application/json",
};

const GITHUB_PAGES = "https://rotemstainai23.github.io/portfolio";
const GH_REPO      = "rotemstainai23/portfolio";

const ORACLE_SYSTEM = `אתה יועץ השקעות פרטי ומנוסה. אתה מכיר את מערכת הניתוח לעומק — הסוכנים, הלוגיקה, הפרומפטים — אבל אתה לא חלק ממנה.
תפקידך: לעזור למשקיע לחשוב, לנתח, לאתגר הנחות, ולקבל החלטות מושכלות יותר.
אתה read-only: לא כותב קבצים, לא מריץ סוכנים, לא מבצע עסקאות, לא משנה שום דבר.

כשהמשקיע רוצה להריץ שרשרת ניתוח על מניה — הכוון אותו להשתמש בכפתור "הרץ שרשרת" בטאב המחקר של האפליקציה.

{{PORTFOLIO_CONTEXT}}`;

// ── Yahoo Finance helpers ─────────────────────────────────────────────────────

async function fetchChart(symbol, interval, range) {
  const sym = encodeURIComponent(symbol);
  for (const host of ["query1", "query2"]) {
    try {
      const url = `https://${host}.finance.yahoo.com/v8/finance/chart/${sym}` +
                  `?interval=${interval}&range=${range}&includePrePost=false`;
      const r = await fetch(url, { headers: YF_HEADERS, cf: { cacheTtl: 30 } });
      if (r.ok) return await r.json();
    } catch (_) {}
  }
  return null;
}

function quoteFromChart(j) {
  const meta = j?.chart?.result?.[0]?.meta;
  if (!meta) return null;
  const price = meta.regularMarketPrice;
  const prev  = meta.chartPreviousClose ?? meta.previousClose;
  const chg_pct = (price != null && prev) ? ((price / prev - 1) * 100) : null;
  return {
    price:   price != null ? +price.toFixed(2) : null,
    prev:    prev  != null ? +prev.toFixed(2)  : null,
    chg_pct: chg_pct != null ? +chg_pct.toFixed(2) : null,
    currency: meta.currency || "USD",
    time:    meta.regularMarketTime || null,
  };
}

// ── Oracle helpers ────────────────────────────────────────────────────────────

async function buildPortfolioContext() {
  let ctx = "";
  try {
    const [pRes, dRes] = await Promise.all([
      fetch(`${GITHUB_PAGES}/portfolio.json`),
      fetch(`${GITHUB_PAGES}/analyses/_daily/daily_latest.json`),
    ]);
    const port  = pRes.ok  ? await pRes.json()  : null;
    const daily = dRes.ok  ? await dRes.json()  : null;

    if (port) {
      ctx += "=== תיק ===\n";
      (port.holdings || []).forEach(h => {
        const tk = h.symbol || h.ticker;
        ctx += `${tk}: ${h.quantity} מניות @ $${h.buy_price} (שכבה: ${h.layer || "—"})\n`;
      });
      ctx += `מזומן: $${port.cash || 0}\n`;
      if ((port.watchlist || []).length) {
        ctx += "\n=== ווצ'ליסט ===\n";
        port.watchlist.forEach(w => {
          ctx += `${w.symbol || w.ticker}: טריגר $${w.trigger_price} (${w.verdict || "WATCH"}) — ${(w.thesis||"").slice(0,80)}\n`;
        });
      }
    }
    if (daily) {
      ctx += `\n=== יומי ${daily.generated || ""} ===\n`;
      (daily.groq_insights || []).slice(0, 4).forEach(ins => { ctx += `• ${ins}\n`; });
      if ((daily.alert_tickers || []).length)
        ctx += `⚠️ התראות: ${daily.alert_tickers.join(", ")}\n`;
    }
  } catch (_) {
    ctx = "לא ניתן לטעון נתוני תיק כרגע.";
  }
  return ctx || "אין נתוני תיק זמינים.";
}

// ── Main handler ─────────────────────────────────────────────────────────────

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    const url = new URL(request.url);

    // ── POST /oracle ──────────────────────────────────────────────────────────
    if (url.pathname === "/oracle" && request.method === "POST") {
      if (!env.GROQ_API_KEY)
        return json({ error: "GROQ_API_KEY לא מוגדר ב-Worker. הגדר בDashboard → Variables." }, 500);

      const body     = await request.json().catch(() => ({}));
      const messages = body.messages || [];

      const ctx    = await buildPortfolioContext();
      const system = ORACLE_SYSTEM.replace("{{PORTFOLIO_CONTEXT}}", ctx);

      const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.GROQ_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "llama-3.3-70b-versatile",
          max_tokens: 1500,
          messages: [{ role: "system", content: system }, ...messages],
        }),
      });

      if (!groqRes.ok) {
        const err = await groqRes.text();
        return json({ error: err }, groqRes.status);
      }
      const data = await groqRes.json();
      const text = data.choices?.[0]?.message?.content || "אין תגובה";
      return json({ text });
    }

    // ── POST /chain ───────────────────────────────────────────────────────────
    // מפעיל שרשרת ניתוח via GitHub Actions. מקבל {ticker, token}.
    // ה-token מגיע מה-PWA (localStorage) — Worker לא מאחסן אותו.
    if (url.pathname === "/chain" && request.method === "POST") {
      const body   = await request.json().catch(() => ({}));
      const ticker = (body.ticker || "").toUpperCase().trim();
      const token  = body.token || env.GH_TOKEN || "";
      if (!ticker) return json({ error: "ticker חסר" }, 400);
      if (!token)  return json({ error: "GitHub token חסר" }, 400);

      const ghRes = await fetch(
        `https://api.github.com/repos/${GH_REPO}/actions/workflows/research.yml/dispatches`,
        {
          method: "POST",
          headers: {
            "Authorization": `token ${token}`,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ref: "main", inputs: { ticker } }),
        }
      );
      if (ghRes.status === 204) return json({ ok: true, ticker });
      const err = await ghRes.json().catch(() => ({}));
      return json({ error: err.message || ghRes.statusText }, ghRes.status);
    }

    // ── GET /?quotes= ─────────────────────────────────────────────────────────
    const interval = url.searchParams.get("interval") || "1d";
    const range    = url.searchParams.get("range")    || "2d";

    const symbol = url.searchParams.get("symbol");
    if (symbol) {
      const j = await fetchChart(symbol, interval, range);
      if (!j) return json({ error: "fetch failed", symbol }, 502);
      return json(j);
    }

    const quotes = url.searchParams.get("quotes");
    if (quotes) {
      const syms = quotes.split(",").map(s => s.trim().toUpperCase()).filter(Boolean).slice(0, 60);
      const out  = {};
      await Promise.all(syms.map(async sym => {
        const j = await fetchChart(sym, "1d", "2d");
        const q = j ? quoteFromChart(j) : null;
        if (q) out[sym] = q;
      }));
      return json(out);
    }

    return json({ ok: true, usage: "?quotes=AAPL,MSFT | ?symbol=AAPL | POST /oracle | POST /chain" });
  },
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
