window.AGENT_DATA = {
  ticker:'NOW', company:'ServiceNow Inc.', date:'24 במאי 2026',
  fair_value:120, bear_price:80,
  inherited:[
    {icon:'✅',text:'<b>אנליסט:</b> איכות 8.0/10 · שווי הוגן בסיס $120 / שורי $143'},
    {icon:'✅',text:'<b>שטן:</b> סיכון 6/10 · תקרה 8% · סיכון שלילי −20% ל-$80'},
    {icon:'✅',text:'<b>CEO:</b> APPROVED WITH CONDITIONS · 5% · Growth · בתנאי איזון IBIT'},
    {icon:'✅',text:'<b>נתוני ביצוע:</b> גרפים חיים דרך השרת'}
  ],
  technical_cards:[
    {lbl:'מחיר נוכחי',val:'$99.69',color:'c-orange',id:'ind-price',sub:'52W: $81–$211'},
    {lbl:'מהשיא',val:'−53%',color:'c-red',sub:'ירידה משמעותית'},
    {lbl:'מהשפל',val:'+22%',color:'c-green',sub:'קרוב לשפל'},
    {lbl:'משטר שוק',val:'Risk-On',color:'c-green',sub:'VIX 17.4 · S&P מעל 200DMA'},
    {lbl:'דוח הבא',val:'~67 ימים',color:'c-green',sub:'Q2 FY26 (~אוגוסט)'},
    {lbl:'Beta היסטורי',val:'~1.4',sub:'SaaS תנודתי'}
  ],
  filters:{
    description:'7 מתוך 8 עוברים. דגל אחד צהוב — סכין נופלת (לכן Scale In).',
    tiles:[
      {icon:'📅',name:'תזמון דוח',badge:'עבר',val:'~67 ימים',detail:'דוח Q2 רחוק — חופש לפעולה.'},
      {warn:true,icon:'🔪',name:'סכין נופלת',badge:'סומן',val:'−53% מהשיא · −17% בדוח',detail:'לא FOMO — ההפך. דורש <b>Scale In</b>.'},
      {icon:'📊',name:'RSI',badge:'עבר',val:'לחיתוך חי',detail:'סביר באזור 35–45 — לא קנייתֵר.'},
      {icon:'📏',name:'הרחבה מעל 50DMA',badge:'עבר',val:'מתחת ל-50DMA',detail:'לא מורחב כלפי מעלה.'},
      {icon:'📦',name:'נפח',badge:'N/A',val:'אין פריצה לאשר',detail:'קונים חולשה, לא פריצה.'},
      {icon:'🌐',name:'משטר שוק',badge:'Risk-On',val:'VIX 17.4',detail:'תומך — אך מתון עם SaaS במורד.'},
      {icon:'💰',name:'שווי בכניסה',badge:'אטרקטיבי',val:'$100 מול $120',detail:'−17% מתחת לבסיס. <b>שונה מ-Visa.</b>'},
      {icon:'⚖️',name:'סיכון/תשואה',badge:'עבר',val:'2.2 : 1',detail:'חוצה את סף 2:1 <b>כבר במחיר נוכחי</b>.'}
    ]
  },
  rr:{
    description:'תשואה לשווי בסיס ($120) או שורי ($143); סיכון לתרחיש דובי ($80).',
    bars:[
      {label:'🟢 תשואה — אל $120 (בסיס)',pct:'+20%',color:'c-green',width:50,bg:'green',dollar:'+$20'},
      {label:'🟢 תשואה — אל $143 (שורי)',pct:'+43%',color:'c-green',width:100,bg:'green',dollar:'+$43'},
      {label:'🔴 סיכון — אל $80 (דובי שטן)',pct:'−20%',color:'c-red',width:46,bg:'red',dollar:'−$20'}
    ],
    verdict:{style:'green',headline:'R/R = 43.5 ÷ 19.7 = 2.21 : 1',body:'· עובר את סף ה-2:1 כבר במחיר הנוכחי. בטראנשים נמוכים — R/R משתפר דרמטית. <b>זוהי הסיבה שהפסיקה Scale In ולא Wait.</b>'}
  },
  verdict:{
    style:'green',
    headline:'✅ Scale In — המתמטיקה עובדת, המבנה מחייב הדרגתיות',
    paragraphs:[
      'בניגוד ל-Visa שקיבלה "המתן" — NOW עוברת את <b>כל המבחנים המספריים</b>. R/R 2.2:1, שווי אטרקטיבי, משטר תומך, דוח רחוק. <b>אך</b> — מניה שירדה 53% היא <b>סכין נופלת</b>. ההגנה: Scale In עם תמיכות מבניות.'
    ],
    scoreboxes:[
      {lbl:'פסיקה',val:'Scale In',color:'c-green',size:15},
      {lbl:'איכות כניסה',val:'7/10',color:'c-green'},
      {lbl:'R/R נוכחי',val:'2.2:1',color:'c-green'},
      {lbl:'ביטחון',val:'בינוני-גבוה',color:'c-yellow',size:15}
    ]
  },
  plan:{
    description:'גודל פוזיציה מאושר ע"י CEO: <b>5% מהתיק (~$96 בתיק $1,924)</b>. ניתן לעדכן בשדה למטה. T1 ניתן לביצוע מיידי.',
    cash:96,
    cash_hint:'5% מתיק ~$1,924 · מחולק 40/30/30',
    levels:{
      t1:{price:100,pct:40,name:'כניסה 1',color:'#f5c842'},
      t2:{price:90,pct:30,name:'כניסה 2',color:'#2ecc71'},
      t3:{price:82,pct:30,name:'כניסה 3',color:'#2ecc71'},
      stop:{price:75,name:'סטופ-לוס',color:'#e05c5c'},
      tp1:{price:130,name:'TP1 — בסיס',color:'#4da6ff'},
      tp2:{price:155,name:'TP2 — שורי',color:'#a78bfa'}
    },
    rationale:{
      t1:'מחיר נוכחי. R/R כבר 2.2:1 — עובר את הסף. כניסה ראשונית 40% מיידית.',
      t2:'תמיכה עגולה $90, ~10% מתחת. אם נמשיך לרדת, רמת עצירה הגיונית. R/R שם ~5:1.',
      t3:'מעל שפל 52ש\' $81. כל הירידה כבר תומחרה. R/R קיצוני. 30% — כי שפל יכול להישבר.',
      stop:'מתחת לשפל 52ש\' = שבירת רצפה טכנית. סגירה יומית מתחת $75 = התזה השורית קרסה.',
      tp1:'שווי הוגן בסיס של האנליסט. לקיחת רווח חלקית.',
      tp2:'התרחיש השורי — חזרה למכפיל סביר. ~50% מהדרך לשיא 52ש\'.'
    },
    support_resistance:[
      {p:81,l:'תמיכה · שפל 52ש $81'},
      {p:143,l:'התנגדות · יעד אנליסטים $143'}
    ]
  },
  handoff:'חברה: ServiceNow (NOW) · <b>פסיקה:</b> Scale In · <b>איכות:</b> 7/10 · <b>R/R:</b> 2.2:1<br><b>תוכנית:</b> T1 40% ב-$100 (מיידי) · T2 30% ב-$90 (תמיכה) · T3 30% ב-$82 (שפל 52ש\')<br><b>סטופ:</b> $75 · <b>TP:</b> $130 / $155<br><b>סיכון:</b> מניה ב-downtrend עלולה לחתוך גם את $75.',
  footer:'מקור: גרפים — Yahoo Finance דרך שרת הדשבורד. רמות תוכנית מבוססות S/R + R/R.'
};
