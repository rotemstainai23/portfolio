window.AGENT_DATA = {
  ticker:'IBM', company:'International Business Machines Corp.', date:'2 ביוני 2026',
  inherited:[
    {icon:'✅',text:'<b>אנליסט:</b> איכות 7.5/10 · שווי הוגן בסיס $310 / שורי $420 · 0% upside במחיר נוכחי'},
    {icon:'✅',text:'<b>שטן:</b> סיכון 7.5/10 · תוחלת −13.7% · תקרת פוזיציה 0-2.5% · downside −37%'},
    {icon:'✅',text:'<b>תמונת תיק:</b> סה"כ ~$1,999 · Growth 49.9% (נמוך) · Speculation 16% (גבוה) · Cash 3.6%'}
  ],
  layer_fit:{
    description:'IBM = Stability במהותה (דיבידנד, mature-tech, Beta 0.67). <b>בודקים אם יש מקום.</b>',
    headers:['שכבה','קיים','יעד','סטטוס','השפעת הוספת IBM (5%)'],
    rows:[
      {layer:'🛡️ Stability',current:'30.5%',target:'25–35%',status:'🟢 ביעד',status_class:'s-ok',impact:'↑ ל-35.5% — מעבר לגבול עליון',impact_color:'c-red'},
      {layer:'🚀 Growth',current:'49.9%',target:'55–65%',status:'🔴 חסר ~10%',status_class:'s-bad',impact:'ללא שינוי — IBM אינה Growth',impact_color:'c-red'},
      {layer:'🎲 Speculation',current:'16.0%',target:'5–10%',status:'🔴 פי 1.6',status_class:'s-bad',impact:'ללא שינוי (טיפול נפרד)'},
      {layer:'💵 Cash',current:'3.6%',target:'5–10%',status:'🟡 דק',status_class:'s-warn',impact:'↓ — מחמיר את חוסר המזומן',impact_color:'c-red'}
    ],
    note:'<b>Stability כבר ביעד.</b> הוספת IBM תדחוף אותה מעל הגבול העליון. Growth חסרה ~10% — IBM לא פותרת את הבעיה הנכונה.'
  },
  concentration:{
    description:'התיק כבר עמוס AI/Tech. IBM מוסיף שכבה רביעית של אותה חשיפה.',
    flags:[
      '<b>🔴 חפיפה גבוהה:</b> MSFT + GOOG + NVDA + META + AVGO + MU = 6 חשיפות AI/Tech/Cloud כבר בתיק. IBM מוסיף שביעית.',
      '<b>🔴 IBM = "MSFT-lite":</b> אותה חשיפת AI-enterprise כמו MSFT וגוג, בגרסה עם פחות צמיחה ופחות איכות.',
      '<b>⚠️ קורלציה ב-downside:</b> IBM ממותגת AI. ב-sell-off AI, תיפול יחד עם שאר התיק — אפס דיברסיפיקציה.',
      '<b>🟢 GLDM הוא ה-hedge האמיתי</b> — לא IBM. IBM רגישה לאותו מאקרו כמו שאר התיק.'
    ],
    note:'<b>מסקנה:</b> הוספת IBM מעמיקה ריכוז בדיוק הרגע שצריך לגוון. IBM אינה diversifier.'
  },
  opportunity_cost:{
    options:[
      {title:'חלופה 1: גזום Speculation + מלא מזומן (מומלץ)',recommended:true,body:'OKLO/APLD/IBIT מ-16% ל-~10%. משחרר ~$120-150. מתקן חוסר מזומן (3.6%→6%). פותר בעיה אמיתית של התיק.'},
      {title:'חלופה 2: הוסף ל-Growth קיים (NVDA/META)',body:'סוגר פער Growth מ-49.9% ל-55%+. NVDA וMETA צומחים מהר מ-IBM עם upside אמיתי. פותר בעיה אמיתית.'},
      {title:'חלופה 3: IBM (נדחה)',body:'0% upside בבסיס. מחמיר ריכוז AI. Stability כבר מלאה. תוחלת −13.7%. לא פותר בעיה כלשהי בתיק.'},
      {title:'חלופה 4: החזק מזומן',body:'3.6% ריבית נמוכה. אבל עדיף על IBM עם תוחלת −13.7%. המתנה לחלון תיקון.'}
    ],
    verdict:'<b>פסיקה:</b> חלופה 1 — גזום Speculation ומלא מזומן. לא IBM.'
  },
  behavioral:{
    biases:[
      {title:'FOMO',warn:true,body:'🔴 <b>סיכון גבוה.</b> IBM עלתה +26% בשבוע. הקנייה <b>רודפת</b> אחרי מומנטום — ב-93% מהשיא, RSI 89.8. קלאסיקה של FOMO.'},
      {title:'Narrative Bias',warn:true,body:'🔴 <b>גבוה מאוד.</b> סיפור "IBM GenAI turnaround" + "דיבידנד בטוח" מאוד מושך. אבל 8% צמיחה 2025 חלקית מחזורית. הסיפור מרגש יותר מהמספרים.'},
      {title:'Overconfidence',warn:true,body:'🟡 <b>בינוני.</b> FCF adj $14.7B נראה שיא — אבל FCF standard $12.1B יורד. קל לראות את המספר הגדול ולהתעלם מהקטן.'},
      {title:'Revenge Trade',body:'🟢 לא רלוונטי — אין הפסד קודם על IBM.'},
      {title:'עיגון',body:'🟢 נמוך. אין עיגון על מחיר קנייה קודם.'}
    ],
    circuit_breaker:'<b>מפסק זרם:</b> 🔴 <b>הופעל.</b> FOMO גבוה + Narrative Bias גבוה + תוחלת שלילית. השהייה מינימום 48 שעות.'
  },
  position_size:{
    description:'חישוב: שכנוע × סיכון × התאמה. כל שלושת הגורמים נגד.',
    constraints:[
      {constraint:'תקרת שכבה (Stability)',value:'<b>12%</b>',note:'מקסימום חוקתי'},
      {constraint:'תקרת שטן (סיכון 7.5)',value:'<b>2.5%</b>',note:'קובע — נמוך מהשכבה'},
      {constraint:'מכפיל upside אפסי (0%)',value:'<b>×0</b>',note:'0% upside = 0% גודל'},
      {constraint:'מפסק זרם הופעל',value:'<b>−100%</b>',note:'השהיה 48 שעות'},
      {constraint:'<b>גודל מאושר סופי</b>',value:'<b class="c-red">0%</b>',note:'לא להיכנס'}
    ]
  },
  verdict:{
    style:'red',
    headline:'❌ REJECTED — אל תקנה IBM במחיר הנוכחי',
    paragraphs:[
      'Stability כבר ביעד. IBM מגדיל ריכוז AI במקום לגוון. 0% upside בתרחיש הבסיס. מפסק זרם הופעל. <b>אין תרחיש שבו קנייה היום הגיונית.</b>',
      '<b>הפעולה הנכונה:</b><br>1️⃣ <b>גזום Speculation</b> מ-16% ל-~10% (OKLO/APLD/IBIT).<br>2️⃣ <b>מלא מזומן</b> מ-3.6% ל-5-7%.<br>3️⃣ <b>השלם Growth</b> ל-55%+ (NVDA/META).<br>IBM נשאר בחוץ — לא watchlist, לא כניסה חלקית.'
    ],
    scoreboxes:[
      {lbl:'פסיקה',val:'REJECTED',color:'c-red',size:13},
      {lbl:'גודל מאושר',val:'0%',color:'c-red'},
      {lbl:'שכבה',val:'Stability',color:'c-blue',size:15},
      {lbl:'מפסק זרם',val:'הופעל 🔴',color:'c-red',size:14}
    ],
    handoff:'חברה: IBM · <b>החלטה:</b> REJECTED · <b>גודל:</b> 0% · <b>שכבה:</b> Stability<br><b>סיבת הדחייה:</b> Stability מלאה, ריכוז AI מוגבר, 0% upside, FOMO גבוה.<br><b>פעולה במקום זאת:</b> גזום Spec 16%→10%, מלא Cash →6%, השלם Growth.<br><b>הטיה שזוהתה:</b> FOMO + Narrative Bias — גבוהים.'
  },
  footer:'מקור: handoff אנליסט + handoff שטן + טבלת תיק עדכנית. ה-CEO לא ניתח מחדש.'
};
