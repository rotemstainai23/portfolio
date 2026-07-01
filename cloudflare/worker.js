// Cloudflare Worker — portfolio-proxy
//
// GET  /?quotes=AAPL,MSFT     → מחירים חיים
// GET  /?symbol=AAPL&...      → chart passthrough
// POST /oracle                 → Oracle AI עם כלי ניהול תיק (GROQ_API_KEY; טוקן GitHub מהלקוח)
// POST /chain                  → הרצת שרשרת via GitHub Actions (טוקן GitHub מהלקוח)
// POST /portfolio              → ניהול אחזקות (add/update/remove); דורש טוקן GitHub מהלקוח
//
// Secret יחיד: GROQ_API_KEY (Cloudflare Dashboard → Worker → Settings → Variables).
// כתיבות לתיק מאומתות בטוקן ה-GitHub של המשתמש שנשלח מהאפליקציה — לא בסוד ב-Worker.

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

const ORACLE_SYSTEM = `אתה "אורקל" — מנהל מערכת ויועץ השקעות פרטי.
יש לך גישה מלאה לתיק ההשקעות וכלים לניהולו:

כלים זמינים:
• add_holding    — הוספת אחזקה חדשה
• update_holding — עדכון כמות / מחיר / שכבה / הערות של אחזקה קיימת
• remove_holding — מחיקת אחזקה מהתיק

כללים:
- כשמשקיע מבקש שינוי בתיק — בצע מיד עם הכלי המתאים ואשר בתגובה.
- לניתוח לעומק של מניה — הכוון לכפתור "הרץ שרשרת" בטאב המחקר.
- אתה לא מבצע עסקאות בפועל — רק מנהל רשומות.
- ענה תמיד בעברית, בצורה תמציתית ומקצועית.

{{PORTFOLIO_CONTEXT}}`;

const ORACLE_TOOLS = [
  {
    type: "function",
    function: {
      name: "add_holding",
      description: "מוסיף אחזקה חדשה לתיק ההשקעות",
      parameters: {
        type: "object",
        properties: {
          symbol:    { type: "string",  description: "טיקר המניה באותיות גדולות (NVDA, AAPL...)" },
          name:      { type: "string",  description: "שם החברה" },
          quantity:  { type: "number",  description: "כמות מניות" },
          buy_price: { type: "number",  description: "מחיר כניסה בדולרים" },
          layer:     { type: "string",  enum: ["Growth","Stability","Speculation","Core"], description: "שכבת סיכון" },
          sector:    { type: "string",  description: "סקטור" },
          notes:     { type: "string",  description: "הערות" },
        },
        required: ["symbol","quantity","buy_price"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "update_holding",
      description: "מעדכן שדות של אחזקה קיימת בתיק (כמות, מחיר, שכבה, הערות)",
      parameters: {
        type: "object",
        properties: {
          symbol:    { type: "string" },
          quantity:  { type: "number" },
          buy_price: { type: "number" },
          layer:     { type: "string", enum: ["Growth","Stability","Speculation","Core"] },
          notes:     { type: "string" },
        },
        required: ["symbol"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "remove_holding",
      description: "מוחק אחזקה מהתיק",
      parameters: {
        type: "object",
        properties: {
          symbol: { type: "string", description: "טיקר למחיקה" },
        },
        required: ["symbol"],
      },
    },
  },
];

// ── Yahoo Finance ─────────────────────────────────────────────────────────────

async function fetchChart(symbol, interval, range) {
  const sym = encodeURIComponent(symbol);
  for (const host of ["query1","query2"]) {
    try {
      const url = `https://${host}.finance.yahoo.com/v8/finance/chart/${sym}?interval=${interval}&range=${range}&includePrePost=false`;
      const r = await fetch(url, { headers: YF_HEADERS, cf: { cacheTtl: 30 } });
      if (r.ok) return await r.json();
    } catch (_) {}
  }
  return null;
}

function quoteFromChart(j) {
  const meta = j?.chart?.result?.[0]?.meta;
  if (!meta) return null;
  const price   = meta.regularMarketPrice;
  const prev    = meta.chartPreviousClose ?? meta.previousClose;
  const chg_pct = (price != null && prev) ? ((price / prev - 1) * 100) : null;
  return {
    price:    price   != null ? +price.toFixed(2)   : null,
    prev:     prev    != null ? +prev.toFixed(2)    : null,
    chg_pct:  chg_pct != null ? +chg_pct.toFixed(2) : null,
    currency: meta.currency || "USD",
    time:     meta.regularMarketTime || null,
  };
}

// ── GitHub portfolio helpers ──────────────────────────────────────────────────

async function readPortfolioJson(token) {
  const r = await fetch(
    `https://api.github.com/repos/${GH_REPO}/contents/portfolio.json`,
    { headers: { Authorization: `token ${token}`, Accept: "application/vnd.github+json" } }
  );
  if (!r.ok) throw new Error(`GitHub ${r.status}: לא ניתן לקרוא portfolio.json`);
  const data    = await r.json();
  const content = JSON.parse(atob(data.content.replace(/\n/g, "")));
  return { content, sha: data.sha };
}

async function writePortfolioJson(token, content, sha, message) {
  const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(content, null, 2))));
  const r = await fetch(
    `https://api.github.com/repos/${GH_REPO}/contents/portfolio.json`,
    {
      method: "PUT",
      headers: {
        Authorization: `token ${token}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message, content: encoded, sha }),
    }
  );
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.message || `GitHub write ${r.status}`);
  }
}

function applyPortfolioAction(portfolio, action, args) {
  const sym = (args.symbol || "").toUpperCase().trim();
  if (!sym) throw new Error("symbol חסר");
  if (!portfolio.holdings) portfolio.holdings = [];

  if (action === "remove") {
    const before = portfolio.holdings.length;
    portfolio.holdings = portfolio.holdings.filter(h => (h.symbol || h.ticker) !== sym);
    if (portfolio.holdings.length === before) throw new Error(`${sym} לא נמצא בתיק`);
    return `הוסר ${sym} מהתיק`;
  }

  const idx      = portfolio.holdings.findIndex(h => (h.symbol || h.ticker) === sym);
  const existing = idx >= 0 ? portfolio.holdings[idx] : {};
  const merged   = {
    symbol:    sym,
    name:      args.name      ?? existing.name      ?? sym,
    quantity:  args.quantity  ?? existing.quantity  ?? 0,
    buy_price: args.buy_price ?? existing.buy_price ?? 0,
    layer:     args.layer     ?? existing.layer     ?? "Growth",
    sector:    args.sector    ?? existing.sector    ?? "",
    notes:     args.notes     ?? existing.notes     ?? "",
  };

  if (idx >= 0) {
    portfolio.holdings[idx] = merged;
    return `עודכן ${sym}: ${merged.quantity} מניות @ $${merged.buy_price}`;
  }
  portfolio.holdings.push(merged);
  return `נוסף ${sym}: ${merged.quantity} מניות @ $${merged.buy_price} (${merged.layer})`;
}

// ── Oracle context ────────────────────────────────────────────────────────────

async function buildPortfolioContext() {
  try {
    const [pRes, dRes] = await Promise.all([
      fetch(`${GITHUB_PAGES}/portfolio.json`),
      fetch(`${GITHUB_PAGES}/analyses/_daily/daily_latest.json`),
    ]);
    const port  = pRes.ok ? await pRes.json() : null;
    const daily = dRes.ok ? await dRes.json() : null;
    let ctx = "";

    if (port) {
      ctx += "=== תיק ===\n";
      (port.holdings || []).forEach(h => {
        ctx += `${h.symbol||h.ticker}: ${h.quantity} מניות @ $${h.buy_price} (שכבה: ${h.layer||"—"})\n`;
      });
      ctx += `מזומן: $${port.cash || 0}\n`;
      if ((port.watchlist || []).length) {
        ctx += "\n=== ווצ'ליסט ===\n";
        port.watchlist.forEach(w => {
          ctx += `${w.symbol||w.ticker}: טריגר $${w.trigger_price} (${w.verdict||"WATCH"}) — ${(w.thesis||"").slice(0,80)}\n`;
        });
      }
    }
    if (daily) {
      ctx += `\n=== יומי ${daily.generated||""} ===\n`;
      (daily.groq_insights||[]).slice(0,4).forEach(ins => { ctx += `• ${ins}\n`; });
      if ((daily.alert_tickers||[]).length)
        ctx += `⚠️ התראות: ${daily.alert_tickers.join(", ")}\n`;
    }
    return ctx || "אין נתוני תיק זמינים.";
  } catch (_) {
    return "לא ניתן לטעון נתוני תיק כרגע.";
  }
}

// ── Main handler ─────────────────────────────────────────────────────────────

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    const url = new URL(request.url);

    // ── POST /oracle ──────────────────────────────────────────────────────────
    if (url.pathname === "/oracle" && request.method === "POST") {
      if (!env.GROQ_API_KEY)
        return json({ error: "GROQ_API_KEY לא מוגדר ב-Worker — הגדר ב-Cloudflare Dashboard" }, 500);

      const body     = await request.json().catch(() => ({}));
      const messages = body.messages || [];
      /* טוקן GitHub מגיע מהלקוח (localStorage) — ה-Worker לא מחזיק סוד כתיבה לתיק */
      const ghToken  = (body.token || "").trim();
      const ctx      = await buildPortfolioContext();
      const system   = ORACLE_SYSTEM.replace("{{PORTFOLIO_CONTEXT}}", ctx);

      // קריאה ראשונה — Groq עם function calling
      const res1 = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: { Authorization: `Bearer ${env.GROQ_API_KEY}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "llama-3.3-70b-versatile",
          max_tokens: 1000,
          messages: [{ role: "system", content: system }, ...messages],
          tools: ORACLE_TOOLS,
          tool_choice: "auto",
        }),
      });

      if (!res1.ok) return json({ error: await res1.text() }, res1.status);
      const data1 = await res1.json();
      const msg1  = data1.choices?.[0]?.message;

      // אם Groq רצה לקרוא לכלים — בצע
      if (msg1?.tool_calls?.length) {
        const toolResults = [];

        for (const tc of msg1.tool_calls) {
          let result;
          try {
            if (!ghToken) throw new Error("אין הרשאת כתיבה — הגדר GitHub token בהגדרות האפליקציה");
            const args = JSON.parse(tc.function.arguments);
            const action = tc.function.name === "add_holding"    ? "add"
                         : tc.function.name === "update_holding" ? "update"
                         : "remove";
            const { content: portfolio, sha } = await readPortfolioJson(ghToken);
            result = applyPortfolioAction(portfolio, action, args);
            await writePortfolioJson(ghToken, portfolio, sha, `oracle: ${action} ${args.symbol||""}`);
          } catch (e) {
            result = `שגיאה: ${e.message}`;
          }
          toolResults.push({ role: "tool", tool_call_id: tc.id, content: result });
        }

        // קריאה שנייה — תגובה סופית עם תוצאות
        const res2 = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: { Authorization: `Bearer ${env.GROQ_API_KEY}`, "Content-Type": "application/json" },
          body: JSON.stringify({
            model: "llama-3.3-70b-versatile",
            max_tokens: 600,
            messages: [{ role: "system", content: system }, ...messages, msg1, ...toolResults],
          }),
        });
        const data2 = await res2.json();
        return json({ text: data2.choices?.[0]?.message?.content || "בוצע" });
      }

      return json({ text: msg1?.content || "אין תגובה" });
    }

    // ── POST /portfolio ───────────────────────────────────────────────────────
    if (url.pathname === "/portfolio" && request.method === "POST") {
      const body   = await request.json().catch(() => ({}));
      /* אימות: טוקן GitHub של המשתמש חובה — בלעדיו GitHub ידחה את הכתיבה */
      const pToken = (body.token || "").trim();
      if (!pToken) return json({ error: "חסר GitHub token — הגדר בהגדרות האפליקציה" }, 401);
      const action = body.action;
      const args   = body.holding || body;
      try {
        const { content: portfolio, sha } = await readPortfolioJson(pToken);
        const result = applyPortfolioAction(portfolio, action, args);
        await writePortfolioJson(pToken, portfolio, sha, `portfolio: ${action} ${args.symbol||""}`);
        return json({ ok: true, message: result });
      } catch (e) {
        return json({ error: e.message }, 400);
      }
    }

    // ── POST /chain ───────────────────────────────────────────────────────────
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
            Authorization: `token ${token}`,
            Accept: "application/vnd.github+json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ ref: "main", inputs: { ticker } }),
        }
      );
      if (ghRes.status === 204) return json({ ok: true, ticker });
      const err = await ghRes.json().catch(() => ({}));
      return json({ error: err.message || ghRes.statusText }, ghRes.status);
    }

    // ── GET /?quotes= / /?symbol= ─────────────────────────────────────────────
    const interval = url.searchParams.get("interval") || "1d";
    const range    = url.searchParams.get("range")    || "2d";
    const symbol   = url.searchParams.get("symbol");

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

    return json({ ok: true, usage: "?quotes=AAPL,MSFT | ?symbol=AAPL | POST /oracle | POST /chain | POST /portfolio" });
  },
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
