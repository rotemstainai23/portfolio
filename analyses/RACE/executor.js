// CLAUDE-AUTO-GENERATED — מחק שורה זו כדי לנעול את הקובץ מפני דריסה
window.AGENT_DATA = {
  "ticker": "RACE",
  "company": "Ferrari N.V.",
  "date": "2026-06-01 <span style=\"display:inline-block;font-size:10px;font-weight:700;padding:3px 9px;border-radius:11px;background:rgba(120,120,120,.12);border:1px solid #2ecc7155;color:#2ecc71;margin-right:6px\">🟢 Fresh · 0d</span>",
  "fair_value": 378,
  "bear_price": 255,
  "inherited": [
    { "icon": "✅", "text": "<b>אנליסט:</b> איכות 8/10 · שווי הוגן $378 · entry target $310-320 post Q2 2026 · stress test 41/50" },
    { "icon": "⚠️", "text": "<b>שטן:</b> 5/10 · R/R 0.38:1 ב-$345 · Luce = existential brand test · 4 kill switches מוגדרים" },
    { "icon": "⏸", "text": "<b>CEO:</b> WAIT · 0% עכשיו · 4% מותנה post-Q2 2026 (30 יולי) · מימון מ-IBIT rebalance 10%→4%" },
    { "icon": "📡", "text": "<b>נתוני ביצוע:</b> RACE 10.17% מתחת ל-200DMA · RSI 53.89 (ניטרלי) · VIX 15.42 (Risk-On)" }
  ],
  "technical_cards": [
    { "lbl": "מחיר נוכחי", "val": "$345", "color": "c-text", "id": "ind-price", "sub": "52W: $300–$519" },
    { "lbl": "vs 200DMA", "val": "-10.17%", "color": "c-red", "sub": "מתחת ל-200DMA" },
    { "lbl": "RSI (14)", "val": "53.89", "color": "c-text", "sub": "ניטרלי — לא קנייתר" },
    { "lbl": "משטר שוק", "val": "Risk-On", "color": "c-green", "sub": "VIX 15.42 · SPY מעל 200DMA" },
    { "lbl": "Q2 Earnings", "val": "30 יולי 2026", "color": "c-blue", "sub": "~59 ימים · אירוע בינארי: Luce" },
    { "lbl": "קונצנזוס אנליסטים", "val": "$440.57", "color": "c-green", "sub": "Strong Buy · +27.7% מ-$345" }
  ],
  "filters": {
    "description": "6 מסננים מוסדיים. 2 נכשלים — מחיר ו-R/R. WAIT עד תנאי כניסה מתקיימים ב-30 יולי 2026.",
    "tiles": [
      { "icon": "📅", "name": "תזמון דוח", "badge": "59 ימים", "val": "30 יולי 2026", "detail": "Q2 2026 = אירוע בינארי על Luce demand. כניסה לפניו = תשלום premium uncertainty מקסימלי. המסנן מדרג: המתן." },
      { "icon": "📊", "name": "RSI", "badge": "עבר", "val": "53.89 — ניטרלי", "detail": "לא קנייתר ולא מוכרתר. אין urgency טכנית בכיוון כלשהו. מאפשר כניסה סלקטיבית." },
      { "warn": true, "icon": "💵", "name": "שווי בכניסה", "badge": "לא אטרקטיבי", "val": "$345 = EV ($378 בסיס)", "detail": "ב-$345 מחיר = שווי הוגן בסיס. אין margin of safety. ב-$320 post-Q2 חיובי: 15% discount + R/R 2:1+." },
      { "warn": true, "icon": "⚖️", "name": "סיכון/תשואה", "badge": "נכשל", "val": "0.38:1 ב-$345", "detail": "מינימום מוסדי: 2:1. R/R 2:1 מתקיים רק ב-≤$296 (מתחת ל-52W low). Post-Q2 חיובי ב-$320: R/R ~2:1+." },
      { "icon": "🌐", "name": "משטר שוק", "badge": "Risk-On", "val": "VIX 15.42", "detail": "SPY מעל 200DMA — משטר תומך. אין contra-indicator למשטר. לא חסם כניסה." },
      { "icon": "🏗️", "name": "מבנה תיק", "badge": "חסם", "val": "IBIT rebalance קודם", "detail": "Cash 3.6% < 5% רצפה. חייב IBIT 10%→4% (שחרור ~$115) לפני כל קנייה. חסם מבני, לא ניתן לעקוף." }
    ]
  },
  "rr": {
    "description": "ב-$345 המחיר = EV. אין margin of safety. R/R 0.38:1 לא עובר סף מינימום. Post-Q2 חיובי ב-$320 R/R משתפר ל-~2:1.",
    "bars": [
      { "label": "🟢 תשואה — אל $378 (בסיס)", "pct": "+9.6%", "color": "c-green", "width": 28, "bg": "green", "dollar": "+$33" },
      { "label": "🟢 תשואה — אל $480 (שורי)", "pct": "+39%", "color": "c-green", "width": 100, "bg": "green", "dollar": "+$135" },
      { "label": "🔴 סיכון — אל $255 (bear)", "pct": "-26%", "color": "c-red", "width": 68, "bg": "red", "dollar": "-$90" },
      { "label": "🔴 סיכון — אל $184 (disaster)", "pct": "-47%", "color": "c-red", "width": 100, "bg": "red", "dollar": "-$161" }
    ],
    "verdict": {
      "style": "red",
      "headline": "R/R = 9.6% ÷ 26% = 0.38:1 — מתחת לסף 2:1",
      "body": "· ב-$345 אין edge. Post-Q2 חיובי ב-$320: R/R = ~2:1. <b>לכן: כניסה מותנית ב-Q2, לא AVOID מוחלט.</b>"
    }
  },
  "verdict": {
    "style": "yellow",
    "headline": "⏸ WAIT — 59 ימים ל-Q2 2026 (30 יולי) · R/R לא מצדיק כניסה ב-$345",
    "paragraphs": [
      "RACE הוא העסק הטוב ביותר שניתחנו — אבל לא ב-$345. שלושה חסמים: מחיר = EV (אין margin of safety), Q2 2026 = אירוע בינארי Luce שטרם נפתר, ומבנה תיק מחייב IBIT rebalance קודם. תוכנית כניסה מוגדרת ל-30 יולי 2026."
    ],
    "scoreboxes": [
      { "lbl": "פסיקה", "val": "WAIT", "color": "c-yellow", "size": 15 },
      { "lbl": "R/R נוכחי", "val": "0.38:1", "color": "c-red" },
      { "lbl": "כניסה מותנית", "val": "$310-320", "color": "c-blue" },
      { "lbl": "תאריך trigger", "val": "30/7/2026", "color": "c-purple" }
    ]
  },
  "plan": {
    "description": "תוכנית Scale In מותנית: כניסה רק אחרי Q2 2026 (30 יולי) עם Luce order intake חיובי + EBIT ≥29%. גודל CEO מאושר: <b>4% ראשוני (~$76)</b>, scalable ל-8% עם Luce Q4 2026.",
    "cash": 76,
    "cash_hint": "4% מתיק ~$1,900 · מחולק 40/30/30 · מקור: IBIT rebalance 10%→4%",
    "levels": {
      "t1": { "price": 320, "pct": 40, "name": "כניסה 1 — post-Q2 trigger", "color": "#f5c842" },
      "t2": { "price": 315, "pct": 30, "name": "כניסה 2 — Luce confirmation", "color": "#2ecc71" },
      "t3": { "price": 345, "pct": 30, "name": "כניסה 3 — momentum מאושר", "color": "#4da6ff" },
      "stop": { "price": 289, "name": "סטופ-לוס (2×ATR)", "color": "#e05c5c" },
      "tp1": { "price": 390, "name": "TP1 — קרוב לשיא אחרון", "color": "#4da6ff" },
      "tp2": { "price": 450, "name": "TP2 — שורי מלא", "color": "#a78bfa" }
    },
    "rationale": {
      "t1": "Q2 2026 חיובי = Luce לא מזיק + EBIT ≥29%. $320 = 15% discount לשווי הוגן. LIMIT order ביום earnings.",
      "t2": "אם המניה נסוגה לאחר Q2 עקב profit taking — $315 = תמיכה טכנית הגיונית. R/R שם ~2.4:1.",
      "t3": "אם RACE ממשיכה לעלות post-Q2 + Luce confirmation חזק — $345 עם momentum מאושר שווה 30% נוספים.",
      "stop": "$289 = 2×ATR מתחת לכניסה $315. מתחת ל-52W support zone. סגירה יומית מתחת = thesis קרסה.",
      "tp1": "שווי הוגן בסיס $378 + buffer. לקיחת רווח חלקית (40% מהפוזיציה) לנעילת רווח.",
      "tp2": "תרחיש שורי מלא עם Luce success + multiple expansion. שאר הפוזיציה (60%) עד $450."
    },
    "support_resistance": [
      { "p": 289, "l": "תמיכה · stop-loss · 2×ATR מ-$315" },
      { "p": 310, "l": "תמיכה · כניסה תחתית מתוכננת" },
      { "p": 378, "l": "התנגדות · שווי הוגן בסיס" },
      { "p": 440, "l": "התנגדות · קונצנזוס אנליסטים $440.57" }
    ]
  },
  "handoff": "חברה: Ferrari N.V. (RACE) · <b>פסיקה:</b> WAIT · <b>trigger:</b> Q2 2026 (30 יולי 2026)<br><b>תוכנית:</b> T1 40%@$320 LIMIT · T2 30%@$315 · T3 30%@$345 (momentum)<br><b>סטופ:</b> $289 (2×ATR) · <b>TP:</b> $390 / $450<br><b>מימון:</b> IBIT rebalance 10%→4% = ~$115 מתפנה",
  "footer": "מקור: מחיר + RSI + 200DMA — Finviz/Yahoo Finance דרך שרת הדשבורד. VIX — Yahoo Finance. SPY 200DMA אומת עצמאית. Q2 earnings date — SEC calendar."
};
