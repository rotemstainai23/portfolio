// CLAUDE-AUTO-GENERATED — מחק שורה זו כדי לנעול את הקובץ מפני דריסה
window.AGENT_DATA = {
  ticker: 'ROCK',
  company: 'Gibraltar Industries',
  date: '2026-06-01',
  fair_value: 50,
  bear_price: 22,
  inherited: [
    {icon: '✅', text: '<b>אנליסט:</b> ציון 6/10 · שווי הוגן בסיס $49-52 · שורי $82-85 · דובי $12-15'},
    {icon: '✅', text: '<b>שטן:</b> ציון סיכון 7/10 · תקרה 4% · downside -43% ב-miss 17% · entry אטרקטיבי $26-28'},
    {icon: '✅', text: '<b>CEO:</b> WAIT · גודל 0% עכשיו (2% לאחר תנאים) · שכבה: Speculation'},
    {icon: '⚠️', text: '<b>נתוני ביצוע:</b> לא הוזנו — ניתוח R/R מבוסס נתוני handoff בלבד. גרף חי נטען מהשרת.'}
  ],
  technical_cards: [
    {lbl: 'מחיר נוכחי', val: '$38.65', color: 'c-orange', sub: '52W: ~$30–$75.08'},
    {lbl: 'מהשיא', val: '−49%', color: 'c-red', sub: 'ירידה חדה מהשיא'},
    {lbl: 'Net Leverage', val: '3.9x', color: 'c-red', sub: 'Covenant max 5.25x'},
    {lbl: 'EBITDA Guided', val: '$318M', color: 'c-yellow', sub: 'Midpoint FY2026E'},
    {lbl: 'דוח הבא', val: 'Q2 2026', color: 'c-yellow', sub: 'אוגוסט 2026 (est.)'},
    {lbl: 'R/R נוכחי', val: '0.71:1', color: 'c-red', sub: 'מתחת לסף 2:1'}
  ],
  filters: {
    description: '2 מתוך 7 פילטרים עוברים. R/R שובר את הפילטר הבסיסי ביותר — לא ניתן להמשיך לביצוע ב-$38.65.',
    tiles: [
      {icon: '📅', name: 'תזמון דוח', badge: 'אזהרה', val: 'Q2 — אוגוסט 2026', warn: true, detail: 'דוח Q2 הוא moment of truth לכל התזה. כניסה לפני = ספקולציה ללא confirmation על OmniMax.'},
      {icon: '⚖️', name: 'סיכון/תשואה', badge: 'נכשל', val: '0.71:1', warn: true, detail: '<b>שובר פילטר.</b> R/R בסיס = 0.71:1 — מתחת לסף 2:1. מחיר כניסה ל-2:1: ~$26-28.'},
      {icon: '🏗️', name: 'מבנה תיק', badge: 'נכשל', val: 'Spec 16.3%', warn: true, detail: '<b>שובר פילטר.</b> ספקולציה 16.3% (יעד 10%). CEO אסר כניסה ללא קיצוץ IBIT קודם.'},
      {icon: '📊', name: 'RSI', badge: 'N/A', val: 'נתון חסר', detail: 'נתוני ביצוע לא הוזנו. נדרש לפני כניסה — oversold יכול לשפר timing.'},
      {icon: '📏', name: '20/50/200 DMA', badge: 'N/A', val: 'נתון חסר', detail: 'נדרש לקיבוע רמות כניסה מדויקות ואישור מגמה.'},
      {icon: '💰', name: 'שווי בכניסה', badge: 'הוגן בלבד', val: '$38.65 מול $50', detail: 'לא bargain. הוגן לבסיס. מחיר אטרקטיבי: $26-28 (EV/EBITDA 5.8-6.2x עם buffer).'},
      {icon: '🌐', name: 'משטר שוק', badge: 'OK', val: 'Risk-On', detail: 'משטר שוק תומך כללית. לא שיקול מכריע ב-ROCK — leverage-driven בעיקרו.'}
    ]
  },
  rr: {
    description: 'R/R מחושב על בסיס נתוני handoff: שווי הוגן בסיס $50.5 (midpoint $49-52); תרחיש דובי $22 (DA — EBITDA miss 17%). ב-$38.65 — R/R שובר את הסף המינימלי.',
    bars: [
      {label: '🟢 תשואה — אל $50.5 (בסיס)', pct: '+30.7%', color: 'c-green', width: 48, bg: 'green', dollar: '+$11.85'},
      {label: '🟢 תשואה — אל $83 (שורי)', pct: '+114.7%', color: 'c-green', width: 100, bg: 'green', dollar: '+$44.35'},
      {label: '🔴 סיכון — אל $22 (דובי, EBITDA miss 17%)', pct: '−43.1%', color: 'c-red', width: 67, bg: 'red', dollar: '−$16.65'}
    ],
    verdict: {style: 'red', headline: 'R/R = 30.7 ÷ 43.1 = 0.71:1 — נכשל בסף 2:1', body: '· ב-$38.65 הבסיס לא מספיק לכסות את הסיכון. כניסה ל-R/R=2:1 דורשת מחיר ~$26-28. בתרחיש שורי בלבד ($83) R/R = 2.66:1 — אבל תלוי בתרחיש שהוערך ב-20% הסתברות.'}
  },
  verdict: {
    style: 'yellow',
    headline: 'WAIT — R/R נכשל, מבנה תיק לא מאפשר, Q2 לא אושר',
    paragraphs: [
      'שלושה פילטרים נשברים בו-זמנית: <b>R/R 0.71:1</b> (מתחת לסף 2:1), <b>שכבת ספקולציה 16.3%</b> (פי 1.6 מהתקרה), <b>Q2 2026 טרם פורסם</b> (moment of truth לתזה כולה). מחיר כניסה לR/R=2:1: <b>≈$26-28</b>. תוכנית מותנית למטה — תופעל רק אם תנאים מתממשים.'
    ],
    scoreboxes: [
      {lbl: 'פסיקה', val: 'WAIT', color: 'c-yellow', size: 15},
      {lbl: 'R/R נוכחי', val: '0.71:1', color: 'c-red'},
      {lbl: 'R/R נדרש', val: '2:1', color: 'c-blue'},
      {lbl: 'Entry אטרקטיבי', val: '$26-28', color: 'c-green', size: 14}
    ]
  },
  plan: {
    description: '<b>תוכנית מותנית</b> — תופעל רק אם: (1) Q2 2026 לא miss, (2) IBIT קוצץ ל-4%, (3) מחיר ≤$35. עד אז: WAIT. רמות הכניסה להלן אינדיקטיביות — יידוקנו בביצוע עם DMA ו-ATR.',
    cash: 40,
    cash_hint: '2% מתיק ~$1,986 · חלוקה 50/50 · תלוי בתנאים',
    levels: {
      t1: {price: 35, pct: 50, name: 'כניסה 1', color: '#f5c842'},
      t2: {price: 27, pct: 50, name: 'כניסה 2', color: '#2ecc71'},
      stop: {price: 22, name: 'סטופ-לוס', color: '#e05c5c'},
      tp1: {price: 50, name: 'TP1 — בסיס', color: '#4da6ff'},
      tp2: {price: 83, name: 'TP2 — שורי', color: '#a78bfa'}
    },
    rationale: {
      t1: 'כניסה ראשונה ב-$35 — לאחר Q2 confirmation + IBIT trim. R/R שם ~2.1:1 לבסיס. 50% מהפוזיציה.',
      t2: 'כניסה שנייה ב-$27 = מחיר אטרקטיבי אמיתי לפי DA. R/R ~3:1 לבסיס. 50% מהפוזיציה.',
      stop: 'מתחת ל-$22 = תרחיש דובי DA מתממש (EBITDA miss 17%). equity destruction territory — יציאה מיידית.',
      tp1: 'שווי הוגן בסיס אנליסט $49-52. לקיחת רווח חלקי (50% מהפוזיציה).',
      tp2: 'תרחיש שורי. חזרה ל-EV/EBITDA 11x עם deleveraging מוצלח. יציאה מלאה.'
    },
    support_resistance: [
      {p: 22, l: 'תמיכה · תרחיש דובי DA — EBITDA miss 17%'},
      {p: 50, l: 'התנגדות · שווי הוגן בסיס אנליסט'}
    ]
  },
  handoff: 'חברה: Gibraltar Industries (ROCK) · <b>פסיקה:</b> WAIT · <b>R/R נוכחי:</b> 0.71:1 (נכשל)<br><b>מחיר כניסה לR/R=2:1:</b> ~$26-28<br><b>תנאים לכניסה:</b> Q2 לא miss + IBIT trim + מחיר ≤$35<br><b>סטופ:</b> $22 · <b>TP:</b> $50 / $83<br><b>סיכון:</b> Covenant Breach = equity כמעט אפס — סיכון binary, לא חלקי.',
  footer: 'מקור: נתוני handoff מהשרשרת. גרף — Yahoo Finance דרך שרת הדשבורד. תוכנית אינדיקטיבית — תידוקן עם DMA+ATR בכניסה.'
};
