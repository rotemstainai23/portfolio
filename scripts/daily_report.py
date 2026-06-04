"""
דוח יומי — שני עד שישי, 5:00.
קורא נתונים קיימים + מחירים מ-Yahoo Finance.
שולח לטלגרם ווואצאפ. ללא קריאות Claude API.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime

# ── נתיבים ──────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PORTFOLIO_JSON  = os.path.join(ROOT, 'portfolio.json')
ANALYSES_DIR    = os.path.join(ROOT, 'analyses')

from notifications import send_both


# ── טעינת נתוני תיק ─────────────────────────────────────────────────────────
def load_portfolio() -> dict:
    with open(PORTFOLIO_JSON, encoding='utf-8') as f:
        return json.load(f)


def load_reviews(ticker: str) -> dict:
    """טוען את כל ה-reviews הקיימים לטיקר."""
    rev_dir = os.path.join(ANALYSES_DIR, ticker, '_reviews')
    out = {}
    if not os.path.isdir(rev_dir):
        return out
    for fname in os.listdir(rev_dir):
        if fname.endswith('.json') and fname != 'quick.json':
            agent = fname.replace('.json', '')
            try:
                with open(os.path.join(rev_dir, fname), encoding='utf-8') as f:
                    out[agent] = json.load(f)
            except Exception:
                pass
    return out


# ── מחירים מ-Yahoo Finance ───────────────────────────────────────────────────
def get_prices(tickers: list[str]) -> dict:
    """שולף מחירים נוכחיים + שינוי יומי מ-Yahoo Finance."""
    results = {}
    for ticker in tickers:
        try:
            url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
                   f'?interval=1d&range=2d')
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.load(r)
            meta = data['chart']['result'][0]['meta']
            current = meta.get('regularMarketPrice', 0)
            prev    = meta.get('chartPreviousClose', meta.get('previousClose', current))
            chg_pct = ((current - prev) / prev * 100) if prev else 0
            results[ticker] = {
                'price':   round(current, 2),
                'chg_pct': round(chg_pct, 2),
            }
        except Exception:
            results[ticker] = {'price': None, 'chg_pct': None}
    return results


# ── עיצוב הודעה ──────────────────────────────────────────────────────────────
def build_message(portfolio: dict, prices: dict) -> tuple[str, str]:
    """מחזיר (full_telegram, short_whatsapp)."""
    today    = datetime.now().strftime('%d/%m/%Y')
    holdings = portfolio.get('holdings', [])

    lines_tg = [f'*דוח בוקר — {today}*\n']
    lines_wa = [f'דוח בוקר {today}\n']

    any_alert = False
    for h in holdings:
        ticker = h.get('symbol') or h.get('ticker', '')
        if not ticker:
            continue
        p = prices.get(ticker, {})
        price    = p.get('price')
        chg_pct  = p.get('chg_pct')
        reviews  = load_reviews(ticker)
        ic_rv    = reviews.get('ic') or reviews.get('analyst') or {}
        verdict  = ic_rv.get('verdict', '?')
        score    = ic_rv.get('score', '?')

        price_str = f'${price:.2f}' if price else '?'
        chg_str   = (f'{chg_pct:+.2f}%' if chg_pct is not None else '?')
        arrow     = ('↑' if (chg_pct or 0) > 0 else '↓' if (chg_pct or 0) < 0 else '→')

        # kill switch בדיקה
        kill_hit = False
        for agent_rv in reviews.values():
            if isinstance(agent_rv, dict) and agent_rv.get('verdict') in ('SELL', 'EXIT', 'REVIEW'):
                kill_hit = True
                break

        line_tg = f'{arrow} *{ticker}* {price_str} ({chg_str}) — {verdict} {score}/100'
        line_wa = f'{arrow} {ticker} {price_str} ({chg_str}) {verdict}'

        if kill_hit:
            line_tg += ' *⚠ REVIEW*'
            line_wa += ' !! REVIEW'
            any_alert = True

        thesis = ic_rv.get('thesis', '')
        if thesis:
            line_tg += f'\n  _{thesis[:100]}_'

        lines_tg.append(line_tg)
        lines_wa.append(line_wa)

    # watchlist
    watchlist = portfolio.get('watchlist', [])
    wl_hits = []
    for w in watchlist:
        ticker  = w.get('symbol') or w.get('ticker', '')
        trigger = w.get('trigger_price') or w.get('entry_trigger')
        if not ticker or not trigger:
            continue
        p = prices.get(ticker, {})
        price = p.get('price')
        if price and abs(price - float(trigger)) / float(trigger) < 0.03:
            wl_hits.append(f'{ticker} קרוב לטריגר ${trigger} (נוכחי ${price:.2f})')

    if wl_hits:
        lines_tg.append('\n*ווצ\'ליסט — קרוב לטריגר:*')
        lines_wa.append('\nWATCHLIST:')
        for hit in wl_hits:
            lines_tg.append(f'  · {hit}')
            lines_wa.append(f'  {hit}')

    if any_alert:
        lines_tg.insert(1, '*ALERT: אחזקות לבדיקה — ראה פירוט*\n')

    full_tg = '\n'.join(lines_tg)
    short_wa = '\n'.join(lines_wa)
    return full_tg, short_wa


# ── ריצה ─────────────────────────────────────────────────────────────────────
def main():
    print('[daily_report] מתחיל...')
    portfolio = load_portfolio()
    all_tickers = [
        (h.get('symbol') or h.get('ticker', ''))
        for h in portfolio.get('holdings', []) + portfolio.get('watchlist', [])
        if h.get('symbol') or h.get('ticker')
    ]
    print(f'[daily_report] שולף מחירים ל-{len(all_tickers)} טיקרים...')
    prices = get_prices(all_tickers)

    full_tg, short_wa = build_message(portfolio, prices)
    result = send_both(short_text=short_wa, full_text=full_tg)
    print(f'[daily_report] נשלח: {result}')


if __name__ == '__main__':
    main()
