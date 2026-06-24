"""
Investment OS — Python/Flask Backend
Launch : python app.py  (or via start.bat)
Dashboard: http://127.0.0.1:5000
"""

import json
import os
import re
import shutil
import subprocess
import time
import threading
import webbrowser
from datetime import datetime

# truststore: use Windows native certificate store (fixes Yahoo SSL handshake on
# Python distributions whose certifi bundle lacks the relevant intermediate CAs).
# Must be imported and injected BEFORE the requests import to take effect.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import requests as _requests
from flask import Flask, jsonify, request, send_file, send_from_directory

try:
    import yfinance as yf
    _HAS_YF = True
except ImportError:
    _HAS_YF = False

ROOT           = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_FILE = os.path.join(ROOT, 'portfolio.json')
ANALYSES_DIR   = os.path.join(ROOT, 'analyses')
PROMPTS_DIR    = os.path.join(ROOT, 'מערכת תיק ההשקעות')
CONFIG_FILE    = os.path.join(ROOT, 'config.json')
DECISIONS_FILE = os.path.join(ROOT, 'decision_log.json')

PROMPT_FILES = {
    'analyst':  'Unified_Analyst.md',
    'devils':   'DevilsAdvocate_Updated.md',
    'ceo':      'CEO_Agent_Updated.md',
    'executor': 'Executor_Updated.md',
    'ic':       'InvestmentCommittee_Updated.md',
    'scanner':  'Scanner_Agent.md',
    'health':   'Portfolio_Health_Agent.md',
}

AGENT_ORDER = ['analyst', 'devils', 'ceo', 'executor', 'ic']
AGENT_LABELS = {
    'analyst':  'Analyst',
    'devils':   'Devil\'s Advocate',
    'ceo':      'CEO',
    'executor': 'Executor',
    'ic':       'Investment Committee',
}

# Run-tracking (in-memory; killed on restart, which is fine for a local single-user app)
_runs: dict = {}
_runs_lock = threading.Lock()

app = Flask(__name__, static_folder=None)

_price_cache: dict = {}  # {sym: {'ts': float, 'data': {current_price, day_change_pct}}}
_price_lock        = threading.Lock()
CACHE_TTL          = 45
STALE_MAX_AGE      = 14_400  # 4h — prices older than this are refused, not shown as stale


# ── Data helpers ──────────────────────────────────────────────────────────────

def load_portfolio() -> dict:
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'cash': 0, 'holdings': [], 'trades': [], 'watchlist': []}


def save_portfolio(data: dict):
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _fetch_yahoo_price(sym: str) -> dict:
    """Source 1: Yahoo Finance v8 chart API (two CDN hosts). Returns dict or Nones."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept':     'application/json',
    }
    for host in ('query1', 'query2'):
        try:
            url = (f'https://{host}.finance.yahoo.com/v8/finance/chart/{sym}'
                   f'?interval=1d&range=2d&includePrePost=false')
            r = _requests.get(url, headers=headers, timeout=6)
            if r.ok:
                result = r.json().get('chart', {}).get('result') or []
                if not result:
                    continue
                meta = result[0]['meta']
                curr = meta.get('regularMarketPrice')
                prev = meta.get('previousClose') or meta.get('chartPreviousClose')
                if curr:
                    chg = (curr - prev) / prev * 100 if prev and prev > 0 else None
                    return {'current_price': float(curr), 'day_change_pct': chg, 'source': 'yahoo'}
        except Exception as e:
            ts = datetime.now().strftime('%H:%M:%S')
            print(f'[{ts}] Yahoo {host} {sym}: {type(e).__name__}: {e}')
    return {'current_price': None, 'day_change_pct': None, 'source': None}


def _fetch_nasdaq_price(sym: str) -> dict:
    """Source 3: Nasdaq official quote API — free, JSON, independent from Yahoo."""
    try:
        # Nasdaq provides asset class hints; try stocks first, then etf
        for asset_class in ('stocks', 'etf', 'index'):
            url = f'https://api.nasdaq.com/api/quote/{sym}/info?assetclass={asset_class}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'application/json, text/plain, */*',
            }
            r = _requests.get(url, headers=headers, timeout=8)
            if not r.ok:
                continue
            body = r.json()
            primary = (body.get('data') or {}).get('primaryData') or {}
            raw = primary.get('lastSalePrice', '')
            # Strip "$" and "," e.g. "$1,035.50" → 1035.50
            raw_clean = raw.replace('$', '').replace(',', '').strip()
            if raw_clean and raw_clean not in ('--', 'N/A', ''):
                price = float(raw_clean)
                if price > 0:
                    # Parse percentage change
                    pct_raw = primary.get('percentageChange', '').replace('%', '').replace('+', '').strip()
                    chg = float(pct_raw) if pct_raw and pct_raw not in ('--', 'N/A') else None
                    return {'current_price': price, 'day_change_pct': chg, 'source': 'nasdaq'}
    except Exception as e:
        ts = datetime.now().strftime('%H:%M:%S')
        print(f'[{ts}] Nasdaq {sym}: {type(e).__name__}: {e}')
    return {'current_price': None, 'day_change_pct': None, 'source': None}


def _fetch_finviz_price(sym: str) -> dict:
    """Source 2: Finviz quote page — fallback when Yahoo fails."""
    try:
        url = f'https://finviz.com/quote.ashx?t={sym}&ty=c&ta=1&p=d'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finviz.com/',
        }
        r = _requests.get(url, headers=headers, timeout=10)
        if r.ok:
            # Try multiple patterns — Finviz layout varies by version
            patterns = [
                r'"regularMarketPrice":\s*([\d.]+)',          # embedded JSON
                r'class="quote-price[^"]*"[^>]*>([\d.,]+)',   # new layout
                r'snapshot-td2-cp[^>]*><b>([\d.,]+)</b>',     # old table layout
                r'<strong[^>]*id="last"[^>]*>([\d.,]+)',       # alt layout
                r'Last\s+Price[^<]*<[^>]*>([\d.,]+)',          # text match
            ]
            for pat in patterns:
                m = re.search(pat, r.text)
                if m:
                    price = float(m.group(1).replace(',', ''))
                    if price > 0:
                        return {'current_price': price, 'day_change_pct': None, 'source': 'finviz'}
    except Exception as e:
        ts = datetime.now().strftime('%H:%M:%S')
        print(f'[{ts}] Finviz {sym}: {type(e).__name__}: {e}')
    return {'current_price': None, 'day_change_pct': None, 'source': None}


def get_prices(symbols: list) -> dict:
    """Per-symbol cache (45s TTL) + last-known-good fallback.
    Sources: Yahoo v8 (primary) → Finviz (secondary).
    Prices older than STALE_MAX_AGE (4h) are treated as expired — not shown.

    Cache shape: { sym: {'data': {current_price,day_change_pct,source}, 'ts': float} }
    Response shape: {'current_price', 'day_change_pct', 'stale_age_s': int|None, 'source': str|None}
    """
    now = time.time()
    results: dict = {}
    if not symbols:
        return results

    fresh, stale, expired, failed = [], [], [], []

    for sym in symbols:
        with _price_lock:
            cached = _price_cache.get(sym)

        # Warm cache
        if cached and now - cached['ts'] < CACHE_TTL:
            results[sym] = {**cached['data'], 'stale_age_s': None}
            continue

        # Fetch — Yahoo (1) → Finviz (2) → Nasdaq (3)
        data = _fetch_yahoo_price(sym)
        if data['current_price'] is None:
            data = _fetch_finviz_price(sym)
        if data['current_price'] is None:
            data = _fetch_nasdaq_price(sym)

        if data['current_price'] is not None:
            with _price_lock:
                _price_cache[sym] = {'ts': now, 'data': data}
            results[sym] = {**data, 'stale_age_s': None}
            fresh.append(f"{sym}({data.get('source','?')})")
        elif cached:
            age = int(now - cached['ts'])
            if age > STALE_MAX_AGE:
                # Too old to trust — serve None so UI shows "unavailable"
                results[sym] = {'current_price': None, 'day_change_pct': None,
                                'stale_age_s': age, 'source': None}
                expired.append(f'{sym}({age}s)')
            else:
                results[sym] = {**cached['data'], 'stale_age_s': age}
                stale.append(f'{sym}({age}s)')
        else:
            results[sym] = {**data, 'stale_age_s': None}
            failed.append(sym)

    ts = datetime.now().strftime('%H:%M:%S')
    if fresh:   print(f'[{ts}] prices OK: {" ".join(fresh)}')
    if stale:   print(f'[{ts}] prices STALE: {" ".join(stale)}')
    if expired: print(f'[{ts}] prices EXPIRED(>4h): {" ".join(expired)}')
    if failed:  print(f'[{ts}] prices FAIL: {" ".join(failed)}')
    return results


def next_trade_id(trades: list) -> str:
    nums = []
    for t in trades:
        try:
            nums.append(int(t.get('trade_id', '').split('-')[1]))
        except Exception:
            pass
    return f'TRD-{(max(nums) + 1):03d}' if nums else 'TRD-001'


def _extract_analysis_meta(ticker: str) -> dict:
    """חילוץ metadata בסיסי מ-analyst.js לטיקר נתון."""
    fpath = os.path.join(ANALYSES_DIR, ticker, 'analyst.js')
    if not os.path.exists(fpath):
        return {}
    try:
        content = open(fpath, encoding='utf-8').read()
        out = {}
        for key, pattern in (
            ('date',    r'date:\s*["\']([^"\']+)["\']'),
            ('company', r'company:\s*["\']([^"\']+)["\']'),
        ):
            m = re.search(pattern, content)
            if m:
                out[key] = m.group(1)
        for key, pattern in (
            ('price_at_analysis', r'price_current:\s*([\d.]+)'),
        ):
            m = re.search(pattern, content)
            if m:
                out[key] = float(m.group(1))
        return out
    except Exception:
        return {}


# ── Static file serving ───────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_file(os.path.join(ROOT, 'portfolio.html'))


@app.route('/scanner-inject')
def scanner_inject():
    return send_file(os.path.join(ROOT, 'scanner-inject.html'))


@app.route('/api/scanner')
def api_scanner():
    """מחזיר תוצאות סריקה מה-JSON שכותב Claude Code."""
    p = os.path.join(ROOT, 'scanner-results.json')
    if not os.path.exists(p):
        return jsonify([])
    with open(p, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/scanner/run', methods=['POST'])
def api_scanner_run():
    """מפעיל סריקה חדשה של Goldman Sachs Scanner Agent ב-thread נפרד."""
    run_id = f'scanner_{int(time.time())}'
    with _runs_lock:
        _runs[run_id] = {'run_id': run_id, 'agent': 'scanner',
                         'status': 'queued', 'started': datetime.now().isoformat()}

    def _run_scanner(rid):
        def upd(**kw):
            with _runs_lock:
                _runs[rid].update(kw)
        try:
            upd(status='running')
            sys_path = os.path.join(PROMPTS_DIR, PROMPT_FILES['scanner'])
            with open(sys_path, encoding='utf-8') as f:
                sys_prompt = f.read()
            # הוסף context תיק נוכחי (לסינון מניות קיימות)
            portfolio = load_portfolio()
            held = [h['symbol'] for h in portfolio.get('holdings', [])]
            watch = [w['symbol'] for w in portfolio.get('watchlist', [])]
            ctx_block = f'## מניות קיימות בתיק (אל תכלול אותן בסריקה)\nHoldings: {", ".join(held)}\nWatchlist: {", ".join(watch)}\n'
            res = _run_llm(sys_prompt, ctx_block, timeout=480)
            if not res['ok'] or not res['output'].strip():
                upd(status='failed', error=res.get('error') or 'empty output',
                    finished=datetime.now().isoformat())
                return
            # נסה לפרסר JSON מהפלט
            output = res['output'].strip()
            # הסר backticks אם קיימים
            output = re.sub(r'^```(?:json)?\s*', '', output)
            output = re.sub(r'\s*```$', '', output)
            try:
                results = json.loads(output)
                if not isinstance(results, list):
                    results = []
            except Exception:
                # נסה למצוא מערך JSON בפלט
                m = re.search(r'\[[\s\S]*\]', output)
                results = json.loads(m.group()) if m else []
            # שמור תוצאות
            out_path = os.path.join(ROOT, 'scanner-results.json')
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            upd(status='done', count=len(results), finished=datetime.now().isoformat())
        except Exception as e:
            upd(status='failed', error=str(e), finished=datetime.now().isoformat())

    threading.Thread(target=_run_scanner, args=(run_id,), daemon=True).start()
    return jsonify({'run_id': run_id})


# ── API: portfolio health monitor ────────────────────────────────────────────

def _build_health_context(portfolio: dict) -> str:
    """בונה context מפורט לHealth Agent: holdings, kill switches, וסטטוס אחרון."""
    holdings = portfolio.get('holdings', [])
    watchlist = portfolio.get('watchlist', [])
    watch_by_sym = {w['symbol']: w for w in watchlist}

    lines = ['## תיק נוכחי\n']
    for h in sorted(holdings, key=lambda x: -x.get('risk_score', 0)):
        sym = h['symbol']
        lines.append(
            f"- **{sym}** ({h.get('name','')}) | "
            f"Sector: {h.get('sector','-')} | Layer: {h.get('layer','-')} | "
            f"risk_score: {h.get('risk_score','-')}/10 | "
            f"buy_price: ${h.get('buy_price','-')} | qty: {h.get('quantity','-')}"
        )
        # kill switch מה-watchlist
        w = watch_by_sym.get(sym)
        if w:
            if w.get('kill_switch'):
                lines.append(f"  kill_switch: {w['kill_switch']}")
            if w.get('thesis'):
                lines.append(f"  thesis: {w['thesis'][:150]}")
            if w.get('trigger_price'):
                lines.append(f"  trigger: ${w['trigger_price']} ({w.get('trigger_direction','below')})")
        # סטטוס quick-check אחרון
        qpath = os.path.join(ANALYSES_DIR, sym, '_reviews', 'quick.json')
        if os.path.exists(qpath):
            try:
                with open(qpath, encoding='utf-8') as f:
                    q = json.load(f)
                lines.append(
                    f"  last_check: {q.get('verdict','?')} "
                    f"(score:{q.get('score','?')}) — {q.get('handoff_summary','')[:80]}"
                )
            except Exception:
                pass

    return '\n'.join(lines)


@app.route('/api/portfolio/health', methods=['POST'])
def api_portfolio_health():
    """מפעיל בדיקת בריאות תיק מלאה (batch Health Agent)."""
    run_id = f'health_{int(time.time())}'
    with _runs_lock:
        _runs[run_id] = {'run_id': run_id, 'agent': 'health',
                         'status': 'queued', 'started': datetime.now().isoformat()}

    def _run_health(rid):
        def upd(**kw):
            with _runs_lock:
                _runs[rid].update(kw)
        try:
            upd(status='running')
            sys_path = os.path.join(PROMPTS_DIR, PROMPT_FILES['health'])
            with open(sys_path, encoding='utf-8') as f:
                sys_prompt = f.read()
            portfolio = load_portfolio()
            ctx_block = _build_health_context(portfolio)
            timeout = 480
            res = _run_llm(sys_prompt, ctx_block, timeout=timeout)
            # ניסיון נוסף אחד אם נכשל
            if not res['ok'] or not res['output'].strip():
                print(f'[RETRY] health — {res.get("error","empty output")}')
                res = _run_llm(sys_prompt, ctx_block, timeout=timeout)
            if not res['ok'] or not res['output'].strip():
                upd(status='failed', error=res.get('error') or 'empty output',
                    finished=datetime.now().isoformat())
                return
            # פרסר JSON
            output = res['output'].strip()
            output = re.sub(r'^```(?:json)?\s*', '', output, flags=re.MULTILINE)
            output = re.sub(r'\s*```\s*$', '', output, flags=re.MULTILINE)
            try:
                results = json.loads(output)
                if not isinstance(results, list):
                    results = []
            except Exception:
                m = re.search(r'\[[\s\S]*\]', output)
                results = json.loads(m.group()) if m else []
            # שמור health report
            now = datetime.now()
            report = {
                'run_date': now.strftime('%Y-%m-%d'),
                'run_time': now.strftime('%H:%M'),
                'tickers_checked': len(results),
                'results': results,
                'summary': {
                    'intact': sum(1 for r in results if r.get('status') == 'INTACT'),
                    'review': sum(1 for r in results if r.get('status') == 'REVIEW'),
                    'rerun':  sum(1 for r in results if r.get('status') == 'RERUN'),
                    'urgent': sum(1 for r in results if r.get('status') == 'URGENT'),
                }
            }
            out_path = os.path.join(ROOT, 'portfolio-health.json')
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            # Obsidian (fail-soft)
            try:
                import obsidian_layer
                obsidian_layer.save_health_report(report)
            except Exception as e:
                print(f'[obsidian health] {e}')
            upd(status='done', summary=report['summary'],
                finished=now.isoformat())
        except Exception as e:
            upd(status='failed', error=str(e), finished=datetime.now().isoformat())

    threading.Thread(target=_run_health, args=(run_id,), daemon=True).start()
    return jsonify({'run_id': run_id})


@app.route('/api/portfolio/health/latest')
def api_portfolio_health_latest():
    """מחזיר את בדיקת הבריאות האחרונה."""
    p = os.path.join(ROOT, 'portfolio-health.json')
    if not os.path.exists(p):
        return jsonify(None)
    with open(p, encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/ceo-weekly/run', methods=['POST'])
def api_ceo_weekly_run():
    """מפעיל CEO Weekly Intelligence Briefing (סקירת תיק שבועית מקיפה)."""
    run_id = f'ceo_weekly_{int(time.time())}'
    with _runs_lock:
        _runs[run_id] = {'run_id': run_id, 'agent': 'ceo_weekly',
                         'status': 'queued', 'started': datetime.now().isoformat()}

    def _run_ceo_weekly(rid):
        def upd(**kw):
            with _runs_lock:
                _runs[rid].update(kw)
        try:
            upd(status='running')
            sys_path = os.path.join(PROMPTS_DIR, PROMPT_FILES.get('ceo_weekly', 'CEO_Weekly_Agent.md'))
            if not os.path.exists(sys_path):
                sys_path = os.path.join(PROMPTS_DIR, 'CEO_Weekly_Agent.md')
            with open(sys_path, encoding='utf-8') as f:
                sys_prompt = f.read()

            portfolio = load_portfolio()
            today     = datetime.now().strftime('%Y-%m-%d')

            # context: snapshot + watchlist + כל ה-reviews + scanner
            context_parts = [
                f'DATE: {today}',
                f'AGENT: CEO Weekly Intelligence Briefing',
                '', '━━━ PORTFOLIO SNAPSHOT ━━━',
                _portfolio_snapshot_compact(),
                '', '━━━ WATCHLIST ━━━',
                _watchlist_compact(),
            ]
            # כל ה-reviews
            all_reviews = []
            analyses_dir = os.path.join(ROOT, 'analyses')
            if os.path.isdir(analyses_dir):
                for tk_dir in sorted(os.listdir(analyses_dir)):
                    rev_dir = os.path.join(analyses_dir, tk_dir, '_reviews')
                    if not os.path.isdir(rev_dir):
                        continue
                    for rv_file in ['ic.json', 'analyst.json']:
                        rv_path = os.path.join(rev_dir, rv_file)
                        if os.path.exists(rv_path):
                            try:
                                with open(rv_path, encoding='utf-8') as f:
                                    rv = json.load(f)
                                all_reviews.append(
                                    f'{tk_dir}: {rv.get("verdict","?")} {rv.get("score","?")} — '
                                    f'{rv.get("thesis","")[:100]}'
                                )
                            except Exception:
                                pass
                            break
            if all_reviews:
                context_parts += ['', '━━━ CURRENT REVIEWS (כל האחזקות) ━━━']
                context_parts.extend(all_reviews)

            # scanner results
            scanner_path = os.path.join(ROOT, 'scanner-results.json')
            if os.path.exists(scanner_path):
                try:
                    with open(scanner_path, encoding='utf-8') as f:
                        scanner_data = json.load(f)
                    if scanner_data:
                        context_parts += ['', '━━━ SCANNER RESULTS (מהסקנר האחרון) ━━━']
                        for opp in scanner_data[:5]:
                            context_parts.append(
                                f'{opp.get("ticker")}: {opp.get("catalyst","")} '
                                f'(conviction {opp.get("conviction")}/5)'
                            )
                except Exception:
                    pass

            context_parts += ['', '━━━ END OF CONTEXT ━━━']
            _ceo_ctx = '\n'.join(context_parts)

            res = _run_llm(sys_prompt, _ceo_ctx, timeout=600)
            if not res['ok'] or not res['output'].strip():
                print(f'[RETRY] ceo_weekly — {res.get("error","empty output")}')
                res = _run_llm(sys_prompt, _ceo_ctx, timeout=600)
            if not res['ok'] or not res['output'].strip():
                upd(status='failed', error=res.get('error') or 'empty output',
                    finished=datetime.now().isoformat())
                return

            # חלץ dashboard-json בלוק
            dash_data = _extract_dashboard_json(res['output'])

            # שמור JS לדשבורד
            weekly_dir = os.path.join(ROOT, 'analyses', '_weekly')
            os.makedirs(weekly_dir, exist_ok=True)
            js_path   = os.path.join(weekly_dir, 'ceo_weekly.js')
            json_path = os.path.join(weekly_dir, 'ceo_weekly.json')

            payload = dash_data or {'generated': today, 'raw': res['output'][:2000]}
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(f'window.WEEKLY_DATA = {json.dumps(payload, ensure_ascii=False, indent=2)};\n')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            # חלץ notification-summary בלוק אם קיים
            notif_m = re.search(r'```notification-summary\s*([\s\S]*?)```', res['output'])
            notif_text = notif_m.group(1).strip() if notif_m else ''

            upd(status='done', finished=datetime.now().isoformat(),
                js_path=js_path, notification_summary=notif_text)
        except Exception as e:
            upd(status='failed', error=str(e), finished=datetime.now().isoformat())

    threading.Thread(target=_run_ceo_weekly, args=(run_id,), daemon=True).start()
    return jsonify({'run_id': run_id})


@app.route('/api/ceo-weekly/latest')
def api_ceo_weekly_latest():
    """מחזיר את הדוח השבועי האחרון."""
    p = os.path.join(ROOT, 'analyses', '_weekly', 'ceo_weekly.json')
    if not os.path.exists(p):
        return jsonify(None)
    with open(p, encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/daily/latest')
def api_daily_latest():
    """מחזיר את הדוח היומי האחרון."""
    p = os.path.join(ROOT, 'analyses', '_daily', 'daily_latest.json')
    if not os.path.exists(p):
        return jsonify(None)
    with open(p, encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/monthly-close/latest')
def api_monthly_close_latest():
    """מחזיר את נתוני הסגירה החודשית האחרונה."""
    import re as _re
    monthly_dir = os.path.join(ROOT, 'analyses', '_monthly')
    if not os.path.isdir(monthly_dir):
        return jsonify(None)
    periods = sorted([
        d for d in os.listdir(monthly_dir)
        if os.path.isdir(os.path.join(monthly_dir, d)) and len(d) == 7 and d[4] == '-'
    ], reverse=True)
    for period in periods:
        js_path = os.path.join(monthly_dir, period, 'monthly_close.js')
        if os.path.exists(js_path):
            with open(js_path, encoding='utf-8') as f:
                content = f.read()
            match = _re.search(r'=\s*(\{[\s\S]*\})\s*;?\s*$', content)
            if match:
                return jsonify(json.loads(match.group(1)))
    return jsonify(None)


@app.route('/templates/<path:filename>')
def serve_template(filename):
    return send_from_directory(os.path.join(ROOT, 'templates'), filename)


@app.route('/analyses/<path:filename>')
def serve_analysis(filename):
    return send_from_directory(os.path.join(ROOT, 'analyses'), filename)


# ── Oracle: דף + צ'אט ─────────────────────────────────────────────────────────

@app.route('/oracle')
def oracle_page():
    return send_from_directory(os.path.join(ROOT, 'templates'), 'oracle.html')


@app.route('/oracle/council', methods=['POST'])
def oracle_council():
    data     = request.json or {}
    messages = data.get('messages', [])

    try:
        with open(os.path.join(ROOT, 'scanner-results.json'), encoding='utf-8') as f:
            scanner = json.load(f)[:3]
    except Exception:
        scanner = []
    try:
        with open(DECISIONS_FILE, encoding='utf-8') as f:
            dl = json.load(f)[-3:]
    except Exception:
        dl = []

    ctx = (
        f"=== PORTFOLIO ===\n{_portfolio_snapshot_compact()}\n\n"
        f"=== WATCHLIST ===\n{_watchlist_compact()}\n\n"
        f"=== SCANNER ===\n{json.dumps(scanner, ensure_ascii=False)}\n\n"
        f"=== DECISION LOG ===\n{json.dumps(dl, ensure_ascii=False)}"
    )

    council_system = f"""אתה מועצת יועצי השקעות. נתח את השאלה מ-5 זוויות שונות.

לפני הניתוח — אם השאלה נוגעת למניה ספציפית או לאירוע שוק, בצע WebSearch לחדשות רלוונטיות ושלב ממצאים בניתוח.

## נתוני התיק
{ctx}

## פורמט תשובה (חובה בדיוק):

🔴 **הסקפטן**
[מה יכול להשתבש, מה מוחמץ, הטיעון הכי חזק נגד — 150 מילים]

🟢 **האופטימיסט**
[פוטנציאל מוחמץ, תרחיש upside — 150 מילים]

🔵 **מהשורש**
[מה בעצם מנסים לפתור, האם השאלה נכונה — 100 מילים]

👁 **עיניים טריות**
[מה קללת הידע מסתירה — 100 מילים]

⚡ **המבצע**
[צעד ראשון ספציפי ומדיד — 80 מילים]

---
## פסיקת המועצה
**מסכימים על:** ...
**חולקים על:** ...
**המלצה:** ...
**צעד ראשון:** ..."""

    history = ''.join([
        f"{'USER' if m.get('role') == 'user' else 'COUNCIL'}: {m.get('content', '')}\n"
        for m in messages[:-1]
    ])
    last   = messages[-1].get('content', '') if messages else ''
    result = _run_llm(council_system, f'{history}USER: {last}\nCOUNCIL:', timeout=180)
    text   = result['output'].strip() if result['ok'] else f'שגיאה: {result.get("error", "")}'
    return jsonify({'text': text, 'elapsed': result.get('elapsed', 0), 'mode': 'council'})


@app.route('/oracle/chat', methods=['POST'])
def oracle_chat():
    data     = request.json or {}
    messages = data.get('messages', [])

    try:
        with open(os.path.join(ROOT, 'scanner-results.json'), encoding='utf-8') as f:
            scanner = json.load(f)[:5]
    except Exception:
        scanner = []
    try:
        with open(DECISIONS_FILE, encoding='utf-8') as f:
            dl = json.load(f)[-5:]
    except Exception:
        dl = []

    ctx = (
        f"=== PORTFOLIO ===\n{_portfolio_snapshot_compact()}\n\n"
        f"=== WATCHLIST ===\n{_watchlist_compact()}\n\n"
        f"=== SCANNER (אחרון) ===\n{json.dumps(scanner, ensure_ascii=False)}\n\n"
        f"=== DECISION LOG (5 אחרונים) ===\n{json.dumps(dl, ensure_ascii=False)}"
    )

    oracle_path = os.path.join(PROMPTS_DIR, 'Oracle_Agent.md')
    with open(oracle_path, encoding='utf-8') as f:
        system = f.read().replace('{{PORTFOLIO_CONTEXT}}', ctx)

    history = ''.join([
        f"{'USER' if m.get('role') == 'user' else 'ORACLE'}: {m.get('content', '')}\n"
        for m in messages[:-1]
    ])
    last = messages[-1].get('content', '') if messages else ''
    result = _run_llm(system, f'{history}USER: {last}\nORACLE:', timeout=120)
    text   = result['output'].strip() if result['ok'] else f'שגיאה: {result.get("error", "unknown")}'
    return jsonify({'text': text, 'elapsed': result.get('elapsed', 0)})


# ── API: ping ─────────────────────────────────────────────────────────────────

@app.route('/api/ping')
def api_ping():
    return jsonify({'ok': True, 'mode': 'python', 'time': datetime.now().strftime('%H:%M:%S')})


@app.route('/api/cache/clear', methods=['POST'])
def api_cache_clear():
    with _price_lock:
        _price_cache.clear()
    return jsonify({'ok': True})


@app.route('/api/prices/validate')
def api_prices_validate():
    """Cross-validate ALL held + watchlisted symbols against 3 independent sources.
    Returns per-symbol agreement/conflict. Slow (live fetches) — run on demand only.
    """
    port = _load_portfolio()
    symbols = list({h['symbol'] for h in port.get('holdings', [])} |
                   {w['symbol'] for w in port.get('watchlist', [])})

    results = []
    for sym in sorted(symbols):
        yahoo  = _fetch_yahoo_price(sym)
        finviz = _fetch_finviz_price(sym)
        nasdaq = _fetch_nasdaq_price(sym)

        prices = {k: v['current_price'] for k, v in
                  [('yahoo', yahoo), ('finviz', finviz), ('nasdaq', nasdaq)]
                  if v['current_price'] is not None}

        if len(prices) == 0:
            status = 'no_data'
            conflict = None
        elif len(prices) == 1:
            status = 'single_source'
            conflict = None
        else:
            vals = list(prices.values())
            spread = (max(vals) - min(vals)) / min(vals) * 100
            if spread <= 2.0:
                status = 'agree'
            elif spread <= 5.0:
                status = 'minor_diff'
            else:
                status = 'conflict'
            conflict = round(spread, 2)

        results.append({
            'symbol': sym,
            'status': status,
            'spread_pct': conflict,
            'sources': {k: round(v, 2) for k, v in prices.items()},
            'sources_checked': 3,
            'sources_returned': len(prices),
        })

    ts = datetime.now().strftime('%H:%M:%S')
    conflicts = [r for r in results if r['status'] == 'conflict']
    if conflicts:
        print(f'[{ts}] Price conflicts: {[c["symbol"] for c in conflicts]}')

    return jsonify({
        'validated_at': ts,
        'symbols_checked': len(results),
        'all_agree': all(r['status'] == 'agree' for r in results if r['status'] != 'no_data'),
        'conflicts': [r['symbol'] for r in results if r['status'] == 'conflict'],
        'results': results,
    })


@app.route('/api/prices/status')
def api_prices_status():
    """Diagnostic: show age + source of every cached price."""
    now = time.time()
    with _price_lock:
        snap = dict(_price_cache)
    items = []
    for sym, entry in sorted(snap.items()):
        age = int(now - entry['ts'])
        d = entry.get('data', {})
        items.append({
            'symbol': sym,
            'price': d.get('current_price'),
            'source': d.get('source'),
            'age_s': age,
            'age_human': f'{age//3600}h {(age%3600)//60}m' if age >= 3600 else f'{age//60}m {age%60}s',
            'status': 'fresh' if age < CACHE_TTL else ('stale' if age < STALE_MAX_AGE else 'expired'),
        })
    return jsonify({'cache_size': len(items), 'stale_max_age_s': STALE_MAX_AGE, 'items': items})


# ── API: chart proxy ──────────────────────────────────────────────────────────

@app.route('/api/chart')
def api_chart():
    symbol   = request.args.get('symbol', 'V')
    interval = request.args.get('interval', '1d')
    range_   = request.args.get('range', '6mo')
    hdrs     = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept':     'application/json',
    }
    for host in ('query1', 'query2'):
        try:
            url = (f'https://{host}.finance.yahoo.com/v8/finance/chart/{symbol}'
                   f'?interval={interval}&range={range_}')
            r   = _requests.get(url, headers=hdrs, timeout=12)
            if r.ok:
                return r.content, 200, {'Content-Type': 'application/json; charset=utf-8'}
        except Exception:
            pass
    return jsonify({'error': 'yahoo fetch failed'}), 502


# ── API: portfolio ────────────────────────────────────────────────────────────

@app.route('/api/portfolio')
def api_portfolio():
    portfolio = load_portfolio()
    holdings  = portfolio.get('holdings', [])
    cash      = float(portfolio.get('cash', 0))
    trades    = portfolio.get('trades', [])
    watchlist = portfolio.get('watchlist', [])

    all_syms = list({h['symbol'] for h in holdings} | {w['symbol'] for w in watchlist})
    prices   = get_prices(all_syms)

    enriched    = []
    total_value = 0.0
    total_cost  = 0.0
    today_chg   = 0.0

    for h in holdings:
        sym  = h['symbol']
        p    = prices.get(sym, {})
        curr = p.get('current_price')
        chg  = p.get('day_change_pct')
        cost = float(h['buy_price']) * float(h['quantity'])
        mval = curr * float(h['quantity']) if curr is not None else None
        pnl  = mval - cost if mval is not None else None
        pnlP = pnl / cost * 100 if pnl is not None and cost > 0 else None

        if mval:
            total_value += mval
        total_cost += cost
        if curr and chg is not None:
            prev       = curr / (1 + chg / 100)
            today_chg += (curr - prev) * float(h['quantity'])

        enriched.append({
            'symbol':         sym,
            'name':           h.get('name', sym),
            'quantity':       float(h['quantity']),
            'buy_price':      float(h['buy_price']),
            'current_price':  curr,
            'day_change_pct': chg,
            'price_stale_s':  p.get('stale_age_s'),
            'price_source':   p.get('source'),
            'market_value':   round(mval, 4)  if mval is not None else None,
            'cost_basis':     round(cost, 4),
            'pnl':            round(pnl, 4)   if pnl  is not None else None,
            'pnl_pct':        round(pnlP, 4)  if pnlP is not None else None,
            'layer':          h.get('layer'),
            'sector':         h.get('sector'),
            'analyst_score':  h.get('analyst_score'),
            'risk_score':     h.get('risk_score'),
            'notes':          h.get('notes', ''),
        })

    w_enriched = []
    for w in watchlist:
        sym       = w['symbol']
        p         = prices.get(sym, {})
        curr      = p.get('current_price')
        trig      = w.get('trigger_price')
        direction = w.get('trigger_direction', 'below')
        alert     = False
        if curr is not None and trig is not None:
            if direction == 'below' and curr <= float(trig):
                alert = True
            elif direction == 'above' and curr >= float(trig):
                alert = True
        dist = (round((curr - float(trig)) / float(trig) * 100, 2)
                if curr and trig and float(trig) > 0 else None)
        w_enriched.append({**w, 'current_price': curr, 'distance_pct': dist, 'alert': alert,
                           'price_stale_s': p.get('stale_age_s'),
                           'price_source': p.get('source')})

    total_pnl = total_value - total_cost
    return jsonify({
        'holdings':  enriched,
        'watchlist': w_enriched,
        'trades':    trades,
        'cash':      cash,
        'summary': {
            'total_value':   round(total_value, 4),
            'total_cost':    round(total_cost,  4),
            'total_pnl':     round(total_pnl,   4),
            'total_pnl_pct': round(total_pnl / total_cost * 100, 4) if total_cost > 0 else 0,
            'today_change':  round(today_chg, 4),
            'grand_total':   round(total_value + cash, 4),
            'positions':     len(enriched),
            'trades_logged': len(trades),
        },
        'timestamp': datetime.now().isoformat(),
    })


# ── Holdings CRUD ─────────────────────────────────────────────────────────────

@app.route('/api/holdings', methods=['GET'])
def api_get_holdings():
    return jsonify(load_portfolio().get('holdings', []))


@app.route('/api/holdings', methods=['POST'])
def api_upsert_holding():
    global _price_cache
    data = request.get_json()
    sym  = data.get('symbol', '').upper()
    if not sym:
        return jsonify({'error': 'symbol required'}), 400

    portfolio = load_portfolio()
    holdings  = portfolio.setdefault('holdings', [])

    for h in holdings:
        if h['symbol'] == sym:
            for k in ('quantity', 'buy_price'):
                if k in data:
                    h[k] = data[k]
            for k in ('name', 'layer', 'sector', 'analyst_score', 'risk_score', 'notes'):
                if k in data and data[k] is not None:
                    h[k] = data[k]
            save_portfolio(portfolio)
            _price_cache.clear()
            return jsonify({'ok': True, 'action': 'updated'})

    holdings.append({
        'symbol':        sym,
        'name':          data.get('name', sym),
        'quantity':      data['quantity'],
        'buy_price':     data['buy_price'],
        'layer':         data.get('layer'),
        'sector':        data.get('sector'),
        'analyst_score': data.get('analyst_score'),
        'risk_score':    data.get('risk_score'),
        'notes':         data.get('notes', ''),
    })
    save_portfolio(portfolio)
    _price_cache.clear()
    return jsonify({'ok': True, 'action': 'added'})


@app.route('/api/holdings/<symbol>', methods=['DELETE'])
def api_delete_holding(symbol):
    portfolio = load_portfolio()
    portfolio['holdings'] = [h for h in portfolio.get('holdings', [])
                             if h['symbol'] != symbol.upper()]
    save_portfolio(portfolio)
    return jsonify({'ok': True})


# ── Watchlist CRUD ────────────────────────────────────────────────────────────

@app.route('/api/watchlist', methods=['GET'])
def api_get_watchlist():
    return jsonify(load_portfolio().get('watchlist', []))


@app.route('/api/watchlist', methods=['POST'])
def api_upsert_watchlist():
    global _price_cache
    data = request.get_json()
    sym  = data.get('symbol', '').upper()
    if not sym:
        return jsonify({'error': 'symbol required'}), 400

    portfolio = load_portfolio()
    wl        = portfolio.setdefault('watchlist', [])

    for i, w in enumerate(wl):
        if w['symbol'] == sym:
            wl[i] = {**w, **data, 'symbol': sym}
            save_portfolio(portfolio)
            _price_cache.clear()
            return jsonify({'ok': True, 'action': 'updated'})

    wl.append({**data, 'symbol': sym})
    save_portfolio(portfolio)
    _price_cache.clear()
    return jsonify({'ok': True, 'action': 'added'})


@app.route('/api/watchlist/<symbol>', methods=['DELETE'])
def api_delete_watchlist(symbol):
    portfolio = load_portfolio()
    portfolio['watchlist'] = [w for w in portfolio.get('watchlist', [])
                              if w['symbol'] != symbol.upper()]
    save_portfolio(portfolio)
    return jsonify({'ok': True})


# ── Trades CRUD ───────────────────────────────────────────────────────────────

@app.route('/api/trades', methods=['GET'])
def api_get_trades():
    return jsonify(load_portfolio().get('trades', []))


@app.route('/api/trades', methods=['POST'])
def api_add_trade():
    data      = request.get_json()
    portfolio = load_portfolio()
    trades    = portfolio.setdefault('trades', [])
    data['trade_id'] = next_trade_id(trades)
    trades.append(data)
    save_portfolio(portfolio)
    return jsonify({'ok': True, 'trade_id': data['trade_id']})


@app.route('/api/trades/<int:idx>', methods=['DELETE'])
def api_delete_trade(idx):
    portfolio = load_portfolio()
    trades    = portfolio.get('trades', [])
    if 0 <= idx < len(trades):
        trades.pop(idx)
        save_portfolio(portfolio)
    return jsonify({'ok': True})


# ── Cash ──────────────────────────────────────────────────────────────────────

@app.route('/api/cash', methods=['PUT'])
def api_update_cash():
    data      = request.get_json()
    portfolio = load_portfolio()
    portfolio['cash'] = data.get('cash', 0)
    save_portfolio(portfolio)
    return jsonify({'ok': True})


# ── Analyses metadata ─────────────────────────────────────────────────────────

@app.route('/api/analyses')
def api_analyses():
    result = {}
    if os.path.isdir(ANALYSES_DIR):
        for ticker in sorted(os.listdir(ANALYSES_DIR)):
            ticker_dir = os.path.join(ANALYSES_DIR, ticker)
            if not os.path.isdir(ticker_dir):
                continue
            agents = sorted(f[:-3] for f in os.listdir(ticker_dir) if f.endswith('.js'))
            if agents:
                result[ticker] = {'agents': agents, **_extract_analysis_meta(ticker)}
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────────────
# Smart Context + Agent Runner
# ─────────────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _portfolio_snapshot_compact() -> str:
    p     = load_portfolio()
    cash  = float(p.get('cash', 0))
    syms  = list({h['symbol'] for h in p.get('holdings', [])} |
                 {w['symbol'] for w in p.get('watchlist', [])})
    prices = get_prices(syms)

    lines = []
    total_v = 0.0
    enriched = []
    for h in p.get('holdings', []):
        sym  = h['symbol']
        curr = prices.get(sym, {}).get('current_price')
        mval = curr * float(h['quantity']) if curr else None
        if mval:
            total_v += mval
        enriched.append((sym, h, curr, mval))

    grand = total_v + cash
    cash_pct = (cash / grand * 100) if grand > 0 else 0

    layers: dict = {}
    for sym, h, curr, mval in enriched:
        l = h.get('layer') or 'Unknown'
        layers[l] = layers.get(l, 0) + (mval or 0)

    lines.append(f'Grand Total: ${grand:,.2f} | Cash: ${cash:,.2f} ({cash_pct:.1f}%) | Positions: {len(enriched)}')
    lines.append('Layer Allocation:')
    for l, v in sorted(layers.items(), key=lambda x: -x[1]):
        pct = (v / grand * 100) if grand > 0 else 0
        lines.append(f'  {l:<13} {pct:5.1f}%')
    lines.append(f'  {"Cash":<13} {cash_pct:5.1f}%')
    lines.append('')
    lines.append('Holdings (by weight):')
    enriched.sort(key=lambda x: -(x[3] or 0))
    for sym, h, curr, mval in enriched:
        w = (mval / grand * 100) if (mval and grand > 0) else 0
        cost = float(h['buy_price']) * float(h['quantity'])
        pnl_pct = ((mval - cost) / cost * 100) if (mval and cost > 0) else None
        pnl_str = f'{pnl_pct:+.1f}%' if pnl_pct is not None else 'N/A'
        lines.append(f'  {sym:<6} {(h.get("layer") or "?"):<11} W:{w:5.1f}%  P&L:{pnl_str:>7}  A/R:{h.get("analyst_score") or "?"}/{h.get("risk_score") or "?"}')
    return '\n'.join(lines)


def _watchlist_compact() -> str:
    p     = load_portfolio()
    wl    = p.get('watchlist', [])
    if not wl:
        return '(empty)'
    syms   = [w['symbol'] for w in wl]
    prices = get_prices(syms)
    lines  = []
    for w in wl:
        sym  = w['symbol']
        curr = prices.get(sym, {}).get('current_price')
        trig = w.get('trigger_price')
        direction = w.get('trigger_direction', 'below')
        dist = None
        alert = False
        if curr and trig:
            dist = (curr - float(trig)) / float(trig) * 100
            if direction == 'below' and curr <= float(trig):  alert = True
            if direction == 'above' and curr >= float(trig):  alert = True
        flag = '⚠AT-TRIGGER' if alert else 'waiting'
        lines.append(f'  {sym:<6} {w.get("verdict","?"):<10} price:${curr if curr else "N/A"} trig:${trig}{"↓" if direction=="below" else "↑"} dist:{dist:+.1f}% [{flag}]'
                     if dist is not None else
                     f'  {sym:<6} {w.get("verdict","?"):<10} price:${curr if curr else "N/A"} trig:${trig} [{flag}]')
        if w.get('thesis'):
            lines.append(f'         תזה: {w["thesis"][:120]}')
        if w.get('kill_switch'):
            lines.append(f'         Kill: {w["kill_switch"][:120]}')
    return '\n'.join(lines)


def _load_prior_handoffs(ticker: str, exclude_agent: str) -> str:
    """Load most-recent handoff per prior agent.

    מעדיף _reviews/<agent>.json (קומפקטי, ~300 תווים) על markdown מלא (~50KB).
    חוסך 80-90% טוקנים מה-context — הפלט הסופי של כל סוכן לא מושפע.
    Fallback ל-markdown מלא אם JSON חסר.
    """
    import json as _json

    hd_dir  = os.path.join(ANALYSES_DIR, ticker, '_handoffs')
    rev_dir = os.path.join(ANALYSES_DIR, ticker, '_reviews')

    if not os.path.isdir(hd_dir) and not os.path.isdir(rev_dir):
        return ''

    by_agent: dict = {}
    if os.path.isdir(hd_dir):
        for fname in sorted(os.listdir(hd_dir)):
            if not fname.endswith('.md'):
                continue
            m = re.match(r'(\d{4}-\d{2}-\d{2})_(\w+)\.md', fname)
            if not m:
                continue
            date, agent = m.group(1), m.group(2)
            if agent == exclude_agent:
                continue
            if agent not in by_agent or date > by_agent[agent][0]:
                by_agent[agent] = (date, fname)

    # ולידציה: כל הסוכנים שקדמו צריכים להיות זמינים
    if exclude_agent in AGENT_ORDER:
        idx = AGENT_ORDER.index(exclude_agent)
        for expected in AGENT_ORDER[:idx]:
            if expected not in by_agent:
                print(f'[WARN handoff] {ticker}/{exclude_agent}: חסר handoff של {expected}')

    chunks = []
    for agent in AGENT_ORDER:
        if agent == exclude_agent or agent not in by_agent:
            continue
        date, fname = by_agent[agent]

        # JSON review קודם — כל המידע המבני ללא prose מיותר
        review_path = os.path.join(rev_dir, f'{agent}.json') if os.path.isdir(rev_dir) else None
        if review_path and os.path.exists(review_path):
            try:
                with open(review_path, encoding='utf-8') as f:
                    rv = _json.load(f)
                risks_str = '; '.join(rv.get('key_risks', []))
                summary = (
                    f'━━━ {AGENT_LABELS.get(agent, agent)} REVIEW ({rv.get("date", date)}) ━━━\n'
                    f'Verdict: {rv.get("verdict","?")} | Score: {rv.get("score","?")} | '
                    f'Position: {rv.get("position_size_pct","?")}%\n'
                    f'Thesis: {rv.get("thesis","")}\n'
                    f'Key Risks: {risks_str}\n'
                    f'Valuation: {rv.get("valuation_summary","")}\n'
                    f'Entry/Exit: {rv.get("entry_exit_plan","")}\n'
                    f'Summary: {rv.get("handoff_summary","")}'
                )
                chunks.append(summary)
                continue
            except Exception:
                pass  # fallback ל-markdown מלא

        # fallback: markdown מלא
        try:
            with open(os.path.join(hd_dir, fname), encoding='utf-8') as f:
                content = f.read()
            chunks.append(f'━━━ {AGENT_LABELS.get(agent, agent)} HANDOFF ({date}) ━━━\n{content.strip()}')
        except Exception:
            pass
    return '\n\n'.join(chunks)


def _compute_market_delta(ticker: str) -> str:
    """Price/score delta vs last analysis."""
    meta = _extract_analysis_meta(ticker)
    if not meta.get('price_at_analysis'):
        return ''
    p_old = meta['price_at_analysis']
    prices = get_prices([ticker])
    p_now = prices.get(ticker, {}).get('current_price')
    if not p_now:
        return f'Previous analysis: {meta.get("date","?")} | Previous price: ${p_old} | Current: N/A'
    pct = (p_now - p_old) / p_old * 100
    return (f'Previous analysis: {meta.get("date","?")} | '
            f'Price then: ${p_old} → Now: ${p_now:.2f} ({pct:+.1f}%)')


def _obsidian_vault_dir() -> str | None:
    cfg = _load_config()
    vault = cfg.get('obsidian_vault')
    if not vault or not os.path.isdir(vault):
        return None
    return vault


def _obsidian_ticker_path(ticker: str) -> str | None:
    vault = _obsidian_vault_dir()
    if not vault:
        return None
    cfg = _load_config()
    folder = cfg.get('obsidian_ticker_folder', 'Tickers')
    return os.path.join(vault, folder, f'{ticker}.md')


def _obsidian_read_section(ticker: str, section_title: str) -> str:
    """Extract a `## section_title` block. Graceful fallback."""
    path = _obsidian_ticker_path(ticker)
    if not path or not os.path.exists(path):
        return ''
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        # match "## section_title" until next "## " or EOF
        pat = rf'(?m)^##\s+{re.escape(section_title)}\s*\n(.+?)(?=^##\s+|\Z)'
        m = re.search(pat, content, re.DOTALL)
        return m.group(1).strip() if m else ''
    except Exception:
        return ''


def _obsidian_append(ticker: str, section_heading: str, body: str) -> bool:
    """Append a new section. Returns True on success, False otherwise (silent fail)."""
    path = _obsidian_ticker_path(ticker)
    if not path:
        return False
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing = ''
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                existing = f.read().rstrip()
        with open(path, 'w', encoding='utf-8') as f:
            if existing:
                f.write(existing + '\n\n')
            f.write(f'## {section_heading}\n\n{body.strip()}\n')
        return True
    except Exception as e:
        print(f'[obsidian write skipped] {e}')
        return False


# ── Decision Journal ─────────────────────────────────────────────────────────

def _load_decisions() -> dict:
    if os.path.exists(DECISIONS_FILE):
        try:
            with open(DECISIONS_FILE, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'decisions': []}


def _save_decisions(data: dict):
    with open(DECISIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _next_decision_id(decisions: list) -> str:
    nums = []
    for d in decisions:
        try:
            nums.append(int(d.get('id', '').split('-')[1]))
        except Exception:
            pass
    return f'DEC-{(max(nums) + 1):03d}' if nums else 'DEC-001'


def _decision_for_ticker(ticker: str) -> dict | None:
    """Latest decision for a ticker (or None)."""
    data = _load_decisions()
    matches = [d for d in data.get('decisions', []) if d.get('ticker') == ticker]
    if not matches:
        return None
    matches.sort(key=lambda d: d.get('date', ''), reverse=True)
    return matches[0]


def _decision_context_block(ticker: str) -> str:
    d = _decision_for_ticker(ticker)
    if not d:
        return ''
    lines = [
        f'Date: {d.get("date","?")}',
        f'Decision: {d.get("decision","?")}',
        f'Position Size: {d.get("position_size_pct","?")}%',
        f'Conviction: {d.get("conviction","?")}',
        f'Why: {d.get("why","")}',
        f'Biggest Risk: {d.get("biggest_risk","")}',
        f'Kill Switch: {d.get("kill_switch","")}',
        f'Original Thesis: {d.get("original_thesis","")}',
    ]
    return '\n'.join(lines)


# ── Dashboard JSON extractor + JS writer ─────────────────────────────────────

_DASHBOARD_JSON_RE = re.compile(r'```dashboard-json\s*(\{.*?\})\s*```', re.DOTALL)


def _extract_dashboard_json(output: str) -> dict | None:
    """Extract the compact dashboard JSON block from agent output."""
    m = _DASHBOARD_JSON_RE.search(output)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _update_review_json(ticker: str, agent: str, dash: dict):
    """Write compact review to analyses/<T>/_reviews/<agent>.json — separate from original .js (which feeds visual templates)."""
    review_dir = os.path.join(ANALYSES_DIR, ticker, '_reviews')
    os.makedirs(review_dir, exist_ok=True)
    payload = {
        'ticker':             ticker,
        'agent':              agent,
        'date':               dash.get('date', datetime.now().strftime('%Y-%m-%d')),
        'verdict':            dash.get('verdict'),
        'score':              dash.get('score'),
        'thesis':             dash.get('thesis'),
        'key_risks':          dash.get('key_risks', []),
        'position_size_pct':  dash.get('position_size_pct'),
        'valuation_summary':  dash.get('valuation_summary'),
        'entry_exit_plan':    dash.get('entry_exit_plan'),
        'handoff_summary':    dash.get('handoff_summary'),
    }
    # D-Lite: persist visual_scores if present so future _write_visual_js
    # regenerations (from cached review only) can still build rich bars.
    if 'visual_scores' in dash and dash['visual_scores']:
        payload['visual_scores'] = dash['visual_scores']
    dest = os.path.join(review_dir, f'{agent}.json')
    with open(dest, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _list_latest_reviews() -> list:
    """Scan analyses/<T>/_reviews/*.json — return latest review per ticker (most recent across agents)."""
    out = []
    if not os.path.isdir(ANALYSES_DIR):
        return out
    for ticker in sorted(os.listdir(ANALYSES_DIR)):
        rdir = os.path.join(ANALYSES_DIR, ticker, '_reviews')
        if not os.path.isdir(rdir):
            continue
        reviews = []
        for fname in os.listdir(rdir):
            if not fname.endswith('.json'):
                continue
            try:
                with open(os.path.join(rdir, fname), encoding='utf-8') as f:
                    d = json.load(f)
                d['mtime'] = os.path.getmtime(os.path.join(rdir, fname))
                reviews.append(d)
            except Exception:
                continue
        if reviews:
            reviews.sort(key=lambda r: r.get('mtime', 0), reverse=True)
            out.append(reviews[0])
    # Newest reviews first across all tickers
    out.sort(key=lambda r: r.get('mtime', 0), reverse=True)
    return out


# ── Quick Mode prompt (inline, not .md) ──────────────────────────────────────

QUICK_SYSTEM_PROMPT = """You are a Quick Check Reviewer.

You evaluate ONE ticker against its prior analysis and current state.
You DO NOT do deep research. You only check: has anything materially changed?

Use WebSearch sparingly (max 2-3 searches) for very recent news/earnings only.

Your output MUST be exactly this structure:

```
STATUS: 🟢 INTACT | 🟡 REVIEW | 🔴 RE-RUN

WHAT CHANGED (1 sentence):
[one sentence]

RATIONALE (2-3 sentences):
[2-3 sentences citing specific signals]

ACTION:
[one line: hold / monitor X / run full chain because Y]
```

Then include the dashboard-json block as instructed.

Be concise. Total response: under 400 words."""


_DASHBOARD_JSON_INSTRUCTION = """
━━━ STRUCTURED OUTPUT REQUIRED ━━━
At the END of your response, include EXACTLY this block (replace placeholders):

```dashboard-json
{
  "ticker": "TICKER_HERE",
  "date": "YYYY-MM-DD",
  "verdict": "BUY|AVOID|HOLD|SELL|REVIEW|INTACT|RERUN",
  "score": 0,
  "thesis": "1-2 sentence summary of current thesis",
  "key_risks": ["risk 1", "risk 2"],
  "position_size_pct": 0,
  "valuation_summary": "fair value $X, upside Y%",
  "entry_exit_plan": "tranches/stop/TP in one line",
  "handoff_summary": "one paragraph for the next agent in the chain"
}
```

Fill ALL fields. Use null if truly unknown. This drives the dashboard."""


# D-Lite: structured visual scores. ANALYST-only addendum. Strict null-if-unknown.
# Token budget: ~200 instruction + ~250 output = ~450 tokens per analyst run.
_VISUAL_SCORES_ANALYST = """

━━━ OPTIONAL: VISUAL SCORES (analyst only — drives chart bars) ━━━
After the dashboard-json block above, you MAY also include this block. Use
null for ANY number not explicitly stated in your researched sources. NEVER
estimate, interpolate, or infer numbers. Empty list is fine; null is fine.

```visual-scores
{
  "business_engines": [
    {"label": "engine name (e.g., AWS)", "revenue_b": null, "growth_pct": null, "weight_pct": null}
  ],
  "moat_scores": [
    {"label": "moat dimension", "score_0_10": null}
  ],
  "stress_categories": [
    {"label": "category", "score_0_10": null}
  ],
  "valuation": {
    "bear_price": null, "base_price": null, "bull_price": null, "current_price": null
  },
  "financials_3y": [
    {"year": "FY23", "revenue_b": null, "op_margin_pct": null, "fcf_b": null, "eps": null}
  ]
}
```

RULES (HARD):
- null when number not in cited source. Never guess.
- numbers as JSON numbers, not strings ("18.5" wrong, 18.5 right).
- max 6 items per array. Order by importance.
- entire block is optional — omit silently if you have no verified numbers."""


# D-Lite for IC: only risk_reward triangle from existing per-agent verdicts.
_VISUAL_SCORES_IC = """

━━━ OPTIONAL: VISUAL SCORES (IC only) ━━━
After the dashboard-json block above, you MAY also include this block. Numbers
ONLY if explicitly produced by upstream agents (analyst/devils/CEO/executor).
Use null if not stated.

```visual-scores
{
  "risk_reward": {
    "current_price": null,
    "fair_value":    null,
    "trigger_price": null,
    "stop_price":    null,
    "tp1_price":     null
  },
  "agent_scores": {
    "analyst_score_0_10":  null,
    "devils_risk_0_10":    null,
    "ceo_conviction_0_10": null,
    "executor_quality_0_10": null
  }
}
```

RULES: same as analyst. Omit silently if no verified numbers."""


# regex to find the visual-scores block at the END of the agent's output
_VISUAL_SCORES_RE = re.compile(r'```visual-scores\s*(\{.*?\})\s*```', re.DOTALL)


def _extract_visual_scores(output: str) -> dict:
    """Pull visual-scores JSON block from agent output. Returns {} if missing/invalid."""
    m = _VISUAL_SCORES_RE.search(output or '')
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {}


def _build_context(ticker: str, agent: str) -> dict:
    """Build the full prompt = system + context. Returns {prompt, meta}."""
    today = datetime.now().strftime('%Y-%m-%d')

    # Quick Mode uses inline system prompt, no .md file
    if agent == 'quick':
        system = QUICK_SYSTEM_PROMPT
    else:
        sys_path = os.path.join(PROMPTS_DIR, PROMPT_FILES[agent])
        if not os.path.exists(sys_path):
            raise FileNotFoundError(f'system prompt missing: {sys_path}')
        with open(sys_path, encoding='utf-8') as f:
            system = f.read()

    parts = [
        f'TICKER: {ticker}',
        f'DATE: {today}',
        f'AGENT: {AGENT_LABELS.get(agent, agent.title())}',
        '',
        '━━━ PORTFOLIO SNAPSHOT ━━━',
        _portfolio_snapshot_compact(),
    ]

    if agent in ('ceo', 'ic', 'analyst', 'quick'):
        parts += ['', '━━━ WATCHLIST ━━━', _watchlist_compact()]

    # Original decision (anti-drift)
    dec_block = _decision_context_block(ticker)
    if dec_block:
        parts += ['', '━━━ ORIGINAL DECISION (anti-drift anchor) ━━━', dec_block]

    if agent not in ('analyst',):
        prior = _load_prior_handoffs(ticker, exclude_agent=agent)
        if prior:
            # Quick mode gets handoffs truncated to keep it lightweight
            if agent == 'quick' and len(prior) > 6000:
                prior = prior[:6000] + '\n[...truncated for quick mode...]'
            parts += ['', '━━━ PRIOR HANDOFFS ━━━', prior]
        else:
            parts += ['', '━━━ PRIOR HANDOFFS ━━━', '(none — first run for this ticker)']

    delta = _compute_market_delta(ticker)
    if delta:
        parts += ['', '━━━ MARKET DELTA ━━━', delta]

    if agent == 'executor':
        tech_path = os.path.join(ANALYSES_DIR, ticker, 'technical_data.txt')
        if os.path.exists(tech_path):
            with open(tech_path, encoding='utf-8') as f:
                parts += ['', '━━━ TECHNICAL DATA ━━━', f.read()]

    if agent == 'analyst':
        research_path = os.path.join(ANALYSES_DIR, ticker, 'research_data.txt')
        if os.path.exists(research_path):
            with open(research_path, encoding='utf-8') as f:
                parts += ['', '━━━ PRE-GATHERED RESEARCH CONTEXT ━━━', f.read()]

    # ── Vault Memory (Phase 2) — compact prior-knowledge injection ───────────
    # vault_reader בונה בלוק ~600-800 תווים: פסיקה, תזה, שווי, סיכונים, היסטוריה.
    # חוסך token-burn על ניתוחים חוזרים. Fail-soft: כישלון מחזיר ''.
    # מוגבל ל-analyst+devils: שאר הסוכנים מקבלים את ההקשר הזה דרך prior handoffs.
    if agent in ('analyst', 'devils', 'quick'):
        try:
            import obsidian_layer as _ol
            _vault_ctx = _ol.vault_reader.load_ticker_context(ticker)
            if _vault_ctx:
                parts += ['', '━━━ VAULT MEMORY — ידע קודם על ' + ticker + ' ━━━', _vault_ctx]
        except Exception as _ve:
            # fallback: try legacy section read
            _obs = _obsidian_read_section(ticker, 'תזה נוכחית') or _obsidian_read_section(ticker, 'Thesis')
            if _obs:
                parts += ['', '━━━ OBSIDIAN: תזה ━━━', _obs[:1500]]

    parts += [
        '',
        '━━━ MEMORY DIRECTIVE ━━━',
        f'אם זמין plugin claude-mem: שמור רק עובדות בעלות-אות גבוה על {ticker}:',
        'thesis breaks, kill switch triggers, capital decisions, big mistakes.',
        'אסור לשמור מחירים יומיים, נתוני שוק שגרתיים, או חישובי מכפילים.',
        _DASHBOARD_JSON_INSTRUCTION,
    ]
    # D-Lite: agent-conditional visual scores instruction (analyst + ic only)
    if agent == 'analyst':
        parts.append(_VISUAL_SCORES_ANALYST)
    elif agent == 'ic':
        parts.append(_VISUAL_SCORES_IC)
    parts += [
        '',
        '━━━ END OF CONTEXT — הרץ עכשיו ━━━',
    ]

    context = '\n'.join(parts)
    prompt  = f'{system}\n\n{context}'
    return {'prompt': prompt, 'system': system, 'context': context, 'token_estimate': len(prompt) // 4}


def _save_handoff(ticker: str, agent: str, content: str) -> dict:
    """Save raw handoff + extract dashboard JSON → update .js + Obsidian append."""
    today    = datetime.now().strftime('%Y-%m-%d')
    hd_dir   = os.path.join(ANALYSES_DIR, ticker, '_handoffs')
    os.makedirs(hd_dir, exist_ok=True)
    raw_path = os.path.join(hd_dir, f'{today}_{agent}.md')
    with open(raw_path, 'w', encoding='utf-8') as f:
        f.write(content)

    saved = {'raw': raw_path, 'obsidian': False, 'template_js': False, 'dashboard_json': False}
    dash = None  # initialized for obsidian_layer hook later; populated by extractor below

    # Extract dashboard JSON + update .js (quick mode uses _quick_check.js)
    try:
        dash = _extract_dashboard_json(content)
        if dash:
            saved['dashboard_json'] = True
            # D-Lite: pick up the optional visual-scores block and attach to dash so
            # the enricher can read it. Persisted to _reviews/<agent>.json as well.
            vs = _extract_visual_scores(content)
            if vs:
                dash['visual_scores'] = vs
                saved['visual_scores'] = True
            review_agent = 'quick' if agent == 'quick' else agent
            _update_review_json(ticker, review_agent, dash)
            saved['review_json'] = True
            # Auto-generate visual .js (or .auto.js if manual exists). Never overwrites manual.
            try:
                saved['visual_js'] = _write_visual_js(ticker, agent, dash)
            except Exception as e:
                print(f'[visual js skipped] {e}')
            # Auto-sync IC verdict only — final approval layer per AGENT_CHAIN.md
            if agent == 'ic':
                try:
                    saved['verdict_sync'] = _sync_verdict_to_portfolio(ticker, agent, dash)
                except Exception as e:
                    print(f'[verdict sync skipped] {e}')
    except Exception as e:
        print(f'[js update skipped] {e}')

    # Append to Obsidian (best-effort) — legacy single-file-per-ticker
    try:
        agent_label = AGENT_LABELS.get(agent, 'Quick Check' if agent == 'quick' else agent.title())
        if _obsidian_append(ticker, f'{today} — {agent_label}', content):
            saved['obsidian'] = True
    except Exception as e:
        print(f'[obsidian append skipped] {e}')

    # ── Phase 1: obsidian_layer integration (vault_writer) ─────────────
    # Fail-soft. Respects config flags obsidian_enabled + obsidian_dry_run.
    try:
        import obsidian_layer
        saved['obsidian_vault'] = obsidian_layer.on_save_handoff(
            ticker, agent, content, dash or {})
    except Exception as e:
        print(f'[obsidian_layer skipped] {e}')

    return saved


def _sync_verdict_to_portfolio(ticker: str, agent: str, dash: dict) -> dict:
    """Auto-sync IC verdict → portfolio.json / pending_trades.json.

    Authority: agent == 'ic' only (IC is final approval layer per AGENT_CHAIN.md).
    Caller in _save_handoff already gates on agent == 'ic'; the internal guard
    here is defense-in-depth.

    WATCHLIST                            → upsert watchlist[] (idempotent)
    BUY / APPROVED / APPROVED_WITH_*     → log to pending_trades.json — NEVER
                                           touches portfolio.json trades[]
    WAIT / REJECTED / PASS / AVOID       → log only (print)
    """
    if agent != 'ic':
        return {'synced': False, 'reason': f'{agent} not final approval layer'}

    verdict = (dash.get('verdict') or '').upper().strip().replace(' ', '_')
    if not verdict:
        return {'synced': False, 'reason': 'no verdict in dashboard-json'}

    today = datetime.now().strftime('%Y-%m-%d')
    tk    = ticker.upper()

    if verdict == 'WATCHLIST':
        # שדות מערכת (מיוצרים אוטומטית מה-IC). שדות שלא ברשימה הזו
        # נחשבים user-added ונשמרים כפי שהם.
        entry = {
            'symbol':             tk,
            'company':            dash.get('company') or tk,
            'date_added':         today,
            'verdict':            'WATCHLIST',
            'layer':              dash.get('layer'),
            'analyst_score':      dash.get('score'),
            'risk_score':         dash.get('risk_score'),
            'confidence':         dash.get('confidence'),
            'fair_value':         dash.get('fair_value'),
            'trigger_price':      dash.get('trigger_price'),
            'trigger_direction':  dash.get('trigger_direction') or 'below',
            'thesis':             dash.get('thesis'),
            'fragile_assumption': dash.get('fragile_assumption'),
            'kill_switch':        dash.get('kill_switch'),
            'next_review':        dash.get('next_review'),
            'notes':              dash.get('handoff_summary') or dash.get('entry_exit_plan'),
        }
        entry = {k: v for k, v in entry.items() if v is not None}
        portfolio = load_portfolio()
        wl = portfolio.setdefault('watchlist', [])
        # התאמה idempotent: case-insensitive + strip, מונע כפילויות
        # AMZN/amzn/' AMZN '. ערך קיים מתעדכן in-place; שדות שהמשתמש
        # הוסיף ידנית (לא ב-entry) נשמרים כי entry מורכב על w.
        for i, w in enumerate(wl):
            existing = (w.get('symbol') or '').strip().upper()
            if existing == tk:
                wl[i] = {**w, **entry}
                save_portfolio(portfolio)
                _price_cache.clear()
                print(f'[watchlist] updated existing: {tk}')
                return {'synced': True, 'action': 'watchlist_updated'}
        wl.append(entry)
        save_portfolio(portfolio)
        _price_cache.clear()
        print(f'[watchlist] created new: {tk}')
        return {'synced': True, 'action': 'watchlist_added'}

    if verdict in ('BUY', 'APPROVED', 'APPROVED_WITH_CONDITIONS'):
        pending_path = os.path.join(ROOT, 'pending_trades.json')
        pending = {'pending': []}
        if os.path.exists(pending_path):
            try:
                with open(pending_path, encoding='utf-8') as f:
                    pending = json.load(f)
            except Exception:
                pass
        pending.setdefault('pending', [])
        next_id = f'PND-{(len(pending["pending"]) + 1):03d}'
        pending['pending'].append({
            'id':                next_id,
            'ticker':            tk,
            'agent':             agent,
            'date':              today,
            'verdict':           verdict,
            'position_size_pct': dash.get('position_size_pct'),
            'entry_exit_plan':   dash.get('entry_exit_plan'),
            'thesis':            dash.get('thesis'),
            'status':            'awaiting_confirmation',
        })
        with open(pending_path, 'w', encoding='utf-8') as f:
            json.dump(pending, f, indent=2, ensure_ascii=False)
        print(f'[verdict] {tk} {verdict} → pending {next_id} (awaiting user confirmation)')
        return {'synced': True, 'action': 'pending_logged', 'id': next_id}

    if verdict in ('WAIT', 'REJECTED', 'REJECT', 'PASS', 'AVOID'):
        print(f'[verdict] {tk} {verdict} — logged, no portfolio change')
        return {'synced': True, 'action': 'logged_no_change'}

    return {'synced': False, 'reason': f'unknown verdict: {verdict}'}


# ── Rich-dashboard adapter (handoff-MD → visual JSON) ────────────────────────
# המודל כבר כותב סקציות מסודרות בקובץ ה-handoff (## כותרת + גוף). הקובצי
# .js מתעלמים מזה היום וקוראים רק את ה-JSON המינימלי בסוף. ה-helpers כאן
# מחלצים סקציות *טקסטואליות* בלבד מה-handoff (פסקאות / bullets) — אסור
# לחלץ מספרים מפרוזה. מספרים מגיעים אך ורק מ-dashboard-json של המודל
# (verdict, score, position_size_pct וכו'), שהם JSON מובנה שהמודל הפיק.

_AUTO_MARKER = '// CLAUDE-AUTO-GENERATED — מחק שורה זו כדי לנעול את הקובץ מפני דריסה\n'

_HANDOFF_HEADER_RE = re.compile(r'^#{1,2}\s+(.+?)\s*$', re.MULTILINE)
# שינוי מ-{1,6} ל-{1,2}: ה-LLM משתמש ב-### לתת-קטגוריות בתוך סקציה
# (קונפליקט א/ב/ג, קטגוריה א-ה). אם נחתוך עליהן — גוף הסקציה האב יישאר ריק.
# Bullet markers: standard MD (- * •) + Hebrew/check (✓ ✅ ✗ ❌) + arrows + numbered.
_HANDOFF_BULLET_RE = re.compile(
    r'^\s*(?:[-*•➤▶→◆◇]|✓|✅|✗|❌|🔴|🟡|🟢|\d+\.)\s+(.+?)\s*$',
    re.MULTILINE,
)


def _extract_table_first_col(body: str, skip_header: bool = True, max_rows: int = 8) -> list:
    """Extract first-cell text from each markdown table row in body. Skips
    separator rows (|---|) and the header row by default. Returns list of strings."""
    if not body:
        return []
    out = []
    for line in body.splitlines():
        s = line.lstrip()
        if not s.startswith('|') or '---' in s:
            continue
        cells = [c.strip() for c in s.strip('|').split('|') if c.strip()]
        if cells:
            out.append(cells[0])
    if skip_header and out:
        out = out[1:]  # drop header row
    return out[:max_rows]


def _items_from_section(body: str) -> list:
    """Return structured items from a section. Prefers table rows (first col),
    falls back to bullets, then to sub-section headers."""
    if not body:
        return []
    rows = _extract_table_first_col(body)
    if rows:
        return rows
    bullets = _extract_bullets(body)
    if bullets:
        return bullets
    return [h for h, _ in _drill_subsections(body)]


def _is_auto_generated(path: str) -> bool:
    """True if file's first line matches our auto-generated marker."""
    try:
        with open(path, encoding='utf-8') as f:
            return f.readline() == _AUTO_MARKER
    except Exception:
        return False


def _latest_handoff_md(ticker: str, agent: str) -> str | None:
    """Newest analyses/<T>/_handoffs/<date>_<agent>.md path, or None."""
    hd_dir = os.path.join(ANALYSES_DIR, ticker.upper(), '_handoffs')
    if not os.path.isdir(hd_dir):
        return None
    suffix = f'_{agent}.md'
    cands  = [f for f in os.listdir(hd_dir) if f.endswith(suffix)]
    if not cands:
        return None
    cands.sort(reverse=True)  # ISO date prefix → lex sort = newest first
    return os.path.join(hd_dir, cands[0])


def _parse_handoff_sections(path: str) -> list:
    """Split markdown by ## headers → list of (header_text, body) tuples."""
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except Exception:
        return []
    matches = list(_HANDOFF_HEADER_RE.finditer(text))
    out = []
    for i, m in enumerate(matches):
        header     = m.group(1).strip()
        body_start = m.end()
        body_end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body       = text[body_start:body_end].strip()
        out.append((header, body))
    return out


def _find_section(sections, *needles) -> str:
    """Return body of first section whose header contains any needle (case-insensitive).
    Skips sections with empty body — common pattern in our handoffs is a 'חלק X'
    parent header followed immediately by sub-headers (e.g. 'ב.1', 'ב.2'). The
    parent's body is empty; we want the first NON-EMPTY match."""
    fallback = ''  # if all matches are empty, return the first empty match (preserves prior behavior)
    for header, body in sections:
        h_low = header.lower()
        for n in needles:
            if n.lower() in h_low:
                if body.strip():
                    return body
                if not fallback:
                    fallback = body
                break
    return fallback


def _md_inline_to_html(s: str) -> str:
    """Minimal inline markdown → HTML. Conservative: only **bold**, `code`, blockquote prefix."""
    if not s:
        return ''
    s = s.strip()
    # הסרת בלוקי `> "..."` (blockquote) — משאיר את הטקסט בלבד
    s = re.sub(r'^>\s+', '', s, flags=re.MULTILINE)
    # `code`
    s = re.sub(r'`([^`\n]+?)`', r'<code>\1</code>', s)
    # **bold**
    s = re.sub(r'\*\*([^*\n]+?)\*\*', r'<b>\1</b>', s)
    return s


def _extract_bullets(body: str, skip_tables: bool = True) -> list:
    """Bullet items as plain strings. Skips markdown table rows (|...|)."""
    if not body:
        return []
    if skip_tables:
        body = '\n'.join(l for l in body.splitlines() if not l.lstrip().startswith('|'))
    return [m.group(1).strip() for m in _HANDOFF_BULLET_RE.finditer(body)]


def _first_paragraph(body: str, max_len: int = 800) -> str:
    """First non-empty paragraph, until blank line. Tables/blockquotes stripped."""
    if not body:
        return ''
    # ניקוי טבלאות לפני חיתוך פסקאות
    cleaned = '\n'.join(l for l in body.splitlines() if not l.lstrip().startswith('|'))
    chunks  = re.split(r'\n\s*\n', cleaned.strip())
    for c in chunks:
        c = c.strip()
        if c:
            return c[:max_len]
    return ''


def _all_paragraphs(body: str, max_count: int = 6) -> list:
    """Body → list of paragraph strings (HTML-escaped lightly via _md_inline_to_html).
    Skips paragraphs that are pure bullet lists (they're handled separately)."""
    if not body:
        return []
    cleaned = '\n'.join(l for l in body.splitlines() if not l.lstrip().startswith('|'))
    raw     = [p.strip() for p in re.split(r'\n\s*\n', cleaned.strip()) if p.strip()]
    out     = []
    for p in raw[:max_count]:
        lines = [ln for ln in p.splitlines() if ln.strip()]
        # דלג על פסקאות שכולן bullets — מטופלות ב-_extract_bullets
        if lines and all(_HANDOFF_BULLET_RE.match(ln) for ln in lines):
            continue
        out.append(_md_inline_to_html(' '.join(lines)))
    return out


# ── D-Lite: visual_scores → template-ready structures ───────────────────────
# קלט: dash['visual_scores'] (אופציונלי) שהמודל הפיק כ-JSON. אם null/חסר
# בכל שדה — מדלגים. אסור לחשב/לאמת מספרים שלא הופיעו במפורש.
# ההמרה מנרמלת גובה bars ל-max=65 (כדי לא לפרוץ את ה-CSS ceiling של .scen).

def _norm_heights(values: list, max_pct: int = 65) -> list:
    """Scale a list of positive numbers so the largest maps to max_pct, others proportional.
    Returns same length; None/0/negative stays None. None values mean 'no bar'."""
    nums = [v for v in values if isinstance(v, (int, float)) and v > 0]
    if not nums:
        return [None] * len(values)
    mx = max(nums)
    return [
        int(round(v / mx * max_pct)) if isinstance(v, (int, float)) and v > 0 else None
        for v in values
    ]


def _engines_from_scores(scores: dict) -> list:
    """visual_scores.business_engines → analyst template engines[]. Pct from weight_pct
    or revenue_b (normalized). Skips entries missing both label and any number."""
    src = scores.get('business_engines') or []
    if not src:
        return []
    # Prefer weight_pct (already a %); fall back to revenue_b normalized
    weights  = [e.get('weight_pct') for e in src]
    if not any(isinstance(w, (int, float)) and w > 0 for w in weights):
        weights = _norm_heights([e.get('revenue_b') for e in src], max_pct=100)
    out = []
    palette = ['var(--blue)', 'var(--purple)', 'var(--orange)', 'var(--green)', 'var(--gold)', 'var(--red)']
    for i, e in enumerate(src[:6]):
        if not e.get('label'):
            continue
        pct = weights[i] if i < len(weights) and weights[i] else 0
        rev = e.get('revenue_b')
        gr  = e.get('growth_pct')
        rev_str = f'${rev}B' if isinstance(rev, (int, float)) else '—'
        gr_str  = f'{"+" if isinstance(gr,(int,float)) and gr >= 0 else ""}{gr}%' if isinstance(gr, (int, float)) else ''
        out.append({
            'label':  _md_inline_to_html(str(e['label'])[:60]),
            'pct':    pct or 12,  # minimum visible bar
            'color':  palette[i % len(palette)],
            'val':    rev_str,
            'growth': gr_str,
        })
    return out


def _moat_items_from_scores(scores: dict) -> list:
    """visual_scores.moat_scores → analyst template moat.items[]. score_0_10 → bar width."""
    src = scores.get('moat_scores') or []
    out = []
    for m in src[:8]:
        if not m.get('label'):
            continue
        sc = m.get('score_0_10')
        if not isinstance(sc, (int, float)):
            continue
        sc_int = max(0, min(10, int(round(sc))))
        if sc_int >= 8:
            color, tag = 'var(--green)', f'🟢 חזק · {sc_int}/10'
        elif sc_int >= 5:
            color, tag = 'var(--yellow)', f'🟡 בינוני · {sc_int}/10'
        else:
            color, tag = 'var(--red)', f'🔴 חלש · {sc_int}/10'
        out.append({
            'label': _md_inline_to_html(str(m['label'])[:60]),
            'score': sc_int,
            'color': color,
            'tag':   tag,
        })
    return out


def _stress_from_scores(scores: dict) -> dict | None:
    """visual_scores.stress_categories → analyst stress_test {categories, total, summary}."""
    src = scores.get('stress_categories') or []
    cats, total = [], 0
    for c in src[:5]:
        if not c.get('label'):
            continue
        sc = c.get('score_0_10')
        if not isinstance(sc, (int, float)):
            continue
        sc_int = max(0, min(10, int(round(sc))))
        total += sc_int
        if sc_int >= 8:
            color, icon = 'var(--green)', '🟢'
        elif sc_int >= 5:
            color, icon = 'var(--yellow)', '🟡'
        else:
            color, icon = 'var(--red)', '🔴'
        cats.append({'label': _md_inline_to_html(str(c['label'])[:60]),
                     'score': sc_int, 'color': color, 'icon': icon})
    if not cats:
        return None
    max_total = len(cats) * 10
    return {
        'categories': cats,
        'total':      f'{total}/{max_total}',
        'summary':    f'<b>{total}/{max_total}</b> — ניקוד מבוסס {len(cats)} קטגוריות מאומתות (visual estimate from analyst handoff).',
    }


def _valuation_from_scores(scores: dict) -> dict | None:
    """visual_scores.valuation → analyst valuation {bear/base/bull/curline}.
    Heights normalized to max=65 to stay within CSS .scen ceiling without clipping."""
    v = scores.get('valuation') or {}
    bear_p = v.get('bear_price')
    base_p = v.get('base_price')
    bull_p = v.get('bull_price')
    cur_p  = v.get('current_price')
    if not any(isinstance(p, (int, float)) for p in (bear_p, base_p, bull_p)):
        return None

    # heights from prices themselves (relative). Skip missing prices visually.
    heights = _norm_heights([bear_p, base_p, bull_p], max_pct=65)
    def pct_label(p):
        if not isinstance(p, (int, float)) or not isinstance(cur_p, (int, float)) or cur_p == 0:
            return '—'
        delta = (p - cur_p) / cur_p * 100
        return f'{"+" if delta >= 0 else ""}{delta:.0f}%'

    out = {}
    out['description'] = 'תרחישים יחסיים מנורמלים לפי המחירים שהמודל ציטט (לא הומצאו).'
    if isinstance(bear_p, (int, float)):
        out['bear'] = {'price': f'${bear_p:g}', 'height': heights[0] or 12,
                       'pct': pct_label(bear_p), 'sub': 'תרחיש דובי'}
    if isinstance(base_p, (int, float)):
        out['base'] = {'price': f'${base_p:g}', 'height': heights[1] or 12,
                       'pct': pct_label(base_p), 'sub': 'תרחיש בסיס'}
    if isinstance(bull_p, (int, float)):
        out['bull'] = {'price': f'${bull_p:g}', 'height': heights[2] or 12,
                       'pct': pct_label(bull_p), 'sub': 'תרחיש שורי'}
    # All three required by template (template reads d.valuation.bear.price unguarded).
    # If only some emitted, fill missing with safe stubs.
    for k in ('bear', 'base', 'bull'):
        if k not in out:
            out[k] = {'price': '—', 'height': 12, 'pct': '—', 'sub': '(לא צוין במקור)'}
    if isinstance(cur_p, (int, float)):
        out['curline'] = f'מחיר נוכחי: <b>${cur_p:g}</b>'
    return out


def _financials_charts_from_scores(scores: dict) -> dict | None:
    """visual_scores.financials_3y → analyst financials_3y {charts, table}."""
    src = scores.get('financials_3y') or []
    if not src:
        return None
    # Filter rows that have at least year + one number
    rows = [r for r in src if r.get('year') and any(
        isinstance(r.get(k), (int, float)) for k in ('revenue_b','op_margin_pct','fcf_b','eps')
    )]
    if not rows:
        return None
    charts = []
    def mkchart(title, key, color, suffix=''):
        bars = []
        for r in rows[:5]:
            v = r.get(key)
            if isinstance(v, (int, float)):
                bars.append({'year': r['year'], 'label': f'{v:g}{suffix}',
                             'v': float(v), 'color': color})
        if len(bars) >= 2:
            charts.append({'title': title, 'bars': bars, 'foot': ''})
    mkchart('הכנסות ($B)',    'revenue_b',     'var(--blue)',   '')
    mkchart('מרווח תפעולי (%)', 'op_margin_pct', 'var(--purple)', '%')
    mkchart('FCF ($B)',        'fcf_b',         'var(--green)',  '')
    mkchart('EPS ($)',         'eps',           'var(--gold)',   '')
    if not charts:
        return None
    return {
        'description': 'מבוסס על מספרים מאומתים שהמודל ציטט (visual scores). חסרי-מקור נשמטו.',
        'charts':      charts,
    }


def _risk_reward_html(rr: dict, scores: dict) -> str:
    """IC: render a small horizontal scale showing current vs trigger vs fair_value."""
    cp = rr.get('current_price'); fv = rr.get('fair_value')
    tp = rr.get('trigger_price'); sl = rr.get('stop_price'); t1 = rr.get('tp1_price')
    if not any(isinstance(x, (int, float)) for x in (cp, fv, tp, t1)):
        return ''
    items = []
    if isinstance(cp, (int, float)):
        items.append({'lbl': 'מחיר נוכחי', 'val': f'${cp:g}'})
    if isinstance(tp, (int, float)):
        items.append({'lbl': 'טריגר כניסה', 'val': f'${tp:g}'})
    if isinstance(fv, (int, float)):
        items.append({'lbl': 'שווי הוגן', 'val': f'${fv:g}'})
    if isinstance(t1, (int, float)):
        items.append({'lbl': 'TP1', 'val': f'${t1:g}'})
    if isinstance(sl, (int, float)):
        items.append({'lbl': 'Stop', 'val': f'${sl:g}'})
    if not items:
        return ''
    return _cards_grid_html(items, color_class='c-blue')


# ── Visual helpers (HTML primitives, no template touch) ──────────────────────
# מטרה: לארוז רשימות מ-handoff לתוך grid של .cards (CSS קיים) שמשתל
# כ-HTML בתוך description של כל סקציה. הטמפלט כבר מרנדר description
# כ-raw HTML, ולכן אין צורך לגעת בו. שום מספר לא מומצא מפרוזה —
# הכרטיסים מציגים רק labels טקסטואליים מה-bullets.

def _severity_from_emoji(text: str) -> str:
    """Map leading 🔴/🟡/🟢 to severity color class. Default 'red' for red_flags."""
    t = (text or '').lstrip()
    if t.startswith('🟢') or t.startswith('✅'):
        return 'green'
    if t.startswith('🟡') or t.startswith('⚠️'):
        return 'yellow'
    if t.startswith('🔴') or t.startswith('❌'):
        return 'red'
    return 'red'


def _cards_grid_html(items, color_class: str = 'c-text', label_prefix: str = '') -> str:
    """Render list of {lbl?, val} or plain strings as a .cards grid (CSS primitive)."""
    if not items:
        return ''
    cells = []
    for i, it in enumerate(items[:6]):
        if isinstance(it, dict):
            lbl = it.get('lbl') or (f'{label_prefix} {i+1}' if label_prefix else f'#{i+1}')
            val = it.get('val', '')
            sub = it.get('sub', '')
        else:
            lbl = f'{label_prefix} {i+1}' if label_prefix else f'#{i+1}'
            val = str(it)
            sub = ''
        sub_html = f'<div class="sub">{sub}</div>' if sub else ''
        cells.append(
            f'<div class="card"><div class="lbl">{lbl}</div>'
            f'<div class="val {color_class}" style="font-size:13px;line-height:1.4">{val}</div>'
            f'{sub_html}</div>'
        )
    grid_style = 'margin:14px 0 6px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr))'
    return f'<div class="cards" style="{grid_style}">' + ''.join(cells) + '</div>'


def _short_label(s: str, max_len: int = 90) -> str:
    """Compact label for card display: strip leading emoji marker, drop trailing
    parenthetical/source notes, cap length. KEEPS the meaningful body (no
    aggressive split on first ' — ', which loses info when prefix is shared)."""
    if not s:
        return ''
    s = s.strip()
    # שלוף emoji תחילי + רווח (🔴/🟡/🟢/✅ וכו') כדי לא להציג אותו פעמיים
    s = re.sub(r'^[🔴🟡🟢✅⚠️❌➤◆◇•\-*]+\s*', '', s)
    # קצוץ הערות-מקור בסוגריים בסוף ("(מקור: ...)")
    s = re.sub(r'\s*\([^)]{0,40}\)\s*$', '', s)
    if len(s) > max_len:
        s = s[:max_len].rstrip() + '…'
    return _md_inline_to_html(s)


def _drill_subsections(body: str) -> list:
    """Split body into (subheader, sub_body) tuples. Supports BOTH:
      - markdown ### headers (require own line)
      - **bold:** style markers (line start, may have inline body following)

    Frequency heuristic: a bold label that REPEATS across the body is a
    sub-label (e.g., 'ראיה:' appearing once per conflict), NOT a section
    header. Such repeated bolds are skipped to avoid fragmenting the output.
    Bolds appearing exactly once are treated as section headers."""
    if not body:
        return []
    spans = []  # (start, header_end, header_text)
    for m in re.finditer(r'^#{3,}\s+(.+?)\s*$', body, re.MULTILINE):
        spans.append((m.start(), m.end(), m.group(1).strip().rstrip(':').strip()))
    # bold pattern — count occurrences first; keep only labels appearing once
    bold_matches = list(re.finditer(r'^\s*\*\*([^*\n]{2,80})\*\*\s*:?', body, re.MULTILINE))
    if bold_matches:
        from collections import Counter
        labels = [m.group(1).strip().rstrip(':').strip() for m in bold_matches]
        counts = Counter(labels)
        for m, lbl in zip(bold_matches, labels):
            if counts[lbl] == 1:  # unique → likely a real section header
                spans.append((m.start(), m.end(), lbl))
    if not spans:
        return []
    spans.sort()
    # de-overlap: drop any span that starts inside a previous span
    deduped = []
    last_end = -1
    for s, e, h in spans:
        if s >= last_end:
            deduped.append((s, e, h))
            last_end = e
    out = []
    for i, (_, hend, h) in enumerate(deduped):
        next_start = deduped[i + 1][0] if i + 1 < len(deduped) else len(body)
        sub_body = body[hend:next_start].strip()
        if not h or not sub_body:
            continue
        out.append((h, sub_body))
    return out


def _freshness_chip_html(path: str | None, fallback_date: str = '') -> str:
    """Return 'date <chip>🟢 Fresh (Nd)</chip>' HTML, computed from file mtime."""
    from datetime import datetime as _dt
    if path and os.path.exists(path):
        try:
            mtime = os.path.getmtime(path)
            age_days = (time.time() - mtime) / 86400
            dt_str   = _dt.fromtimestamp(mtime).strftime('%Y-%m-%d')
        except Exception:
            return fallback_date or ''
    else:
        return fallback_date or ''
    if age_days < 14:
        emoji, label, color = '🟢', 'Fresh', '#2ecc71'
    elif age_days < 45:
        emoji, label, color = '🟡', 'Aging', '#f5c842'
    else:
        emoji, label, color = '🔴', 'Stale', '#e05c5c'
    days_int = int(age_days)
    chip = (f' <span style="display:inline-block;font-size:10px;font-weight:700;'
            f'padding:3px 9px;border-radius:11px;background:rgba(120,120,120,.12);'
            f'border:1px solid {color}55;color:{color};margin-right:6px">'
            f'{emoji} {label} · {days_int}d</span>')
    return (fallback_date or dt_str) + chip


def _ticker_current_price(ticker: str) -> float | None:
    """Live price from in-memory price cache or fresh fetch. Returns None on failure."""
    try:
        prices = get_prices([ticker.upper()])
        p = prices.get(ticker.upper(), {})
        return float(p['current_price']) if p.get('current_price') is not None else None
    except Exception:
        return None


# ── Structural drift resilience helpers ─────────────────────────────────────
# המודל לפעמים משנה את שמות הסקציות בין ריצות. ה-helpers הללו מספקים
# fallback דטרמיניסטי כדי שהדשבורד יישאר עקבי. אסור inference; רק שילוב
# של data מובנה (dashboard-json, visual_scores) ושל סקציות שנמצאו במפורש.

def _growth_from_engines(vs: dict) -> dict | None:
    """Build a 'growth' section from business_engines visual_scores when no
    dedicated 'מנועי צמיחה' section was emitted. Each engine becomes a stat card
    showing its label + growth_pct (REAL numbers from JSON — not inferred)."""
    engines = (vs or {}).get('business_engines') or []
    stats = []
    for e in engines[:5]:
        if not e.get('label'):
            continue
        gp = e.get('growth_pct')
        if not isinstance(gp, (int, float)):
            continue
        sign = '+' if gp >= 0 else ''
        color = 'c-green' if gp >= 15 else ('c-yellow' if gp >= 0 else 'c-red')
        stats.append({
            'lbl':    _md_inline_to_html(str(e['label'])[:50]),
            'val':    f'{sign}{gp}%',
            'growth': 'צמיחה YoY (מתוך visual scores)',
        })
    if not stats:
        return None
    return {
        'description': 'מנועי צמיחה גזורים מ-business_engines (אותם מספרים שהמודל אמת).',
        'stats':       stats,
    }


def _crash_banner_from_handoff(dash: dict, sections: list) -> dict | None:
    """Return {title, body} ONLY when an explicit drawdown/volatility mention exists.
    Order of preference (deterministic, no inference):
      1. Section explicitly titled crash/drawdown/ירידה/מצב נוכחי
      2. key_risks[] entry containing both a drawdown keyword and a '%' marker
    Returns None if nothing explicit was found."""
    # (1) explicit section
    for needle in ('crash', 'drawdown', 'ירידה משמעותית', 'drawdown context', '52w low'):
        body = _find_section(sections, needle)
        if body:
            first = _first_paragraph(body, 500)
            if first:
                return {'title': '📉 הקשר ירידה (מצוטט מ-handoff)',
                        'body':  _md_inline_to_html(first)}
    # (2) explicit drawdown wording in key_risks
    risks = dash.get('key_risks') if dash else None
    if isinstance(risks, list):
        kw = ('drawdown', 'ירידה', 'crash', 'collapsed', 'fell from', 'ירד מ',
              'נפילה', 'sell-off', 'plunge')
        for r in risks:
            s = str(r)
            if any(k.lower() in s.lower() for k in kw) and '%' in s:
                return {'title': '⚠️ סיכון משמעותי מסומן ב-key_risks',
                        'body':  _md_inline_to_html(s)}
    return None


def _matrix_from_agent_reviews(ticker: str) -> dict | None:
    """Fallback IC matrix: build a 3-row table (verdict / score / position_size_pct)
    across analyst/devils/ceo/executor/ic from cached _reviews/<agent>.json.
    Uses ONLY structured numbers — no prose extraction."""
    rdir = os.path.join(ANALYSES_DIR, ticker.upper(), '_reviews')
    if not os.path.isdir(rdir):
        return None
    agent_order  = ['analyst', 'devils', 'ceo', 'executor', 'ic']
    agent_labels = {'analyst': 'אנליסט', 'devils': 'שטן', 'ceo': 'CEO',
                    'executor': 'מבצע',  'ic': 'ועדה'}
    per = {}
    for ag in agent_order:
        rp = os.path.join(rdir, f'{ag}.json')
        if os.path.exists(rp):
            try:
                per[ag] = json.load(open(rp, encoding='utf-8'))
            except Exception:
                continue
    if len(per) < 2:
        return None

    def vclass(v):
        v = (str(v or '').upper().replace(' ', '_'))
        if v in ('BUY', 'APPROVED', 'APPROVED_WITH_CONDITIONS'):
            return 'cell-g'
        if v in ('WATCHLIST', 'HOLD', 'REVIEW', 'PENDING', 'PENDING_TECHNICAL_DATA'):
            return 'cell-y'
        if v in ('AVOID', 'SELL', 'REJECTED'):
            return 'cell-r'
        return ''

    present = [a for a in agent_order if a in per]
    headers = [agent_labels[a] for a in present]
    def fmt(v, suffix=''):
        return f'{v}{suffix}' if v is not None and v != '' else '—'
    rows = [
        {'label': 'פסיקה',
         'cells': [{'cls': vclass(per[a].get('verdict')),
                    'text': fmt(per[a].get('verdict'))} for a in present]},
        {'label': 'ציון',
         'cells': [{'cls': '',
                    'text': fmt(per[a].get('score'), '/100')} for a in present]},
        {'label': 'גודל מומלץ',
         'cells': [{'cls': '',
                    'text': fmt(per[a].get('position_size_pct'), '%')} for a in present]},
    ]
    return {
        'description': 'מטריצת קונסנזוס: dashboard-json מכל סוכן (verdict/ציון/גודל). מספרים אמיתיים בלבד.',
        'headers':     headers,
        'rows':        rows,
        'note':        '',
    }


def _enrich_analyst_dashboard(data: dict, sections: list, dash: dict | None = None) -> None:
    """Add text-only rich sections to analyst data, in-place. No numbers from prose.
    Optional: dash['visual_scores'] (D-Lite) upgrades grids to true scored bars."""

    vs = (dash or {}).get('visual_scores') or {}

    # ── מודל עסקי: description + רשת מנועי הכנסה ────────────────────────
    bm = _find_section(sections, 'מודל עסקי', 'business model')
    engines = _engines_from_scores(vs)
    if bm or engines:
        if bm:
            items = _items_from_section(bm)
            desc  = _md_inline_to_html(_first_paragraph(bm))
            grid  = _cards_grid_html(
                [{'lbl': f'מנוע {i+1}', 'val': _short_label(b, 90)} for i, b in enumerate(items[:6])],
                color_class='c-blue',
            ) if items else ''
            data['business_model'] = {'description': desc + grid}
        else:
            data['business_model'] = {'description': 'מנועי הכנסה (visual scores)'}
        if engines:
            data['business_model']['engines']       = engines
            data['business_model']['engines_label'] = 'מנועי הכנסה (visual scores)'

    # ── מנועי צמיחה: section אם קיים, אחרת fallback מ-business_engines ──
    gr = _find_section(sections, 'מנועי צמיחה', 'מקורות צמיחה', 'growth drivers',
                       'growth engines', 'engines of growth')
    growth_fallback = _growth_from_engines(vs)
    if gr:
        items = _items_from_section(gr)
        desc  = _md_inline_to_html(_first_paragraph(gr))
        grid  = _cards_grid_html(
            [{'lbl': f'מנוע צמיחה {i+1}', 'val': _short_label(b, 90)} for i, b in enumerate(items[:6])],
            color_class='c-green',
        ) if items else ''
        data['growth'] = {'description': desc + grid}
        # אם יש גם growth_pct ב-visual_scores → הוסף stats לכרטיסי .statbig
        if growth_fallback:
            data['growth']['stats'] = growth_fallback['stats']
    elif growth_fallback:
        # אין סקציה — בנה אך ורק מ-visual_scores (מספרים אמיתיים)
        data['growth'] = growth_fallback

    # ── חפיר: description + רשת חוזקות חפיר ─────────────────────────────
    mo = _find_section(sections, 'חפיר', 'יתרון תחרותי', 'moat')
    moat_items = _moat_items_from_scores(vs)
    if mo or moat_items:
        if mo:
            items = _items_from_section(mo)
            desc  = _md_inline_to_html(_first_paragraph(mo))
            grid  = _cards_grid_html(
                [{'lbl': f'חוזק {i+1}', 'val': _short_label(b, 90)} for i, b in enumerate(items[:6])],
                color_class='c-gold',
            ) if items else ''
            data['moat'] = {'description': desc + grid}
        else:
            data['moat'] = {'description': 'חפיר (visual scores)'}
        if moat_items:
            data['moat']['items'] = moat_items
            data['moat']['note']  = '<b>ניקוד 0-10</b> מבוסס visual scores שהמודל סיפק. ערכים חסרים נשמטו.'

    # ── רבעון אחרון: description + כרטיסי KPIs מטקסט ──────────────────
    qu = _find_section(sections, 'רבעון אחרון', 'אבחונים רבעוניים', 'הערכה רבעונית', 'רבעוני')
    if qu:
        items = _items_from_section(qu)
        desc  = _md_inline_to_html(_first_paragraph(qu))
        grid  = _cards_grid_html(
            [{'lbl': f'KPI {i+1}', 'val': _short_label(b, 90)} for i, b in enumerate(items[:4])],
            color_class='c-blue',
        ) if items else ''
        data['quarterly'] = {'description': desc + grid}

    # ── מבחן לחץ: summary + (אם visual_scores) categories עם bars ──────
    # התנאי: הסקציה במ"ד OR visual_scores. כך גם כש-handoff שינה את שמות
    # הסקציות אנחנו עדיין מציגים scored bars אם המודל הפיק visual_scores.
    st = _find_section(sections, 'מבחן לחץ', 'stress test')
    stress_scored = _stress_from_scores(vs)
    if st or stress_scored:
        cat_items = _items_from_section(st) if st else []
        cat_grid  = _cards_grid_html(
            [{'lbl': f'תחום {i+1}', 'val': _short_label(c, 80)} for i, c in enumerate(cat_items[:5])],
            color_class='c-purple',
        ) if cat_items else ''
        st_desc = _md_inline_to_html(_first_paragraph(st, 600)) if st else ''
        if stress_scored:
            data['stress_test'] = {
                'summary':    (st_desc + cat_grid) or stress_scored['summary'],
                'total':      stress_scored['total'],
                'categories': stress_scored['categories'],
            }
        else:
            data['stress_test'] = {
                'summary':    (st_desc + cat_grid) or 'מבחן לחץ מוסדי — ראה handoff המלא',
                'total':      '—',
                'categories': [],
            }

    # ── valuation: bear/base/bull (D-Lite בלבד; אין fallback ל-prose) ──
    valuation = _valuation_from_scores(vs)
    if valuation:
        data['valuation'] = valuation

    # ── financials_3y: charts מ-visual_scores בלבד ────────────────────
    fin = _financials_charts_from_scores(vs)
    if fin:
        data['financials_3y'] = fin

    # ── red_flags: items עם severity מאמוג'י תחילית (לא מומצא) ─────────
    # מעדיף שורות-טבלה (מקור הסיווג של ה-LLM עם 🔴🟡🟢), bullets רק כ-fallback.
    rf_body  = _find_section(sections, 'דגלים אדומים', 'דגלים פורנזיים', 'red flags')
    rf_items = _items_from_section(rf_body)
    if rf_items:
        data['red_flags'] = [
            {
                'rank':     str(i + 1),
                'severity': _severity_from_emoji(b),
                'title':    _short_label(b, 120),
                'body':     _md_inline_to_html(b),
            }
            for i, b in enumerate(rf_items[:6])
        ]
    elif data.get('key_risks'):
        data['red_flags'] = [
            {
                'rank':     str(i + 1),
                'severity': _severity_from_emoji(str(r)),
                'title':    _short_label(str(r), 120),
                'body':     _md_inline_to_html(str(r)),
            }
            for i, r in enumerate(data['key_risks'][:5])
        ]

    # ── final: paragraphs + scorecard מ-dashboard-json בלבד (לא מ-prose) ─
    fn_body = _find_section(sections, 'שיפוט איכות סופי', 'שיפוט סופי', 'סיכום אנליסט')
    paras   = _all_paragraphs(fn_body) if fn_body else []
    if data.get('thesis') and (not paras or data['thesis'] not in (paras[0] if paras else '')):
        paras = [_md_inline_to_html(data['thesis'])] + paras
    sc_card = []
    if data.get('verdict'):
        sc_card.append({'lbl': 'פסיקה', 'val': data['verdict'], 'color': 'c-blue'})
    if data.get('score') is not None:
        sc_card.append({'lbl': 'ציון איכות', 'val': f"{data['score']}/100", 'color': 'c-green'})
    if data.get('position_size_pct') is not None:
        sc_card.append({'lbl': 'גודל פוזיציה', 'val': f"{data['position_size_pct']}%", 'color': 'c-text'})
    if paras or data.get('handoff_summary') or sc_card:
        data['final'] = {
            'headline':   data.get('verdict') or 'סיכום אנליסט',
            'paragraphs': paras[:4],
            'scorecard':  sc_card,
            'handoff':    _md_inline_to_html(data.get('handoff_summary', '')),
        }

    # ── crash_banner: רק אם יש אזכור drawdown מפורש (לא inference) ─────
    cb = _crash_banner_from_handoff(dash or {}, sections)
    if cb:
        data['crash_banner'] = cb

    # ── footer: מאימות מקורות / sources / verification — תמיד מנסה ─────
    src = _find_section(sections, 'אימות מקורות', 'source verification',
                        'verification', 'sources', 'מקורות')
    if src:
        data['footer'] = _md_inline_to_html(_first_paragraph(src, 400))
    elif not data.get('footer'):
        # fallback דטרמיניסטי — תמיד יש footer מינימלי
        data['footer'] = '<b>אימות מקורות:</b> פרטי handoff המלא ב-analyses/' + str(data.get('ticker') or '') + '/_handoffs/'

    # ── disclaimer: תמיד יש (deterministic default אם אין מ-handoff) ──
    if not data.get('disclaimer'):
        data['disclaimer'] = 'מסמך זה אינו ייעוץ השקעות. הנתונים מבוססים על מקורות שצוטטו בלבד ב-handoff. הסתמכות עצמית.'


def _enrich_ic_dashboard(data: dict, sections: list, dash: dict | None = None) -> None:
    """Add text-only rich sections to IC data, in-place. Replaces verdict string with object.
    Optional: dash['visual_scores'] adds risk/reward block from explicit numbers."""

    vs = (dash or {}).get('visual_scores') or {}

    # ── risk/reward (D-Lite): כרטיסי מחיר נוכחי/טריגר/שווי הוגן ─────
    rr = vs.get('risk_reward') or {}
    rr_html = _risk_reward_html(rr, vs) if rr else ''
    if rr_html:
        data['risk_reward_html'] = rr_html  # יוטמע ב-triggers.description אח"כ

    # inherited — בדרך כלל טבלה. נשלוף את התא הראשון כ-text-bullets.
    inh = _find_section(sections, 'אימות קלטים', 'אימות קלט')
    if inh:
        rows = [l for l in inh.splitlines() if l.lstrip().startswith('|') and '---' not in l]
        items = []
        for row in rows[:8]:
            cells = [c.strip() for c in row.strip('|').split('|') if c.strip()]
            if cells and len(cells) >= 2:
                items.append({'icon': '✓', 'text': _md_inline_to_html(' · '.join(cells))})
        if items:
            data['inherited'] = items
        else:
            # אם זה לא טבלה — נסה bullets
            for b in _extract_bullets(inh)[:8]:
                data.setdefault('inherited', []).append(
                    {'icon': '✓', 'text': _md_inline_to_html(b)}
                )

    # consensus_points — bullets מתוך "ניתוח קונסנזוס" / "קונסנזוס סוכנים"
    cp_body  = _find_section(sections, 'קונסנזוס סוכנים', 'ניתוח קונסנזוס')
    cp_items = _extract_bullets(cp_body)
    if cp_items:
        data['consensus_points'] = [
            {
                'title': _short_label(b, 100),
                'body':  _md_inline_to_html(b),
            }
            for b in cp_items[:6]
        ]

    # disagreements — עמיד ל-### subsections. תמיד מנסה drill לפני שמחזיר פסקה.
    dis = _find_section(sections, 'חילוקי דעות', 'disagreements', 'conflicts',
                        'קונפליקטים', 'נקודות מחלוקת')
    if dis:
        # נסה תמיד drill קודם — אם יש ### → הוצא תקצירים מפורטים יותר.
        # רק אם אין subsections, חזור לפסקה הראשונה.
        subs = _drill_subsections(dis)
        if subs:
            parts = []
            for sub_h, sub_body in subs[:4]:
                first = _first_paragraph(sub_body, 350)
                if first:
                    parts.append(
                        f'<b>{_md_inline_to_html(sub_h)}:</b> {_md_inline_to_html(first)}'
                    )
            if parts:
                data['disagreements'] = '<br><br>'.join(parts)
            else:
                data['disagreements'] = _md_inline_to_html(_first_paragraph(dis, 1200))
        else:
            data['disagreements'] = _md_inline_to_html(_first_paragraph(dis, 1200))

    # blindspot — headline + paragraphs (טקסט בלבד; אין impact מבוצר אם אין)
    bs = _find_section(sections, 'חשיבת-עדר', 'חשיבת עדר', 'נקודה עיוורת')
    if bs:
        bs_paras = _all_paragraphs(bs, max_count=4)
        data['blindspot'] = {
            'headline':   'נקודה עיוורת משותפת',
            'paragraphs': bs_paras if bs_paras else [_md_inline_to_html(_first_paragraph(bs, 1000))],
        }

    # most_right — needles רחבים + fallback ישיר מ-_reviews (לא תלוי בסדר build)
    mr = _find_section(sections, 'הכי צודק', 'מי צודק', 'יהיה צודק',
                       'most likely correct', 'closest to right', 'best signal',
                       'אמינות גבוהה', 'הסוכן הקובע')
    if mr:
        data['most_right'] = _md_inline_to_html(_first_paragraph(mr, 800))
    else:
        # fallback דטרמיניסטי: קרא ישירות את _reviews של 4 הסוכנים האחרים
        # ובחר את זה עם הציון הגבוה ביותר. אינו תלוי ב-data['matrix'].
        tk = data.get('ticker')
        if tk:
            rdir = os.path.join(ANALYSES_DIR, tk.upper(), '_reviews')
            if os.path.isdir(rdir):
                labels = {'analyst': 'אנליסט', 'devils': 'שטן', 'ceo': 'CEO',
                          'executor': 'מבצע'}
                scored = []
                for ag, lbl in labels.items():
                    rp = os.path.join(rdir, f'{ag}.json')
                    if os.path.exists(rp):
                        try:
                            d = json.load(open(rp, encoding='utf-8'))
                            sc = d.get('score')
                            if isinstance(sc, (int, float)):
                                scored.append((float(sc), lbl, d.get('verdict') or ''))
                        except Exception:
                            continue
                if scored:
                    scored.sort(reverse=True)
                    best_sc, best_lbl, best_vd = scored[0]
                    data['most_right'] = (
                        f'<b>{best_lbl}</b> ({best_vd}) מקבל את הציון הגבוה ביותר '
                        f'({best_sc:.0f}/100) מ-4 הסוכנים. fallback דטרמיניסטי — '
                        f'ה-handoff לא כלל סקציה מפורשת על הסוכן הצודק.'
                    )

    # hard_truth — needles רחבים + fallback ל-key_risks[0] (deterministic)
    ht = _find_section(sections, 'האמת הקשה', 'hard truth', 'bottom line',
                       'risk reality', 'הסיכון האמיתי', 'מה לא יודעים',
                       'מסקנה כנה', 'brutal truth', 'הסיכון הקריטי')
    if ht:
        first = _first_paragraph(ht, 800)
        if first:
            data['hard_truth'] = _md_inline_to_html(first)
        else:
            # סקציה קיימת אבל ריקה — נסה drill ל-### תת-סעיף
            subs = _drill_subsections(ht)
            if subs and subs[0][1]:
                data['hard_truth'] = _md_inline_to_html(_first_paragraph(subs[0][1], 800))
    # fallback אחרון: אם אין hard_truth מסקציה, השתמש ב-key_risks[0]
    if not data.get('hard_truth') and isinstance(data.get('key_risks'), list) and data['key_risks']:
        data['hard_truth'] = ('<b>הסיכון המוביל לפי ה-dashboard-json:</b> '
                              + _md_inline_to_html(str(data['key_risks'][0])))

    # triggers — bullets מתוך "לוח זמני מעקב" / "תנאים נדרשים"; fallback ל-entry_exit_plan
    tr_body  = _find_section(sections, 'לוח זמני מעקב', 'טריגרי מעקב', 'תנאים נדרשים')
    tr_items = _extract_bullets(tr_body)
    rr_html_prefix = data.pop('risk_reward_html', '')  # אם נמצא, מטמיע מעל ה-description
    if tr_items:
        data['triggers'] = {
            'title':       'טריגרי מעקב',
            'description': rr_html_prefix + _md_inline_to_html(_first_paragraph(tr_body, 400)),
            'items':       [{'icon': '◆', 'text': _md_inline_to_html(b)} for b in tr_items[:8]],
        }
    elif data.get('entry_exit_plan'):
        data['triggers'] = {
            'title':       'תוכנית כניסה/יציאה',
            'description': rr_html_prefix,
            'items':       [{'icon': '◆', 'text': _md_inline_to_html(data['entry_exit_plan'])}],
        }
    elif rr_html_prefix:
        # רק risk/reward קיים, ללא bullets/entry_exit_plan
        data['triggers'] = {
            'title':       'מטריצת סיכון/תשואה',
            'description': rr_html_prefix,
            'items':       [],
        }

    # scorecard — אך ורק מ-dashboard-json (מספרים שהמודל הפיק כ-JSON, לא prose)
    sc = []
    if data.get('verdict'):
        sc.append({'lbl': 'פסיקת ועדה', 'val': data['verdict'], 'color': 'c-blue'})
    if data.get('score') is not None:
        sc.append({'lbl': 'ציון',         'val': str(data['score']), 'color': 'c-text'})
    if data.get('position_size_pct') is not None:
        sc.append({'lbl': 'גודל פוזיציה', 'val': f"{data['position_size_pct']}%", 'color': 'c-text'})
    if data.get('valuation_summary'):
        sc.append({'lbl': 'שווי',         'val': data['valuation_summary'][:80], 'color': 'c-text'})
    if sc:
        data['scorecard'] = sc

    # verdict OBJECT (החלפת מחרוזת ה-verdict). ה-template מצפה ל-d.verdict.headline/etc.
    # מקור הסקציה: "פסיקת ועדה סופית" / "החלטת השקעה סופית" / "פסיקת ועדה"
    vrd_body  = _find_section(sections, 'פסיקת ועדה סופית', 'החלטת השקעה סופית', 'פסיקת ועדה')
    vrd_paras = _all_paragraphs(vrd_body) if vrd_body else []
    if not vrd_paras and data.get('handoff_summary'):
        vrd_paras = [_md_inline_to_html(data['handoff_summary'])]
    scoreboxes = []
    if data.get('verdict'):
        scoreboxes.append({'lbl': 'פסיקה',  'val': data['verdict'],         'color': 'c-blue', 'size': '20'})
    if data.get('score') is not None:
        scoreboxes.append({'lbl': 'ציון',   'val': str(data['score']),      'color': 'c-text', 'size': '24'})
    if data.get('position_size_pct') is not None:
        scoreboxes.append({'lbl': 'גודל',   'val': f"{data['position_size_pct']}%", 'color': 'c-text', 'size': '20'})
    style_map = {
        'BUY': 'green', 'APPROVED': 'green', 'APPROVED_WITH_CONDITIONS': 'green',
        'WATCHLIST': 'yellow', 'HOLD': 'yellow', 'REVIEW': 'yellow',
        'AVOID': 'red', 'SELL': 'red', 'REJECTED': 'red',
    }
    style    = style_map.get(str(data.get('verdict') or '').upper().replace(' ', '_'), 'green')
    headline = data.get('verdict') or 'החלטת ועדה'
    if vrd_paras or scoreboxes:
        # ה-template דורש object — אנו דורסים את ה-string הקודם.
        # מחרוזת ה-verdict המקורית נשמרת ב-_reviews/<agent>.json שמשמש לסנכרון.
        data['verdict'] = {
            'style':       style,
            'headline':    headline,
            'paragraphs':  vrd_paras[:3],
            'scoreboxes':  scoreboxes,
        }

    # ── matrix: fallback מ-_reviews של כל סוכן (verdict/score/position) ─
    # זוהי טבלת קונסנזוס מבוססת dashboard-json של 5 הסוכנים — מספרים
    # מובנים בלבד, אפס prose extraction. ה-template עוטף ב-`if d.matrix`.
    if not data.get('matrix'):
        tk = data.get('ticker')
        if tk:
            m = _matrix_from_agent_reviews(tk)
            if m:
                data['matrix'] = m

    # handoff title + body
    if data.get('handoff_summary'):
        data['handoff_title'] = 'HANDOFF למתעד עסקאות'
        data['handoff']       = _md_inline_to_html(data['handoff_summary'])

    # footer מינימלי אם חסר
    if not data.get('footer'):
        data['footer'] = '<b>החלטת ועדה:</b> מבוססת על 4 handoffs (analyst/devils/CEO/executor). פרטים מלאים: analyses/' + str(data.get('ticker') or '') + '/_handoffs/'


def _write_visual_js(ticker: str, agent: str, dash: dict) -> dict:
    """Generate analyses/<T>/<agent>.js (or <agent>.auto.js if manual).

    Manual detection: a primary file is considered "manual" (do-not-overwrite)
    unless its first line equals _AUTO_MARKER. New auto files are written WITH
    the marker → next run safely overwrites them as primary.

    Enrichment: parses the agent's handoff markdown for text-only rich sections
    (paragraphs, bullets). Numbers come ONLY from dashboard-json — never inferred
    from prose. If handoff missing → minimal preview shape (backward compatible).
    """
    tdir = os.path.join(ANALYSES_DIR, ticker.upper())
    os.makedirs(tdir, exist_ok=True)
    primary = os.path.join(tdir, f'{agent}.js')

    if not os.path.exists(primary) or _is_auto_generated(primary):
        target = primary
    else:
        target = os.path.join(tdir, f'{agent}.auto.js')

    # freshness chip: מבוסס על mtime של _reviews/<agent>.json (הקובץ הסטרוקטורי
    # שנשמר במקביל). אם חסר, fallback למחרוזת התאריך כפי שהיא.
    review_path  = os.path.join(tdir, '_reviews', f'{agent}.json')
    base_date    = dash.get('date') or datetime.now().strftime('%Y-%m-%d')
    date_with_chip = _freshness_chip_html(review_path, base_date)

    data = {
        'ticker':              ticker.upper(),
        'company':             dash.get('company') or ticker.upper(),
        'date':                date_with_chip,
        'sector':              dash.get('sector', ''),
        'period':              dash.get('period', ''),
        'verdict':             dash.get('verdict'),
        'score':               dash.get('score'),
        'position_size_pct':   dash.get('position_size_pct'),
        'valuation_summary':   dash.get('valuation_summary'),
        'thesis':              dash.get('thesis', ''),
        'key_risks':           dash.get('key_risks', []),
        'verification_banner': dash.get('verification_banner',
                                       'נתונים אוטומטיים מ-handoff + dashboard-json'),
        'market_cards': [
            {'lbl': 'Verdict',       'val': dash.get('verdict') or '—', 'color': 'c-blue'},
            {'lbl': 'Score',         'val': str(dash.get('score') or '—')},
            {'lbl': 'Position Size', 'val': f'{dash.get("position_size_pct") or "—"}%'},
            {'lbl': 'Valuation',     'val': dash.get('valuation_summary') or '—'},
        ],
        'handoff_summary': dash.get('handoff_summary', ''),
        'entry_exit_plan': dash.get('entry_exit_plan', ''),
    }

    # העשרה טקסטואלית מ-handoff (אם קיים) — לא מוסיף טוקני LLM, רק קריאת קובץ.
    # D-Lite: dash מועבר כדי שה-enricher יקרא dash['visual_scores'] (אם המודל הפיק).
    md_path = _latest_handoff_md(ticker, agent)
    if md_path:
        sections = _parse_handoff_sections(md_path)
        if agent == 'analyst':
            _enrich_analyst_dashboard(data, sections, dash)
        elif agent == 'ic':
            _enrich_ic_dashboard(data, sections, dash)
        # devils/ceo/executor: נשארים על ה-shape המינימלי הקיים (התאמת template
        # נפרדת תידרש לעתיד; אין שינוי התנהגות).

    js = _AUTO_MARKER + 'window.AGENT_DATA = ' + json.dumps(data, ensure_ascii=False, indent=2) + ';\n'
    with open(target, 'w', encoding='utf-8') as f:
        f.write(js)
    return {
        'written': os.path.basename(target),
        'kind':    'primary' if target == primary else 'auto-alongside-manual',
    }


def _run_claude(prompt: str, timeout: int = 600, quick: bool = False) -> dict:
    """Invoke `claude -p` via tempfile redirect. Returns {ok, output, error, elapsed}.

    Why tempfile + shell redirect: subprocess.run with input= doesn't reliably
    pipe stdin to .cmd shims on Windows. Writing prompt to a UTF-8 file and
    using shell redirection works deterministically across .cmd/.exe.
    """
    start = time.time()
    claude_bin = shutil.which('claude') or 'claude'

    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8',
                                     delete=False, newline='\n')
    try:
        tmp.write(prompt)
        tmp.close()
        # shell=True + redirect handles stdin properly for .cmd shims on Windows.
        # --allowedTools: one-click invocation cannot answer interactive permission
        # prompts. Allow only read-only research tools the agents actually need.
        allowed = 'WebSearch WebFetch Read Glob Grep'
        cmd_str = f'"{claude_bin}" -p --allowedTools {allowed} < "{tmp.name}"'
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=timeout,
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            return {'ok': True, 'output': result.stdout, 'error': '', 'elapsed': elapsed}
        return {'ok': False,
                'output': result.stdout,
                'error': (result.stderr or '').strip() or f'exit {result.returncode}',
                'elapsed': elapsed}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'output': '', 'error': f'timeout after {timeout}s',
                'elapsed': time.time() - start}
    except FileNotFoundError:
        return {'ok': False, 'output': '', 'error': 'claude CLI not found in PATH', 'elapsed': 0}
    except Exception as e:
        return {'ok': False, 'output': '', 'error': str(e), 'elapsed': time.time() - start}
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


_GROQ_MODEL = 'llama-3.3-70b-versatile'


def _run_groq(system: str, user: str, timeout: int = 600, max_tokens: int = 7000) -> dict:
    """Groq API (llama-3.3-70b-versatile) — free tier, same return shape as _run_claude."""
    start   = time.time()
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        return {'ok': False, 'output': '', 'error': 'GROQ_API_KEY not set', 'elapsed': 0}
    try:
        resp = _requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model':       _GROQ_MODEL,
                'messages':    [
                    {'role': 'system', 'content': system},
                    {'role': 'user',   'content': user},
                ],
                'max_tokens':  max_tokens,
                'temperature': 0.3,
            },
            timeout=(15, min(timeout, 120)),
        )
        resp.raise_for_status()
        elapsed = time.time() - start
        content = resp.json()['choices'][0]['message']['content'].strip()
        return {'ok': True, 'output': content, 'error': '', 'elapsed': elapsed}
    except Exception as e:
        return {'ok': False, 'output': '', 'error': str(e), 'elapsed': time.time() - start}


def _run_llm(system: str, user: str, timeout: int = 600) -> dict:
    """Dispatcher: Groq אם GROQ_API_KEY מוגדר ומצליח, אחרת Claude CLI."""
    if os.environ.get('GROQ_API_KEY', '').strip():
        result = _run_groq(system, user, timeout=timeout)
        if result['ok']:
            return result
        print(f'[GROQ→CLAUDE FALLBACK] {result.get("error", "empty")}')
    return _run_claude(f'{system}\n\n{user}', timeout=timeout)


def _run_agent_thread(run_id: str, ticker: str, agent: str, chain: bool = False):
    """Background thread: build context → call claude → save → update run state."""
    def update(**kwargs):
        with _runs_lock:
            _runs[run_id].update(kwargs)

    try:
        if chain:
            update(status='running', current_agent='analyst', progress=0, completed_agents=[])
            for i, ag in enumerate(AGENT_ORDER):
                update(current_agent=ag, progress=int(i / len(AGENT_ORDER) * 100))
                ctx = _build_context(ticker, ag)
                # analyst עושה תחקיר רב-מקורות עמוק; D-Lite מוסיף עומס ~5 דק'.
                # AMZN ראינו ~21 דק' עם visual-scores → 1500s budget בטוח.
                # שאר הסוכנים מסתפקים בברירת המחדל 600s.
                timeout = 1500 if ag == 'analyst' else 600
                res = _run_llm(ctx['system'], ctx['context'], timeout=timeout)
                # ניסיון נוסף אחד אם נכשל או פלט ריק
                if not res['ok'] or not res['output'].strip():
                    print(f'[RETRY] {ticker}/{ag} — {res.get("error", "empty output")}')
                    res = _run_llm(ctx['system'], ctx['context'], timeout=timeout)
                if not res['ok'] or not res['output'].strip():
                    update(status='failed', error=f'{ag}: {res.get("error") or "empty output"}',
                           finished=datetime.now().isoformat())
                    return
                saved = _save_handoff(ticker, ag, res['output'])
                with _runs_lock:
                    completed = list(_runs[run_id].get('completed_agents', []))
                    completed.append(ag)
                    _runs[run_id].setdefault('steps', []).append({
                        'agent': ag, 'ok': True, 'elapsed': round(res['elapsed'], 1),
                        'tokens_est': ctx['token_estimate'], 'saved': saved,
                    })
                    _runs[run_id]['completed_agents'] = completed
            update(status='done', progress=100, finished=datetime.now().isoformat())
            # ── Phase 1 hook: archive consolidated full-chain to vault ─────
            try:
                import obsidian_layer, json as _json
                hd_dir = os.path.join(ANALYSES_DIR, ticker, '_handoffs')
                rv_dir = os.path.join(ANALYSES_DIR, ticker, '_reviews')
                today  = datetime.now().strftime('%Y-%m-%d')
                handoffs_map  = {}
                dash_by_agent = {}
                for a in AGENT_ORDER:
                    hp = os.path.join(hd_dir, f'{today}_{a}.md')
                    if os.path.exists(hp):
                        try:
                            with open(hp, encoding='utf-8') as f:
                                handoffs_map[a] = f.read()
                        except Exception: pass
                    rp = os.path.join(rv_dir, f'{a}.json')
                    if os.path.exists(rp):
                        try:
                            with open(rp, encoding='utf-8') as f:
                                dash_by_agent[a] = _json.load(f)
                        except Exception: pass
                obsidian_layer.on_chain_complete(ticker, today, handoffs_map, dash_by_agent)
            except Exception as e:
                print(f'[obsidian chain-complete skipped] {e}')
        else:
            update(status='running', current_agent=agent)
            ctx = _build_context(ticker, agent)
            # Quick mode: shorter timeout, returns faster
            is_quick = (agent == 'quick')
            timeout = 180 if is_quick else 600
            res = _run_llm(ctx['system'], ctx['context'], timeout=timeout)
            # ניסיון נוסף אחד אם נכשל או פלט ריק
            if not res['ok'] or not res['output'].strip():
                print(f'[RETRY] {ticker}/{agent} — {res.get("error", "empty output")}')
                res = _run_llm(ctx['system'], ctx['context'], timeout=timeout)
            if not res['ok'] or not res['output'].strip():
                update(status='failed', error=res.get('error') or 'empty output',
                       finished=datetime.now().isoformat())
                return
            saved = _save_handoff(ticker, agent, res['output'])
            update(status='done', elapsed=round(res['elapsed'], 1),
                   tokens_est=ctx['token_estimate'], saved=saved,
                   output_preview=res['output'][:500] if is_quick else None,
                   finished=datetime.now().isoformat())
    except Exception as e:
        update(status='failed', error=str(e), finished=datetime.now().isoformat())


# ── API: run / status ─────────────────────────────────────────────────────────

@app.route('/api/run', methods=['POST'])
def api_run():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    ticker = (data.get('ticker') or '').upper().strip()
    agent  = (data.get('agent')  or '').lower().strip()
    if not ticker:
        return jsonify({'error': 'ticker required'}), 400

    chain = (agent == 'chain')
    is_quick = (agent == 'quick')
    if not chain and not is_quick and agent not in PROMPT_FILES:
        return jsonify({'error': f'unknown agent: {agent}'}), 400

    # ── שער טריות: מניעת ריצה כפולה תוך 14 יום ────────────────────────────
    # quick תמיד מותר. chain בודק IC (השלב האחרון). force=true עוקף את השער.
    if not is_quick and not bool(data.get('force')):
        rv_dir   = os.path.join(ANALYSES_DIR, ticker, '_reviews')
        check_ag = AGENT_ORDER if chain else [agent]
        stale    = []
        for ag in check_ag:
            rp = os.path.join(rv_dir, f'{ag}.json')
            if not os.path.exists(rp) or (time.time() - os.path.getmtime(rp)) / 86400 >= 14:
                stale.append(ag)
        if not stale:
            youngest = min(
                (time.time() - os.path.getmtime(os.path.join(rv_dir, f'{ag}.json'))) / 86400
                for ag in check_ag
            )
            return jsonify({
                'status':     'skipped',
                'reason':     'freshness_gate',
                'ticker':     ticker,
                'agent':      agent,
                'days_since': round(youngest, 1),
                'message':    f'ניתוח {ticker} עדכני ({round(youngest, 1)} ימים). שלח force=true לעקיפה.',
            }), 200

    run_id = f'{ticker}_{agent}_{int(time.time())}'
    with _runs_lock:
        _runs[run_id] = {
            'run_id':  run_id,
            'ticker':  ticker,
            'agent':   agent,
            'chain':   chain,
            'status':  'queued',
            'started': datetime.now().isoformat(),
        }
    threading.Thread(target=_run_agent_thread, args=(run_id, ticker, agent, chain), daemon=True).start()
    return jsonify({'run_id': run_id})


@app.route('/api/run-status/<run_id>')
def api_run_status(run_id):
    with _runs_lock:
        return jsonify(_runs.get(run_id, {'status': 'unknown', 'run_id': run_id}))


@app.route('/api/handoffs/<ticker>')
def api_handoffs(ticker):
    """List handoff files for a ticker."""
    hd_dir = os.path.join(ANALYSES_DIR, ticker.upper(), '_handoffs')
    if not os.path.isdir(hd_dir):
        return jsonify([])
    items = []
    for fname in sorted(os.listdir(hd_dir), reverse=True):
        if fname.endswith('.md'):
            items.append({
                'filename': fname,
                'url':      f'/handoffs/{ticker.upper()}/{fname}',
                'size':     os.path.getsize(os.path.join(hd_dir, fname)),
            })
    return jsonify(items)


@app.route('/api/ticker-history/<ticker>')
def api_ticker_history(ticker):
    """Per-ticker run history: full chains (5 agents same date), quick checks,
    last review per agent, days_since. Drives Phase-B freshness UI.

    Returns: {
      ticker, full_runs:[{date, agents:[...], complete:bool}],
      quick_runs:[{date}], last_review:{agent:{date,mtime,days}}
    }
    """
    from datetime import datetime as _dt
    tk     = ticker.upper()
    hd_dir = os.path.join(ANALYSES_DIR, tk, '_handoffs')
    rv_dir = os.path.join(ANALYSES_DIR, tk, '_reviews')

    by_date = {}  # date_str → set(agents)
    quick   = []
    if os.path.isdir(hd_dir):
        for f in os.listdir(hd_dir):
            if not f.endswith('.md'):
                continue
            # filename: YYYY-MM-DD_<agent>.md
            m = re.match(r'^(\d{4}-\d{2}-\d{2})_([a-z]+)\.md$', f)
            if not m:
                continue
            d, ag = m.group(1), m.group(2)
            if ag == 'quick':
                quick.append({'date': d})
            else:
                by_date.setdefault(d, set()).add(ag)

    full_runs = []
    for d in sorted(by_date.keys(), reverse=True):
        agents = sorted(by_date[d])
        full_runs.append({
            'date':     d,
            'agents':   agents,
            'complete': len(agents) >= 5,  # analyst+devils+ceo+executor+ic
        })

    last_review = {}
    if os.path.isdir(rv_dir):
        for f in os.listdir(rv_dir):
            if not f.endswith('.json'):
                continue
            ag    = f[:-5]
            path  = os.path.join(rv_dir, f)
            mtime = os.path.getmtime(path)
            days  = int((time.time() - mtime) / 86400)
            last_review[ag] = {
                'date':       _dt.fromtimestamp(mtime).strftime('%Y-%m-%d'),
                'mtime':      mtime,
                'days_since': days,
                'freshness':  'fresh' if days < 14 else 'aging' if days < 45 else 'stale',
            }

    return jsonify({
        'ticker':      tk,
        'full_runs':   full_runs,
        'quick_runs':  sorted(quick, key=lambda x: x['date'], reverse=True),
        'last_review': last_review,
    })


@app.route('/handoffs/<ticker>/<path:filename>')
def serve_handoff(ticker, filename):
    return send_from_directory(
        os.path.join(ANALYSES_DIR, ticker.upper(), '_handoffs'),
        filename,
        mimetype='text/plain; charset=utf-8',
    )


# ── API: latest reviews (compact dashboard cards) ─────────────────────────────

@app.route('/api/latest-reviews')
def api_latest_reviews():
    return jsonify(_list_latest_reviews())


@app.route('/api/latest-reviews/<ticker>')
def api_latest_reviews_ticker(ticker):
    """All reviews for a single ticker (newest first)."""
    rdir = os.path.join(ANALYSES_DIR, ticker.upper(), '_reviews')
    out = []
    if os.path.isdir(rdir):
        for fname in os.listdir(rdir):
            if not fname.endswith('.json'):
                continue
            try:
                with open(os.path.join(rdir, fname), encoding='utf-8') as f:
                    d = json.load(f)
                d['mtime'] = os.path.getmtime(os.path.join(rdir, fname))
                out.append(d)
            except Exception:
                continue
    out.sort(key=lambda r: r.get('mtime', 0), reverse=True)
    return jsonify(out)


# ── API: Obsidian memory (read-only, free, no LLM tokens) ─────────────────────

@app.route('/api/memory')
def api_memory_list():
    """רשימת הטיקרים שיש להם פתק זיכרון בכספת. קריאה בלבד, fail-soft."""
    vault = _obsidian_vault_dir()
    if not vault:
        return jsonify([])
    folder = _load_config().get('obsidian_ticker_folder', 'Tickers')
    tdir = os.path.join(vault, folder)
    out = []
    if os.path.isdir(tdir):
        for fname in os.listdir(tdir):
            if fname.endswith('.md'):
                path = os.path.join(tdir, fname)
                out.append({
                    'ticker': fname[:-3],
                    'mtime': os.path.getmtime(path),
                })
    out.sort(key=lambda r: r.get('mtime', 0), reverse=True)
    return jsonify(out)


@app.route('/api/memory/search')
def api_memory_search():
    """חיפוש טקסט חופשי בכל פתקי הזיכרון בכספת. קריאה בלבד, fail-soft."""
    q = (request.args.get('q') or '').strip()
    if len(q) < 2:
        return jsonify({'query': q, 'results': []})
    vault = _obsidian_vault_dir()
    if not vault:
        return jsonify({'query': q, 'results': []})
    folder = _load_config().get('obsidian_ticker_folder', 'Tickers')
    tdir = os.path.join(vault, folder)
    ql = q.lower()
    results = []
    if os.path.isdir(tdir):
        for fname in sorted(os.listdir(tdir)):
            if not fname.endswith('.md'):
                continue
            try:
                with open(os.path.join(tdir, fname), encoding='utf-8') as f:
                    lines = f.read().splitlines()
            except Exception:
                continue
            snippets, count = [], 0
            for ln in lines:
                if ql in ln.lower():
                    count += 1
                    s = ln.strip()
                    if len(snippets) < 4 and s:
                        snippets.append(s[:240])
            if count:
                results.append({'ticker': fname[:-3], 'count': count, 'snippets': snippets})
    results.sort(key=lambda r: r['count'], reverse=True)
    return jsonify({'query': q, 'results': results})


@app.route('/api/memory/<ticker>')
def api_memory_ticker(ticker):
    """מחזיר את ה-markdown הגולמי של פתק הזיכרון לטיקר. קריאה בלבד."""
    path = _obsidian_ticker_path(ticker.upper())
    if not path or not os.path.exists(path):
        return jsonify({'ticker': ticker.upper(), 'exists': False, 'markdown': ''})
    try:
        with open(path, encoding='utf-8') as f:
            md = f.read()
        return jsonify({'ticker': ticker.upper(), 'exists': True, 'markdown': md})
    except Exception as e:
        return jsonify({'ticker': ticker.upper(), 'exists': False, 'error': str(e), 'markdown': ''})


# ── API: Decision Journal ─────────────────────────────────────────────────────

@app.route('/api/decisions', methods=['GET'])
def api_get_decisions():
    return jsonify(_load_decisions().get('decisions', []))


@app.route('/api/decisions/<ticker>', methods=['GET'])
def api_get_decisions_for_ticker(ticker):
    all_d = _load_decisions().get('decisions', [])
    matches = [d for d in all_d if d.get('ticker') == ticker.upper()]
    return jsonify(matches)


@app.route('/api/decisions', methods=['POST'])
def api_add_decision():
    data = request.get_json() or {}
    ticker = (data.get('ticker') or '').upper().strip()
    if not ticker:
        return jsonify({'error': 'ticker required'}), 400

    journal = _load_decisions()
    decisions = journal.setdefault('decisions', [])
    entry = {
        'id':                _next_decision_id(decisions),
        'ticker':            ticker,
        'date':              data.get('date') or datetime.now().strftime('%Y-%m-%d'),
        'decision':          data.get('decision'),
        'position_size_pct': data.get('position_size_pct'),
        'why':               data.get('why', ''),
        'biggest_risk':      data.get('biggest_risk', ''),
        'kill_switch':       data.get('kill_switch', ''),
        'conviction':        data.get('conviction'),
        'original_thesis':   data.get('original_thesis', ''),
    }
    decisions.append(entry)
    _save_decisions(journal)
    return jsonify({'ok': True, 'id': entry['id']})


@app.route('/api/decisions/<id>', methods=['DELETE'])
def api_delete_decision(id):
    journal = _load_decisions()
    journal['decisions'] = [d for d in journal.get('decisions', []) if d.get('id') != id]
    _save_decisions(journal)
    return jsonify({'ok': True})


# ── דוחות כספיים (SEC EDGAR XBRL) ──────────────────────────────────────────

# Cache פנימי: ticker→CIK (רשימה גלובלית) + companyfacts per-ticker (TTL 1h)
_SEC_CIK_CACHE = {}           # ticker.upper() → cik_padded (str, 10 digits)
_SEC_FACTS_CACHE = {}         # ticker.upper() → {'ts': float, 'facts': dict}
_SEC_FACTS_TTL   = 3600       # שעה

_EDGAR_HEADERS = {
    'User-Agent':  'Portfolio Investment App rotemstain23@gmail.com',
    'Accept':      'application/json',
    'Accept-Encoding': 'gzip',
}

# ---- מיפוי שמות-תצוגה → תגיות XBRL (סדר עדיפות) ----
_INC_METRICS = [
    ('Total Revenue',    ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet']),
    ('Cost of Revenue',  ['CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostOfGoodsSold']),
    ('Gross Profit',     ['GrossProfit']),
    ('R&D Expense',      ['ResearchAndDevelopmentExpense']),
    ('SG&A Expense',     ['SellingGeneralAndAdministrativeExpense', 'GeneralAndAdministrativeExpense']),
    ('Operating Income', ['OperatingIncomeLoss']),
    ('Interest Expense', ['InterestExpense', 'InterestExpenseDebt', 'InterestAndDebtExpense']),
    ('Pretax Income',    ['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
                          'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments']),
    ('Income Tax',       ['IncomeTaxExpenseBenefit']),
    ('Net Income',       ['NetIncomeLoss', 'ProfitLoss']),
]

_BAL_METRICS = [
    ('Cash & Equivalents',    ['CashAndCashEquivalentsAtCarryingValue', 'Cash']),
    ('Short-term Investments',['ShortTermInvestments', 'MarketableSecuritiesCurrent']),
    ('Accounts Receivable',   ['AccountsReceivableNetCurrent', 'ReceivablesNetCurrent']),
    ('Inventory',             ['InventoryNet', 'InventoryFinishedGoodsNetOfReserves']),
    ('Total Current Assets',  ['AssetsCurrent']),
    ('PP&E Net',              ['PropertyPlantAndEquipmentNet']),
    ('Goodwill',              ['Goodwill']),
    ('Total Assets',          ['Assets']),
    ('Accounts Payable',      ['AccountsPayableCurrent']),
    ('Total Current Liab.',   ['LiabilitiesCurrent']),
    ('Long-term Debt',        ['LongTermDebtNoncurrent', 'LongTermDebt']),
    ('Total Liabilities',     ['Liabilities']),
    ("Stockholders' Equity",  ['StockholdersEquity', 'StockholdersEquityAttributableToParent']),
]

_CF_METRICS = [
    ('Operating Cash Flow',  ['NetCashProvidedByUsedInOperatingActivities']),
    ('CapEx',                ['PaymentsToAcquireProductiveAssets', 'PaymentsToAcquirePropertyPlantAndEquipment',
                              'PaymentsForCapitalImprovements', 'SegmentExpenditureAdditionToLongLivedAssets']),
    ('Investing Activities', ['NetCashProvidedByUsedInInvestingActivities']),
    ('Debt Repayment',       ['RepaymentsOfLongTermDebt', 'RepaymentsOfDebt']),
    ('Stock Buybacks',       ['PaymentsForRepurchaseOfCommonStock']),
    ('Financing Activities', ['NetCashProvidedByUsedInFinancingActivities']),
]


def _edgar_cik(ticker: str) -> str | None:
    """ticker → CIK padded to 10 digits. מאחסן ב-cache."""
    t = ticker.upper()
    if t in _SEC_CIK_CACHE:
        return _SEC_CIK_CACHE[t]
    try:
        r = _requests.get('https://www.sec.gov/files/company_tickers.json',
                          headers=_EDGAR_HEADERS, timeout=10)
        if not r.ok:
            return None
        for entry in r.json().values():
            _SEC_CIK_CACHE[entry.get('ticker', '').upper()] = str(entry['cik_str']).zfill(10)
        return _SEC_CIK_CACHE.get(t)
    except Exception:
        return None


def _edgar_facts(ticker: str) -> dict | None:
    """companyfacts JSON (us-gaap section). Cache TTL 1h."""
    t = ticker.upper()
    cached = _SEC_FACTS_CACHE.get(t)
    if cached and (time.time() - cached['ts']) < _SEC_FACTS_TTL:
        return cached['facts']
    cik = _edgar_cik(t)
    if not cik:
        return None
    try:
        r = _requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
                          headers=_EDGAR_HEADERS, timeout=30)
        if not r.ok:
            return None
        facts = r.json().get('facts', {}).get('us-gaap', {})
        _SEC_FACTS_CACHE[t] = {'ts': time.time(), 'facts': facts}
        return facts
    except Exception:
        return None


def _edgar_metric(facts: dict, tags: list, period: str, max_periods: int = 4) -> list:
    """חלץ מטריקה מ-EDGAR facts → [{label, val}] מהעדכני ביותר."""
    for tag in tags:
        if tag not in facts:
            continue
        usd = facts[tag].get('units', {}).get('USD', [])
        if period == 'quarterly':
            entries = [e for e in usd if e.get('form') == '10-Q']
        else:
            entries = [e for e in usd if e.get('form') == '10-K' and e.get('fp') == 'FY']
        if not entries:
            continue
        # deduplicate per end date (קח את ה-filing הכי עדכני לכל תאריך)
        entries.sort(key=lambda e: (e.get('end', ''), e.get('filed', '')), reverse=True)
        seen, result = set(), []
        for e in entries:
            end = e.get('end')
            if end not in seen:
                seen.add(end)
                result.append({'label': end, 'val': e['val']})
        return result[:max_periods]
    return []


def _edgar_build_periods(facts: dict, metrics: list, period: str) -> list:
    """בנה מבנה תקופות עם variances לכל מטריקה."""
    # קבע labels מהמטריקה הראשונה שיש לה נתונים
    labels = []
    raw_by_metric = {}
    for name, tags in metrics:
        rows = _edgar_metric(facts, tags, period)
        if rows and not labels:
            labels = [r['label'] for r in rows]
        raw_by_metric[name] = {r['label']: r['val'] for r in rows}

    if not labels:
        return []

    periods = []
    for i, lbl in enumerate(labels):
        data = {name: raw_by_metric[name].get(lbl) for name, _ in metrics}
        periods.append({'label': lbl, 'data': data, 'variances': {}})

    # חשב variances: כל תקופה vs. הקודמת לה
    for i in range(len(periods) - 1):
        curr_d, prev_d = periods[i]['data'], periods[i + 1]['data']
        var = {}
        for k in curr_d:
            c, p = curr_d.get(k), prev_d.get(k)
            if c is not None and p is not None and p != 0:
                var[k] = round((c - p) / abs(p) * 100, 1)
            else:
                var[k] = None
        periods[i]['variances'] = var
    return periods


def _edgar_analyst_ctx(ticker: str) -> dict:
    """הקשר מ-analyst.js (קריאת דיסק, ללא LLM)."""
    path = os.path.join(ANALYSES_DIR, ticker.upper(), 'analyst.js')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        m = re.search(r'window\.AGENT_DATA\s*=\s*(\{.*\})\s*;?\s*$', raw, re.DOTALL)
        if not m:
            return {}
        ad = json.loads(m.group(1))
        return {
            'company':       ad.get('company'),
            'sector':        ad.get('sector'),
            'financials_3y': ad.get('financials_3y'),
            'quarterly':     ad.get('quarterly'),
            'growth':        ad.get('growth'),
        }
    except Exception:
        return {}


@app.route('/api/financial-statements/<ticker>')
def api_financial_statements(ticker):
    """Income Statement, Balance Sheet, Cash Flow + variances.

    מקור: SEC EDGAR XBRL (חינמי, ללא API key) + analyst.js לקונטקסט.
    period: annual (ברירת-מחדל) | quarterly
    """
    ticker = ticker.upper().strip()
    period = request.args.get('period', 'annual')

    facts = _edgar_facts(ticker)
    if facts is None:
        return jsonify({'error': f'לא נמצאו נתוני EDGAR עבור {ticker}', 'ticker': ticker}), 404

    return jsonify({
        'ticker':           ticker,
        'period':           period,
        'income_statement': _edgar_build_periods(facts, _INC_METRICS, period),
        'balance_sheet':    _edgar_build_periods(facts, _BAL_METRICS, period),
        'cash_flow':        _edgar_build_periods(facts, _CF_METRICS,  period),
        'analyst_context':  _edgar_analyst_ctx(ticker),
    })


# ── Entry point ───────────────────────────────────────────────────────────────

def _open_browser():
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print()
    print('  ============================================')
    print('   Investment OS  --  Python/Flask Engine')
    print('  ============================================')
    print('  Dashboard : http://127.0.0.1:5000')
    print('  API       : /api/portfolio')
    print('  ============================================')
    print()
    threading.Thread(target=_open_browser, daemon=True).start()
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    app.run(host=host, port=5000, debug=False)
