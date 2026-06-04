"""
סגירה חודשית — מריץ בכל Sunday רביעי מתוך sunday_report.py.
אגרגציה טהורה מנתונים קיימים — ללא LLM call.
כותב:
  analyses/_monthly/<YYYY-MM>/monthly_close.js
  analyses/_monthly/<YYYY-MM>/scanner_calibration.json
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta
from glob import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from variance import build_variance_block

PORTFOLIO_JSON   = os.path.join(ROOT, 'portfolio.json')
DECISION_LOG     = os.path.join(ROOT, 'decision_log.json')
ANALYSES_DIR     = os.path.join(ROOT, 'analyses')
WEEKLY_DIR       = os.path.join(ANALYSES_DIR, '_weekly')
SCANNER_ARCHIVE  = os.path.join(ANALYSES_DIR, '_monthly', '_scanner_archive')
MONTHLY_DIR      = os.path.join(ANALYSES_DIR, '_monthly')


# ── עזרים ───────────────────────────────────────────────────────────────────

def load_json(path: str, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def parse_js_data(path: str) -> dict:
    """קורא קובץ JS עם window.X = {...} ומחזיר את ה-dict."""
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        # הסר prefix window.X_DATA = ... ;
        match = re.search(r'=\s*(\{[\s\S]*\})\s*;?\s*$', content)
        if match:
            return json.loads(match.group(1))
    except Exception:
        pass
    return {}


def get_price(ticker: str) -> dict:
    """שולף מחיר נוכחי + שינוי חודשי מ-Yahoo Finance."""
    try:
        url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
               f'?interval=1mo&range=3mo')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        result = data['chart']['result'][0]
        meta   = result['meta']
        closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
        current = meta.get('regularMarketPrice', 0) or 0
        month_ago = closes[-2] if len(closes) >= 2 else current
        chg_month = ((current - month_ago) / month_ago * 100) if month_ago else 0
        return {'price': round(current, 2), 'chg_month': round(chg_month, 2)}
    except Exception:
        return {'price': None, 'chg_month': None}


def get_prices_batch(tickers: list) -> dict:
    return {t: get_price(t) for t in tickers}


# ── Day 1: ביצועי תיק ───────────────────────────────────────────────────────

def build_portfolio_performance(portfolio: dict, prices: dict) -> tuple[dict, list]:
    holdings = portfolio.get('holdings', [])
    cash     = portfolio.get('cash', 0)

    total_cost    = cash
    total_current = cash
    monthly_gains = []

    holdings_monthly = []
    for h in holdings:
        ticker = h.get('symbol') or h.get('ticker', '')
        qty    = h.get('quantity', 0)
        buy_px = h.get('buy_price', 0)
        p      = prices.get(ticker, {})
        curr   = p.get('price') or buy_px
        chg_m  = p.get('chg_month', 0) or 0

        cost    = qty * buy_px
        current = qty * curr
        total_cost    += cost
        total_current += current
        monthly_gains.append((ticker, chg_m))

        # קרא IC review
        ic_path = os.path.join(ANALYSES_DIR, ticker, 'ic.js')
        ic_data = parse_js_data(ic_path) if os.path.exists(ic_path) else {}
        verdict = (ic_data.get('final_decision', {}).get('verdict', '')
                   or ic_data.get('meta', {}).get('verdict', '')
                   or 'HOLD')

        holdings_monthly.append({
            'ticker':       ticker,
            'company':      h.get('name', ticker),
            'layer':        h.get('layer', ''),
            'buy_price':    round(buy_px, 2),
            'current_price': round(curr, 2),
            'qty':          qty,
            'cost_basis':   round(cost, 2),
            'current_value': round(current, 2),
            'unrealized_pnl': round(current - cost, 2),
            'unrealized_pnl_pct': round((curr - buy_px) / buy_px * 100, 2) if buy_px else 0,
            'chg_month_pct': round(chg_m, 2),
            'ic_verdict':   verdict,
        })

    month_pct = round((total_current - total_cost) / total_cost * 100, 2) if total_cost else 0
    best  = max(monthly_gains, key=lambda x: x[1] or -999, default=('', 0))
    worst = min(monthly_gains, key=lambda x: x[1] or 999,  default=('', 0))

    perf = {
        'total_cost':       round(total_cost, 2),
        'total_current':    round(total_current, 2),
        'total_unrealized': round(total_current - total_cost, 2),
        'month_pct':        month_pct,
        'cash':             round(cash, 2),
        'num_positions':    len(holdings),
        'best_ticker':      best[0],
        'best_pct':         round(best[1], 2),
        'worst_ticker':     worst[0],
        'worst_pct':        round(worst[1], 2),
    }
    return perf, holdings_monthly


# ── Day 2: Thesis Reconciliation ───────────────────────────────────────────

def build_thesis_adherence(holdings: list, decisions: list) -> tuple[dict, list]:
    decision_map = {d.get('ticker'): d for d in decisions}
    intact = drift = broken = 0
    details = []

    for h in holdings:
        ticker  = h['ticker']
        verdict = h.get('ic_verdict', 'HOLD').upper()
        dec     = decision_map.get(ticker, {})
        kill    = dec.get('kill_switch', '')
        thesis  = dec.get('original_thesis', dec.get('why', ''))

        if verdict in ('BUY', 'HOLD', 'WATCHLIST', 'INTACT'):
            status = 'intact'
            intact += 1
        elif verdict in ('REDUCE', 'PARTIAL', 'REVIEW'):
            status = 'drift'
            drift += 1
        else:
            status = 'broken'
            broken += 1

        details.append({
            'ticker':        ticker,
            'original_thesis': thesis[:120] if thesis else 'N/A',
            'ic_verdict':    verdict,
            'status':        status,
            'kill_switch':   kill[:100] if kill else '',
            'chg_month_pct': h.get('chg_month_pct', 0),
        })

    total = intact + drift + broken
    score = round((intact + drift * 0.5) / total * 100) if total else 0
    return {'score_0_100': score, 'intact': intact, 'drift': drift, 'broken': broken}, details


# ── Day 3: Allocation Reconciliation ───────────────────────────────────────

def build_allocation(portfolio: dict, holdings_monthly: list) -> dict:
    layer_targets = {
        'Growth':      40,
        'Stability':   35,
        'Speculation': 15,
        'Cash':        10,
    }
    total_value = sum(h['current_value'] for h in holdings_monthly) + portfolio.get('cash', 0)
    if not total_value:
        return {'actual': {}, 'target': layer_targets, 'drift': {}}

    layer_actual = {}
    for h in holdings_monthly:
        layer = h.get('layer', 'Other')
        layer_actual[layer] = layer_actual.get(layer, 0) + h['current_value']

    cash_pct = round(portfolio.get('cash', 0) / total_value * 100, 1)
    layer_actual['Cash'] = portfolio.get('cash', 0)

    actual_pct = {
        layer: round(val / total_value * 100, 1)
        for layer, val in layer_actual.items()
    }
    drift = {
        layer: round(actual_pct.get(layer, 0) - layer_targets.get(layer, 0), 1)
        for layer in set(list(layer_targets.keys()) + list(actual_pct.keys()))
    }
    return {'actual': actual_pct, 'target': layer_targets, 'drift': drift}


# ── Day 4: החלטות + רענון ──────────────────────────────────────────────────

def build_decisions_this_month(decisions: list, period: str) -> list:
    """מסנן החלטות מהחודש הנוכחי בלבד."""
    year, month = period.split('-')
    prefix = f'{year}-{month}'
    return [d for d in decisions if d.get('date', '').startswith(prefix)]


def build_analysis_freshness(holdings: list) -> list:
    freshness = []
    now = datetime.now()
    for h in holdings:
        ticker = h['ticker']
        ic_path = os.path.join(ANALYSES_DIR, ticker, 'ic.js')
        if os.path.exists(ic_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(ic_path))
            days  = (now - mtime).days
            status = 'green' if days < 14 else ('yellow' if days < 45 else 'red')
        else:
            days   = 999
            status = 'red'
        freshness.append({'ticker': ticker, 'days_since': days, 'status': status})
    return freshness


# ── Day 5: Scanner Performance ─────────────────────────────────────────────

def build_scanner_calibration(period: str, prices: dict) -> tuple[dict, dict]:
    """
    בודק את כל המלצות הסורק מהחודש הנוכחי מול מחירים עדכניים.
    מחזיר: (calibration_json, scanner_performance_summary)
    """
    year, month = period.split('-')
    archive_glob = os.path.join(SCANNER_ARCHIVE, f'scanner-{year}-{month}-*.json')
    archive_files = sorted(glob(archive_glob))

    recommendations = []
    for fpath in archive_files:
        rec_date = os.path.basename(fpath).replace('scanner-', '').replace('.json', '')
        results  = load_json(fpath, default=[])
        if not isinstance(results, list):
            continue
        for r in results:
            ticker = r.get('ticker', '')
            if not ticker:
                continue
            entry_price  = r.get('entry_price') or r.get('price')
            upside_tgt   = r.get('upside_pct', 15)
            downside_tgt = r.get('downside_pct', 7)
            conviction   = r.get('conviction', 3)
            catalyst     = r.get('catalyst', '')

            curr_price = (prices.get(ticker) or {}).get('price')
            if not entry_price or not curr_price:
                outcome       = 'UNKNOWN'
                actual_return = None
            else:
                actual_return = round((curr_price - entry_price) / entry_price * 100, 2)
                if actual_return >= upside_tgt * 0.5:
                    outcome = 'SUCCESS'
                elif actual_return <= -downside_tgt:
                    outcome = 'FAIL'
                else:
                    outcome = 'PARTIAL'

            recommendations.append({
                'ticker':           ticker,
                'recommended_date': rec_date,
                'entry_price':      entry_price,
                'current_price':    curr_price,
                'conviction':       conviction,
                'upside_target_pct': upside_tgt,
                'downside_target_pct': downside_tgt,
                'actual_return_pct': actual_return,
                'outcome':          outcome,
                'catalyst':         catalyst[:100] if catalyst else '',
            })

    # חשב סטטיסטיקות
    known = [r for r in recommendations if r['outcome'] != 'UNKNOWN']
    successes = [r for r in known if r['outcome'] == 'SUCCESS']
    failures  = [r for r in known if r['outcome'] == 'FAIL']
    hit_rate  = round(len(successes) / len(known) * 100) if known else 0
    returns   = [r['actual_return_pct'] for r in known if r['actual_return_pct'] is not None]
    avg_return = round(sum(returns) / len(returns), 2) if returns else 0

    by_conviction: dict = {}
    for r in known:
        c = str(r['conviction'])
        by_conviction.setdefault(c, {'count': 0, 'hits': 0})
        by_conviction[c]['count'] += 1
        if r['outcome'] == 'SUCCESS':
            by_conviction[c]['hits'] += 1
    conviction_stats = {
        c: round(v['hits'] / v['count'] * 100) if v['count'] else 0
        for c, v in by_conviction.items()
    }

    best  = max(known, key=lambda r: r.get('actual_return_pct') or -999, default=None)
    worst = min(known, key=lambda r: r.get('actual_return_pct') or 999,  default=None)

    stats = {
        'total':           len(recommendations),
        'evaluated':       len(known),
        'hit_rate_pct':    hit_rate,
        'avg_return_pct':  avg_return,
        'successes':       len(successes),
        'failures':        len(failures),
        'by_conviction':   conviction_stats,
        'best_ticker':     best['ticker'] if best else '',
        'best_return_pct': best['actual_return_pct'] if best else None,
        'worst_ticker':    worst['ticker'] if worst else '',
        'worst_return_pct': worst['actual_return_pct'] if worst else None,
    }

    calibration = {
        'period':          period,
        'generated':       datetime.now().strftime('%Y-%m-%d'),
        'recommendations': recommendations,
        'stats':           stats,
    }
    performance_summary = {
        'hit_rate_pct':   hit_rate,
        'avg_return_pct': avg_return,
        'total_calls':    len(known),
        'by_conviction':  conviction_stats,
        'best_ticker':    best['ticker'] if best else '',
        'best_return_pct': best['actual_return_pct'] if best else None,
        'worst_ticker':   worst['ticker'] if worst else '',
        'worst_return_pct': worst['actual_return_pct'] if worst else None,
    }
    return calibration, performance_summary


# ── CEO Weekly Trend ────────────────────────────────────────────────────────

def build_weekly_trend() -> list:
    """מסכם 4 CEO weeklies האחרונים."""
    files = sorted(glob(os.path.join(WEEKLY_DIR, 'ceo_weekly_*.js')), reverse=True)[:4]
    trend = []
    for f in files:
        d = parse_js_data(f)
        trend.append({
            'date':    os.path.basename(f).replace('ceo_weekly_', '').replace('.js', ''),
            'verdict': d.get('ceo_verdict', '')[:120],
            'regime':  (d.get('portfolio_performance') or {}).get('regime', ''),
            'week_pct': (d.get('portfolio_performance') or {}).get('week_pct'),
        })
    return list(reversed(trend))


# ── Close Checklist ────────────────────────────────────────────────────────

def build_close_checklist(holdings_monthly: list, thesis: dict, allocation: dict,
                          decisions_this_month: list, scanner_perf: dict) -> list:
    """5-day close checklist עם סטטוס אוטומטי."""
    checks = [
        {
            'day': 'T+1',
            'task': 'ביצועי תיק חודשיים — P&L, מחירים, best/worst',
            'status': 'complete' if any(h.get('current_price') for h in holdings_monthly) else 'blocked',
            'note': f'{len(holdings_monthly)} פוזיציות עודכנו',
        },
        {
            'day': 'T+2',
            'task': 'Thesis Reconciliation — בדיקת תזה לכל אחזקה',
            'status': 'complete',
            'note': f'Thesis Score: {thesis.get("score_0_100", 0)}/100',
        },
        {
            'day': 'T+3',
            'task': 'Allocation Reconciliation — actual vs. target',
            'status': 'complete',
            'note': 'drift מחושב לכל שכבה',
        },
        {
            'day': 'T+4',
            'task': 'סקירת החלטות + ניתוחים מיושנים',
            'status': 'complete',
            'note': f'{len(decisions_this_month)} החלטות החודש',
        },
        {
            'day': 'T+5',
            'task': 'ביצועי ראדר + סגירה + אג\'נדה לחודש הבא',
            'status': 'complete' if scanner_perf.get('total_calls', 0) > 0 else 'partial',
            'note': f'Hit Rate: {scanner_perf.get("hit_rate_pct", "N/A")}%' if scanner_perf.get('total_calls') else 'אין נתוני ראדר עדיין',
        },
    ]
    return checks


# ── Prior Month Loader ─────────────────────────────────────────────────────

def load_prior_month_data(period: str) -> dict:
    """טוען monthly_close.js של החודש הקודם (לחישוב variance deltas)."""
    year, month = period.split('-')
    y, m = int(year), int(month)
    if m == 1:
        y, m = y - 1, 12
    else:
        m -= 1
    prior_period = f'{y:04d}-{m:02d}'
    prior_path = os.path.join(MONTHLY_DIR, prior_period, 'monthly_close.js')
    if os.path.exists(prior_path):
        return parse_js_data(prior_path)
    return {}


# ── כתיבת פלט ──────────────────────────────────────────────────────────────

def write_monthly_close(period: str, data: dict) -> str:
    out_dir = os.path.join(MONTHLY_DIR, period)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'monthly_close.js')
    js = f'window.MONTHLY_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(js)
    print(f'[monthly_close] כתב {path}')
    return path


def write_scanner_calibration(period: str, calibration: dict) -> str:
    out_dir = os.path.join(MONTHLY_DIR, period)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'scanner_calibration.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(calibration, f, ensure_ascii=False, indent=2)
    print(f'[monthly_close] כתב {path}')
    return path


# ── ריצה ─────────────────────────────────────────────────────────────────────

def run(period: str | None = None) -> dict:
    """
    period: 'YYYY-MM' (ברירת מחדל: החודש הנוכחי)
    מחזיר את monthly_data שנכתב.
    """
    if not period:
        period = datetime.now().strftime('%Y-%m')
    print(f'[monthly_close] מריץ סגירת חודש {period}...')

    portfolio = load_json(PORTFOLIO_JSON)
    decisions = load_json(DECISION_LOG, default={'decisions': []}).get('decisions', [])
    holdings  = portfolio.get('holdings', [])
    tickers   = [h.get('symbol') or h.get('ticker', '') for h in holdings if h.get('symbol') or h.get('ticker')]

    # שלוף מחירים (כולל כל הטיקרים מהסורק)
    scanner_tickers = set()
    scanner_archive_glob = os.path.join(SCANNER_ARCHIVE, f'scanner-{period[:4]}-{period[5:]}-*.json')
    for fpath in glob(scanner_archive_glob):
        for r in (load_json(fpath, default=[]) or []):
            if isinstance(r, dict) and r.get('ticker'):
                scanner_tickers.add(r['ticker'])
    all_tickers = list(set(tickers) | scanner_tickers)
    print(f'[monthly_close] שולף מחירים ל-{len(all_tickers)} טיקרים...')
    prices_raw = get_prices_batch(all_tickers)
    # prices_raw[ticker] = {'price': X, 'chg_month': Y}
    # לסורק צריך רק price
    prices_flat = {t: d for t, d in prices_raw.items()}

    # בנה כל שכבה
    portfolio_perf, holdings_monthly = build_portfolio_performance(portfolio, prices_raw)
    thesis_summary, thesis_detail     = build_thesis_adherence(holdings_monthly, decisions)
    allocation                         = build_allocation(portfolio, holdings_monthly)
    decisions_this_month               = build_decisions_this_month(decisions, period)
    freshness                          = build_analysis_freshness(holdings_monthly)
    weekly_trend                       = build_weekly_trend()

    # scanner calibration
    calibration, scanner_perf = build_scanner_calibration(period, prices_flat)
    write_scanner_calibration(period, calibration)

    close_checklist = build_close_checklist(
        holdings_monthly, thesis_summary, allocation,
        decisions_this_month, scanner_perf,
    )

    # next month agenda
    stale = [h['ticker'] for h in freshness if h['status'] == 'red']
    review_needed = [h['ticker'] for h in holdings_monthly
                     if h.get('ic_verdict', '').upper() in ('REDUCE', 'SELL', 'EXIT')]
    next_month_agenda = {
        'refresh_analyses': stale,
        'review_positions': review_needed,
        'scanner_targets':  [r['ticker'] for r in calibration['recommendations']
                              if r['outcome'] == 'SUCCESS'][:3],
    }

    # variance attribution (אפס LLM)
    prior_data = load_prior_month_data(period)
    variance_block = build_variance_block(
        holdings_monthly, portfolio, scanner_perf, thesis_summary, prior_data
    )

    monthly_data = {
        'period':    period,
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        # Day 1
        'portfolio_performance': portfolio_perf,
        'holdings_monthly':      holdings_monthly,
        # Day 2
        'thesis_adherence':  thesis_summary,
        'thesis_detail':     thesis_detail,
        # Day 3
        'allocation':        allocation,
        # Day 4
        'decisions_this_month': decisions_this_month,
        'analysis_freshness':   freshness,
        'weekly_trend':         weekly_trend,
        # Day 5
        'scanner_performance':           scanner_perf,
        'scanner_recommendations_review': calibration['recommendations'],
        'next_month_agenda':             next_month_agenda,
        'close_checklist':               close_checklist,
        # variance attribution
        'variance':                      variance_block,
    }

    write_monthly_close(period, monthly_data)
    print(f'[monthly_close] סגירת חודש {period} הושלמה.')
    return monthly_data


if __name__ == '__main__':
    period_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run(period_arg)
