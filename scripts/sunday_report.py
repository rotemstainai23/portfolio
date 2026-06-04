"""
דוח ראשון — 5:00.
מרכיב דוח CEO שבועי מנתונים קיימים.
אם יש ANTHROPIC_API_KEY — מריץ CEO_Weekly_Agent לניתוח עמוק.
בכל מקרה שולח הודעה ומעדכן את ceo_weekly.js.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from notifications import send_both

PORTFOLIO_JSON  = os.path.join(ROOT, 'portfolio.json')
ANALYSES_DIR    = os.path.join(ROOT, 'analyses')
SCANNER_RESULTS = os.path.join(ROOT, 'scanner-results.json')
SUNDAY_TARGET   = os.path.join(ROOT, 'sunday-analysis-target.json')
WEEKLY_JS       = os.path.join(ANALYSES_DIR, '_weekly', 'ceo_weekly.js')
WEEKLY_DIR      = os.path.join(ANALYSES_DIR, '_weekly')
FLASK_BASE      = os.environ.get('FLASK_BASE', 'http://127.0.0.1:5000')


# ── עזרים ───────────────────────────────────────────────────────────────────

def load_json(path: str, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def get_prices(tickers: list[str]) -> dict:
    results = {}
    for ticker in tickers:
        try:
            url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
                   f'?interval=1d&range=7d')
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.load(r)
            meta  = data['chart']['result'][0]['meta']
            close = data['chart']['result'][0].get('indicators', {}).get('quote', [{}])[0].get('close', [])
            current  = meta.get('regularMarketPrice', 0)
            week_ago = close[0] if close else current
            chg_week = ((current - week_ago) / week_ago * 100) if week_ago else 0
            results[ticker] = {
                'price':    round(current, 2),
                'chg_week': round(chg_week, 2),
            }
        except Exception:
            results[ticker] = {'price': None, 'chg_week': None}
    return results


# ── בניית דוח ממידע קיים ────────────────────────────────────────────────────

def build_weekly_data_from_files(portfolio: dict, prices: dict) -> dict:
    """בונה weekly data JSON מנתונים קיימים ללא Claude."""
    today = datetime.now().strftime('%Y-%m-%d')
    week_start = (datetime.now() - timedelta(days=6)).strftime('%d/%m')
    week_end   = datetime.now().strftime('%d/%m')

    holdings_weekly = []
    for h in portfolio.get('holdings', []):
        ticker = h.get('symbol') or h.get('ticker', '')
        if not ticker:
            continue
        rev_dir = os.path.join(ANALYSES_DIR, ticker, '_reviews')
        ic_rv   = load_json(os.path.join(rev_dir, 'ic.json'))
        an_rv   = load_json(os.path.join(rev_dir, 'analyst.json'))
        rv      = ic_rv if ic_rv else an_rv
        p       = prices.get(ticker, {})

        holdings_weekly.append({
            'ticker':           ticker,
            'company':          rv.get('company', ticker),
            'price_change_pct': p.get('chg_week'),
            'status':           rv.get('verdict', 'UNKNOWN'),
            'headline':         rv.get('handoff_summary', '')[:120],
            'thesis_check':     'HOLDING' if rv.get('verdict') in ('INTACT', 'BUY') else 'REVIEW',
            'key_news':         rv.get('thesis', '')[:100],
        })

    scanner = load_json(SCANNER_RESULTS, default=[])
    opportunities = [
        {
            'ticker':         o.get('ticker'),
            'catalyst':       o.get('catalyst'),
            'conviction':     o.get('conviction'),
            'timeframe':      o.get('timeframe'),
            'why_not_others': f'R/R {o.get("upside_pct",0)}/{o.get("downside_pct",0)}, {o.get("sector","")}',
        }
        for o in sorted(scanner, key=lambda x: x.get('conviction', 0), reverse=True)[:3]
    ]

    return {
        'generated':  today,
        'week_label': f'שבוע {week_start}-{week_end}',
        'portfolio_performance': {
            'week_pct':   None,
            'ytd_pct':    None,
            'vs_spy_week': None,
            'regime':     'mixed',
            'regime_confidence': 'low',
        },
        'holdings_weekly': holdings_weekly,
        'macro_snapshot':  {
            'vix': None, 'spy_week_pct': None, 'qqq_week_pct': None,
            'dxy_trend': 'flat', 'rate_outlook': 'neutral',
            'regime_note': 'נתוני מקרו לא זמינים — הפעל CEO_Weekly_Agent לניתוח עמוק',
        },
        'risk_matrix':   [],
        'opportunities': opportunities,
        'scenarios_next_week': {
            'bull': {'probability_pct': 35, 'trigger': 'ראה CEO_Weekly_Agent', 'outcome': ''},
            'base': {'probability_pct': 45, 'trigger': 'ראה CEO_Weekly_Agent', 'outcome': ''},
            'bear': {'probability_pct': 20, 'trigger': 'ראה CEO_Weekly_Agent', 'outcome': ''},
        },
        'ceo_verdict':  'דוח בסיסי — הרץ CEO_Weekly_Agent לניתוח מלא',
        'action_items': [],
    }


def run_ceo_weekly_via_flask() -> dict | None:
    """מריץ CEO Weekly דרך Flask API (/api/ceo-weekly/run)."""
    try:
        req = urllib.request.Request(
            f'{FLASK_BASE}/api/ceo-weekly/run',
            data=b'{}',
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.load(r)
        run_id = resp.get('run_id')
        if not run_id:
            return None
        print(f'[sunday] CEO weekly run_id={run_id} — ממתין...')
        for _ in range(20):
            time.sleep(30)
            try:
                with urllib.request.urlopen(
                    f'{FLASK_BASE}/api/run-status/{run_id}', timeout=10
                ) as sr:
                    status = json.load(sr)
                if status.get('status') == 'done':
                    json_path = WEEKLY_JS.replace('.js', '.json')
                    return load_json(json_path) or {}
            except Exception:
                pass
    except Exception as e:
        print(f'[sunday] Flask לא נגיש: {e}')
    return None


def archive_weekly_js() -> None:
    """ארכב גרסה קודמת של ceo_weekly.js לפני דריסה."""
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
        print(f'[sunday] ארכב weekly ל-{dest_path}')
        # שמור עד 8 קבצים (2 חודשים)
        from glob import glob as _glob
        archives = sorted(_glob(os.path.join(WEEKLY_DIR, 'ceo_weekly_*.js')))
        for old in archives[:-8]:
            os.remove(old)
    except Exception as e:
        print(f'[sunday] שגיאת ארכיב: {e}')


def is_fourth_sunday() -> bool:
    """True אם היום הוא ה-Sunday הרביעי של החודש (day >= 22)."""
    today = datetime.now()
    return today.weekday() == 6 and today.day >= 22


def run_monthly_close() -> None:
    """מריץ סגירת חודש אחרי ה-CEO שבועי."""
    try:
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        monthly_script = os.path.join(scripts_dir, 'monthly_close.py')
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


def write_weekly_js(data: dict) -> None:
    """כותב ceo_weekly.js לדשבורד."""
    os.makedirs(os.path.dirname(WEEKLY_JS), exist_ok=True)
    js = f'window.WEEKLY_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n'
    with open(WEEKLY_JS, 'w', encoding='utf-8') as f:
        f.write(js)
    print(f'[sunday] כתב {WEEKLY_JS}')


def build_wow_delta(current_data: dict, prices: dict) -> dict:
    """
    מחשב שינוי שבועי: ערך תיק, מניות שזזו הכי הרבה, ו-allocation flags.
    משתמש ב-chg_week מ-prices ובארכיב הקודם של ceo_weekly.
    """
    from glob import glob as _glob

    holdings = current_data.get('holdings_weekly', [])
    movers = []
    for h in holdings:
        tk  = h.get('ticker', '')
        chg = (prices.get(tk) or {}).get('chg_week')
        if chg is not None:
            movers.append({'ticker': tk, 'chg_week': chg})
    movers.sort(key=lambda x: abs(x['chg_week']), reverse=True)

    # השווה לארכיב השבוע הקודם
    archives = sorted(_glob(os.path.join(WEEKLY_DIR, 'ceo_weekly_*.js')))
    prior_value = None
    if archives:
        import re as _re
        try:
            with open(archives[-1], encoding='utf-8') as f:
                content = f.read()
            match = _re.search(r'=\s*(\{[\s\S]*\})\s*;?\s*$', content)
            if match:
                import json as _json
                prior = _json.loads(match.group(1))
                prior_value = (prior.get('portfolio_performance') or {}).get('total_value')
        except Exception:
            pass

    return {
        'top_movers':    movers[:3],
        'prior_value':   prior_value,
    }


def format_telegram_message(data: dict) -> tuple[str, str]:
    today = datetime.now().strftime('%d/%m/%Y')
    holdings = data.get('holdings_weekly', [])

    wow      = data.get('wow_delta') or {}
    lines_tg = [f'*דוח CEO שבועי — {today}*\n*{data.get("week_label","")}*\n']
    lines_wa = [f'דוח CEO שבועי {today}\n']

    # ביצועי אחזקות
    for h in holdings:
        tk  = h.get('ticker', '')
        chg = h.get('price_change_pct')
        chg_str = (f'{chg:+.1f}%' if chg is not None else '?')
        st  = h.get('status', '')
        lines_tg.append(f'· *{tk}* {chg_str} — {st}')
        lines_wa.append(f'· {tk} {chg_str} {st}')

    # הזדמנויות
    opps = data.get('opportunities', [])
    if opps:
        lines_tg.append('\n*הזדמנויות שבוע:*')
        lines_wa.append('\nהזדמנויות:')
        for o in opps[:2]:
            lines_tg.append(f'· *{o.get("ticker")}* — {o.get("catalyst","")[:80]}')
            lines_wa.append(f'· {o.get("ticker")} — {o.get("catalyst","")[:60]}')

    # פסיקת מנכ"ל
    verdict = data.get('ceo_verdict', '')
    if verdict:
        lines_tg.append(f'\n*פסיקת מנכ"ל:* {verdict}')

    # שינוי שבועי (top movers)
    movers = wow.get('top_movers') or []
    if movers:
        lines_tg.append('\n*שינויים שבועיים:*')
        lines_wa.append('\nשינויים:')
        for mv in movers[:3]:
            chg_str = f'{mv["chg_week"]:+.1f}%'
            lines_tg.append(f'· *{mv["ticker"]}* {chg_str}')
            lines_wa.append(f'· {mv["ticker"]} {chg_str}')

    # לינק לדשבורד
    dashboard_url = os.environ.get('DASHBOARD_URL', '')
    if dashboard_url:
        lines_tg.append(f'\n[פתח דשבורד שבועי]({dashboard_url}/templates/ceo-weekly.html)')

    return '\n'.join(lines_tg), '\n'.join(lines_wa)


# ── ריצה ─────────────────────────────────────────────────────────────────────

def main():
    print('[sunday_report] מתחיל...')
    archive_weekly_js()
    portfolio = load_json(PORTFOLIO_JSON)
    all_tickers = [
        h.get('symbol') or h.get('ticker', '')
        for h in portfolio.get('holdings', [])
        if h.get('symbol') or h.get('ticker')
    ]
    prices = get_prices(all_tickers)
    print(f'[sunday_report] שלף מחירים ל-{len(prices)} טיקרים')

    # נסה Flask קודם לניתוח עמוק
    weekly_data = run_ceo_weekly_via_flask()

    # אחרת בנה מנתונים קיימים (חינם)
    if not weekly_data:
        print('[sunday_report] בונה דוח בסיסי מנתונים קיימים...')
        weekly_data = build_weekly_data_from_files(portfolio, prices)

    wow_delta = build_wow_delta(weekly_data, prices)
    weekly_data['wow_delta'] = wow_delta
    write_weekly_js(weekly_data)

    full_tg, short_wa = format_telegram_message(weekly_data)
    result = send_both(short_text=short_wa, full_text=full_tg)
    print(f'[sunday_report] נשלח: {result}')

    if is_fourth_sunday():
        print('[sunday_report] Sunday רביעי — מריץ סגירת חודש...')
        run_monthly_close()


if __name__ == '__main__':
    main()
