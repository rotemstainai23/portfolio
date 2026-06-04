window.AGENT_DATA = {
  ticker:'IBM', company:'International Business Machines Corp.', date:'2 ביוני 2026',
  inherited:{
    items:[
      {k:'מחיר נוכחי',v:'$320.42'},
      {k:'שווי הוגן (בסיס)',v:'$310 (−3%)'},
      {k:'שווי הוגן (דובי)',v:'$235 (−26%)'},
      {k:'ציון איכות',v:'7.5/10'},
      {k:'P/E TTM',v:'~27x'},
      {k:'FCF adj / std',v:'$14.7B / $12.1B ⚠️'},
      {k:'חוב נטו',v:'$51B'},
      {k:'Software ARR',v:'$23.6B'}
    ],
    note:'ההנחה השבירה: ש-8% צמיחת 2025 מבנית. המתקפה תתמקד כאן — ובפער FCF adj/std.'
  },
  attack:{
    headline:'הריצה של +26% בשבוע היא לא מומנטום — היא FOMO על פיק מחזורי שמתהפך',
    paragraphs:[
      'הסיפור שמספרים השוורים: "IBM בטרנספורמציה, Software ARR גדל, דיבידנד בטוח". הסיפור שעורך הדין השטן רואה: <b>אתה משלם 27x P/E על צמיחה שחלקה הגדול ארעי.</b> IBM Z עלתה +67% ב-Q4 2025 ו-+51% ב-Q1 2026 — ואת ה-Infrastructure הזה ההנהלה עצמה מנחה לרדת ב-2026. <span class="punch">מה נשאר? Consulting שגדל 1-4% ו-Software שגדל 10%.</span> תמחור בסיס ריאלי: 2-4% צמיחה, לא 8%.',
      '<b>הדגל הכי מדאיג שהאנליסט חישב אך לא דגיש מספיק:</b> FCF standard $12.7B→$12.4B→$12.1B — <b>יורד</b> שלוש שנים, בזמן שהכנסות עלו $5.6B. חברה שמגדילה מכירות 9% ולא מצליחה להגדיל מזומן = מבנה עלויות/הון חוזר שמכרסם. <span class="punch">הנרטיב כולו נשען על FCF adjusted שהפסיקה $2.6B מ-standard. שני המספרים לא יכולים להיות נכונים.</span>',
      'הסיכון הנסתר שרוב המשקיעים מתעלמים ממנו: <b>IBM היא מלכודת ערך מחופשת ל-AI play.</b> GenAI book מפסיק להיות מדווח בנפרד מ-2026. אם המספר הזה היה מרשים — היו ממשיכים לדווח. כשהשוק יבין ש-IBM לא AI winner אלא legacy IT במכפיל מנופח, <b>de-rating מ-27x ל-18x = -33% גם בלי שינוי ברווחים.</b>'
    ]
  },
  risk_scorecard:{
    description:'הוגנות: IBM היא עסק יציב ורווחי. הסיכון אינו בקיום החברה — הוא בתמחור מלא על בסיס צמיחה ארעית.',
    items:[
      {lbl:'שבירות תזה',val:'🔴 גבוהה',color:'red',note:'נשענת על 8% צמיחה מחזורית + FCF adj מנופח'},
      {lbl:'סיכון עסקי',val:'🟡 בינוני',color:'yellow',note:'Software חזק; Consulting סחורתי; Infrastructure מחזורי'},
      {lbl:'סיכון פיננסי',val:'🔴 גבוה',color:'red',note:'FCF std יורד, חוב $64.6B, פער adj/std גדל'},
      {lbl:'סיכון שווי',val:'🔴 גבוה',color:'red',note:'27x על פיק; 0% upside בסיס; downside -37%'},
      {lbl:'סיכון מאקרו',val:'🟡 בינוני',color:'yellow',note:'IT spending + ריבית גבוהה לחוב $64.6B'},
      {lbl:'סיכון אירוע',val:'🔴 גבוה',color:'red',note:'Q2 2026 בלי GenAI book; השוואת מיינפריים קשה'}
    ]
  },
  valuation_risk:{
    description:'EPS TTM מרומז ~$11.80 (מחיר $320 / P/E 27x). גם בלי שינוי ברווח — de-rating בלבד.',
    scenarios:[
      {price:'$320',height:100,pct:'0%',lbl:'נוכחי',sub:'~27x TTM',color:'c-blue',bg:'blue'},
      {price:'$283',height:88,pct:'−11%',lbl:'de-rating קל',sub:'~24x',color:'c-yellow',bg:'yellow'},
      {price:'$236',height:74,pct:'−26%',lbl:'היסטורי IBM',sub:'~20x TTM',color:'c-orange',bg:'orange'},
      {price:'$191',height:60,pct:'−40%',lbl:'legacy IT + EPS −10%',sub:'18x · $10.62',color:'c-red',bg:'red'}
    ],
    note:'<b>זו לא תחזית — זו מתמטיקה של רגישות.</b> IBM נסחרה ב-16-20x P/E היסטורית. <b>חזרה לנורמל = -26% עד -40%.</b> "דיבידנד בטוח" לא מגן על הון מ-de-rating.'
  },
  stress_test:{
    description:'הסתברויות מעוגנות: פרמיית מחיר 27x + FCF std יורד תומכים בדובי; Software ARR חזק תומך בבסיס; אסימטריה שלילית.',
    gradient:'var(--yellow) 0 35%,var(--red) 35% 73%,#6b1a1a 73% 100%',
    scenarios:[
      {color:'var(--green)',name:'🟢 שורי — Software מאיץ, קוונטום, re-rating ל-26x',prob:'15%'},
      {color:'var(--yellow)',name:'🟡 בסיס — Software +10%, מיינפריים מתקרר, מכפיל יציב',prob:'35%'},
      {color:'var(--red)',name:'🔴 דובי — מיינפריים קורס, de-rating ל-18-20x',prob:'38%'},
      {color:'#6b1a1a',name:'⚫ אסון — FCF std < $11B + חיתוך דיבידנד',prob:'12%'}
    ],
    rows:[
      {scenario:'🟢 שורי',prob:'15%',conditions:'Software מאיץ, re-rating ל-26x',stock_impact:'+25%',stock_color:'c-green',pf_impact:'+1.5%',pf_color:'c-green'},
      {scenario:'🟡 בסיס',prob:'35%',conditions:'Software +10%, מיינפריים מתקרר',stock_impact:'−2.5%',stock_color:'c-yellow',pf_impact:'−0.3%',pf_color:'c-yellow'},
      {scenario:'🔴 דובי',prob:'38%',conditions:'מיינפריים מתהפך, de-rating',stock_impact:'−30%',stock_color:'c-red',pf_impact:'−1.8%',pf_color:'c-red'},
      {scenario:'⚫ אסון',prob:'12%',conditions:'FCF ≤ $11B, חיתוך דיבידנד',stock_impact:'−45%',stock_color:'c-red',pf_impact:'−2.7%',pf_color:'c-red'}
    ],
    note:'* בהנחת פוזיציה 6% אילוסטרטיבית. תוחלת משוקללת: <b style="color:var(--red)">−13.7%</b> — שלילית מובהקת.'
  },
  kill_switches:[
    {trigger:'FCF standard < $11.5B שנתי',action:'יציאה מיידית — FCF אמיתי קרס'},
    {trigger:'הכנסות Infrastructure −10% YoY ברבעון',action:'פיק מחזורי אושר — יציאה'},
    {trigger:'חיתוך/הקפאת דיבידנד ($1.69/רבעון)',action:'יציאה מיידית — סיגנל FCF חמור'},
    {trigger:'חוב ברוטו > $70B',action:'מינוף יוצא משליטה — צמצם'},
    {trigger:'Guidance FY2026 צמיחה < 3%',action:'תזה מבנית הופרכה — יציאה'},
    {trigger:'IBM Z YoY שלילי לשני רבעונים',action:'אישור מחזוריות — יציאה'}
  ],
  verdict:{
    style:'red',
    headline:'🔴 סיכון גבוה — תוחלת שלילית של −13.7%',
    body:'0% upside בתרחיש הבסיס מול downside −33% עד −41%. FCF standard יורד 3 שנים. פיק מחזורי מתהפך. המחיר מגלם כבר את כל החדשות הטובות.',
    scoreboxes:[
      {lbl:'ציון סיכון',val:'7.5/10',color:'c-red',size:15},
      {lbl:'תוחלת',val:'−13.7%',color:'c-red'},
      {lbl:'גודל מקסימלי',val:'0–2.5%',color:'c-red'},
      {lbl:'פסיקה',val:'סיכון גבוה',color:'c-red',size:14}
    ],
    handoff:'חברה: IBM · תאריך: 2.6.2026<br><b>ציון סיכון:</b> 7.5/10 (גבוה) · <b>סיכון שלילי:</b> −33% עד −41% · <b>תוחלת:</b> −13.7%<br><b>הסיכון הגדול:</b> מלכודת ערך מחזורית — 27x P/E על פיק מיינפריים<br><b>Kill Switches:</b> FCF std <$11.5B · Infrastructure −10% YoY<br><b>גודל מקסימלי:</b> 0% (מומלץ) / 2.5% (תקרה)'
  },
  footer:'מקור: נתוני דשבורד אנליסט (ירושה). לא ניתחתי מחדש — תקפתי את המסקנות.'
};
