window.AGENT_DATA = {
  meta: {
    ticker: "RKLB",
    company: "Rocket Lab Corporation",
    date: "25.05.2026",
    agent: "executor",
    tagline: "מספרים בלבד — R/R שולט"
  },

  // ── נתוני כניסה ──────────────────────────────────────
  entry_analysis: {
    price_current: 135.76,
    price_52w_low: 23.92,
    price_52w_high: 139.76,

    // ATR אומדן (Finviz לא זמין חינם)
    atr_estimated: 10.5,         // ⚠️ אומדן: טווח חודשי $73.99–$139.76 ÷ ~6 שבועות
    atr_source: "⚠️ אומדן מטווח חודשי Chartmill — אין ATR מדויק מ-Finviz",
    atr_note: "ATR ~$10-12 ביום — מניה תנודתית מאוד (Beta 2.31)",

    // Moving Averages — נקודות תמיכה
    ma_200d: 66.47,
    ma_50d: 90.7,
    support_primary: 119.71,     // שפל יומי 25.05.2026
    support_secondary: 99.0,     // אזור MA50 לפני הריצה
    support_tertiary: 80.0,      // post-Q1 pullback scenario
    resistance_1: 139.76         // 52w high
  },

  // ── חישוב R/R לתרחישי כניסה ─────────────────────────
  rr_scenarios: [
    {
      scenario: "כניסה מיידית עכשיו",
      entry: 135.76,
      stop_loss: 119.71,         // תמיכה עיקרית
      target_1: 160.0,           // ~18% upside (PT Needham $120 כבר מתחת)
      rr_1: 1.52,
      target_consensus: 120.0,   // PT ממוצע אנליסטים
      rr_consensus: -0.98,       // שלילי! המחיר כבר מעל PT ממוצע
      verdict: "🔴 FAIL — R/R 1.52:1 — מתחת ל-2:1 מינימום. יעד קונצנזוס מתחת למחיר",
      pass_minimum: false
    },
    {
      scenario: "כניסה אחרי פול-בק — אזור $95",
      entry: 95.0,
      stop_loss: 80.0,           // מתחת לאזור MA50
      target_1: 135.0,           // חזרה לרמה הנוכחית
      rr_1: 2.67,
      target_2: 150.0,
      rr_2: 3.67,
      verdict: "✅ PASS — R/R 2.67:1 — עומד בסף 2:1. אבל צריך pullback -30%",
      pass_minimum: true,
      note: "דורש Neutron catalyst + market pullback. לא סביר בטווח קצר"
    },
    {
      scenario: "כניסה אחרי Neutron success — $85",
      entry: 85.0,
      stop_loss: 68.0,
      target_1: 130.0,
      rr_1: 2.65,
      verdict: "✅ PASS — R/R 2.65:1. תרחיש: Neutron נכשל ← מחיר נופל ← נקנה",
      pass_minimum: true,
      note: "ironically — כדאי לחכות שהשוק ייבהל מכישלון ואז לקנות"
    }
  ],

  // ── פרמטרי כניסה מומלצים (אם יגיע ל-trigger) ─────────
  recommended_entry: {
    trigger_price: 95.0,
    trigger_conditions: [
      "מחיר מגיע ל-$95 (+/- $3)",
      "RSI יורד מתחת ל-50",
      "IBIT כבר קוצץ ל-4% (תנאי מקדים!)",
      "OR: Neutron test flight מוצלח ← buy the news"
    ],
    position_size_pct: 2.0,        // מקסימום בגלל ספקולציה כבר מלאה
    position_size_usd: 38,
    stop_loss: 80.0,
    stop_loss_pct_from_entry: -15.8,
    target_1: 130.0,
    target_1_pct: 36.8,
    target_2: 160.0,
    target_2_pct: 68.4,
    rr_at_trigger: 2.67,
    scale_in_allowed: false,       // פוזיציה קטנה — כניסה אחת
    scale_in_note: "שכבת ספקולציה מוגבלת — אין מקום לחלוקה"
  },

  // ── סיכום Executor ────────────────────────────────────
  summary: {
    action_now: "NO ACTION — R/R לא עומד בסף",
    action_watch: "הגדר התרעה ב-$95",
    current_rr: 1.52,
    minimum_rr: 2.0,
    gap: -0.48,
    verdict_color: "red",
    verdict_text: "⛔ לא לקנות במחיר $135.76. R/R=1.52 — מתחת לסף 2:1. הגדר alert ב-$95."
  }
};
