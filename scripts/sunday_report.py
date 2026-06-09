"""
דוח CEO שבועי — ראשון 5:00.
Yahoo Finance (חינם) + scanner-results מיום שבת + Groq synthesis (חינם).
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from glob import glob as _glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from notifications import send_notification
from yahoo_client import get_chart_result, extract_closes
from groq_client import call_groq, extract_json_array

PORTFOLIO_JSON  = os.path.join(ROOT, 'portfolio.json')
ANALYSES_DIR    = os.path.join(ROOT, 'analyses')
SCANNER_RESULTS = os.path.join(ROOT, 'scanner-results.json')
WEEKLY_JS       = os.path.join(ANALYSES_DIR, '_weekly', 'ceo_weekly.js')
WEEKLY_JSON     = os.path.join(ANALYSES_DIR, '_weekly', 'ceo_weekly.json')
WEEKLY_DIR      = os.path.join(ANALYSES_DIR, '_weekly')

# ── עזרים ─────────────────────────────────────────────────────────────────────

def load_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def load_review(ticker):
    """טוען review קיים לטיקר — ic.json עדיפות, fallback analyst.json."""
    rev_dir = os.path.join(ANALYSES_DIR, ticker, '_reviews')
    for fname in ('ic.json', 'analyst.json'):
        rv = load_json(os.path.join(rev_dir, fname))
        if rv:
            return rv
    return {}


# ── נתוני שוק ─────────────────────────────────────────────────────────────────

def get_price_7d(ticker):
    """מחיר + שינוי שבועי — עם dual-host fallback + retry מ-yahoo_client."""
    result = get_chart_result(ticker, period='7d')
    if not result:
        return {}
    meta   = result.get('meta', {})
    closes = extract_closes(result)
    current = meta.get('regularMarketPrice') or (closes[-1] if closes else None)
    if not current or len(closes) < 2:
        return {}
    chg_week = round((current / closes[0] - 1) * 100, 1) if closes[0] else 0
    return {'price': round(current, 2), 'chg_week': chg_week}


def _fetch_all_prices(tickers):
    """שולף מחירים לכל הטיקרים במקביל (max 2 threads) + מאקרו סדרתי."""
    prices = {}
    macro  = {}

    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = {ex.submit(get_price_7d, t): t for t in tickers}
        for fut in as_completed(futures):
            t = futures[fut]
            prices[t] = fut.result() or {}

    for ticker, key in [('SPY', 'spy'), ('QQQ', 'qqq'), ('^VIX', 'vix')]:
        d = get_price_7d(ticker)
        if d:
            macro[key] = d

    print(f'[sunday] מאקרו: {macro}')
    return prices, macro


def compute_portfolio_stats(holdings, prices):
    """ערך תיק, P&L שבועי וכולל."""
    total_value = 0.0
    total_cost  = 0.0
    week_pnl    = 0.0
    for h in holdings:
        ticker = h.get('symbol') or h.get('ticker', '')
        qty    = float(h.get('quantity', 0) or h.get('shares', 0) or 0)
        cost   = float(h.get('buy_price', 0) or 0)
        p      = prices.get(ticker, {})
        price  = p.get('price') or 0
        chg    = p.get('chg_week') or 0
        if price and qty:
            val          = price * qty
            total_value += val
            total_cost  += cost * qty
            week_pnl    += val * chg / 100
    pnl_pct       = round((total_value - total_cost) / total_cost * 100, 1) if total_cost else 0
    start_of_week = total_value - week_pnl
    week_pnl_pct  = round(week_pnl / start_of_week * 100, 1) if start_of_week > 0 else 0
    return {
        'total_value':  round(total_value),
        'total_cost':   round(total_cost),
        'pnl_pct':      pnl_pct,
        'week_pnl_pct': week_pnl_pct,
    }


# ── Groq synthesis ─────────────────────────────────────────────────────────────

def run_groq_synthesis(context_dict):
    """קריאה אחת ל-Groq — 4 תובנות שבועיות."""
    if not os.environ.get('GROQ_API_KEY'):
        print('[sunday] אין GROQ_API_KEY — דולג')
        return []

    system = """אתה יועץ תיק השקעות שבועי. קבל נתוני ביצועים בJSON וספק בדיוק 4 תובנות.

ענה ב-JSON בלבד, ללא הסברים:
["תובנה 1", "תובנה 2", "תובנה 3", "תובנה 4"]

מבנה התובנות:
1. מגמת השבוע: מה הסביר את ביצועי התיק ביחס לשוק
2. סיכון עיקרי לשבוע הבא: מה עלול להכאיב
3. הזדמנות הסקנר: האם הקטליסט של ה-top pick עדיין רלוונטי
4. פעולה ספציפית אחת: מה כדאי לעשות או לעקוב

כל תובנה: 1-2 משפטים בעברית, מבוססת על הנתונים בלבד."""

    raw = call_groq(system, json.dumps(context_dict, ensure_ascii=False),
                    max_tokens=500, timeout=45)
    if not raw:
        return []
    results = [str(r) for r in extract_json_array(raw) if r]
    if not results:
        print(f'[sunday] Groq: לא נמצא JSON array. raw={raw[:200]}')
    return results


# ── פורמט הודעה ───────────────────────────────────────────────────────────────

def format_message(holdings_weekly, stats, macro, scanner_top, insights, failed=None):
    now        = datetime.now()
    today      = now.strftime('%d/%m/%Y')
    week_start = (now - timedelta(days=6)).strftime('%d/%m')
    lines = [f'דוח שבועי {today} ({week_start}-{now.strftime("%d/%m")})']

    if failed:
        lines.append(f'נתונים חלקיים: {len(failed)} טיקרים לא נטענו ({", ".join(failed[:3])}{"..." if len(failed) > 3 else ""})')

    val_str  = f'${stats["total_value"]:,}'
    week_str = f'{stats["week_pnl_pct"]:+.1f}%'
    pnl_str  = f'{stats["pnl_pct"]:+.1f}%'
    lines.append(f'תיק: {val_str} ({week_str} שבועי | {pnl_str} כולל)')

    macro_parts = []
    if macro.get('spy'):
        macro_parts.append(f'SPY {macro["spy"]["chg_week"]:+.1f}%')
    if macro.get('qqq'):
        macro_parts.append(f'QQQ {macro["qqq"]["chg_week"]:+.1f}%')
    if macro.get('vix'):
        macro_parts.append(f'VIX {macro["vix"]["price"]:.1f}')
    if macro_parts:
        lines.append('מאקרו: ' + ' | '.join(macro_parts))

    lines.append('')

    chunks = []
    for h in holdings_weekly:
        tk  = h['ticker']
        chg = h.get('price_change_pct')
        chg_str = f'{chg:+.1f}%' if chg is not None else '?'
        chunks.append(f'{tk:<5} {chg_str}')
    for i in range(0, len(chunks), 2):
        lines.append('  '.join(chunks[i:i+2]))

    if scanner_top:
        lines.append('')
        lines.append('סקנר שבת:')
        for i, opp in enumerate(scanner_top[:2], 1):
            conv = opp.get('conviction', '?')
            up   = opp.get('upside_pct', '?')
            cat  = (opp.get('catalyst') or '')[:70]
            lines.append(f'{i}. {opp.get("ticker")} | {conv}/5 | +{up}%')
            if cat:
                lines.append(f'   {cat}')

    if insights:
        lines.append('')
        lines.append('תובנות:')
        for ins in insights:
            lines.append(f'- {ins}')

    return '\n'.join(lines)


# ── ארכיב + JS ────────────────────────────────────────────────────────────────

def archive_weekly_js():
    if not os.path.exists(WEEKLY_JS):
        return
    os.makedirs(WEEKLY_DIR, exist_ok=True)
    date_str  = datetime.now().strftime('%Y-%m-%d')
    dest_path = os.path.join(WEEKLY_DIR, f'ceo_weekly_{date_str}.js')
    try:
        with open(WEEKLY_JS, encoding='utf-8') as f:
            content = f.read()
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        archives = sorted(_glob(os.path.join(WEEKLY_DIR, 'ceo_weekly_*.js')))
        for old in archives[:-8]:
            os.remove(old)
        print(f'[sunday] ארכב ל-{dest_path}')
    except Exception as e:
        print(f'[sunday] שגיאת ארכיב: {e}')


def write_weekly_js(data):
    os.makedirs(WEEKLY_DIR, exist_ok=True)
    js = f'window.WEEKLY_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n'
    with open(WEEKLY_JS, 'w', encoding='utf-8') as f:
        f.write(js)
    with open(WEEKLY_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'[sunday] כתב {WEEKLY_JS} + {WEEKLY_JSON}')


def is_fourth_sunday():
    today = datetime.now()
    return today.weekday() == 6 and today.day >= 22


def run_monthly_close():
    try:
        monthly_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monthly_close.py')
        if not os.path.exists(monthly_script):
            print('[sunday] monthly_close.py לא נמצא — דלג')
            return
        import importlib.util
        spec = importlib.util.spec_from_file_location('monthly_close', monthly_script)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run()
    except Exception as e:
        print(f'[sunday] שגיאת monthly_close: {e}')


# ── ריצה ─────────────────────────────────────────────────────────────────────

def main():
    print('[sunday_report] מתחיל...')
    archive_weekly_js()

    portfolio = load_json(PORTFOLIO_JSON)
    holdings  = [h for h in portfolio.get('holdings', [])
                 if h.get('symbol') or h.get('ticker')]
    tickers   = [h.get('symbol') or h.get('ticker', '') for h in holdings]

    print(f'[sunday] שולף מחירים ל-{len(tickers)} טיקרים + מאקרו במקביל...')
    prices, macro = _fetch_all_prices(tickers)
    for t in tickers:
        status = f'${prices[t]["price"]}' if prices.get(t) else 'כשל'
        print(f'[sunday] {t}: {status}')

    failed = [t for t in tickers if not prices.get(t)]
    if failed:
        print(f'[sunday] נתונים חסרים: {failed}')

    stats = compute_portfolio_stats(holdings, prices)
    print(f'[sunday] תיק: ${stats["total_value"]:,} ({stats["week_pnl_pct"]:+.1f}% שבועי | {stats["pnl_pct"]:+.1f}% כולל)')

    scanner_top = sorted(
        load_json(SCANNER_RESULTS, default=[]),
        key=lambda x: x.get('conviction', 0), reverse=True
    )[:3]
    print(f'[sunday] סקנר: {len(scanner_top)} הזדמנויות')

    holdings_context = []
    for ticker, h in zip(tickers, holdings):
        price = (prices.get(ticker) or {}).get('price') or 0
        cost  = float(h.get('buy_price') or 0)
        pnl   = round((price / cost - 1) * 100, 1) if (cost and price) else None
        holdings_context.append({
            'ticker':   ticker,
            'sector':   h.get('sector', ''),
            'chg_week': (prices.get(ticker) or {}).get('chg_week'),
            'pnl_pct':  pnl,
        })

    vix_price = (macro.get('vix') or {}).get('price')
    spy_chg   = (macro.get('spy') or {}).get('chg_week')
    qqq_chg   = (macro.get('qqq') or {}).get('chg_week')

    groq_context = {
        'holdings':    holdings_context,
        'portfolio':   stats,
        'macro': {
            'spy_week_pct': spy_chg,
            'qqq_week_pct': qqq_chg,
            'vix':          vix_price,
        },
        'scanner_top': [{'ticker': o.get('ticker'),
                         'catalyst': (o.get('catalyst') or '')[:80],
                         'conviction': o.get('conviction')} for o in scanner_top],
    }
    insights = run_groq_synthesis(groq_context)
    print(f'[sunday] Groq החזיר {len(insights)} תובנות')

    holdings_weekly = []
    for ticker, h in zip(tickers, holdings):
        rv      = load_review(ticker)
        chg     = (prices.get(ticker) or {}).get('chg_week')
        verdict = rv.get('verdict', '')
        holdings_weekly.append({
            'ticker':           ticker,
            'company':          rv.get('company', ticker),
            'price_change_pct': chg,
            'status':           verdict,
            'key_news':         rv.get('thesis', '')[:100],
            'headline':         rv.get('handoff_summary', '')[:120],
            'thesis_check':     ('HOLDING' if verdict in ('INTACT', 'BUY')
                                 else ('REVIEW' if verdict else '')),
        })

    if vix_price is not None:
        regime = 'risk_on' if vix_price < 20 else ('risk_off' if vix_price > 25 else 'mixed')
    else:
        regime = 'mixed'

    regime_note = (f'נתונים חלקיים: {len(tickers)-len(failed)}/{len(tickers)} טיקרים נטענו'
                   if failed else None)

    vs_spy = round(stats['week_pnl_pct'] - spy_chg, 1) if spy_chg is not None else None

    now = datetime.now()
    write_weekly_js({
        'generated':  now.strftime('%Y-%m-%d'),
        'week_label': (f'שבוע {(now-timedelta(days=6)).strftime("%d/%m")}'
                       f'-{now.strftime("%d/%m")}'),
        'ceo_verdict': insights[0] if insights else '',
        'portfolio_performance': {
            'total_value':   stats['total_value'],
            'week_pct':      stats['week_pnl_pct'],
            'total_pnl_pct': stats['pnl_pct'],
            'ytd_pct':       None,
            'vs_spy_week':   vs_spy,
            'regime':        regime,
        },
        'macro_snapshot': {
            'vix':          vix_price,
            'spy_week_pct': spy_chg,
            'qqq_week_pct': qqq_chg,
            'dxy_trend':    None,
            'rate_outlook': None,
            'regime_note':  regime_note,
        },
        'holdings_weekly': holdings_weekly,
        'risk_matrix':     [],
        'opportunities': [
            {
                'ticker':         o.get('ticker'),
                'conviction':     o.get('conviction'),
                'timeframe':      o.get('timeframe', '1-2 שבועות'),
                'catalyst':       o.get('catalyst', ''),
                'why_not_others': f'R/R {o.get("upside_pct",0)}/{o.get("downside_pct",0)}, {o.get("sector","")}',
            }
            for o in scanner_top
        ],
        'scenarios_next_week': {},
        'action_items': insights,
        'macro':         macro,
    })

    msg    = format_message(holdings_weekly, stats, macro, scanner_top, insights, failed=failed)
    result = send_notification(msg, title='דוח שבועי', tags=['chart_with_upwards_trend'])
    print(f'[sunday] נשלח: {result}')

    if is_fourth_sunday():
        print('[sunday_report] Sunday רביעי — מריץ סגירת חודש...')
        run_monthly_close()


if __name__ == '__main__':
    main()
