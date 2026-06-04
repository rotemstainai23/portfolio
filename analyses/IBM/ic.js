window.AGENT_DATA = {
  ticker:'IBM', company:'International Business Machines Corp.', date:'2 ביוני 2026',
  inherited:[
    {icon:'✅',text:'<b>אנליסט:</b> איכות 7.5/10 · שווי הוגן בסיס $310 / שורי $420 · 0% upside'},
    {icon:'✅',text:'<b>שטן:</b> סיכון 7.5/10 · תוחלת −13.7% · downside −37% · תקרה 0-2.5%'},
    {icon:'✅',text:'<b>CEO:</b> REJECTED · 0% · Stability מלאה · מפסק זרם הופעל'},
    {icon:'✅',text:'<b>Executor:</b> הימנע · איכות כניסה 1.5/10 · R/R 0.005:1 · 6/7 פילטרים נכשלו'}
  ],
  matrix:{
    description:'קונסנזוס פה-אחד לדחייה — 4/4 סוכנים. שונה מ-NOW שבה כולם אישרו.',
    headers:['אנליסט','שטן','CEO','Executor','ועדה'],
    rows:[
      {label:'איכות עסק',cells:[
        {cls:'cell-y',icon:'🟡',text:'7.5/10 · בינוני-חזק'},
        {cls:'cell-y',icon:'🟡',text:'"legacy IT · מחזורי"'},
        {cls:'cell-y',icon:'🟡',text:'3/10 התאמה'},
        {cls:'cell-y',icon:'🟡',text:'פילטרים נכשלו'},
        {cls:'cell-v verdict',text:'🟡 בינוני'}
      ]},
      {label:'רמת סיכון',cells:[
        {cls:'cell-r',icon:'🔴',text:'פיק מיינפריים'},
        {cls:'cell-r',icon:'🔴',text:'7.5/10 גבוה'},
        {cls:'cell-r',icon:'🔴',text:'מפסק הופעל'},
        {cls:'cell-r',icon:'🔴',text:'RSI 89.8 קיצוני'},
        {cls:'cell-v verdict',text:'🔴 גבוה'}
      ]},
      {label:'הערכת שווי',cells:[
        {cls:'cell-r',icon:'🔴',text:'0% upside בסיס'},
        {cls:'cell-r',icon:'🔴',text:'27x על פיק'},
        {cls:'cell-r',icon:'🔴',text:'יקר'},
        {cls:'cell-r',icon:'🔴',text:'מחיר=תקרת בסיס'},
        {cls:'cell-v verdict',text:'🔴 יקר'}
      ]},
      {label:'עיתוי כניסה',cells:[
        {cls:'cell-y',text:'—'},
        {cls:'cell-r',icon:'🔴',text:'תוחלת −13.7%'},
        {cls:'cell-r',icon:'🔴',text:'FOMO גבוה'},
        {cls:'cell-r',icon:'🔴',text:'R/R 0.005:1'},
        {cls:'cell-v verdict',text:'🔴 גרוע'}
      ]},
      {label:'גודל פוזיציה',cells:[
        {cls:'cell-y',text:'—'},
        {cls:'cell-r',icon:'🔴',text:'0% / תקרה 2.5%'},
        {cls:'cell-r',icon:'🔴',text:'0% מאושר'},
        {cls:'cell-r',icon:'🔴',text:'הימנע'},
        {cls:'cell-v verdict',text:'0% (לא להיכנס)'}
      ]},
      {label:'המלצה',cells:[
        {cls:'cell-y',icon:'🟡',text:'תזה שברירית'},
        {cls:'cell-r',icon:'🔴',text:'סיכון גבוה'},
        {cls:'cell-r',icon:'🔴',text:'REJECTED'},
        {cls:'cell-r',icon:'🔴',text:'הימנע'},
        {cls:'cell-v verdict',text:'❌ REJECTED'}
      ]}
    ],
    note:'* קונסנזוס חזק = ביטחון גבוה. אך בדקנו חשיבת-עדר — ראה סעיף "נקודה עיוורת".'
  },
  consensus_points:[
    {title:'✓ 0% upside בתרחיש הבסיס — מתמטיקה, לא דעה',body:'מחיר $320 מול שווי הוגן בסיס $310. זה לא פרשנות — זה עובדה. אין מרווח ביטחון.'},
    {title:'✓ FCF standard יורד 3 שנים ברצף',body:'$12.7B→$12.4B→$12.1B. כל הנרטיב נשען על FCF adjusted ($14.7B). הפער $2.6B גדל. זה דגל איכות רווח.'},
    {title:'✓ RSI 89.8 + פאראבול +26% = כניסה בלתי-ניתנת-להגנה',body:'6/7 פילטרי Executor נכשלו. גם עסק מצוין לא מצדיק כניסה בנקודה הזו.'},
    {title:'✓ הפעולה הנכונה: גזום Speculation, מלא מזומן',body:'CEO זיהה את הבעיה האמיתית בתיק — Speculation 16% (יעד 5-10%) ומזומן 3.6% (יעד 5-10%). IBM לא פותר אחת מהן.'}
  ],
  disagreements:'<b>כמעט אין.</b> קונסנזוס 4/4. ניואנס אחד: האנליסט נותן 7.5/10 (עסק טוב) בעוד שטן/CEO מדגישים בעיקר את המחיר. <b>שני הצדדים צודקים ואינם סותרים.</b> IBM היא עסק טוב במחיר גרוע.',
  blindspot:{
    headline:'⚠️ ההנחה המשותפת: מחזור המיינפריים יתהפך בוודאות ב-2026',
    paragraphs:[
      '4 הסוכנים אותו מודל AI. כשהקונסנזוס 4/4 — חובה לשאול: <b>מה כולנו לא בדקנו?</b>',
      'ההנחה המשותפת: <b>IBM Z מחזורי ויתקרר ב-2026.</b> אך יש תרחיש שלא תומחר: מה אם היחס בין מחזור-לצמיחה-מבנית שגוי? IBM Z17 כולל האצת AI חדשה — אם לקוחות ממשיכים לשדרג בגלל AI inference capabilities, המחזור ארוך יותר מהמוקדם.',
      'בנוסף: <b>אופציונליות קוונטום עם גיבוי $2B ממשלתי</b> לא תומחרה בכלל. 4 סוכנים דחו כ"ספקולטיבי" — אך מענק ממשלתי + מפעל Anderson הוא אירוע אמיתי.'
    ],
    impact:'<b>השפעה מינורית — הדחייה נשארת.</b> גם אם המחזור ארוך יותר, המחיר $320 לא מגלם מרווח ביטחון. גם אם הקוונטום אמיתי, הוא 2029+ ואינו מצדיק תמחור נוכחי. <b>הנקודה העיוורת מחלישה את הביטחון דרגה אחת — לא הופכת את ההחלטה.</b>'
  },
  most_right:'<b>עורך הדין השטן.</b> הוא זיהה את הליבה: "מלכודת ערך מחזורית — 27x P/E על פיק מיינפריים." זו לא אבחנה טכנית חולפת אלא יסודית. FCF standard יורד + מיינפריים מחזורי + מכפיל מנופח = שילוב שמסביר את תוחלת −13.7%. גם אם צמיחת Software מבנית, המחיר כבר מגלם זאת.',
  scorecard:[
    {lbl:'איכות עסק',val:'בינוני (7.5/10)',color:'c-yellow'},
    {lbl:'רמת סיכון',val:'גבוה (7.5/10)',color:'c-red'},
    {lbl:'הערכת שווי',val:'יקר (0% upside)',color:'c-red'},
    {lbl:'התאמה לתיק',val:'חלש (3/10)',color:'c-red'},
    {lbl:'איכות כניסה',val:'גרוע (1.5/10)',color:'c-red'},
    {lbl:'נקודה עיוורת משותפת',val:'זוהתה (מחזור z17)',color:'c-yellow'},
    {lbl:'רמת ביטחון',val:'גבוה',color:'c-green'},
    {lbl:'גודל פוזיציה מומלץ',val:'0%',color:'c-red'}
  ],
  verdict:{
    style:'red',
    headline:'❌ REJECTED — פה אחד, ביטחון גבוה',
    paragraphs:[
      'זה ההפך מ-NOW. שם כולם הסכימו "פעל". כאן כולם מסכימים "אל תפעל". <b>עסק טוב. מחיר גרוע. עיתוי גרוע. התאמה לתיק גרועה.</b> שלוש סיבות עצמאיות, כל אחת מספיקה לבדה.',
      '<b>פעולה ספציפית:</b><br>1️⃣ IBM — לא נכנסים. גם לא watchlist פעיל.<br>2️⃣ גזום OKLO/APLD/IBIT → Speculation 16%→10% (משחרר ~$120-150).<br>3️⃣ מלא מזומן → 5-7%.<br>4️⃣ השלם Growth → 55%+ (NVDA/META).<br>5️⃣ הצב התראת מחיר IBM ב-$255 לבדיקה חוזרת.'
    ],
    scoreboxes:[
      {lbl:'פסיקה',val:'REJECTED',color:'c-red',size:13},
      {lbl:'ביטחון',val:'גבוה',color:'c-yellow',size:15},
      {lbl:'גודל',val:'0%',color:'c-red'},
      {lbl:'קונסנזוס',val:'4/4 דחייה',color:'c-red',size:13}
    ]
  },
  triggers:{
    title:'טריגרי בדיקה חוזרת (Watchlist פסיבי)',
    description:'IBM לא נשכחת — אבל נבדקת רק כשהתנאים משתנים.',
    items:[
      {icon:'💰',text:'<b>טריגר מחיר: $255</b> — R/R מגיע ל-2.75:1. RSI צריך להתאפס < 50 לפני כניסה.'},
      {icon:'📅',text:'<b>טריגר זמן: דוח Q2 יולי 2026</b> — לבחון Infrastructure YoY ו-Software ARR קיימות.'},
      {icon:'📅',text:'<b>טריגר זמן: דוח Q3 אוקטובר 2026</b> — אם מיינפריים שמר צמיחה YoY חיובית = תזה מחזוריות הופרכה.'},
      {icon:'📈',text:'<b>טריגר יסודי: FCF std > $13B</b> שנתי — אות שהפער adj/std מצטמצם. ביקורת מחדש.'},
      {icon:'🛑',text:'<b>Kill Switch מיידי:</b> FCF std < $11.5B, Infrastructure −10% YoY, חיתוך דיבידנד.'}
    ]
  },
  hard_truth:'<b>ה"דיבידנד הבטוח" לא מגן.</b> IBM משלמת ~$6B+ דיבידנד שנתי. משקיעים מנחמים את עצמם: "לפחות יש תשואה". אבל de-rating מ-27x ל-18x = הפסד הון של -33% שאף דיבידנד 2% לא יכסה. <b>IBM ב-$320 היא לקנות את הדיבידנד ולאבד את הקרן.</b>',
  handoff_title:'סיכום ועדה',
  handoff:'חברה: IBM · תאריך: 2.6.2026<br><b>פסיקה:</b> REJECTED · <b>גודל מאושר:</b> 0% · <b>ביטחון:</b> גבוה · <b>קונסנזוס:</b> 4/4<br><b>פעולה הבאה:</b> לא IBM. גזום Speculation→10%, מלא Cash→6%, השלם Growth.<br><b>בדיקה חוזרת:</b> מחיר $255 / דוח Q2 יולי 2026 / FCF std > $13B<br><b>Kill Switches:</b> FCF std <$11.5B · Infrastructure −10% YoY · חיתוך דיבידנד.',
  footer:'סינתזה של 4 handoffs. הוועדה לא ניתחה מחדש — סינתזה והכריעה. כל מספר — מהאנליסט/שטן/CEO/Executor.'
};
