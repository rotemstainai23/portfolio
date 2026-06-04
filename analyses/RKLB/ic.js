window.AGENT_DATA = {
  meta: {
    ticker: "RKLB",
    company: "Rocket Lab Corporation",
    date: "25.05.2026",
    agent: "ic",
    tagline: "ועדת השקעות — פסיקה סופית"
  },

  // ── הצבעות סוכנים ─────────────────────────────────────
  agent_votes: [
    {
      agent: "אנליסט",
      vote: "WATCHLIST",
      confidence: 7,
      one_liner: "עסק יוצא דופן, מחיר קיצוני — מניה אמיתית אבל ב-PS=111 אי-אפשר להצדיק כניסה"
    },
    {
      agent: "עורך דין שטן",
      vote: "DANGER ZONE",
      confidence: 9,
      one_liner: "Neutron לא הוכח, FCF שלילי -$316M, SpaceX IPO מאיים על ה-proxy premium"
    },
    {
      agent: "CEO",
      vote: "WATCHLIST",
      confidence: 8,
      one_liner: "תיק בחריגה קשה — ספקולציה 17.4%. אי-אפשר לפתוח פוזיציה חדשה לפני ניקוי"
    },
    {
      agent: "Executor",
      vote: "NO ACTION",
      confidence: 9,
      one_liner: "R/R=1.52 — מתחת לסף 2:1. טריגר ב-$95 בלבד"
    }
  ],

  // ── בדיקת חשיבת-עדר ────────────────────────────────────
  groupthink_check: {
    consensus: "ועדה אחידה — כולם מסרבים לקנות עכשיו",
    devil_position: "האם יש מצב שאנחנו פספסנו משהו?",
    contrarian_check: [
      {
        question: "מה אם RKLB היא ה-NVIDIA של החלל?",
        answer: "NVDA ב-2020 הייתה PS~15. RKLB ב-PS=111 מחיר לפני הצמיחה הגדולה. גם אם הצמיחה מתממשת — הרבה ממנה כבר מגולם"
      },
      {
        question: "מה אם Neutron יעוף עוד חודש?",
        answer: "תרחיש Upside: +20-30% — עדיין R/R גרוע ממחיר $135. אחרי 'buy the rumor', אפשר שנראה 'sell the news'"
      },
      {
        question: "SpaceX IPO יכול לגרור את RKLB גבוה יותר?",
        answer: "אפשרי בטווח קצר. אבל ה-proxy premium לא מחזיק לאחר שיש אלטרנטיבה ישירה"
      }
    ],
    conclusion: "הבדיקה לא מצאה תרחיש שמשנה את הפסיקה"
  },

  // ── פסיקה סופית ───────────────────────────────────────
  final_verdict: {
    decision: "WATCHLIST",
    decision_color: "yellow",
    trigger_price: 95.0,
    trigger_conditions: [
      "מחיר ≤ $95 (pullback -30% מהשיא)",
      "IBIT קוצץ ל-4% (תנאי מקדים חובה)",
      "OR: Neutron test flight מוצלח (buy the catalyst)"
    ],
    max_allocation_pct: 2.0,
    max_allocation_usd: 38,
    stop_loss_if_bought: 80.0,

    // עבור portfolio.json
    portfolio_json_entry: {
      ticker: "RKLB",
      verdict: "WATCHLIST",
      trigger_price: 95.0,
      max_size_pct: 2.0,
      layer: "speculation",
      note: "Neutron test flight catalyst. Pre-condition: קצץ IBIT→4% קודם",
      date_added: "25.05.2026"
    }
  },

  // ── ציר זמן ──────────────────────────────────────────
  timeline: {
    q2_2026: "Q2 earnings אוגוסט 2026 — אם Revenue >$240M → bullish. מתחת → pullback",
    neutron_h2_2026: "Neutron launch attempt H2 2026 — binary catalyst. הצלחה: +20-40%. כישלון: -40%",
    spacex_ipo_june_2026: "SpaceX IPO יוני 2026 — עלול לגרום לתנודתיות קשה ב-RKLB",
    revisit: "בדיקה מחדש: אחרי SpaceX IPO ו/או Neutron first attempt"
  },

  // ── עדכון watchlist מוצע ─────────────────────────────
  watchlist_action: {
    action: "הוסף ל-Watchlist",
    trigger: 95.0,
    note: "⚠️ תנאי מקדים: קצץ IBIT ל-4% לפני כל קנייה"
  },

  // ── סיכום ─────────────────────────────────────────────
  executive_summary: {
    headline: "RKLB — עסק מצוין, מחיר גרוע, תיק לא מוכן",
    body: "Rocket Lab היא חברה חלל אמיתית עם הכנסות אמיתיות ($200M Q1), backlog שוות-ערך ($2.2B), וחוזי ביטחון לאומי הולכים וגדלים. הנהלה פיתחה מודל עסקי אנכי שאין לו מקבילה ציבורית. זה הבול-קייס. הבר-קייס: PS=111, Neutron לא הוכח, FCF שלילי -$316M, SpaceX IPO מאיים על ה-proxy premium, ותיק המשתמש כבר ב-17.4% ספקולציה — פי 2 מהמותר. המסקנה: רשימת המעקב ב-$95, לא עכשיו ב-$135.",
    action_required_now: "🚨 קצץ IBIT עכשיו (מ-10.9% ל-4%) — זה דחוף יותר מ-RKLB"
  }
};
