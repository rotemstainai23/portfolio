# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> כללים גלובליים: `~/CLAUDE.md`. זיכרון חי: `~/CLAUDE MEMORY/Projects/portfolio/`.

## סקירה

דשבורד מקומי לניהול תיק השקעות אישי. שרת PowerShell HTTP נטיב (`.NET HttpListener`) שמגיש דשבורד HTML, proxy ל-Yahoo Finance API (עוקף CORS), ו-REST API ל-CRUD על holdings + watchlist + יומן עסקאות. מקור אמת יחיד: `portfolio.json`. **אין build, אין dependencies מלבד PowerShell ודפדפן.**

## פקודות

```powershell
# הפעלה (port 5000, נפתח דפדפן אוטומטית):
powershell -ExecutionPolicy Bypass -File portfolio\serve.ps1

# בריאות:
curl http://localhost:5000/api/ping
```

**אזהרה:** `start.bat` מפעיל את `app.py` (Flask נטוש) — לא להשתמש בו. הפעלה נכונה היא דרך `serve.ps1` בלבד.

בעת עריכת `serve.ps1` כשהשרת רץ → להפעיל מחדש (אין hot-reload).

## ארכיטקטורה

```
portfolio\
├── serve.ps1                      ← שרת HTTP + Yahoo proxy + REST API
├── portfolio.json                 ← מקור אמת (cash, holdings, trades, watchlist)
├── decision_log.json              ← יומן החלטות השקעה (DEC-001, DEC-002...)
├── portfolio.html                 ← UI ראשי, polls /api/portfolio כל 60s
├── מערכת תיק ההשקעות\            ← פרומטי סוכנים (master copies)
│   ├── Unified_Analyst.md
│   ├── CEO_Agent_Updated.md
│   ├── DevilsAdvocate_Updated.md
│   ├── Executor_Updated.md
│   ├── InvestmentCommittee_Updated.md
│   └── TradeRecorder_Updated.md
├── templates\                     ← תבניות דוחות רב-שימושיות (הדפוס הנוכחי)
│   ├── _shared.css                ← CSS vars לערכה הכהה (SSOT לעיצוב)
│   └── analyst.html, ceo.html, devils.html, executor.html, ic.html
└── analyses\<TICKER>\             ← נתוני ניתוח לפי טיקר
    ├── analyst.js, ceo.js, ...    ← כל אחד מציב window.AGENT_DATA
    ├── _handoffs\                 ← קבצי Markdown של HANDOFF בין סוכנים
    │   └── <YYYY-MM-DD>_analyst.md
    └── _reviews\                  ← סקירות מהירות בין ועדות
        └── quick.json
```

### שני דפוסי דוחות

- **Legacy**: קבצי `*_report_*.html` עצמאיים בשורש (נתונים מקודדים בקוד). לא להוסיף עוד כאלה.
- **נוכחי (מועדף)**: `templates\<agent>.html?ticker=<TICKER>`. התבנית טוענת `analyses\<TICKER>\<agent>.js` (שמציב `window.AGENT_DATA`) ואז מרנדרת. **להוסיף טיקר חדש**: ליצור `analyses\<TICKER>\<agent>.js` לכל סוכן בשרשרת.

### נקודות קצה (serve.ps1)

| Path | Method | תיאור |
|---|---|---|
| `/` | GET | מגיש `portfolio.html` |
| `/api/portfolio` | GET | תיק מועשר (מחירים חיים, P&L, התרעות watchlist). זו הנקודה שהסוכנים צורכים. |
| `/api/chart?symbol=&interval=&range=` | GET | proxy ל-Yahoo Finance v8 (עוקף CORS דפדפן) |
| `/api/holdings`, `/api/holdings/{sym}` | GET/POST/DELETE | CRUD על אחזקות |
| `/api/watchlist`, `/api/watchlist/{sym}` | GET/POST/DELETE | CRUD על watchlist (`trigger_price` + `trigger_direction`) |
| `/api/trades`, `/api/trades/{idx}` | GET/POST/DELETE | יומן עסקאות (מזהים אוטומטיים `TRD-001`, `TRD-002`...) |
| `/api/cash` | PUT | עדכון יתרת מזומן |
| `/api/ping` | GET | בדיקת בריאות |

מחירים: Yahoo Finance v8 (`query1/query2.finance.yahoo.com/v8/finance/chart`), ללא אימות, cache 55 שניות. POST/DELETE ל-holdings ול-watchlist מאפסים את ה-cache אוטומטית.

### סכמות JSON

**portfolio.json:**
```json
{
  "cash": 71,
  "holdings": [ { "symbol", "name", "quantity", "buy_price",
                  "layer": "Stability|Growth|Speculation",
                  "sector", "analyst_score", "risk_score", "notes" } ],
  "trades":   [ { "trade_id":"TRD-001", "date", "ticker", "action", "verdict",
                  "price", "size_pct", "layer", "analyst_score", "risk_score",
                  "confidence", "fair_value", "upside_pct", "thesis" } ],
  "watchlist":[ { "symbol", "company", "date_added", "verdict", "layer",
                  "analyst_score", "risk_score", "confidence", "fair_value",
                  "trigger_price", "trigger_direction":"below|above",
                  "thesis", "fragile_assumption", "kill_switch",
                  "next_review", "notes" } ]
}
```

**decision_log.json** (DEC-NNN, לא דרך API — עריכה ידנית או על-ידי Claude):
```json
{ "decisions": [ {
  "id": "DEC-001", "ticker", "date", "decision", "position_size_pct",
  "why", "biggest_risk", "kill_switch", "conviction", "original_thesis"
} ] }
```

**analyses/\<TICKER\>/_reviews/quick.json** (סקירה מהירה בין ועדות):
```json
{
  "ticker", "agent":"quick", "date", "verdict":"INTACT|DETERIORATING|EXIT",
  "score", "thesis", "key_risks":[], "position_size_pct",
  "valuation_summary", "entry_exit_plan", "handoff_summary"
}
```

**לערוך portfolio.json תמיד דרך ה-API** כשהשרת רץ (POST/DELETE מאפסים cache). עריכה ידנית בזמן ריצה = מחירים מיושנים.

## שרשרת הסוכנים

פרומטים ב-`portfolio\מערכת תיק ההשקעות\`:

```
Unified_Analyst → DevilsAdvocate → CEO_Agent → Executor → InvestmentCommittee
                                                               ↑
                                               TradeRecorder (אחרי קנייה)
```

- **Analyst**: צלילה פורנזית למניה, מפיק HANDOFF ל-`analyses/<TICKER>/_handoffs/`.
- **DevilsAdvocate**: תוקף את התזה, פולט ציון סיכון ותקרת גודל פוזיציה.
- **CEO**: אדריכל התיק. דורש 3 קלטים: analyst handoff, devil handoff, תיק נוכחי. מבנה יעד: Stability 25-35%, Growth 55-65%, Speculation 5-10%, Cash 5-10%.
- **Executor**: מבנה כניסה (טראנשים, פקודות לימיט, סטופ ATR, R/R).
- **InvestmentCommittee**: אישור סופי.

בעת עריכת פרומט אחד: הפלט שלו = הקלט של הבא. **אל תשנה את סכמת ה-handoff באופן חד-צדדי.**

## מוסכמות סטייל

לדוחות חדשים, להתאים ל-`portfolio.html` ול-`templates/_shared.css`. **לא להמציא טוקני עיצוב חדשים** (פירוט: `~/CLAUDE MEMORY/Shared/design-tokens.md`).

- עברית RTL (`<html lang="he" dir="rtl">`).
- ללא ספריות חיצוניות. עובד offline. גרפים: `conic-gradient` donuts או bar charts CSS ידניים. לא Chart.js.
- פונט Heebo לטקסט גוף בעבודה חדשה.
- `portfolio.html` עצמו נכתב באנגלית (lang="en") כי הוא UI כללי; תבניות הדוחות בעברית RTL.

## מלכודות

- `app.py` ו-`start.bat` נטושים. לא לערוך ולא להפעיל.
- ריכוז AI בתיק = אמונה מכוונת. "concentration risk" = ליבה תמטית, לא דגל אדום.
- `Glob **/*.md` מהבית יחזיר קבצי זבל. לצמצם ל-`portfolio\מערכת תיק ההשקעות\`.
- נתיבים עם עברית (`מערכת תיק ההשקעות`) בשורת Bash: לעטוף במירכאות.
