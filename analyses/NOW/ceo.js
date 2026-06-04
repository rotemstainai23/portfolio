window.AGENT_DATA = {
  ticker:'NOW', company:'ServiceNow Inc.', date:'24 במאי 2026',
  inherited:[
    {icon:'✅',text:'<b>אנליסט:</b> איכות 8.0/10 · שווי הוגן בסיס $120 / שורי $143 · מרווח ביטחון ✓'},
    {icon:'✅',text:'<b>שטן:</b> סיכון 6/10 · תקרת פוזיציה 8% · הסיכון העיקרי — איום AI מבני'},
    {icon:'✅',text:'<b>תמונת תיק:</b> סה"כ ~$1,924 · מזומן 3.7% · AI/Tech 75% · IBIT 11% (חורג מתקרה)'}
  ],
  layer_fit:{
    description:'NOW = צמיחה דו-ספרתית גבוהה עם FCF חזק → <b>שכבת Growth</b>. בודקים אם זה משפר או מחמיר את המבנה.',
    headers:['שכבה','קיים','יעד','סטטוס','השפעת הוספת NOW (5%)'],
    rows:[
      {layer:'🛡️ Stability',current:'31.1%',target:'25–35%',status:'🟢 תקין',status_class:'s-ok',impact:'ללא שינוי'},
      {layer:'🚀 Growth',current:'47.8%',target:'55–65%',status:'🔴 חסר ~10%',status_class:'s-bad',impact:'↑ ל-52.8% — מתקרב ליעד',impact_color:'c-green'},
      {layer:'🎲 Speculation',current:'17.4%',target:'5–10%',status:'🔴 פי 2',status_class:'s-bad',impact:'ללא שינוי (טיפול נפרד)'},
      {layer:'💵 Cash',current:'3.7%',target:'5–10%',status:'🟡 דק',status_class:'s-warn',impact:'↓ ל-—2% (לא ריאלי)',impact_color:'c-red'}
    ],
    note:'<b>הוספה ל-Growth עקרונית טובה</b> — מתקרב ליעד. אך <b>אין מזומן פנוי</b> — חייבים לקצץ. <b>קיצוץ IBIT</b> (11% → 4%) משחרר ~$135.'
  },
  concentration:{
    description:'NOW אינה מניית שבבים אך כן <b>מציגה עצמה כ-AI</b>. חפיפה חלקית.',
    flags:[
      '<b>🟡 חפיפה תמטית קיימת אך לא מלאה.</b> Visa הייתה גיוון אמיתי; NOW היא SaaS-ארגוני שמתחיל לכלול AI. הוספת 5% NOW מעלה Tech מ-75% ל-~78%.',
      '<b>⚠️ מבחן ההיגיון:</b> 3+ פוזיציות בעלות מאפיין משותף = דגל. בתיק יש כבר MSFT, GOOG, META — שלוש "Big Tech + AI" + NOW יהיה רביעית. דורש הצדקה.'
    ],
    note:'<b>הצדקה אפשרית:</b> NOW פועלת ב-SaaS-ארגוני — לֵבר שונה מ-Big Tech. <b>אותו עץ אבל ענף אחר.</b> סביר — אך אינו גיוון מובהק.'
  },
  opportunity_cost:{
    options:[
      {title:'חלופה 1: לקנות NOW (5% מהתיק = ~$96)',recommended:true,body:'תוחלת משוקללת לפי השטן: +5.5%. ציון איכות 8/10. מרווח ביטחון אמיתי. מתקן את חיסור Growth.'},
      {title:'חלופה 2: להוסיף לפוזיציה קיימת',body:'NVDA כבר 14.3% (מעל תקרה) — לא. MSFT/GOOG/META — תוספת קטנה אפשרית. AVGO/MU/VST — מעמיק ריכוז AI.'},
      {title:'חלופה 3: להחזיק מזומן',body:'~5% ריבית = ~$5/שנה על $96. בטוח אך אפסי. רלוונטי רק אם NOW לא עומדת בסף R/R — והיא עומדת.'},
      {title:'חלופה 4: לחכות לרעיון הבא',body:'Visa ממתינה ל-$287. אין אינדיקציה שתגיע. NOW כבר אטרקטיבית — חוסר פעולה = ויתור.'}
    ],
    verdict:'<b>פסיקה:</b> חלופה 1 — NOW — נותנת את התשואה הצפויה הטובה ביותר מותאמת לסיכון.'
  },
  behavioral:{
    biases:[
      {title:'FOMO',body:'🟢 לא רלוונטי — הקנייה <b>נגד</b> תנועת המחיר. אין רדיפה.'},
      {title:'Revenge Trade',body:'🟢 לא — אין הפסד אחרון לשחזר.'},
      {warn:true,title:'עיגון (Anchoring)',body:'🟡 <b>סיכון אמיתי.</b> עלול לעגן על השיא $211 ולחשוב "חזרה = +110%". האנליסט הניח שווי רק $120–143.'},
      {warn:true,title:'חיזוק נרטיב AI',body:'🟡 התיק עמוס AI — הקנייה עלולה להיראות "טבעית". הצדק <b>למה NOW</b>, לא רק "AI".'},
      {title:'סכין נופלת',body:'🟢 לא דגל פסיכולוגי — דגל טכני. ה-Executor יטפל ב-Scale In.'},
      {title:'ביטחון יתר',body:'🟢 הציון 8/10 ולא 10. השטן 6/10. אין יומרה.'}
    ],
    circuit_breaker:'<b>מפסק זרם:</b> 🟢 <b>לא הופעל.</b> אין FOMO, אין revenge, התזה ברורה, אין דחיפות.'
  },
  position_size:{
    description:'נוסחה: שכנוע × סיכון × התאמה. שכנוע גבוה + סיכון בינוני + התאמה חלקית.',
    constraints:[
      {constraint:'תקרת שכבה (Growth)',value:'<b>12%</b>',note:'מקסימום חוקתי'},
      {constraint:'תקרת שטן (סיכון 6)',value:'<b>8%</b>',note:'קובע — נמוך מהשכבה'},
      {constraint:'הפחתה בגין חפיפת AI',value:'<b>−2%</b>',note:'ריכוז תמטי בתיק'},
      {constraint:'הפחתה בגין חשיבת-עדר פוטנציאלית',value:'<b>−1%</b>',note:'הנחת AI לא הוטבעה'},
      {constraint:'<b>גודל מאושר סופי</b>',value:'<b class="c-green">5%</b>',note:'~$96 על תיק $1,924'}
    ]
  },
  verdict:{
    style:'green',
    headline:'✅ APPROVED WITH CONDITIONS · 5% מהתיק · בתנאי איזון מחדש',
    paragraphs:[
      'Visa קיבלה "המתן" כי המחיר לא נכון. <b>NOW מקבלת "אישור עם תנאים"</b> כי המחיר כן נכון, האיכות גבוהה, וההוספה ל-Growth מתקנת חיסור מבני.',
      '<b>שלושה תנאים מחייבים:</b><br>1️⃣ <b>איזון מחדש קודם:</b> קיצוץ IBIT מ-11% ל-~4% (משחרר ~$135). מתקן גם חריגת ספקולציה.<br>2️⃣ <b>Scale In בלבד:</b> ה-Executor יקבע מבנה טראנשים.<br>3️⃣ <b>פוזיציה 5%, לא יותר:</b> חפיפת AI לא מאפשרת לגדול ל-8%.'
    ],
    scoreboxes:[
      {lbl:'פסיקה',val:'APPROVED W/ COND',color:'c-green',size:13},
      {lbl:'גודל מאושר',val:'5%',color:'c-blue'},
      {lbl:'שכבה',val:'Growth',color:'c-blue',size:15},
      {lbl:'מפסק זרם',val:'לא הופעל',color:'c-green',size:14}
    ],
    handoff:'חברה: ServiceNow (NOW) · <b>החלטה:</b> APPROVED WITH CONDITIONS · <b>גודל:</b> 5% (~$96) · <b>שכבה:</b> Growth<br><b>סיבת ההחלטה:</b> מתקן חיסור Growth, איכות 8/10, R/R אטרקטיבי.<br><b>תנאי מקדים:</b> איזון IBIT (11% → 4%) למימון.<br><b>הטיה לעקוב:</b> עיגון על שיא $211.<br><b>פסיקה צפויה ל-Executor:</b> Scale In — לא Buy Now.'
  },
  footer:'מקור: handoff אנליסט + handoff שטן + טבלת תיק. ה-CEO לא ניתח מחדש.'
};
