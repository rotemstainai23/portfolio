// ProPicks Free - סט מועמדים. נוצר 2026-06-19.
// מודל ניקוד פקטורים heuristic v1 (שקוף) על נתונים חינמיים מאומתים (Finviz + stockanalysis).
// נתונים נכון לסגירת 18.6.2026. אינו ייעוץ השקעות. כל מועמד Outperform חייב לעבור את שרשרת הסוכנים לפני קנייה.
window.PROPICKS_DATA = {
  generated: "2026-06-19",
  regime: {
    label: "BULL",
    note: "SPY +8.48% מעל 200DMA, VIX 16.4, QQQ +17.8% מעל 200DMA. שוק שורי מאוחר/מתוח - זינוק פרבולי בשבבים (AMAT +138% ב-6 חודשים, RSI 76). הטיה לטובת מומנטום אך סיכון תזמון כניסה גבוה.",
    spy_vs_200dma: "+8.48%", vix: 16.4
  },
  model_note: "composite = סכום משוקלל של 5 פקטורים (0-100) לפי ארכיטיפ best-fit. Outperform>=70 | Neutral 45-69 | Underperform<45. מודל heuristic שקוף, לא קופסה שחורה.",
  excluded: ["NVDA","MSFT","GOOG","META","AVGO","MU","IBIT","GLDM","VST","APLD","OKLO","V","NOW","AMZN","ROCK"],
  candidates: [
    { ticker:"TER", company:"Teradyne", sector:"Technology", archetype:"Tech Titans", price:437.92,
      factor_scores:{ value:35, growth:98, quality:85, momentum:82, risk:35, composite:82, classification:"Outperform" },
      key:{ pe:81.1, fwd_pe:44.0, peg:0.87, rev_gr:"+86.8%", roic:"26.6%", beta:1.76, perf_6m:"+127.7%" },
      risk_flag:"שווי מתוח (P/E 81, P/FCF 124) + beta 1.76. צמיחה יוצאת דופן אך תמחור מלא. כניסה הדרגתית בלבד.",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=TER" },

    { ticker:"FICO", company:"Fair Isaac", sector:"Technology", archetype:"Quality Compounders", price:1096.48,
      factor_scores:{ value:55, growth:90, quality:95, momentum:20, risk:45, composite:72, classification:"Outperform" },
      key:{ pe:34.7, fwd_pe:20.2, peg:0.69, rev_gr:"+38.7%", roic:"48.9%", beta:1.30, perf_6m:"-38.8%" },
      risk_flag:"איכות עילית (ROIC 49%, מרווח תפעולי 51%) אבל מומנטום שבור (-38.8% ב-6ח, מתחת 200DMA). הזדמנות ערך או 'סכין נופלת' - דורש אימות תזה חזק.",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=FICO" },

    { ticker:"AMAT", company:"Applied Materials", sector:"Technology", archetype:"Tech Titans", price:617.11,
      factor_scores:{ value:38, growth:68, quality:90, momentum:80, risk:45, composite:71, classification:"Outperform" },
      key:{ pe:58.0, fwd_pe:37.5, peg:1.30, rev_gr:"+11.4%", roic:"28.5%", beta:1.58, perf_6m:"+138.4%" },
      risk_flag:"איכות מצוינת (ROIC 28.5%) אך overbought קיצוני (RSI 76, +138% ב-6ח, +94% מעל 200DMA). סיכון mean-reversion גבוה. להמתין למשיכה.",
      confidence:"HIGH", source:"stockanalysis.com/stocks/AMAT + finviz" },

    { ticker:"CAH", company:"Cardinal Health", sector:"Healthcare", archetype:"Top Value", price:221.77,
      factor_scores:{ value:78, growth:58, quality:58, momentum:70, risk:80, composite:69, classification:"Neutral" },
      key:{ pe:33.9, fwd_pe:18.5, peg:1.03, rev_gr:"+11.1%", roic:"28.7%", beta:0.49, perf_6m:"+12.1%" },
      risk_flag:"שווי אטרקטיבי + beta נמוך 0.49 + מומנטום יציב. חולשה: מרווחים דקים מאוד (מודל הפצה). על סף Outperform.",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=CAH" },

    { ticker:"TXN", company:"Texas Instruments", sector:"Technology", archetype:"Beat the S&P 500", price:322.86,
      factor_scores:{ value:35, growth:72, quality:80, momentum:80, risk:50, composite:66, classification:"Neutral" },
      key:{ pe:55.2, fwd_pe:36.1, peg:1.58, rev_gr:"+18.6%", roic:"18.0%", beta:1.30, perf_6m:"+81.8%" },
      risk_flag:"איכות גבוהה (ROE 32%, מרווח 36%) אך יקר אחרי +82% ב-6ח. P/S 15.9 מתוח מול ההיסטוריה שלה.",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=TXN" },

    { ticker:"HEI", company:"HEICO", sector:"Industrials", archetype:"Quality Compounders", price:337.10,
      factor_scores:{ value:28, growth:80, quality:68, momentum:72, risk:68, composite:65, classification:"Neutral" },
      key:{ pe:60.2, fwd_pe:49.3, peg:2.96, rev_gr:"+25.3%", roic:"10.7%", beta:1.04, perf_6m:"+8.6%" },
      risk_flag:"חפיר A&D עמיד + צמיחה חזקה, אבל שווי מתוח מאוד (P/E 60, PEG 2.96).",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=HEI" },

    { ticker:"NUE", company:"Nucor", sector:"Basic Materials", archetype:"Top Value", price:243.83,
      factor_scores:{ value:70, growth:60, quality:45, momentum:72, risk:45, composite:60, classification:"Neutral" },
      key:{ pe:24.2, fwd_pe:14.7, peg:0.49, rev_gr:"+21.3%", roic:"8.2%", beta:1.89, perf_6m:"+50.3%" },
      risk_flag:"זול (PEG 0.49) אך מחזורי בשיא (EPS +98%), beta 1.89, P/FCF 104 (capex כבד). סיכון פסגת מחזור.",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=NUE" },

    { ticker:"ON", company:"ON Semiconductor", sector:"Technology", archetype:"Tech Titans", price:121.62,
      factor_scores:{ value:45, growth:55, quality:35, momentum:82, risk:25, composite:55, classification:"Neutral" },
      key:{ pe:86.7, fwd_pe:28.3, peg:0.81, rev_gr:"+4.7%", roic:"5.5%", beta:1.98, perf_6m:"+122.9%" },
      risk_flag:"מומנטום חזק (+123% ב-6ח) אך איכות נוכחית חלשה (ROIC 5.5%) + beta 1.98. התאוששות כבר מתומחרת.",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=ON" },

    { ticker:"IBM", company:"IBM", sector:"Technology", archetype:"Beat the S&P 500", price:249.10,
      factor_scores:{ value:62, growth:40, quality:68, momentum:30, risk:55, composite:49, classification:"Neutral" },
      key:{ pe:22.0, fwd_pe:18.6, peg:2.25, rev_gr:"+9.5%", roic:"11.5%", beta:0.69, perf_6m:"-17.8%" },
      risk_flag:"הזול בקבוצה + FCF חזק, אך חוב גבוה (D/E 2.12), צמיחה נמוכה, ומומנטום שבור (-17.8% ב-6ח).",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=IBM" },

    { ticker:"MOH", company:"Molina Healthcare", sector:"Healthcare", archetype:"Top Value", price:195.37,
      factor_scores:{ value:50, growth:20, quality:28, momentum:65, risk:62, composite:43, classification:"Underperform" },
      key:{ pe:57.6, fwd_pe:20.8, peg:3.87, rev_gr:"-3.2%", roic:"2.34%", beta:0.76, perf_6m:"+21.4%" },
      risk_flag:"P/S נמוך (0.23) מטעה - קריסת רווחים (EPS השנה -53%, PEG 3.87). המודל דוחה אותה נכון.",
      confidence:"HIGH", source:"finviz.com/quote.ashx?t=MOH" }
  ]
};
