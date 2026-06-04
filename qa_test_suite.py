"""QA test suite — synthetic checks only, no LLM, no real portfolio writes.

Snapshot/restore guarantees real data is untouched. All synthetic tickers are
prefixed with _QA_ for easy cleanup.
"""
import json, os, re, sys, shutil, tempfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app
ROOT = app.ROOT

# ── Test framework ──────────────────────────────────────────────────────────
RESULTS = {'PASS': 0, 'WARN': 0, 'FAIL': 0, 'details': []}

def test(name, fn):
    try:
        r = fn()
        if r is True or r is None:
            print(f'  ✅ PASS   {name}')
            RESULTS['PASS'] += 1
            RESULTS['details'].append(('PASS', name, ''))
        elif isinstance(r, tuple) and r[0] == 'WARN':
            print(f'  ⚠️  WARN   {name}  — {r[1]}')
            RESULTS['WARN'] += 1
            RESULTS['details'].append(('WARN', name, r[1]))
        else:
            print(f'  ❌ FAIL   {name}  — {r}')
            RESULTS['FAIL'] += 1
            RESULTS['details'].append(('FAIL', name, str(r)))
    except Exception as e:
        import traceback
        print(f'  ❌ FAIL   {name}  — EXCEPTION: {e}')
        RESULTS['FAIL'] += 1
        RESULTS['details'].append(('FAIL', name, f'exception: {e}'))


# ── Helpers ─────────────────────────────────────────────────────────────────
def load_js(path):
    if not os.path.exists(path): return None
    txt = open(path, encoding='utf-8').read()
    txt = re.sub(r'^//[^\n]*\n', '', txt)
    txt = re.sub(r'^window\.AGENT_DATA\s*=\s*', '', txt).rstrip().rstrip(';').strip()
    try: return json.loads(txt)
    except Exception: return None

def synth_setup(ticker, handoff_md, agent='analyst'):
    """Create a synthetic ticker with a fake handoff. Returns path to ticker dir."""
    tdir = os.path.join(app.ANALYSES_DIR, ticker)
    hdir = os.path.join(tdir, '_handoffs')
    os.makedirs(hdir, exist_ok=True)
    open(os.path.join(hdir, f'2026-05-28_{agent}.md'), 'w', encoding='utf-8').write(handoff_md)
    return tdir

def synth_teardown(ticker):
    shutil.rmtree(os.path.join(app.ANALYSES_DIR, ticker), ignore_errors=True)

MIN_HANDOFF = """## א.1 — מודל עסקי

תיאור קצר של המודל.

| מנוע | סוג | הערה |
|------|-----|------|
| AWS | Cloud | Primary |

## א.3 — חפיר

תיאור חפיר.

## אימות מקורות

מקורות שונים."""

IC_HANDOFF_HASH = """## [1] אימות קלטים

| HANDOFF | סטטוס |
|---------|--------|
| אנליסט | ✅ מלא |

## [3] חילוקי דעות

### קונפליקט א
פסקה ראשונה של קונפליקט א.

### קונפליקט ב
פסקה ראשונה של קונפליקט ב.

## ⑰ האמת הקשה

זו האמת הקשה."""

IC_HANDOFF_BOLD = """## [1] אימות קלטים

| HANDOFF | סטטוס |
|---------|--------|
| אנליסט | ✅ מלא |

## [3] חילוקי דעות

**קונפליקט א:** פסקה ראשונה של קונפליקט א.

**קונפליקט ב:** פסקה ראשונה של קונפליקט ב.

## ⑰ האמת הקשה

זו האמת הקשה."""

IC_NO_HT_NO_MATRIX = """## [1] אימות קלטים

טקסט בלי טבלה ובלי bullets.

## [2] ניתוח קונסנזוס

- נקודת קונסנזוס אחת."""


# ─────────────────────────────────────────────────────────────────────────────
# 1. Analyst visual resilience
# ─────────────────────────────────────────────────────────────────────────────
print()
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
print(' 1. ANALYST visual resilience (partial visual_scores)')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

BASE_DASH = {
    'ticker': '_QA_T1', 'date': '2026-05-28', 'verdict': 'WATCHLIST', 'score': 50,
    'thesis': 'thesis sample', 'key_risks': ['risk one', 'risk two'],
    'position_size_pct': 2.0,
    'valuation_summary': 'fair value summary',
    'entry_exit_plan': 'plan',
    'handoff_summary': 'handoff summary',
}

def t1a():
    """empty visual_scores → all D-Lite blocks gracefully absent, text grids still work."""
    synth_setup('_QA_T1', MIN_HANDOFF)
    try:
        d = dict(BASE_DASH); d['visual_scores'] = {}
        app._write_visual_js('_QA_T1', 'analyst', d)
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T1', 'analyst.js'))
        if not out: return 'js failed to load'
        if 'business_model' not in out: return 'no business_model'
        if 'engines' in out.get('business_model', {}): return 'engines should not appear without visual_scores'
        if not out.get('footer'): return 'footer missing (should have deterministic default)'
        if not out.get('disclaimer'): return 'disclaimer missing'
    finally: synth_teardown('_QA_T1')

def t1b():
    """visual_scores with ONLY business_engines → engines render, no valuation/financials."""
    synth_setup('_QA_T1', MIN_HANDOFF)
    try:
        d = dict(BASE_DASH); d['visual_scores'] = {
            'business_engines': [
                {'label': 'AWS', 'revenue_b': 100, 'growth_pct': 28, 'weight_pct': 60},
                {'label': 'Ads', 'revenue_b': 70,  'growth_pct': 22, 'weight_pct': 40},
            ],
        }
        app._write_visual_js('_QA_T1', 'analyst', d)
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T1', 'analyst.js'))
        engines = out.get('business_model', {}).get('engines', [])
        if len(engines) != 2: return f'expected 2 engines, got {len(engines)}'
        if 'valuation' in out: return 'valuation should be absent'
        if 'financials_3y' in out: return 'financials_3y should be absent'
        if 'stress_test' in out and out['stress_test'].get('categories'): return 'stress should be absent'
    finally: synth_teardown('_QA_T1')

def t1c():
    """moat_scores all null → moat.items should be empty (filtered), text grid still works."""
    synth_setup('_QA_T1', MIN_HANDOFF)
    try:
        d = dict(BASE_DASH); d['visual_scores'] = {
            'moat_scores': [
                {'label': 'AWS lock-in', 'score_0_10': None},
                {'label': 'Marketplace', 'score_0_10': None},
            ],
        }
        app._write_visual_js('_QA_T1', 'analyst', d)
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T1', 'analyst.js'))
        if 'moat' not in out: return 'moat should exist (from handoff section)'
        items = out['moat'].get('items', [])
        if items: return f'moat.items should be empty when all scores null, got {len(items)}'
    finally: synth_teardown('_QA_T1')

def t1d():
    """valuation with only base_price → bear/bull get safe stubs (no template crash)."""
    synth_setup('_QA_T1', MIN_HANDOFF)
    try:
        d = dict(BASE_DASH); d['visual_scores'] = {
            'valuation': {'bear_price': None, 'base_price': 250, 'bull_price': None, 'current_price': 270},
        }
        app._write_visual_js('_QA_T1', 'analyst', d)
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T1', 'analyst.js'))
        v = out.get('valuation')
        if not v: return 'valuation should exist with base_price present'
        for k in ('bear', 'base', 'bull'):
            if k not in v: return f'{k} missing (template requires all 3)'
            if 'price' not in v[k]: return f'{k}.price missing (template crash risk)'
            if 'height' not in v[k]: return f'{k}.height missing'
        if v['base']['price'] != '$250': return f'base price wrong: {v["base"]["price"]}'
        if v['bear']['price'] != '—': return f'bear price should be em-dash stub, got {v["bear"]["price"]}'
    finally: synth_teardown('_QA_T1')

def t1e():
    """financials with 2 years instead of 3 → charts still render (≥2 bars per chart)."""
    synth_setup('_QA_T1', MIN_HANDOFF)
    try:
        d = dict(BASE_DASH); d['visual_scores'] = {
            'financials_3y': [
                {'year': 'FY24', 'revenue_b': 600, 'op_margin_pct': 10},
                {'year': 'FY25', 'revenue_b': 700, 'op_margin_pct': 11},
            ],
        }
        app._write_visual_js('_QA_T1', 'analyst', d)
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T1', 'analyst.js'))
        f = out.get('financials_3y')
        if not f: return 'financials_3y should exist with 2 years'
        if len(f.get('charts', [])) < 1: return 'no charts rendered'
        for c in f['charts']:
            if len(c.get('bars', [])) < 2: return f'chart {c["title"]} has <2 bars'
    finally: synth_teardown('_QA_T1')

test('1a: empty visual_scores → no D-Lite, text grids OK', t1a)
test('1b: only business_engines present',                 t1b)
test('1c: moat_scores all null → items filtered',         t1c)
test('1d: valuation base only → safe stubs, no crash',    t1d)
test('1e: financials 2 years → charts still render',      t1e)


# ─────────────────────────────────────────────────────────────────────────────
# 2. IC resilience
# ─────────────────────────────────────────────────────────────────────────────
print()
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
print(' 2. IC resilience (structural drift)')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

IC_BASE_DASH = {
    'ticker': '_QA_T2', 'date': '2026-05-28', 'verdict': 'WATCHLIST', 'score': 50,
    'thesis': 'ic thesis', 'key_risks': ['key risk one'],
    'position_size_pct': 1.5,
    'valuation_summary': 'fair val',
    'entry_exit_plan': 'enter at X',
    'handoff_summary': 'committee summary',
}

def t2a():
    """disagreements with ### headers."""
    synth_setup('_QA_T2', IC_HANDOFF_HASH, agent='ic')
    try:
        app._write_visual_js('_QA_T2', 'ic', dict(IC_BASE_DASH))
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T2', 'ic.js'))
        d = out.get('disagreements', '')
        if 'קונפליקט א' not in d: return f'first ### subsection not extracted; got: {d[:100]}'
        if 'קונפליקט ב' not in d: return 'second ### subsection not extracted'
        if '<br><br>' not in d: return 'expected <br><br> between subsections'
    finally: synth_teardown('_QA_T2')

def t2b():
    """disagreements with **bold:** headers (the new pattern we added)."""
    synth_setup('_QA_T2', IC_HANDOFF_BOLD, agent='ic')
    try:
        app._write_visual_js('_QA_T2', 'ic', dict(IC_BASE_DASH))
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T2', 'ic.js'))
        d = out.get('disagreements', '')
        if 'קונפליקט א' not in d: return f'first **bold** subsection not extracted; got: {d[:100]}'
        if 'קונפליקט ב' not in d: return 'second **bold** subsection not extracted'
    finally: synth_teardown('_QA_T2')

def t2c():
    """hard_truth missing → fallback to key_risks[0] is used."""
    synth_setup('_QA_T2', IC_NO_HT_NO_MATRIX, agent='ic')
    try:
        d = dict(IC_BASE_DASH); d['key_risks'] = ['the leading risk']
        app._write_visual_js('_QA_T2', 'ic', d)
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T2', 'ic.js'))
        ht = out.get('hard_truth', '')
        if not ht: return 'hard_truth empty (fallback should fire)'
        if 'the leading risk' not in ht: return f'fallback did not use key_risks[0]; got: {ht[:100]}'
    finally: synth_teardown('_QA_T2')

def t2d():
    """matrix missing (no other _reviews exist) → no matrix in output, no crash."""
    synth_setup('_QA_T2', IC_NO_HT_NO_MATRIX, agent='ic')
    try:
        # only ic _review exists, no analyst/devils/ceo/executor
        app._update_review_json('_QA_T2', 'ic', dict(IC_BASE_DASH))
        app._write_visual_js('_QA_T2', 'ic', dict(IC_BASE_DASH))
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T2', 'ic.js'))
        if 'matrix' in out:
            # if matrix present, must be valid (no crash)
            m = out['matrix']
            if not m.get('rows'): return 'matrix present but empty'
        # Either no matrix (graceful) or valid matrix — both OK
    finally: synth_teardown('_QA_T2')

def t2e():
    """matrix WITH partial _reviews (only 2 agents) → builds matrix with 2 columns."""
    synth_setup('_QA_T2', IC_NO_HT_NO_MATRIX, agent='ic')
    try:
        # plant 2 fake _reviews
        for ag in ('analyst', 'devils'):
            app._update_review_json('_QA_T2', ag, {
                **IC_BASE_DASH, 'agent': ag, 'score': 70 if ag == 'analyst' else 30,
                'verdict': 'BUY' if ag == 'analyst' else 'AVOID',
            })
        app._write_visual_js('_QA_T2', 'ic', dict(IC_BASE_DASH))
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T2', 'ic.js'))
        m = out.get('matrix')
        if not m: return 'matrix should be built from 2 agents'
        if len(m['headers']) < 2: return f'matrix headers={len(m["headers"])} (expected ≥2)'
        if len(m['rows']) != 3: return f'matrix rows={len(m["rows"])} (expected 3)'
    finally: synth_teardown('_QA_T2')

test('2a: disagreements with ### headers',         t2a)
test('2b: disagreements with **bold:** headers',   t2b)
test('2c: hard_truth missing → key_risks fallback',t2c)
test('2d: matrix not buildable → no crash',        t2d)
test('2e: matrix with partial _reviews',           t2e)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Manual protection
# ─────────────────────────────────────────────────────────────────────────────
print()
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
print(' 3. Manual protection (NOW/RKLB never overwritten)')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

def t3a():
    """NOW/analyst.js first line should NOT contain marker."""
    first = open(os.path.join(app.ANALYSES_DIR, 'NOW', 'analyst.js'), encoding='utf-8').readline()
    if first.startswith('//'): return f'NOW has marker on line 1 — manual file got polluted: {first[:80]}'
    return True

def t3b():
    """RKLB/analyst.js first line should NOT contain marker."""
    first = open(os.path.join(app.ANALYSES_DIR, 'RKLB', 'analyst.js'), encoding='utf-8').readline()
    if first.startswith('//'): return f'RKLB has marker on line 1: {first[:80]}'
    return True

def t3c():
    """AMZN/analyst.js SHOULD have marker."""
    first = open(os.path.join(app.ANALYSES_DIR, 'AMZN', 'analyst.js'), encoding='utf-8').readline()
    if not first.startswith('//'): return f'AMZN missing marker: {first[:80]}'
    return True

def t3d():
    """_is_auto_generated(NOW) returns False."""
    if app._is_auto_generated(os.path.join(app.ANALYSES_DIR, 'NOW', 'analyst.js')):
        return 'NOW falsely detected as auto'

def t3e():
    """_is_auto_generated(AMZN) returns True."""
    if not app._is_auto_generated(os.path.join(app.ANALYSES_DIR, 'AMZN', 'analyst.js')):
        return 'AMZN not detected as auto'

def t3f():
    """Calling _write_visual_js for NOW (manual) writes .auto.js, primary untouched."""
    primary = os.path.join(app.ANALYSES_DIR, 'NOW', 'analyst.js')
    auto    = os.path.join(app.ANALYSES_DIR, 'NOW', 'analyst.auto.js')
    primary_before = open(primary, encoding='utf-8').read()
    # Clean any leftover .auto.js
    if os.path.exists(auto): os.remove(auto)
    try:
        result = app._write_visual_js('NOW', 'analyst', {
            'ticker': 'NOW', 'date': '2026-05-28', 'verdict': 'TEST',
            'score': 99, 'thesis': 'test', 'key_risks': [],
        })
        if result['kind'] != 'auto-alongside-manual':
            return f'wrong kind: {result["kind"]} (expected auto-alongside-manual)'
        primary_after = open(primary, encoding='utf-8').read()
        if primary_after != primary_before:
            return 'NOW primary was modified — manual protection broken'
        if not os.path.exists(auto):
            return '.auto.js was not written'
    finally:
        if os.path.exists(auto): os.remove(auto)

test('3a: NOW analyst.js has NO marker (manual)',         t3a)
test('3b: RKLB analyst.js has NO marker (manual)',        t3b)
test('3c: AMZN analyst.js HAS marker (auto)',             t3c)
test('3d: _is_auto_generated(NOW) = False',               t3d)
test('3e: _is_auto_generated(AMZN) = True',               t3e)
test('3f: write to manual ticker → .auto.js, primary untouched', t3f)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Rendering / CSS sanity
# ─────────────────────────────────────────────────────────────────────────────
print()
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
print(' 4. Rendering & CSS sanity (synthetic, no browser)')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

CSS = open(os.path.join(ROOT, 'templates', '_shared.css'), encoding='utf-8').read()

def t4a():
    """Mobile media query exists for narrow viewports."""
    if '@media (max-width:760px)' not in CSS:
        return 'no mobile media query for ≤760px'

def t4b():
    """Valuation ceiling: max-height on sc-fill + min-height on scen."""
    if 'max-height:calc(100% - 80px)' not in CSS and 'max-height:calc(100% - 70px)' not in CSS:
        return 'sc-fill has no max-height cap → bull=100% will overflow'
    if 'min-height:230px' not in CSS:
        return 'scen missing min-height (was 185px hardcoded)'

def t4c():
    """Cards grids use auto-fit minmax (responsive)."""
    if 'repeat(auto-fit,minmax(' not in CSS:
        return 'no auto-fit minmax grid → not responsive'

def t4d():
    """_norm_heights() never produces a height > max_pct cap (65)."""
    cases = [
        ([1, 1, 1], 'all equal'),
        ([100, 200, 500], 'wide range'),
        ([0.001, 1000], 'extreme range'),
        ([1e6, 1, 1], 'one giant'),
    ]
    for vals, label in cases:
        out = app._norm_heights(vals, max_pct=65)
        for v in out:
            if v is not None and v > 65:
                return f'{label}: emitted {v}% > cap 65 — would clip'
            if v is not None and v < 0:
                return f'{label}: negative value {v}'
    return True

def t4e():
    """_short_label truncates long labels with ellipsis, no overflow."""
    s = 'A' * 500
    out = app._short_label(s, max_len=90)
    if len(out) > 92:  # 90 + '…'
        return f'overflow: len={len(out)} for max_len=90'
    if not out.endswith('…'):
        return f'no ellipsis for long input: {out[-20:]}'

def t4f():
    """hbar label has overflow:hidden + text-overflow:ellipsis."""
    if 'text-overflow:ellipsis' not in CSS:
        return 'hbar label has no ellipsis on long text'

def t4g():
    """No infinite-loading: templates always have an onerror fallback."""
    for tmpl in ('analyst.html', 'ic.html'):
        path = os.path.join(ROOT, 'templates', tmpl)
        body = open(path, encoding='utf-8').read()
        if 's.onerror' not in body and 's.onerror=' not in body:
            return f'{tmpl}: no onerror fallback → 404 hangs forever'

def t4h():
    """_norm_heights tiny values still get visible minimum bar."""
    out = app._norm_heights([0.001, 0.002, 100], max_pct=65)
    # The tiny ones will round to 0; in our converter we apply minimum elsewhere.
    # Check that emitting heights via _valuation_from_scores never gives 0.
    vs = {'valuation': {'bear_price': 0.001, 'base_price': 100, 'bull_price': 0.5, 'current_price': 50}}
    v = app._valuation_from_scores(vs)
    for k in ('bear', 'base', 'bull'):
        h = v[k]['height']
        if h is not None and h == 0:
            return f'{k} has zero height → invisible bar'

test('4a: mobile media query present',              t4a)
test('4b: valuation ceiling (max-height + min)',    t4b)
test('4c: cards grids responsive (auto-fit)',       t4c)
test('4d: _norm_heights never exceeds cap',         t4d)
test('4e: _short_label truncates long labels',      t4e)
test('4f: hbar label ellipsis (long text)',         t4f)
test('4g: template onerror fallback (no infinite loading)', t4g)
test('4h: tiny values still get visible bar',       t4h)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Watchlist safety (snapshot/restore around real portfolio.json)
# ─────────────────────────────────────────────────────────────────────────────
print()
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
print(' 5. Watchlist safety (idempotency under casing/whitespace)')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

PORTFOLIO_PATH = os.path.join(ROOT, 'portfolio.json')
PORTFOLIO_BACKUP = open(PORTFOLIO_PATH, encoding='utf-8').read()

def restore_portfolio():
    open(PORTFOLIO_PATH, 'w', encoding='utf-8').write(PORTFOLIO_BACKUP)

def count_amzn():
    p = json.load(open(PORTFOLIO_PATH, encoding='utf-8'))
    return len([w for w in p.get('watchlist', []) if (w.get('symbol') or '').strip().upper() == 'QATSTQA'])

def t5a():
    """Same ticker run 3 times → 1 entry."""
    try:
        # Clean any leftover
        p = json.load(open(PORTFOLIO_PATH, encoding='utf-8'))
        p['watchlist'] = [w for w in p.get('watchlist', []) if (w.get('symbol') or '').strip().upper() != 'QATSTQA']
        json.dump(p, open(PORTFOLIO_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

        for _ in range(3):
            app._sync_verdict_to_portfolio('QATSTQA', 'ic', {
                'ticker': 'QATSTQA', 'verdict': 'WATCHLIST',
                'thesis': 'qa', 'date': '2026-05-28',
            })
        c = count_amzn()
        if c != 1: return f'expected 1 entry, got {c}'
    finally: restore_portfolio()

def t5b():
    """Different casing (qatstqa, QATSTQA, QaTsTqA) → still 1 entry."""
    try:
        # Clean
        p = json.load(open(PORTFOLIO_PATH, encoding='utf-8'))
        p['watchlist'] = [w for w in p.get('watchlist', []) if (w.get('symbol') or '').strip().upper() != 'QATSTQA']
        json.dump(p, open(PORTFOLIO_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

        for case in ('QATSTQA', 'qatstqa', 'QaTsTqA'):
            app._sync_verdict_to_portfolio(case, 'ic', {
                'ticker': case, 'verdict': 'WATCHLIST',
                'thesis': 'qa', 'date': '2026-05-28',
            })
        c = count_amzn()
        if c != 1: return f'expected 1, got {c} entries for varied casing'
    finally: restore_portfolio()

def t5c():
    """Whitespace in ticker → stripped + still 1 entry."""
    try:
        p = json.load(open(PORTFOLIO_PATH, encoding='utf-8'))
        p['watchlist'] = [w for w in p.get('watchlist', []) if (w.get('symbol') or '').strip().upper() != 'QATSTQA']
        # plant an entry with whitespace ' QATSTQA '
        p['watchlist'].append({'symbol': ' QATSTQA ', 'verdict': 'WATCHLIST', 'date_added': '2026-05-01'})
        json.dump(p, open(PORTFOLIO_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

        # now sync clean 'QATSTQA' → should update, not duplicate
        app._sync_verdict_to_portfolio('QATSTQA', 'ic', {
            'ticker': 'QATSTQA', 'verdict': 'WATCHLIST',
            'thesis': 'qa', 'date': '2026-05-28',
        })
        c = count_amzn()
        if c != 1: return f'whitespace duplicate created entries={c}'
    finally: restore_portfolio()

test('5a: same ticker 3 runs → 1 entry',           t5a)
test('5b: varied casing → 1 entry',                t5b)
test('5c: whitespace tolerance → 1 entry',         t5c)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Failure-path tests
# ─────────────────────────────────────────────────────────────────────────────
print()
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
print(' 6. Failure-path tests (defensive, no crash)')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

def t6a():
    """_latest_handoff_md for nonexistent ticker → None (no crash)."""
    r = app._latest_handoff_md('NONEXIST', 'analyst')
    if r is not None: return f'expected None, got {r}'

def t6b():
    """_write_visual_js with no handoff dir → still writes minimal data (no crash)."""
    try:
        result = app._write_visual_js('_QA_T6B', 'analyst', dict(BASE_DASH))
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T6B', 'analyst.js'))
        if not out: return 'no js written'
        if not out.get('ticker'): return 'minimal data missing'
    finally:
        synth_teardown('_QA_T6B')

def t6c():
    """_extract_dashboard_json with malformed text → None, no crash."""
    r = app._extract_dashboard_json('not a dashboard json block at all')
    if r is not None: return f'expected None for malformed, got {r}'
    r2 = app._extract_dashboard_json('```dashboard-json\n{ broken json\n```')
    if r2 is not None: return f'expected None for broken JSON, got {r2}'

def t6d():
    """_extract_visual_scores with malformed JSON → {} not crash."""
    r = app._extract_visual_scores('no block here')
    if r != {}: return f'expected {{}}, got {r}'
    r2 = app._extract_visual_scores('```visual-scores\n{ not json\n```')
    if r2 != {}: return f'expected {{}} for broken JSON, got {r2}'

def t6e():
    """Enricher with empty sections list → no crash."""
    data = dict(BASE_DASH)
    app._enrich_analyst_dashboard(data, [], dash=data)
    app._enrich_ic_dashboard(data, [], dash=data)
    # If we got here without exception, pass

def t6f():
    """_parse_handoff_sections on missing file → []."""
    r = app._parse_handoff_sections('/tmp/does_not_exist_xyz.md')
    if r != []: return f'expected [], got {r}'

def t6g():
    """Malformed visual_scores values (str instead of number) → graceful filtering."""
    d = dict(BASE_DASH); d['visual_scores'] = {
        'business_engines': [{'label': 'AWS', 'revenue_b': 'NaN', 'growth_pct': 'twenty'}],
        'moat_scores': [{'label': 'M1', 'score_0_10': '8'}],  # str not int
        'stress_categories': [{'label': 'C1', 'score_0_10': 'bad'}],
        'valuation': {'bear_price': 'low', 'base_price': 100, 'bull_price': None, 'current_price': 90},
        'financials_3y': [{'year': 'FY24', 'revenue_b': 'six hundred'}],
    }
    synth_setup('_QA_T6G', MIN_HANDOFF)
    try:
        app._write_visual_js('_QA_T6G', 'analyst', d)
        out = load_js(os.path.join(app.ANALYSES_DIR, '_QA_T6G', 'analyst.js'))
        if not out: return 'js not written for malformed inputs'
        # Should not crash; moat may have 0 items (score is str not int)
        m_items = out.get('moat', {}).get('items', [])
        if any(not isinstance(m.get('score'), (int, float)) for m in m_items):
            return 'moat item with non-numeric score leaked through'
        # valuation: base_price=100 valid, others null/stub
        v = out.get('valuation', {})
        if v and v.get('base', {}).get('price') != '$100':
            return f'valuation base mishandled: {v.get("base", {}).get("price")}'
    finally:
        synth_teardown('_QA_T6G')

test('6a: missing handoff → None, no crash',       t6a)
test('6b: missing handoff dir → minimal js write', t6b)
test('6c: malformed dashboard-json → None',        t6c)
test('6d: malformed visual-scores → {}',           t6d)
test('6e: empty sections → enricher no crash',     t6e)
test('6f: parse_sections on missing file → []',    t6f)
test('6g: malformed visual_scores values filtered',t6g)


# ── Summary ────────────────────────────────────────────────────────────────
print()
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
print(' SUMMARY')
print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
total = RESULTS['PASS'] + RESULTS['WARN'] + RESULTS['FAIL']
print(f'  Total: {total}')
print(f'  ✅ PASS: {RESULTS["PASS"]}')
print(f'  ⚠️  WARN: {RESULTS["WARN"]}')
print(f'  ❌ FAIL: {RESULTS["FAIL"]}')
print()
if RESULTS['FAIL']:
    print('━━ Failures ━━')
    for status, name, msg in RESULTS['details']:
        if status == 'FAIL':
            print(f'  ❌ {name}: {msg}')
elif RESULTS['WARN']:
    print('━━ Warnings ━━')
    for status, name, msg in RESULTS['details']:
        if status == 'WARN':
            print(f'  ⚠️  {name}: {msg}')

sys.exit(0 if RESULTS['FAIL'] == 0 else 1)
