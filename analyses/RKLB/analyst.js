window.AGENT_DATA = {
  meta: {
    ticker: "RKLB",
    company: "Rocket Lab Corporation",
    date: "25.05.2026",
    agent: "analyst",
    sector: "Aerospace & Defense / Commercial Space",
    exchange: "NASDAQ"
  },

  // ── נתוני שוק ──────────────────────────────────────────
  market: {
    price_current: 135.76,          // ✅ stockinvest.us + financhill.com (22.05.2026)
    price_52w_high: 139.76,         // ✅ stockinvest.us
    price_52w_low: 23.92,           // ✅ stockinvest.us
    ytd_change_pct: null,           // ⚠️ לא זמין במקורות חינמיים
    performance_1y_pct: 472.16,     // ✅ stockanalysis.com
    market_cap_b: 78.57,            // ✅ stockinvest.us (22.05.2026)
    shares_outstanding_m: 578.75,   // ✅ stockanalysis.com
    shares_growth_1y_pct: 11.16,    // ✅ stockanalysis.com (דילול)
    beta: 2.31,                     // ✅ stockanalysis.com
    short_interest_pct: 5.45,       // ✅ stockanalysis.com
    avg_daily_volume_m: 22.4,       // ✅ stockanalysis.com
    next_earnings: "06.08.2026"     // ✅ stockinvest.us
  },

  // ── פיננסים – Q1 2026 (דוח 07.05.2026) ──────────────
  financials: {
    // הכנסות
    revenue_q1_2026_m: 200.3,       // ✅ SEC 8-K + CNBC + Globe and Mail
    revenue_q1_yoy_pct: 63.5,       // ✅ SEC 8-K מאומת
    revenue_q1_seq_pct: 12.0,       // ✅ Globe and Mail transcript
    revenue_fy2025_m: 602.0,        // ✅ SEC 8-K (שיא שנתי)
    revenue_ttm_m: 679.58,          // ✅ stockanalysis.com
    revenue_growth_5y_cagr_pct: 61.4, // ✅ gurufocus.com

    // פילוח עסקים Q1 2026
    segment_space_systems_m: 136.7, // ✅ CNBC + Globe and Mail
    segment_space_systems_yoy_pct: 57.2, // ✅ CNBC
    segment_launch_services_m: 63.7,    // ✅ CNBC + Globe and Mail
    segment_launch_services_yoy_pct: 78.9, // ✅ mlq.ai earnings

    // רווחיות
    gross_margin_gaap_pct: 38.2,    // ✅ Globe and Mail + stocktitan
    gross_margin_non_gaap_pct: 43.0, // ✅ Globe and Mail + stocktitan
    ebitda_adjusted_loss_q1_m: -11.8, // ✅ stocktitan.net
    net_loss_gaap_q1_m: -45.0,      // ✅ stocktitan.net
    loss_per_share_ttm: -0.33,      // ✅ stockanalysis.com

    // מאזן
    cash_and_securities_b: 1.38,    // ✅ stockanalysis.com
    total_debt_m: 138.67,           // ✅ stockanalysis.com
    net_cash_b: 1.34,               // ✅ stockanalysis.com
    net_cash_per_share: 2.31,       // ✅ stockanalysis.com
    debt_to_equity: 0.06,           // ✅ stockanalysis.com
    current_ratio: 4.47,            // ✅ stockanalysis.com
    liquidity_total_b: 2.0,         // ✅ stocktitan (כולל AT-M proceeds)

    // תזרים
    ocf_ttm_m: -161.63,             // ✅ stockanalysis.com
    capex_ttm_m: -154.67,           // ✅ stockanalysis.com
    fcf_ttm_m: -316.0,              // ✅ stockanalysis.com

    // מכפילים
    ps_ratio: 111.37,               // ✅ gurufocus.com (25.05.2026)
    pe_ratio: null,                 // ⚠️ לא רלוונטי – הפסד נקי
    roe_pct: -13.55,                // ✅ stockanalysis.com
    roic_pct: -8.06                 // ✅ stockanalysis.com
  },

  // ── גב הזמנות (Backlog) ────────────────────────────────
  backlog: {
    backlog_q1_2026_b: 2.2,         // ✅ SEC 8-K + CNBC + stocktitan (מאומת 3 מקורות)
    backlog_yoy_pct: 108.0,         // ✅ Globe and Mail transcript
    backlog_seq_pct: 20.0,          // ✅ Globe and Mail transcript
    backlog_split_launch_pct: 41.5, // ✅ Globe and Mail transcript
    backlog_split_space_pct: 58.5,  // ✅ Globe and Mail transcript
    backlog_12m_conversion_pct: 36.0, // ✅ mlq.ai earnings summary
    electron_contracted_launches: 70, // ✅ Globe and Mail transcript
    new_contracts_q1_count: 31,     // ✅ SEC press release (שיא רבעוני)
    neutron_contracts: 5,           // ✅ SEC press release
    doe_haste_contract_m: 190       // ✅ moneymorning.com ($190M DoD block)
  },

  // ── חוזים מרכזיים 2026 ──────────────────────────────
  key_contracts: [
    {
      name: "Space Force GEO Satellites (Heimdall SDA)",
      value_m: 90,
      date: "21.05.2026",
      details: "2 לוויינים גיאוסטציונריים – פרוייקט ראשון ב-GEO. מפעיל ל-5 שנים",
      source: "✅ Rocket Lab IR + Air and Space Forces Magazine"
    },
    {
      name: "DoD HASTE Block Order",
      value_m: 190,
      date: "Q1 2026",
      details: "20 טיסות ניסוי היפרסוניות – ה-block order הגדול ביותר בהיסטוריית החברה",
      source: "✅ moneymorning.com + mlq.ai earnings"
    },
    {
      name: "Synspective Electron Launch #9",
      value_m: null,
      date: "22.05.2026",
      details: "פריסה מוצלחת של לוויין צפייה לארץ יפני – משימה 9 לאותו לקוח",
      source: "✅ stockanalysis.com news"
    }
  ],

  // ── רכישות אסטרטגיות ───────────────────────────────
  acquisitions: [
    {
      company: "Mynaric AG",
      type: "לייזר-אופטיקל קומוניקציה",
      status: "הושלמה Q1 2026",
      source: "✅ Globe and Mail transcript"
    },
    {
      company: "Motiv Space Systems",
      type: "רובוטיקה חללית + מנגנוני תנועה",
      upfront_m: 40,
      earnout_equity_m: 20,
      status: "הסכם הוחתם 06.05.2026 – סגירה צפויה Q2 2026",
      source: "✅ Rocket Lab IR + Simply Wall St"
    }
  ],

  // ── אנליסטים ──────────────────────────────────────────
  analyst_coverage: {
    buy: 12,
    hold: 5,
    sell: 0,
    total: 17,                      // ✅ 247wallst.com
    buy_pct: 70.6,
    avg_pt_before_q1: 79.0,         // ✅ moneymorning pre-Q1
    pt_needham: 120,                // ✅ moneymorning (raised from $95)
    pt_deutsche_bank: 120,          // ✅ CNN/TipRanks (raised from $73, 12.05.2026)
    pt_247wallst: 110.52,           // ✅ 247wallst proprietary
    new_coverage_new_street: "BUY", // ✅ TipRanks 13.05.2026
    gf_fair_value: 25.86,           // ✅ gurufocus (Significantly Overvalued)
    consensus_note: "Price targets נעו $95–$135. מחיר הנוכחי $135.76 בחלק העליון של הקונצנזוס"
  },

  // ── גידה Q2 2026 ──────────────────────────────────────
  guidance_q2_2026: {
    revenue_low_m: 225,             // ✅ stocktitan.net + mlq.ai
    revenue_high_m: 240,            // ✅ stocktitan.net + mlq.ai
    gross_margin_gaap_low_pct: 33,  // ✅ stocktitan.net
    gross_margin_gaap_high_pct: 35, // ✅ stocktitan.net
    gross_margin_non_gaap_low_pct: 38, // ✅ stocktitan.net
    gross_margin_non_gaap_high_pct: 40, // ✅ stocktitan.net
    ebitda_adj_loss_low_m: -26,     // ✅ stocktitan.net
    ebitda_adj_loss_high_m: -20     // ✅ stocktitan.net
  },

  // ── טכני ──────────────────────────────────────────────
  technical: {
    price: 135.76,
    ma_200d: 66.47,                 // ✅ financhill.com (23.05.2026)
    ma_50d: 90.7,                   // ✅ altindex.com (data snapshot)
    rsi_14: 68.7,                   // ✅ chartmill.com + financhill.com (מאומת 2 מקורות)
    macd: "bullish",                // ✅ chartmill.com
    bollinger_note: "מחיר מעל פס עליון (25) — סימן קנייה לפי Financhill",
    support_1: 119.71,              // ✅ stockanalysis.com (low day May 25)
    support_2: 99.0,                // ⚠️ אומדן מבוסס 52w high prev
    resistance_1: 139.76,           // ✅ 52w high (22.05.2026)
    trend: "עלייה חדה – מעל MA200 ב-104%. RSI 68.7 – קרוב לרוויה-יתר. אין פול-בק נקי מאז Q1 earnings",
    atr_note: "⚠️ ATR לא זמין מ-Finviz (חינמי). מ-chartmill: טווח חודשי $73.99–$139.76 → ATR משוער ~$8–12/יום",
    entry_note: "Chartmill: 'entry quality medium – חכה לקונסולידציה'"
  },

  // ── סיכום אנליסט ─────────────────────────────────────
  summary: {
    bull_case: [
      "מנוע צמיחה: +63.5% YoY הכנסות ב-Q1 2026 – עלה על כל הגידה",
      "Backlog $2.2B – הכפיל תוך שנה. 36% יומר להכנסות ב-12 חודש הבאים",
      "ביטחון לאומי: 3 חוזי ביטחון גדולים בחודשיים (DoD $190M HASTE + Space Force $90M GEO)",
      "SpaceX IPO-proxy: גל הון מוסדי נכנס לסקטור. BlackRock הוסיפה 14.8% ל-Q1",
      "שילוב אנכי מלא: Launch + Space Systems + Components + Robotics (Motiv) + Optical (Mynaric)",
      "מאזן חזק: $2B נזילות, Debt/Equity 0.06 – אין לחץ דילול קצר-טווח",
      "גיוון גיאוגרפי: NZ + US + EU. לקוחות: NASA, DoD, NRO, Synspective, ועוד"
    ],
    bear_case: [
      "מכפיל PS=111 – גבוה ב-452% מחציון היסטורי. GF Value $25.86 vs מחיר $135.76",
      "FCF שלילי -$316M TTM. חברה לא רווחית על בסיס GAAP",
      "Neutron: עדיין לא שוגר. עיכובים חוזרים מ-2024. ה'ריי' כולו מגולם כהצלחה",
      "ספקולציה SpaceX: אם IPO SpaceX ינגוב הון מוסדי – RKLB ייחתך",
      "דילול: מניות +11.16% YoY. AT-M offerings ממשיכות",
      "Cathie Wood מכרה (TipRanks, 21.05.2026) – סימן זהירות",
      "תחרות: Firefly Eclipse, Falcon 9 rideshare. SpaceX יכולה להוריד מחיר אגרסיבית"
    ],
    classification: "SPECULATION",
    rationale: "חברה עם מומנטום תפעולי יוצא דופן, אך הערכה קיצונית (PS=111) + Neutron לא הוכח + FCF שלילי עמוק. מתאים לשכבת ספקולציה בלבד."
  }
};
