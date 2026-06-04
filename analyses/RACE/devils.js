// CLAUDE-AUTO-GENERATED — מחק שורה זו כדי לנעול את הקובץ מפני דריסה
window.AGENT_DATA = {
  "ticker": "RACE",
  "company": "Ferrari N.V.",
  "date": "2026-06-01 <span style=\"display:inline-block;font-size:10px;font-weight:700;padding:3px 9px;border-radius:11px;background:rgba(120,120,120,.12);border:1px solid #2ecc7155;color:#2ecc71;margin-right:6px\">🟢 Fresh · 0d</span>",
  "verdict": {
    "style": "yellow",
    "headline": "⚠️ 5/10 — עסק איכותי, תמחור לא מצדיק, Luce = מבחן קיומי למותג",
    "paragraphs": [
      "עורך הדין השטן מאתגר את ציון 8/10 של האנליסט. הביקורת אינה על הפונדמנטלים — שחלקם מצוינים — אלא על שלושה גורמים: (1) R/R 0.38:1 ב-$345 פשוט לא מספיק בשום מסגרת השקעה מוסדית, (2) Luce EV מאיים על ה-brand DNA שמצדיק את כל הפרמיום של 33x P/E, (3) מגמת סין מבנית ולא מחזורית."
    ],
    "scoreboxes": [
      { "lbl": "ציון ביקורת", "val": "5/10", "color": "c-yellow", "size": 15 },
      { "lbl": "R/R נוכחי", "val": "0.38:1", "color": "c-red" },
      { "lbl": "Luce Risk", "val": "existential", "color": "c-red" },
      { "lbl": "פסיקה", "val": "WAIT ב-$345", "color": "c-yellow", "size": 12 }
    ]
  },
  "attack": {
    "headline": "האנליסט מזר את החפיר — Luce הוא מבחן קיומי לזהות המותג שמצדיקה 33x P/E, לא סיכון מוצר",
    "paragraphs": [
      "Ferrari מתומחרת ב-33x P/E כי השוק מאמין שהחפיר — brand DNA של exclusivity, scarcity, performance — הוא בלתי חדיר. Luce (sedan 5-מושבים, €550K, Jony Ive) מערערת את ההנחה הבסיסית הזו. זה לא סיכון מוצר — זה סיכון זהות.",
      "ה-8/10 של האנליסט מניח שהחפיר שלם. אנחנו טוענים שהוא נמצא תחת מבחן: מניה -8.4% ביום הגילוי, ex-CEO Montezemolo מבקר בפומבי, heritage buyers מאוכזבים. אם הלקוחות הוותיקים מרגישים 'זה לא Ferrari' — ספר ההזמנות מתפרק.",
      "תוסיפו: סין -21% FY2024 אינה מחזורית, R/R 0.38:1 לא מצדיק 33x P/E, ו-capex €4.29B על EV שהשוק דחה — ואתם מקבלים חברה שנסחרת כאילו כל הסיכונים האלה לא קיימים."
    ]
  },
  "risk_scorecard": {
    "description": "5 ממדי סיכון מהותיים שהאנליסט הדגיש אך לא משקלל מספיק בציון 8/10.",
    "items": [
      { "lbl": "Brand DNA Risk (Luce EV)", "val": "גבוה", "color": "red", "note": "מניה -8.4% ביום הגילוי · ex-CEO מבקר · קנאריה במכרה פחם" },
      { "lbl": "China Structural Decline", "val": "גבוה-מבני", "color": "red", "note": "-21% FY2024, -13% YTD · common prosperity = מגמה לא מחזורית" },
      { "lbl": "Margin of Safety", "val": "אפסי", "color": "orange", "note": "R/R 0.38:1 · EV = מחיר שוק · כל ביצוע פחות ממושלם = downside לא מגודר" },
      { "lbl": "EV Capex Risk", "val": "בינוני", "color": "yellow", "note": "€4.29B = 2.3× FCF שנתי · Luce fail = sunk cost + FCF לחץ 2027-2028" },
      { "lbl": "Tariff Exposure (US)", "val": "מנוהל", "color": "yellow", "note": "10% העלאת מחיר כבר מיושמת · EU-US deal pending · לא קטלני" }
    ]
  },
  "valuation_risk": {
    "description": "Ferrari ב-$345 = EV. כל תרחיש גרוע מ-base נשלח ישירות ל-downside לא מגודר. 3 תרחישים עם בעיית R/R חמורה:",
    "scenarios": [
      { "lbl": "🟡 Base", "price": "$378", "pct": "+9.6%", "height": 35, "bg": "yellow", "sub": "אפסייד שולי · מחייב ביצוע מושלם" },
      { "lbl": "🔴 Bear — Luce חלקי", "price": "$255", "pct": "-26%", "height": 70, "bg": "red", "sub": "Luce אכזבה · China ממשיכה · multiple derating" },
      { "lbl": "🔴 Disaster — Luce נדחה", "price": "$184", "pct": "-47%", "height": 90, "bg": "red", "sub": "Luce cancel · brand crisis · capex sunk cost" }
    ],
    "note": "R/R בלתי-סימטרי: upside 10% vs downside 26-47%. מינימום מוסדי: 2:1. $345 מציע 0.38:1. <b>אין edge בתמחור הנוכחי.</b>"
  },
  "stress_test": {
    "description": "4 תרחישים עם הסתברויות — עורך הדין השטן מאתגר את ה-probability distribution ומצביע על תוחלת שלילית ב-$345.",
    "gradient": "var(--green) 0% 25%, var(--yellow) 25% 55%, var(--orange) 55% 80%, var(--red) 80% 100%",
    "scenarios": [
      { "name": "🟢 שורי מלא", "prob": "25%", "color": "var(--green)" },
      { "name": "🟡 בסיס", "prob": "30%", "color": "var(--yellow)" },
      { "name": "🟠 Bear חלקי", "prob": "25%", "color": "var(--orange)" },
      { "name": "🔴 Disaster", "prob": "20%", "color": "var(--red)" }
    ],
    "rows": [
      { "scenario": "🟢 שורי מלא", "prob": "25%", "conditions": "Luce מצליחה + סין מתאוששת + מכסים מוסרים", "stock_impact": "+39% → $480", "stock_color": "c-green", "pf_impact": "+1.6%", "pf_color": "c-green" },
      { "scenario": "🟡 בסיס", "prob": "30%", "conditions": "Luce ניטרלי + guidance מאושר + status quo", "stock_impact": "+10% → $378", "stock_color": "c-text", "pf_impact": "+0.4%", "pf_color": "c-text" },
      { "scenario": "🟠 Bear חלקי", "prob": "25%", "conditions": "Luce אכזבה · China ממשיכה · מכסים נוספים", "stock_impact": "-26% → $255", "stock_color": "c-red", "pf_impact": "-1.0%", "pf_color": "c-red" },
      { "scenario": "🔴 Disaster", "prob": "20%", "conditions": "Luce נדחה · brand crisis · capex sunk cost", "stock_impact": "-47% → $184", "stock_color": "c-red", "pf_impact": "-1.9%", "pf_color": "c-red" }
    ],
    "note": "תוחלת משוקללת: (0.25×39%) + (0.30×10%) + (0.25×-26%) + (0.20×-47%) = <b>שלילית ב-$345</b>. זה לב הבעיה."
  },
  "kill_switches": [
    {
      "title": "🔴 Luce פחות מ-100 יחידות Q4 2026",
      "body": "אם Luce Elettrica לא מאשרת הזמנות משמעותיות ב-Q4 2026 — כישלון brand מוכח. כל פוזיציה = יציאה מיידית."
    },
    {
      "title": "🔴 EBIT Margin מתחת ל-27% למשך 2 רבעונים עוקבים",
      "body": "EBIT 29.5% FY2025 הוא הבסיס. ירידה ל-<27% ×2 רבעונים = שחיקת מרווח שלא נצפתה. הפחתת פוזיציה ב-50% מיידית."
    },
    {
      "title": "🟡 China Shipments מתחת ל-8,000 יחידות שנתי",
      "body": "ירידה מ-13,000+ ל-<8,000 = מגמה בלתי הפיכה. לא kill switch מיידי — thesis review תוך 30 יום."
    },
    {
      "title": "🟡 Multiple Compression מתחת ל-25x Forward P/E",
      "body": "דחיסת מכפיל ל-<25x (מ-37x) = ה-luxury premium narrative קורס. שאלת thesis, לא תנודה."
    }
  ],
  "handoff_summary": "עורך הדין השטן מציג ביקורת על ציון 8/10: RACE מתומחרת לשלמות בעוד שלושה סיכונים מהותיים לא מתומחרים — Luce brand risk (existential), China -21% FY2024 (מבני), R/R 0.38:1 ב-$345 (לא מספיק). ציון 5/10. פסיקה: WAIT ב-$345, כניסה סבירה ≤$320 post-Q2 2026.",
  "entry_exit_plan": "WAIT ב-$345. כניסה ≤$320 post-Q2 2026 + EBIT ≥29%. Kill: Luce <100 units Q4 2026 → יציאה; EBIT <27% ×2Q → הפחתה 50%."
};
