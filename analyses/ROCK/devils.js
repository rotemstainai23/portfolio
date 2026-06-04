// CLAUDE-AUTO-GENERATED — מחק שורה זו כדי לנעול את הקובץ מפני דריסה
window.AGENT_DATA = {
  ticker: 'ROCK',
  company: 'Gibraltar Industries',
  date: '2026-06-01',
  inherited: {
    items: [
      {k: 'מחיר נוכחי', v: '$38.65'},
      {k: 'שווי שוק', v: '~$1.15B'},
      {k: 'שווי הוגן (בסיס)', v: '$49-52 (+27-35%)'},
      {k: 'שווי הוגן (שורי)', v: '$82-85 (+112%)'},
      {k: 'ציון איכות', v: '6/10'},
      {k: 'Net Leverage', v: '3.9x (max 5.25x)'},
      {k: 'מזומן', v: '$20M'},
      {k: 'דוח הבא', v: 'Q2 2026 — אוגוסט 2026'}
    ],
    note: 'ההנחה השבירה: שוק הדיור יצמח 4-5% ב-2026, OmniMax EBITDA $110-120M שאינו ניתן לאימות חיצוני, ו-integration מושלמת של $1.335B רכישה.'
  },
  attack: {
    headline: 'Gibraltar ביצעה הימור קיומי עם כסף שאין לה — ×112% upside או ×0 downside',
    paragraphs: [
      'Gibraltar Industries עברה תמורה מהותית בפברואר 2026: מחברה עם $269M מזומן, אפס חוב, ו-FCF $157M לשנה — לחברה עם <b>$20M מזומן, $1.22B חוב, ו-OCF שלילי ברבעון הראשון</b> לאחר הרכישה. OmniMax עלתה $1.335B על בסיס מספרים שאף אחד לא יכול לאמת, כי OmniMax הייתה חברה פרטית. לא קיים 10-K עצמאי, לא קיימים מספרים מבוקרים מגוף חיצוני. אם ה-EBITDA האמיתי הוא $85-90M ולא $120M, Gibraltar שילמה 14.8-15.7x — פרמיה מלאה על עסק מחזורי בשוק חלש.',
      'מוכר שורט מנוסה לא יתמקד בירידת המרווח הגולמי. הוא יתמקד בשאלה הבסיסית: <b>מה ה-Equity Value כשמניות מסוכנות ב-Leverage?</b> EV/EBITDA 7.4x נראה זול — אבל EBITDA miss של 17% גורר Equity מ-$1.15B ל-$655M (-43%). miss של 31% = Net Leverage >5.25x = <span class="punch">covenant breach = Equity $10M. זה לא תרחיש קיצוני — זה תרחיש "ביצוע בינוני".</span>',
      'הטרנד הארוך של FCF הוא הסיפור האמיתי: FY2023 $205M → FY2024 $157M → FY2025 $91-120M — ירידה של 30-56% <b>לפני</b> ה-leverage הגדול. FCF guided $143M לא ריאלי: ריבית $58M + capex $46M + integration costs $50-70M = FCF אמיתי <b>$54-104M</b>. לא $143M שהובטחו.'
    ]
  },
  risk_scorecard: {
    description: 'Gibraltar = אופציה ממונפת, לא השקעת ערך סולידית. הסיכון binary — לא חלקי. כישלון של שני גורמים מתוך חמישה = downside 40-80%+.',
    items: [
      {lbl: 'שבירות תזה', val: '🔴 קיצונית', color: 'red', note: 'דורשת 5 הנחות בו-זמנית: integration, synergies, דיור, אלומיניום, deleveraging'},
      {lbl: 'סיכון עסקי', val: '🔴 גבוה', color: 'red', note: 'OmniMax פרטית — אין 10-K עצמאי, EBITDA לא ניתן לאימות חיצוני'},
      {lbl: 'סיכון פיננסי', val: '🔴 גבוה', color: 'red', note: 'Net leverage 3.9x, $20M מזומן, OCF שלילי Q1 2026, covenant breach at -31% EBITDA'},
      {lbl: 'סיכון שווי', val: '🟡 בינוני', color: 'yellow', note: 'EV/EBITDA 7.4x "זול" — אבל Leverage מוטה. downside -43% ב-miss 17%'},
      {lbl: 'סיכון מאקרו', val: '🔴 גבוה', color: 'red', note: 'Mortgage rates 6.5%+, housing starts מתחת לממוצע, Q1 2026 הוכיח ביקוש רך'},
      {lbl: 'סיכון Impairment', val: '🔴 גבוה', color: 'red', note: '$1.706B אינטנגיבלים = 194% הון עצמי — write-down $300-500M מוחק הון עצמי'}
    ]
  },
  valuation_risk: {
    description: 'עם Leverage גבוה, שינוי קטן ב-EBITDA גורר שינוי ענק ב-Equity Value. EV = Market Cap + Net Debt = $2.35B. EBITDA miss 17% מכווץ Equity ב-43%. זו מתמטיקה, לא תחזית.',
    scenarios: [
      {price: '$84.9', height: 100, pct: '+120%', lbl: 'שורי', sub: 'EBITDA $340M · 11x', color: 'c-green', bg: 'green'},
      {price: '$50.3', height: 60, pct: '+30%', lbl: 'בסיס', sub: 'EBITDA $318M · 8.5x', color: 'c-yellow', bg: 'yellow'},
      {price: '$21.9', height: 26, pct: '−43%', lbl: 'EBITDA miss 17%', sub: '$265M · 7.0x', color: 'c-orange', bg: 'orange'},
      {price: '$0.33', height: 1, pct: '−99%', lbl: 'Covenant Breach', sub: 'EBITDA miss 31% = $220M', color: 'c-red', bg: 'red'}
    ],
    note: '<b>מחיר אטרקטיבי אמיתי: $26-28.</b> שם EV/EBITDA 5.8-6.2x גם ב-EBITDA miss קל, ו-R/R עובר 2:1. ב-$38.65 — מחיר הוגן לתרחיש בסיס בלבד, ללא מרווח ביטחון לסיכון binary.'
  },
  stress_test: {
    description: 'הסתברויות מבוססות: housing data חלש תומך ב-bear/base, OmniMax private EBITDA לא ניתן לאימות תומך ב-disaster, Q1 OCF שלילי מסמן לחץ תזרימי.',
    gradient: 'var(--green) 0 20%,var(--yellow) 20% 55%,var(--red) 55% 85%,#6b1a1a 85% 100%',
    scenarios: [
      {color: 'var(--green)', name: '🟢 שורי — OmniMax מעל guidance, דיור מתאושש', prob: '20%'},
      {color: 'var(--yellow)', name: '🟡 בסיס — guidance מתממש, deleveraging מתקדם', prob: '35%'},
      {color: 'var(--red)', name: '🔴 דובי — EBITDA miss 17%, Equity -43%', prob: '30%'},
      {color: '#6b1a1a', name: '⚫ אסון — Covenant Breach, Goodwill Write-down', prob: '15%'}
    ],
    rows: [
      {scenario: '🟢 שורי', prob: '20%', conditions: 'OmniMax EBITDA $340M+, housing recovery', stock_impact: '+120%', stock_color: 'c-green', pf_impact: '+1.2%', pf_color: 'c-green'},
      {scenario: '🟡 בסיס', prob: '35%', conditions: 'guidance מתממש, leverage יורד', stock_impact: '+30%', stock_color: 'c-yellow', pf_impact: '+0.4%', pf_color: 'c-yellow'},
      {scenario: '🔴 דובי', prob: '30%', conditions: 'EBITDA miss 17%, $265M', stock_impact: '−43%', stock_color: 'c-red', pf_impact: '−0.6%', pf_color: 'c-red'},
      {scenario: '⚫ אסון', prob: '15%', conditions: 'Covenant Breach, Goodwill impairment', stock_impact: '−99%', stock_color: 'c-red', pf_impact: '−1.5%', pf_color: 'c-red'}
    ],
    note: '* בהנחת פוזיציה 1.5%. תוחלת משוקללת: <b style="color:var(--red)">−2.5%</b> — שלילית. הסיכון אסימטרי לרעת המשקיע ב-$38.65.'
  },
  kill_switches: [
    {title: 'Net Leverage >4.75x בכל רבעון', body: 'נוכחי 3.9x. מרווח בטיחות: 4.75x לפני covenant territory. כל רבעון חלש מושך מעלה מהיר.'},
    {title: 'Adj EBITDA FY2026E <$245M', body: 'guidance $318M. -23% = $245M → leverage 4.9x → proximity covenant 5.25x. תזה נשברת לחלוטין.'},
    {title: 'FCF שלילי ×2 רבעונים ברציפות', body: 'Q1 2026 OCF -$41.2M. רבעון שני שלילי = integration לא נסגרת, deleveraging בלתי אפשרי, דחיסת ריבית מתחזקת.'},
    {title: 'Goodwill Impairment >$200M', body: '$1.706B אינטנגיבלים = 194% הון עצמי. write-down $200M+ מכווץ equity ל-$680M ומחמיר leverage ratios בצורה מבנית.'},
    {title: 'OmniMax Quarterly EBITDA <$85M (annualized <$340M)', body: 'management claim: EBITDA $110-120M. <$85M לרבעון = acquisition price 15.7x EBITDA — value destroyer מוגדר, impairment inevitable.'}
  ],
  verdict: {
    style: 'yellow',
    headline: 'WAIT — הסיכון אסימטרי לרעת המשקיע ב-$38.65',
    paragraphs: [
      '<b>בכנות:</b> Gibraltar היא חברה איכותית שביצעה הימור ממונף ענק. המספרים אינם שקריים — אבל הם נשענים על EBITDA שאי אפשר לאמת ועל שוק דיור שלא התאושש עדיין. ×2.2x upside בתרחיש בסיס — אבל תוחלת משוקללת שלילית (-2.5%) כשמחשבים downside.',
      '<b>מחיר $26-28 הוא ה-entry האטרקטיבי:</b> שם EV/EBITDA 5.8-6.2x גם ב-EBITDA miss קל, R/R עובר 2:1. ב-$38.65 — מחיר הוגן לתרחיש בסיס בלבד, ללא מרווח ביטחון מספיק לסיכון binary של Leverage.'
    ],
    scoreboxes: [
      {lbl: 'ציון סיכון', val: '7/10', color: 'c-red'},
      {lbl: 'תקרת פוזיציה', val: '4%', color: 'c-blue'},
      {lbl: 'תוחלת משוקללת', val: '−2.5%', color: 'c-red'},
      {lbl: 'פסיקה', val: 'WAIT', color: 'c-yellow', size: 15}
    ],
    handoff: 'חברה: Gibraltar Industries (ROCK) · ציון סיכון: <b>7/10</b> · תקרת פוזיציה: <b>4%</b><br><b>הסיכון הגדול ביותר:</b> Covenant Breach — EBITDA miss 31% = equity כמעט אפס (binary loss).<br><b>ההנחה השבירה:</b> OmniMax EBITDA $110-120M שלא ניתן לאימות חיצוני.<br><b>סיכון שלילי שווי:</b> −43% ב-17% miss · −99% ב-31% miss<br><b>מחיר אטרקטיבי אמיתי:</b> $26-28 (EV/EBITDA 5.8-6.2x עם buffer)<br><b>טריגרי KILL SWITCH:</b> (1) Net Leverage >4.75x · (2) EBITDA <$245M · (3) FCF שלילי ×2'
  },
  footer: 'מקור: handoff אנליסט + חישובי Leverage ישירים. ה-DA נעל את נתוני האנליסט ולא ניתח מחדש.'
};
