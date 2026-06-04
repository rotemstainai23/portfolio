window.AGENT_DATA = {
  meta: {
    ticker: "RKLB",
    company: "Rocket Lab Corporation",
    date: "25.05.2026",
    agent: "devils",
    tagline: "כל בועה נראית כמו הזדמנות עד שהיא מתפוצצת"
  },

  // ── ציוני סיכון ──────────────────────────────────────
  risk_scores: {
    valuation_risk: 10,        // חמור ביותר
    execution_risk: 8,         // Neutron לא הוכח
    financial_risk: 7,         // FCF שלילי עמוק
    competition_risk: 7,       // SpaceX dominance
    dilution_risk: 6,          // AT-M offerings ממשיכות
    sentiment_risk: 8,         // SpaceX IPO יכול להפוך לנגד
    overall: 8,
    verdict: "DANGER ZONE — ספקולציה גבוהה בלבד"
  },

  // ── תיקי תביעה מפורטים ───────────────────────────────
  prosecution: [

    {
      id: "V1",
      category: "הערכה",
      severity: "🔴 קריטי",
      title: "PS=111 — הכי יקר ב-Aerospace & Defense",
      argument: "Rocket Lab נסחרת במכפיל מכירות 111x. מחציון הענף הוא 4x — RKLB יקרה ב-2,700% ממחציון הענף. GurFocus מדרגת אותה 'Significantly Overvalued' עם Fair Value $25.86 לעומת מחיר שוק $135.76. אפילו בתרחיש שיהכנסות יגיעו ל-$1.2B ב-2027, ובמכפיל 'נדיב' של 50x — שווי הוגן הוא ~$58B, כ-26% פחות מהיום.",
      data_point: "PS=111 vs. ממוצע ענף 4.02 (gurufocus.com ✅)",
      counter_prepared: "הצמיחה מצדיקה פרמיה — אבל 111x מחיר 'צמיחה מושלמת' לשנים קדימה"
    },

    {
      id: "V2",
      category: "מוצר מרכזי",
      severity: "🔴 קריטי",
      title: "Neutron: הכל מגולם, כלום לא הוכח",
      argument: "המחיר הנוכחי כולל הצלחה מוחלטת של Neutron. הרקטה עוכבה פעמים מרובות (2024→2025→H2 2026). ניסיון ראשון נכשל — המניה עלולה לצנוח 40-50% ביום. Falcon 9 של SpaceX עולה ~$67M לשיגור ייעודי; Neutron מתוכנן ב-$55M. SpaceX יכולה להוריד מחיר ב-10% ולמחוק את כל הנישה של Neutron. קיבולת Neutron (13,000 ק\"ג) נמוכה מ-Falcon 9 (17,500 ק\"ג).",
      data_point: "Neutron מעוכב. 5 חוזים נמכרו — 0 שיגורו (247wallst.com, heygotoge.com ✅)",
      counter_prepared: "5 חוזי Neutron כבר נמכרו — אות ביטחון לקונים. אבל בלי שיגור — רק כסף שנספר"
    },

    {
      id: "V3",
      category: "תזרים מזומנים",
      severity: "🔴 קריטי",
      title: "FCF שלילי -$316M TTM — שריפת הון מסיבית",
      argument: "החברה שרפה $316M מזומנים ב-12 חודשים האחרונים. OCF שלילי -$162M + Capex -$155M. עם $1.38B מזומן + AT-M, יש 'runway' של ~4 שנים — אבל הדילול ממשיך. כל שנה יוצאים $316M. אם Neutron מתעכב עוד שנה — ה-runway מצטמצם לפחות מ-3 שנים. זה לא 'הפסד אסטרטגי' — זה חברה שעדיין בונה את עצמה.",
      data_point: "FCF -$316M TTM (stockanalysis.com ✅). Capex ל-Neutron עדיין בעלייה",
      counter_prepared: "Cash >$2B + AT-M מגנה. אמת — אבל כל שנה כשלון תפעולי מוסיפה לסיכון"
    },

    {
      id: "V4",
      category: "SpaceX IPO",
      severity: "🟡 גבוה",
      title: "SpaceX IPO — הדבר הכי טוב לתיאוריה ועלול להיות הכי רע לביצועים",
      argument: "SpaceX הגישה S-1 ב-01.04.2026, מכוונת ל-IPO ביוני 2026 בשווי $1.75T-$2T. כרגע RKLB היא 'ה-SpaceX של השוק הציבורי' — מכאן מגיע חלק גדול מהפרמיה. ביום שSpaceX תיסחר, אינסטיטוציונלים יוכלו להחזיק את האמיתית. RKLB עלולה לאבד את ה-proxy premium בין לילה.",
      data_point: "SpaceX S-1 הוגש 01.04.2026, IPO ביוני 2026 ~$75B גיוס (stocktwits ✅)",
      counter_prepared: "SpaceX IPO יגדיל את הסקטור — אולי. אבל ייצור גם אלטרנטיבה ישירה"
    },

    {
      id: "V5",
      category: "מוסדיים",
      severity: "🟡 גבוה",
      title: "Cathie Wood מכרה — ה'Smart Money' יוצא",
      argument: "Cathie Wood (ARK Invest), שהייתה אחת הקונות הגדולות ב-RKLB, מוכרת (TipRanks 21.05.2026). ARK מכרה במחיר נמוך יותר — סימן שהיא רואה ערך מוגבל בשלב זה. אמנם BlackRock הוסיפה 14.8% ב-Q1, אבל BlackRock קונה כמעט הכל — זה לא אות ביטחון.",
      data_point: "ARK Invest מוכרת RKLB (TipRanks 21.05.2026 ✅). BlackRock +14.8% Q1 (quiverquant ✅)",
      counter_prepared: "ARK מוכרת ו-BlackRock קונה — ניתן לפרש לשני כיוונים"
    },

    {
      id: "V6",
      category: "דילול",
      severity: "🟡 גבוה",
      title: "AT-M Offerings — 11% דילול בשנה, ייצרה $450M",
      argument: "מניות בחוזר +11.16% תוך שנה. החברה מנפיקה דרך AT-M כבר שנים. כל קונה מחזיק פחות מהחברה כל שנה. עם $78B Market Cap, 11% דילול = ~$8.5B בשנה שיצא מהכיסים של בעלי המניות הקיימים. ביצועי מניה ריאליים חלשים יותר ממה שנראה.",
      data_point: "Shares +11.16% YoY. AT-M $450.3M raised Q1 2026 (stocktitan.net ✅)",
      counter_prepared: "גייסו הון למימון צמיחה — לגיטימי. אבל הדילול ממשיך ואין סוף ברור"
    },

    {
      id: "V7",
      category: "טכני",
      severity: "🟡 גבוה",
      title: "מעל MA200 ב-104% — ריחוק קיצוני מ-'Fair Value' טכני",
      argument: "MA200 ב-$66.47. מחיר נוכחי $135.76 — 104% מעל. RSI 68.7 — קרוב לרוויה-יתר (>70). Chartmill מציין 'entry quality: medium — המתן לקונסולידציה'. Investing.com מדרג 'Strong Sell' לפי ממוצעים נעים. מי שנכנס עכשיו מסתכן בקנייה בשיא אחרי ריצה של +472% בשנה.",
      data_point: "MA200=$66.47, מחיר $135.76 (financhill.com ✅). RSI 68.7 (chartmill.com ✅)",
      counter_prepared: "מגמה ארוכת-טווח חזקה — אבל נקודת הכניסה גרועה"
    }
  ],

  // ── תרחישי ירידה ──────────────────────────────────────
  downside_scenarios: [
    {
      name: "Neutron נכשל / מתעכב",
      probability_pct: 25,
      price_target: 60,
      decline_pct: -56,
      trigger: "שיגור בדיקה נכשל או עיכוב ל-2027"
    },
    {
      name: "SpaceX IPO שואב הון",
      probability_pct: 30,
      price_target: 85,
      decline_pct: -37,
      trigger: "IPO SpaceX מצליח → RKLB מאבדת proxy premium"
    },
    {
      name: "הכנסות מאכזבות Q2/Q3",
      probability_pct: 20,
      price_target: 95,
      decline_pct: -30,
      trigger: "Q2 2026 Revenue מתחת ל-$225M (רצפת guidance)"
    },
    {
      name: "שוק כללי תיקון",
      probability_pct: 20,
      price_target: 80,
      decline_pct: -41,
      trigger: "Beta=2.31 → ירידה של 20% בשוק = -46% ב-RKLB"
    }
  ],

  // ── שורה תחתונה ───────────────────────────────────────
  verdict: {
    recommendation: "⚠️ לא לקנות במחיר נוכחי",
    max_position_pct: 4,
    rationale: "RKLB מציגה ביצועים תפעוליים מרשימים, אבל ב-$135.76 — PS=111 — המחיר מגלם הצלחה מושלמת של Neutron + שמירת כל הנישה + שוק חלל גדל מהירות. כל אחד מאלה לא בטוח. R/R לא מצדיק כניסה בשלב זה.",
    wait_for: "פול-בק ל-$85–$95 (MA50 אזור) ו/או Neutron test flight מוצלח"
  }
};
