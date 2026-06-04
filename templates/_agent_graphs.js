// שכבת גרפים משותפת: מחוגי ציון השוואתיים לכל הסוכנים.
// עצמאית לחלוטין: מזריקה CSS משלה, יוצרת overlay, ושומרת/משחזרת את window.AGENT_DATA
// כדי לא לשבור את הרינדור של התבנית המארחת. רצה אחרי load.
(function(){
  'use strict';
  var AGENTS=[
    {key:'analyst', label:'אנליסט',       color:'#4da6ff'},
    {key:'devils',  label:'עורך דין שטן', color:'#e05c5c'},
    {key:'ceo',     label:'CEO',           color:'#a78bfa'},
    {key:'executor',label:'Executor',      color:'#f0a050'},
    {key:'ic',      label:'ועדה',          color:'#2ecc71'}
  ];

  function injectCSS(){
    if(document.getElementById('ags-shared-css'))return;
    var st=document.createElement('style');st.id='ags-shared-css';
    st.textContent=[
      '#agent-graph-overlay{max-width:1160px;margin:0 auto;padding:0 32px 40px}',
      '.ags-header{font-size:12px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:16px 0 14px;border-top:1px solid var(--border);margin-bottom:4px}',
      '.ags-gauges{display:flex;flex-wrap:wrap;gap:20px;margin-top:16px;justify-content:center}',
      '.ags-gauge{display:flex;flex-direction:column;align-items:center;gap:9px}',
      '.ags-dial{width:112px;height:112px;border-radius:50%;display:grid;place-items:center;position:relative;background:conic-gradient(var(--c) calc(var(--p)*1%), var(--surface) 0);transition:.4s}',
      '.ags-dial::before{content:"";position:absolute;inset:10px;border-radius:50%;background:var(--bg)}',
      '.ags-dial .num{position:relative;font-size:32px;font-weight:800;color:var(--text);line-height:1}',
      '.ags-dial .den{position:relative;font-size:11px;color:var(--muted);margin-top:3px}',
      '.ags-gauge .glabel{font-size:14px;font-weight:700;color:var(--text)}',
      '.ags-gauge .gverdict{font-size:11px;font-weight:600;color:var(--muted2);background:var(--surface);padding:3px 10px;border-radius:11px;border:1px solid var(--border)}',
      '.ags-table{width:100%;border-collapse:collapse;margin-top:10px;font-size:12.5px}',
      '.ags-table th{text-align:right;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.4px;padding:6px 8px;border-bottom:1px solid var(--border)}',
      '.ags-table td{padding:9px 8px;border-bottom:1px solid var(--bg);color:var(--muted2)}',
      '.ags-table td:last-child{font-weight:700;color:var(--text)}',
      '.ags-table tr:last-child td{border-bottom:none}'
    ].join('');
    document.head.appendChild(st);
  }

  function ensureOverlay(){
    var ov=document.getElementById('agent-graph-overlay');
    if(!ov){ov=document.createElement('div');ov.id='agent-graph-overlay';document.body.appendChild(ov);}
    return ov;
  }

  function paint(snaps){
    var ov=ensureOverlay();
    var withScore=snaps.filter(function(s){return s.score!==undefined;});
    if(!withScore.length){return;}
    var gauges=withScore.map(function(s){
      return '<div class="ags-gauge"><div class="ags-dial" style="--c:'+s.color+';--p:'+Math.min(s.score,100)+'">'
        +'<span class="num">'+s.score+'</span><span class="den">/ 100</span></div>'
        +'<span class="glabel">'+s.label+'</span>'
        +(s.verdict?'<span class="gverdict">'+s.verdict+'</span>':'')+'</div>';
    }).join('');
    var rows=withScore.map(function(s){return '<tr><td>'+s.label+'</td><td>'+s.score+'</td></tr>';}).join('');
    ov.innerHTML='<div class="wrap" style="padding-top:0">'
      +'<div class="ags-header">📊 ויזואליזציה משווה — כל הסוכנים</div>'
      +'<div class="section" style="margin-bottom:16px"><h2><span class="bar-accent" style="background:var(--blue)"></span>📊 ציוני סוכנים</h2>'
      +'<div class="desc">ככל שהמחוג מלא יותר והמספר גבוה, הסוכן חיובי יותר על המניה (סולם 0 עד 100).</div>'
      +'<div class="ags-gauges">'+gauges+'</div></div>'
      +'<div class="section" style="margin-bottom:16px"><h2><span class="bar-accent" style="background:var(--purple)"></span>השוואת סוכנים</h2>'
      +'<table class="ags-table"><thead><tr><th>סוכן</th><th>ציון</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
      +'</div>';
  }

  function run(){
    var params=new URLSearchParams(location.search);
    var ticker=params.get('ticker');
    if(!ticker){return;}
    injectCSS();
    var original=window.AGENT_DATA;   // לשמור כדי לא לשבור את התבנית המארחת
    var snaps=[];
    function next(i){
      if(i>=AGENTS.length){window.AGENT_DATA=original;paint(snaps);return;}
      var def=AGENTS[i];
      var el=document.createElement('script');
      el.src='../analyses/'+ticker+'/'+def.key+'.js';
      el.onload=function(){
        var d=window.AGENT_DATA||{};
        var s={label:def.label,color:def.color};
        if(typeof d.score==='number')s.score=d.score;
        if(typeof d.verdict==='string')s.verdict=d.verdict;
        snaps.push(s);next(i+1);
      };
      el.onerror=function(){snaps.push({label:def.label,color:def.color});next(i+1);};
      document.head.appendChild(el);
    }
    next(0);
  }

  if(document.readyState==='complete'){run();}
  else{window.addEventListener('load',run);}
})();
