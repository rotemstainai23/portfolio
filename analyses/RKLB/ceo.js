window.AGENT_DATA = {
  meta: {
    ticker: "RKLB",
    company: "Rocket Lab Corporation",
    date: "25.05.2026",
    agent: "ceo",
    tagline: "ניהול תיק — לא מרוץ תגובות"
  },

  // ── מצב תיק נוכחי (לפי HANDOFF) ─────────────────────
  portfolio_context: {
    total_value: 1924,
    cash_pct: 3.7,
    cash_usd: 71.2,

    // שכבות
    layers: {
      stability: { target_pct: "25–35", actual_pct: 31.1, status: "✅" },
      growth: { target_pct: "55–65", actual_pct: 47.8, status: "🔴 חסר ~10%" },
      speculation: { target_pct: "5–10", actual_pct: 17.4, status: "🔴 פי 2 מהמותר" },
      cash: { target_pct: "5–10", actual_pct: 3.7, status: "🟡 נמוך מדי" }
    },

    // אחזקות ספקולציה קיימות (17.4%)
    existing_speculation: [
      { ticker: "APLD", pct: 2.5 },
      { ticker: "OKLO", pct: 4.0 },
      { ticker: "IBIT", pct: 10.9 }  // ← חריגה עיקרית! תקרה 4%
    ],

    // בעיות דחופות
    urgent_issues: [
      "IBIT: 10.9% vs תקרת ספקולציה 4% — חריגה של 173%",
      "NVDA: 14.3% vs תקרת פוזיציה 12% — חריגה של 19%",
      "שכבת ספקולציה כוללת 17.4% — תקרה 10%"
    ]
  },

  // ── ניתוח התאמה לתיק ────────────────────────────────
  portfolio_fit: {
    proposed_layer: "SPECULATION",
    proposed_allocation_max_pct: 4.0,

    // בדיקות חובה לפני כניסה
    checks: [
      {
        check: "שכבת ספקולציה מלאה?",
        result: "🔴 כן — 17.4% vs תקרה 10%",
        action: "חייב לקצץ לפני כל קנייה חדשה"
      },
      {
        check: "תקציב מזומן לקנייה?",
        result: "🟡 $71.2 מזומן (3.7%) — מתחת ל-5% מינימום",
        action: "אין מזומן פנוי לקנייה חדשה"
      },
      {
        check: "R/R 2:1 מינימלי?",
        result: "🔴 לא — ראה Executor",
        action: "במחיר $135.76 — R/R מתחת ל-2:1 לכל תקרת סביר"
      },
      {
        check: "קורלציה לתיק?",
        result: "🟡 בינונית — חפיפה עם OKLO (חלל/ביטחון). Growth-proxy חדש",
        action: "לא מוסיף פיזור — מחמיר סיכון"
      }
    ],

    // סדר פעולות מחייב לפני כל שקילה
    prerequisite_actions: [
      {
        priority: 1,
        action: "קצץ IBIT מ-10.9% ל-4% (מכור ~$130 שווי)",
        reason: "חריגת ספקולציה קריטית — חייב לפני כל קנייה חדשה",
        already_approved: true,
        note: "כבר אושר ב-NOW handoff — בצע!"
      },
      {
        priority: 2,
        action: "קצץ NVDA ל-12% (מכור ~$44 שווי)",
        reason: "חריגת תקרה פוזיציה",
        already_approved: false
      },
      {
        priority: 3,
        action: "הוסף Growth בשכבה ל-55–65% (לשקול NOW Scale In)",
        reason: "שכבת Growth חסרה ~10%",
        already_approved: true,
        note: "NOW Scale In כבר אושר, trigger $100"
      }
    ]
  },

  // ── הצבעת CEO ─────────────────────────────────────────
  ceo_decision: {
    verdict: "WATCHLIST — לא עכשיו",
    score_strategic_fit: 6,    // מתאים לתזה חלל/ביטחון, אבל תיק כבר עמוס
    score_timing: 3,           // נקודת כניסה גרועה — אחרי +472% שנה
    score_rr: 2,               // R/R לא עומד בסף 2:1
    score_portfolio_health: 2, // תיק בחריגה קשה — לא זמן לפוזיציות חדשות

    conditions_to_revisit: [
      "תקצץ IBIT ל-4% (תנאי מקדים — כבר הוסכם)",
      "RKLB תגיע ל-$90–$100 (pullback לאחר ריצה)",
      "Neutron מבצע test flight מוצלח",
      "Growth layer יגיע ל-55% לפחות לפני פתיחת ספקולציה נוספת"
    ],

    max_future_position_pct: 2.0,  // בגלל OKLO + APLD כבר ב-Spec layer
    max_future_position_usd: 38,

    ceo_note: "RKLB היא חברה אמיתית עם מומנטום אמיתי — אין ספק. אבל התיק כרגע חולה: ספקולציה פי-2 מהמותר, IBIT לא קוצץ, Growth חסרה. לא נוסיף ספקולציה חדשה עד שנתקן את מה שיש. Rule: תיק בריא לפני הזדמנויות חדשות."
  },

  // ── השוואה מניות Watchlist קיימות ──────────────────────
  vs_watchlist: {
    vs_now: "NOW (ServiceNow) — ספקולציה vs Growth. NOW כבר אושרה ויש trigger פעיל. עדיפות ל-NOW.",
    vs_visa: "Visa — Stability vs Speculation. שני מישורים שונים. Visa ממתינה ל-$287."
  }
};
