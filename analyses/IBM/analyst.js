window.AGENT_DATA = {
  ticker:'IBM', company:'International Business Machines Corp.', date:'2 ביוני 2026',
  sector:'NYSE · תוכנת ארגון / Hybrid Cloud / AI ארגוני',
  period:'FY2025 · רבעון אחרון Q1 FY2026',
  verification_banner:'פיננסים — stockanalysis.com · Q1 FY2026 — SEC 8-K + IBM Newsroom · 10-K/10-Q body נחסם (403), הוצלב דרך stockanalysis + הודעות רשמיות. סתירות מסומנות.',
  crash_banner:{title:'📈 IBM עלתה +26% תוך 5 ימים — RSI 89.8, 33% מעל ה-50DMA',
    body:'מניה שרצה פאראבולית אחרי פיק מחזור מיינפריים (IBM Z +67% Q4 2025). <b style="color:#e74c3c">זוהי נקודת הכניסה הגרועה ביותר האפשרית</b> — המחיר כבר בתקרת תרחיש הבסיס עם 0% upside. תפקיד הניתוח: לזהות האם מדובר בצמיחה מבנית אמיתית או רוח-גבית מחזורית.'},
  market_cards:[
    {lbl:'מחיר נוכחי',val:'$320.42',color:'c-red',sub:'+26% ב-5 ימים'},
    {lbl:'שווי שוק',val:'~$300B',sub:'~940M מניות'},
    {lbl:'P/E (TTM)',val:'~27x',sub:'Forward P/E: ~21-25x ⚠️'},
    {lbl:'טווח 52 שבועות',val:'$212–$328',color:'c-red',sub:'97.5% מהשיא'},
    {lbl:'FCF Yield',val:'4.29%',sub:'adj / std שונה ⚠️'},
    {lbl:'הכנסות FY25',val:'$67.5B',sub:'+7.6% YoY'}
  ],
  business_model:{
    description:'IBM היא <b>תשתית ה-IT הארגונית</b> של העולם — מריצה מערכות קריטיות בבנקים, ממשלות וביטוח. 4 מגזרים: <b>Software</b> (מנויים, Red Hat), <b>Consulting</b> (שירותים), <b>Infrastructure</b> (מיינפריים IBM Z), <b>Financing</b>. הלב: ARR $23.6B ב-Software — הכנסה חוזרת ויציבה.',
    engines_label:'מנועי הכנסה — FY2025',
    engines:[
      {label:'Software (ARR)',pct:100,color:'var(--blue)',val:'~$27B',growth:'+9% YoY — "שיא היסטורי"'},
      {label:'Consulting',pct:78,color:'var(--purple)',val:'~$20B',growth:'+1-4% YoY — צומח לאט'},
      {label:'Infrastructure',pct:65,color:'var(--orange)',val:'~$14B',growth:'+10% YoY — פיק מחזורי ⚠️'}
    ],
    revenue_mix:[
      {label:'Software (מנוי/ARR)',pct:40,val:'~$27B',color:'var(--blue)'},
      {label:'Consulting',pct:30,val:'~$20B',color:'var(--purple)'},
      {label:'Infrastructure',pct:20,val:'~$14B',color:'var(--orange)'},
      {label:'Financing + אחר',pct:10,val:'~$6.5B',color:'var(--green)'}
    ],
    note:'<b>Software ARR $23.6B</b> — הוכפל מאז רכישת Red Hat. Red Hat ARR ~$7.5B, OpenShift +30%. ה-recurring revenue גדל ומייצב. <b>הבעיה:</b> Infrastructure (מיינפריים) הוא 20% מהכנסות ומחזורי מאוד — פיק z17 ב-2025 צפוי להתהפך ב-2026.'
  },
  growth:{
    description:'צמיחת 2025 <b>חלקית מבנית, חלקית מחזורית</b> — Software מבנית, Infrastructure ארעית. ההנהלה מנחה Infrastructure לרדת ב-2026.',
    stats:[
      {lbl:'Software ARR 2026',val:'$25.9B+',growth:'▲ יעד +10% · נמשך',
        why:'<b>למה גדל:</b> Red Hat hybrid-cloud, Automation ו-Data האיצו. לקוחות קיימים מרחיבים מנויים ומוסיפים מודולי AI. <b>למה זה חשוב:</b> ARR הוא הכנסה עתידית מובטחת — מדד בריאות אמיתי של עסק ה-Software.'},
      {lbl:'FCF שנתי 2026',val:'$15.7B',growth:'▲ הנחיה +$1B YoY (adj)',
        why:'<b>אזהרה:</b> זהו FCF adjusted. FCF standard FY2025 היה $12.1B — <b>יורד</b> שנה שלישית ברצף. הפער $2.6B מוסבר ע"י התאמות שצמחו. <b>למה זה חשוב:</b> המספר שלא ניתן ל"התאמה" מראה שהמזומן האמיתי לא גדל.'},
      {lbl:'Software מרווח תפעולי',val:'+1pp',growth:'▲ הנחיה להתרחבות',
        why:'<b>למה מתרחב:</b> תמהיל מוצרים משתפר לכיוון Software רווחי. <b>אחזה:</b> Infrastructure יורד ב-2026 — יקצץ את התרומה המרווחית הגבוהה.'}
    ]
  },
  financials_3y:{
    description:'צמיחת 2025 האיצה ל-7.6% — הגבוהה ב-10 שנים. אך FCF standard שטוח/יורד, וחוב עלה $6B.',
    charts:[
      {title:'הכנסות נטו ($B)',foot:'↑ האצה ב-2025, חלקית מחזורית',bars:[
        {year:'FY23',label:'61.9',v:61.9,color:'var(--blue)'},
        {year:'FY24',label:'62.8',v:62.8,color:'var(--blue)',yoy:'+1.4%'},
        {year:'FY25',label:'67.5',v:67.5,color:'var(--blue)',yoy:'+7.6%'}
      ]},
      {title:'מרווח גולמי (%)',foot:'↑ מתרחב — תמהיל Software',bars:[
        {year:'FY23',label:'55.4',v:55.4,color:'var(--purple)'},
        {year:'FY24',label:'56.7',v:56.7,color:'var(--purple)',yoy:'+1.2pp'},
        {year:'FY25',label:'58.2',v:58.2,color:'var(--purple)',yoy:'+1.5pp'}
      ]},
      {title:'FCF adjusted ($B)',foot:'↑ עולה — אך adjusted',bars:[
        {year:'FY23',label:'11.2',v:11.2,color:'var(--green)'},
        {year:'FY24',label:'12.7',v:12.7,color:'var(--green)',yoy:'+13%'},
        {year:'FY25',label:'14.7',v:14.7,color:'var(--green)',yoy:'+16%'}
      ]},
      {title:'FCF standard ($B) ⚠️',foot:'🔴 שטוח/יורד — הדגל האמיתי',bars:[
        {year:'FY23',label:'12.7',v:12.7,color:'var(--red)'},
        {year:'FY24',label:'12.4',v:12.4,color:'var(--red)',yoy:'-2.4%'},
        {year:'FY25',label:'12.1',v:12.1,color:'var(--red)',yoy:'-2.4%'}
      ]},
      {title:'EPS מדולל GAAP ($)',foot:'* FY24 נמוך בגלל חיובים חד-פעמיים',bars:[
        {year:'FY23',label:'8.14',v:8.14,color:'var(--gold)'},
        {year:'FY24',label:'6.43',v:6.43,color:'var(--gold)',yoy:'-21%'},
        {year:'FY25',label:'11.17',v:11.17,color:'var(--gold)',yoy:'+74%'}
      ]},
      {title:'חוב נטו ($B)',foot:'🔴 עלה $7B ב-2 שנים — M&A',bars:[
        {year:'FY23',label:'46.5',v:46.5,color:'var(--red)'},
        {year:'FY24',label:'43.8',v:43.8,color:'var(--red)',yoy:'-6%'},
        {year:'FY25',label:'51.0',v:51.0,color:'var(--red)',yoy:'+16%'}
      ]}
    ],
    table:{
      headers:['מדד','FY2023','FY2024','FY2025','מגמה'],
      rows:[
        ['הכנסות','$61.9B','$62.8B','$67.5B','<span class="up">↑ האיץ</span>'],
        ['מרווח גולמי','55.45%','56.65%','58.19%','<span class="up">↑ מתרחב</span>'],
        ['מרווח תפעולי GAAP','16.64%','11.97%*','18.16%','<span class="warn">→ מעוות</span>'],
        ['FCF adj','$11.2B','$12.7B','$14.7B','<span class="up">↑ עולה (adjusted)</span>'],
        ['FCF standard','$12.7B','$12.4B','$12.1B','<span class="down">↓ יורד 3 שנים</span>'],
        ['EPS GAAP','$8.14','$6.43*','$11.17','<span class="warn">→ מעוות FY24</span>'],
        ['חוב נטו','$46.5B','$43.8B','$51B','<span class="down">↑ עולה ב-25</span>']
      ]
    },
    readout:[
      {metric:'הכנסות +7.6% FY2025',sig:'good',text:'<b>טוב — אך חלקית מחזורי.</b> Infrastructure (+21% Q4, IBM Z +67%) הוביל. Software +9% הוא המנוע המבני. ב-2026 Infrastructure צפוי לרדת.'},
      {metric:'מרווח גולמי 58.2% עולה',sig:'good',text:'<b>טוב.</b> תמהיל מוצרים מוסט ל-Software הרווחי. מגמה חיובית מבנית.'},
      {metric:'FCF adj $14.7B vs FCF std $12.1B',sig:'bad',text:'<b>דגל מבני.</b> הפער $2.6B גדל משנה לשנה. FCF standard — שלא ניתן לשנות — יורד 3 שנים ברצף בזמן שהכנסות עולות. איכות תזרים מתדרדרת.'},
      {metric:'חוב נטו עלה ל-$51B (+$7B)',sig:'bad',text:'<b>מגביל.</b> חוב ברוטו $64.6B. מממן M&A שמסתיר חוסר צמיחה אורגנית. Refinancing בסביבת ריבית גבוהה מכביד על FCF עתידי.'},
      {metric:'EPS GAAP $11.17 — קפיצה',sig:'warn',text:'<b>זהירות.</b> הקפיצה מ-$6.43 ל-$11.17 חלקית בגלל בסיס נמוך (FY24 חיובים חד-פעמיים). הנורמליזציה מציגה +37% — יותר מינים אבל לא הוכפל.'}
    ],
    note:'<b>קריאת אנליסט:</b> FCF standard יורד ($12.7B→$12.1B) בזמן הכנסות עולות (+$4.7B) — זוהי דיברגנציה של איכות רווח. ה"שיא הפיננסי" של 2025 נשען על FCF adjusted ועל פיק מיינפריים שמתהפך.'
  },
  moat:{
    description:'הליבה: <b>עלויות מעבר עצומות</b> — מיינפריים נעוץ בליבת בנקים/ממשלות + Red Hat היברידי.',
    items:[
      {label:'עלויות מעבר (מיינפריים/ארגוני)',score:90,color:'var(--green)',tag:'🟢 חזק מאוד — 60 שנה'},
      {label:'נכסים בלתי-מוחשיים (Red Hat/פטנטים)',score:85,color:'var(--green)',tag:'🟢 ARR $23.6B'},
      {label:'כוח מותג / אמון ארגוני',score:80,color:'var(--green)',tag:'🟢 "trusted enterprise"'},
      {label:'יתרון קנה-מידה',score:65,color:'var(--yellow)',tag:'🟡 גלובלי אך סחורתי'},
      {label:'אפקטי רשת (OpenShift ecosystem)',score:55,color:'var(--yellow)',tag:'🟡 open-source, חלש'},
      {label:'IP / קוונטום',score:45,color:'var(--yellow)',tag:'🟡 ספקולטיבי, 2029'},
      {label:'יתרון עלות',score:40,color:'var(--yellow)',tag:'🟡 Consulting סחורתי'},
      {label:'חסמים רגולטוריים',score:60,color:'var(--yellow)',tag:'🟡 FedRAMP / regulated'}
    ],
    note:'<b>מסקנת חפיר: מתחזקת — עם נקודת תורפה.</b> Software ARR + Red Hat מחזקים את ה-recurring moat. <b>האיום הגדול:</b> היפר-סקיילרים (AWS/Azure/GCP) מכרסמים ב-on-premise, ו-AI עלול לסחור את ה-Consulting.'
  },
  quarterly:{
    period:'Q1 FY2026 (הסתיים 31.3.2026)',
    description:'<b>Beat בכל מדד — אבל המניה נענשה.</b> השוק מתמחר פחד מהתהפכות מיינפריים.',
    cards:[
      {lbl:'הכנסות',val:'$15.9B',color:'c-green',sub:'▲ +9% YoY (+6% cc)',reasons:[
        '<b>Software +11% YoY</b> — מנוע עקבי ומבני, מאשר תזת ARR.',
        '<b>Infrastructure +15% YoY</b> — מחזור z17 עדיין תורם אך מתקרר (ירד מ-+21% ב-Q4).',
        '<b>Consulting +4% YoY</b> — התאוששות מ-+1% ב-Q4, אך עדיין חלש מול מתחרים.'
      ]},
      {lbl:'מרווח גולמי',val:'56.2%',color:'c-green',sub:'▲ +100bps YoY',reasons:[
        '<b>מיקס Software</b> — מגזר Software הרווחי יותר גדל מהר יותר ומרים את הממוצע.',
        '<b>משמעת עלויות</b> — IBM המשיכה לשפר יעילות תפעולית.',
        '<b>מגמה עקבית</b> — 55.4%→56.7%→58.2% (FY23-25), ו-Q1 26 מאשר.'
      ]},
      {lbl:'מרווח תפעולי',val:'13.4%',color:'c-green',sub:'▲ +140bps YoY',reasons:[
        '<b>מינוף תפעולי</b> — עלויות גדלות לאט מהכנסות.',
        '<b>Software dominance</b> — חלק גדל יותר מהכנסות מגיע ממגזר בעל מרווח גבוה.',
        '<b>ייצוב Consulting</b> — מגזר שהיה חלש ב-2024 חזר לרווחיות סבירה.'
      ]},
      {lbl:'IBM Z (מיינפריים)',val:'(בתוך Infrastructure +15%)',color:'c-yellow',sub:'⚠️ מתקרר מ-+67% Q4',reasons:[
        '<b>מחזור z17 ממשיך</b> — לקוחות ממשיכים לשדרג, אך הגל ראשוני עבר.',
        '<b>האצה התקררה</b> — +67% (Q4 2025) → +51% (Q1 2026) → צפוי לרדת עוד.',
        '<b>⚠️ סיגנל אזהרה:</b> ההנהלה מנחה Infrastructure לרדת low-single-digit ב-FY2026 כולו.'
      ]}
    ],
    note:'ב-Q1 2026 גם הנחיית FY2026 אושרה: Software +10%, FCF adj ~$15.7B, מרווח +1pp. <b>אבל:</b> Infrastructure ירד מהנחיה שנתית — השוק ענש על כך.'
  },
  stress_test:{
    categories:[
      {label:'א · מודל עסקי',score:8,color:'var(--green)',icon:'🟢'},
      {label:'ב · סיכון ושרשרת',score:7,color:'var(--yellow)',icon:'🟡'},
      {label:'ג · יושרה חשבונאית',score:8,color:'var(--green)',icon:'🟢'},
      {label:'ד · הנהלה והון',score:8,color:'var(--green)',icon:'🟢'},
      {label:'ה · יעילות תפעולית',score:7,color:'var(--yellow)',icon:'🟡'}
    ],
    total:38,
    summary:'<b style="color:var(--text)">סה"כ 38/50 — איכות בינונית-גבוהה.</b> עסק מבוסס ואמין, אך עם חשיפה מחזורית לחומרה ו-FCF standard שמעיד על איכות רווח מתדרדרת.'
  },
  red_flags:[
    {rank:'1',severity:'red',title:'🔴 פיק מחזורי מיינפריים — ההנחה הכי שברירית',body:'IBM Z +67% ב-Q4 2025 → +51% ב-Q1 2026 → ירידה צפויה. ההנהלה עצמה מנחה Infrastructure לרדת ב-2026. חלק ניכר מ"הצמיחה המהירה ביותר זה שנים" של 2025 היא ארעית, לא מבנית.'},
    {rank:'2',severity:'red',title:'🔴 FCF standard יורד 3 שנים ברצף',body:'$12.7B→$12.4B→$12.1B. כל הנרטיב נשען על FCF adjusted ($14.7B) שגדל ב-$2.6B מ-standard. הפער הולך וגדל — סימן שההתאמות מנופחות.'},
    {rank:'3',severity:'yellow',title:'🟡 חוב עלה ל-$64.6B (+$6B FY2025)',body:'מימן M&A (HashiCorp וכו\'). חוב נטו $51B. Refinancing בריבית גבוהה מכביד. FCF standard יורד + חוב עולה = ל-חץ בכיוון אחד.'},
    {rank:'4',severity:'yellow',title:'🟡 GenAI book מפסיק להיות מדווח בנפרד',body:'מ-2026 IBM לא תדווח GenAI book בנפרד. נרטיב השוק: "IBM AI winner". אם המספר היה מרשים — היו ממשיכים לדווח. הפסקת שקיפות = אות שלילי.'},
    {rank:'✓',severity:'green',title:'🟢 Software ARR $23.6B — מנוע מבני אמיתי',body:'הוכפל מאז Red Hat. +10% יעד ל-2026. FCF מ-Software גבוה. 3 מתוך 4 תת-מגזרים בצמיחה דו-ספרתית. זהו החפיר האמיתי.'}
  ],
  valuation:{
    description:'<b>0% upside בתרחיש הבסיס.</b> P/E ~27x על EPS שנמצא בפיק מחזורי. ה-de-rating הוא הסיכון, לא הרעה עסקית.',
    bear:{price:'$235',height:42,pct:'−26%',sub:'מיינפריים קורס, de-rating ל-18x'},
    base:{price:'$310',height:73,pct:'−3%',sub:'Software +10%, מכפיל יציב ~22x'},
    bull:{price:'$420',height:100,pct:'+31%',sub:'קוונטום/AI ממומש, 26x'},
    curline:'מחיר נוכחי: <b>$320</b> · שווי הוגן (בסיס): <b>$310</b> · שווי (שורי): <b>$420</b>',
    note:'<b>מרווח ביטחון: לא ❌</b> המחיר כבר בתקרת הבסיס. אסימטריה הפוכה: −26% downside מול −3% ל"בסיס". <b>פעם ראשונה בשרשרת שאנחנו רואים תוחלת שלילית.</b>'
  },
  final:{
    headline:'עסק איכותי · מחיר מלא · עם פיק מחזורי שמתהפך',
    paragraphs:[
      'IBM FY2025 הוא עסק בטרנספורמציה מוצלחת: Software ARR גדל, FCF שיא, מרווחים מתרחבים, Red Hat הוכפל. Arvind Krishna ביצע טרנספורמציה אמינה.',
      '<b>הבעיה אינה העסק — היא המחיר ו-התזמון.</b> חלק ניכר מהצמיחה של 2025 מחזורי (מיינפריים), המחיר מגלם 0% upside בבסיס, ו-RSI 89.8 אחרי +26% בשבוע. השאלה אינה "האם IBM עסק טוב" אלא "האם זהו הזמן ומחיר הכניסה הנכון".'
    ],
    scorecard:[
      {lbl:'איכות עסק',val:'7.5/10',color:'c-yellow'},
      {lbl:'חפיר',val:'8/10',color:'c-green'},
      {lbl:'יושרה חשבונאית',val:'8/10',color:'c-green'},
      {lbl:'הנהלה',val:'8/10',color:'c-green'},
      {lbl:'שווי / מחיר',val:'5/10',color:'c-red'},
      {lbl:'ציון כולל',val:'7.5/10',color:'c-yellow'}
    ],
    handoff:'חברה: IBM · מחיר $320 · שווי הוגן (בסיס) $310 · ציון איכות 7.5/10<br><b>ההנחה השבירה ביותר:</b> ש-8% צמיחת 2025 <b>מבנית</b> — בעוד ראיות (IBM Z +67%→פיק) מצביעות על מחזורית.<br><b>נתונים נעולים:</b> הכנסות $61.9/$62.8/$67.5B · FCF adj $11.2/$12.7/$14.7B · FCF std $12.7/$12.4/$12.1B<br><b>דגל אדום מרכזי:</b> FCF standard יורד 3 שנים בזמן שהכנסות עולות + פיק מיינפריים.'
  },
  competitors:{
    description:'IBM מובילה ב-hybrid-cloud + מיינפריים ארגוני; נחותה בצמיחה ומכפיל מול MSFT/GOOG',
    table:[
      {ticker:'IBM',name:'IBM',pe:27,ps:4.37,rev_growth:'7.6%',gross_margin:'58.2%',market_cap:'$300B',vs_company:'בסיס — recurring חזק, חפיר מיינפריים, חשיפה מחזורית'},
      {ticker:'ACN',name:'Accenture',pe:13.7,ps:1.79,rev_growth:'~5%',gross_margin:'30.3%',market_cap:'$112B',vs_company:'זול בהרבה, צמיחת ייעוץ דומה, ללא IP תוכנה'},
      {ticker:'MSFT',name:'Microsoft',pe:35,ps:13,rev_growth:'13%+',gross_margin:'~70%',market_cap:'>$3T',vs_company:'גדל מהר יותר, שולי גבוהים יותר — IBM זולה אך צומחת לאט יותר'},
      {ticker:'ORCL',name:'Oracle',pe:30,ps:8,rev_growth:'~10%+',gross_margin:'~70%',market_cap:'>$500B',vs_company:'תחרות ישירה ב-DB/ארגוני; Oracle אגרסיבית בענן AI'}
    ],
    edge:'החפיר הייחודי: מיינפריים נעוץ (switching costs) + Red Hat hybrid + אמון רגולטורי. אף מתחרה לא מחזיק את כל השלושה.'
  },
  news_catalysts:{
    description:'סנטימנט חיובי-נטו: AI/קוונטום ממשלתי + ריצה פאראבולית, מאוזן ע"י הנחיה שמרנית',
    items:[
      {date:'2026-01-28',headline:'Q4 2025: הכנסות +12%, Software +14%, FCF שיא $14.7B',type:'earnings',direction:'green',impact:'אישור טרנספורמציה; net income +93%'},
      {date:'2026-04-22',headline:'Q1 2026: הכנסות $15.9B (+9%), Beat — המניה נענשה',type:'earnings',direction:'yellow',impact:'Beat אך הנחיה שמרנית; הנחיית Infrastructure שלילית'},
      {date:'2026-05-28',headline:'Project Lightwell — $5B עם Red Hat לאבטחת open-source',type:'product',direction:'green',impact:'מנוע subscription חדש, חיזוק חפיר'},
      {date:'2026-05-29',headline:'תמיכה ממשלתית $2B בקוונטום + מפעל Anderson (CHIPS Act)',type:'regulatory',direction:'green',impact:'אופציונליות קוונטום מגובה ממשלה'},
      {date:'2026-06-01',headline:'Barclays: מחיר יעד $350 (overweight)',type:'sentiment',direction:'green',impact:'~10% upside לפי האנליסט'}
    ],
    net_sentiment:'bullish',
    net_sentiment_why:'מומנטום AI/קוונטום חזק, אך מאוזן ע"י הנחיה שמרנית ל-2026 ופיק מיינפריים מתקרר.'
  },
  strategic_roadmap:{
    description:'מעבר ל-recurring software + הימור ארוך-טווח על קוונטום ו-GenAI ארגוני',
    initiatives:[
      {title:'Software-led growth (Red Hat + Automation + Data)',timeline:'מתמשך',scale:'ARR $23.6B, יעד +10% 2026',credibility:'high',status:'בביצוע — הקצב הגבוה בהיסטוריה'},
      {title:'GenAI book of business',timeline:'2024-מתמשך',scale:'>$12.5B מצטבר',credibility:'high',status:'מעל שליש מהזמנות ייעוץ; מפסיק להיות מדווח בנפרד'},
      {title:'Quantum computing (FTQC 2029)',timeline:'FTQC עד 2029',scale:'>$10B/5 שנים',credibility:'medium',status:'$2B ממשלה + מפעל Anderson'},
      {title:'Confluent acquisition',timeline:'סגירה אמצע 2026',scale:'$600M דילול',credibility:'high',status:'בתהליך אישור'}
    ],
    hidden_gem:'מהלך הקוונטום מגובה-הממשלה ($2B CHIPS) — השוק מתמחר IBM כחברת-ערך בוגרת ולא כ-quantum leader פוטנציאלי ל-2029.'
  },
  alpha_signal:{
    description:'אופציונליות קוונטום + recurring software — אך תמחור מלא כרגע',
    signals:[
      {type:'hidden_optionality',detail:'$10B/5שנים בקוונטום + CHIPS $2B; לא בתמחור DCF סטנדרטי',conviction:'SPECULATIVE'},
      {type:'sentiment_divergence',detail:'Beat Q1 2026 אך מניה נענשה — פוטנציאל לתיקון חיובי אם Infrastructure לא יקרוס',conviction:'MEDIUM'},
      {type:'institutional_accumulation',detail:'Barclays overweight $350; HSBC שדרג; מומנטום אנליסטים',conviction:'MEDIUM'}
    ],
    thesis:'השוק מתמחר IBM כחברת-ערך ב-27x, מתעלם משתי אופציות: (1) Software ARR ממשיך לאיץ, (2) קוונטום מגובה-ממשלה ל-2029. הטריגר: רבעון Software נוסף מעל 11% + אבן-דרך קוונטום.',
    confidence:'MEDIUM'
  },
  footer:'<b>אימות מקורות:</b> ✅ פיננסים — stockanalysis.com · ✅ Q1 FY2026 — IBM Newsroom 22.4.2026 · ✅ שיחת ועידה Q4 — Motley Fool · ⚠️ FCF conflict: adj $14.7B vs std $12.1B · 🔴 10-K/10-Q body נחסם (HTTP 403).',
  disclaimer:'מספרים FY23-25 הם GAAP אלא אם צוין. FCF adjusted vs standard — הפרש $2.6B. אינו ייעוץ השקעות.'
};
