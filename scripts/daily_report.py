"""
דוח בוקר יומי — שני עד שישי, 5:00.
נפח חריג + RSI + יעד אנליסטים + רווחים קרובים + חדשות + Groq insights.
ללא קריאות Claude API. מקורות: Yahoo Finance RSS/v8/v10 + Groq (חינם).
"""
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from notifications import send_notification

PORTFOLIO_JSON = os.path.join(ROOT, 'portfolio.json')
ANALYSES_DIR   = os.path.join(ROOT, 'analyses')
GROQ_URL       = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL     = 'llama-3.3-70b-versatile'

COMPETITORS = {
    'NVDA': ['AMD', 'INTC'],
    'MSFT': ['GOOGL', 'AAPL'],
    'GOOG': ['META', 'MSFT'],
    'META': ['SNAP', 'PINS'],
    'AVGO': ['QCOM', 'MRVL'],
    'MU':   ['WDC', 'LRCX'],
    'VST':  ['CEG', 'NEE'],
    'APLD': ['CORZ', 'IREN'],
    'OKLO': ['CEG', 'SMR'],
}


# ── שליפת נתונים ─────────────────────────────────────────────────────────────

def _fetch(url: str, timeout: int = 12) -> str:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception:
        return ''


def get_enriched_quote(ticker: str) -> dict:
    """מחיר + שינוי יומי + נפח_ratio + RSI מ-Yahoo Finance v8 (חודש אחרון)."""
    url  = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1mo'
    html = _fetch(url)
    if not html:
        return {}
    try:
        data   = json.loads(html)
        result = data['chart']['result'][0]
        meta   = result.get('meta', {})
        quote  = result.get('indicators', {}).get('quote', [{}])[0]

        closes  = [c for c in quote.get('close', [])  if c is not None]
        volumes = [v for v in quote.get('volume', []) if v is not None]

        if len(closes) < 2:
            return {}

        price    = closes[-1]
        prev     = closes[-2]
        chg_pct  = round((price / prev - 1) * 100, 2) if prev else 0

        # נפח יום vs ממוצע 30 יום קודמים
        vol_today = volumes[-1] if volumes else None
        vol_hist  = [v for v in volumes[:-1] if v]
        avg_vol   = sum(vol_hist) / len(vol_hist) if vol_hist else None
        vol_ratio = round(vol_today / avg_vol, 1) if (vol_today and avg_vol) else None

        # RSI 14 יום
        rsi = None
        if len(closes) >= 15:
            diffs  = [closes[i] - closes[i-1] for i in range(len(closes)-14, len(closes))]
            gains  = [max(d, 0) for d in diffs]
            losses = [max(-d, 0) for d in diffs]
            ag = sum(gains) / 14
            al = sum(losses) / 14
            rsi = round(100 - 100 / (1 + ag / al), 0) if al else 100

        return {
            'price':     round(price, 2),
            'chg_pct':   chg_pct,
            'vol_ratio': vol_ratio,
            'rsi':       rsi,
            'currency':  meta.get('currency', 'USD'),
        }
    except Exception as e:
        print(f'[daily] quote שגיאה {ticker}: {e}')
        return {}


def get_target_and_52w(ticker: str) -> dict:
    """יעד אנליסטים + 52w range + תאריך רווחים קרוב מ-Yahoo Finance v10."""
    url  = (f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}'
            f'?modules=summaryDetail,financialData,calendarEvents')
    html = _fetch(url)
    if not html:
        return {}
    try:
        data    = json.loads(html)
        summary = data.get('quoteSummary', {}).get('result', [{}])[0]

        def val(d, k):
            v = d.get(k, {})
            if isinstance(v, dict):
                return v.get('raw') if v.get('raw') is not None else v.get('fmt')
            return v if v is not None else None

        detail  = summary.get('summaryDetail', {})
        fin     = summary.get('financialData', {})
        cal     = summary.get('calendarEvents', {})

        target     = val(fin, 'targetMeanPrice')
        w52_high   = val(detail, 'fiftyTwoWeekHigh')
        w52_low    = val(detail, 'fiftyTwoWeekLow')

        # אחוז מיקום ב-52 שבועות
        w52_pct = None
        if w52_high and w52_low and w52_high > w52_low:
            # לא שולפים price פה — ישתמשו מ-get_enriched_quote
            w52_pct = (w52_high, w52_low)

        # רווחים קרובים
        next_earnings = None
        earnings_list = cal.get('earnings', {}).get('earningsDate', [])
        if earnings_list:
            item = earnings_list[0]
            ts   = item.get('raw') if isinstance(item, dict) else item
            if ts:
                try:
                    dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                    days_away = (dt.date() - datetime.now(tz=timezone.utc).date()).days
                    if 0 <= days_away <= 21:
                        next_earnings = days_away
                except Exception:
                    pass

        return {
            'target':       round(target, 2) if target else None,
            'w52_range':    w52_pct,
            'next_earnings': next_earnings,
        }
    except Exception as e:
        print(f'[daily] v10 שגיאה {ticker}: {e}')
        return {}


def get_news_headlines(ticker: str, max_items: int = 3) -> list:
    """כותרות חדשות מ-Yahoo Finance RSS."""
    url  = f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US'
    html = _fetch(url, timeout=8)
    if not html:
        return []
    try:
        root = ET.fromstring(html)
        return [
            item.findtext('title', '').strip()
            for item in root.findall('.//item')[:max_items]
            if item.findtext('title', '').strip()
        ]
    except Exception:
        return []


def load_reviews(ticker: str) -> dict:
    """טוען reviews קיימים לטיקר מ-analyses/<ticker>/_reviews/."""
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


# ── Groq insights ─────────────────────────────────────────────────────────────

def run_groq_insights(holdings_data: list) -> list:
    """שלח את כל נתוני האחזקות ל-Groq, קבל 3-4 תובנות יומיות."""
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        return []

    context = json.dumps(holdings_data, ensure_ascii=False, separators=(',', ':'))

    system = """אתה אנליסט תיק השקעות. קיבלת נתוני בוקר על תיק מניות בפורמט JSON.

ענה ב-JSON בלבד — מערך של 3 עד 4 strings בעברית.
כל string: משפט אחד שמסביר מה קורה, לא רק מחזיר את המספרים.

כללים:
- אם יש חדשות — ציין את הקטליסט הספציפי שגרם לתנועה
- תנועה גדולה ללא חדשות — נסח השערה מבוססת סקטור/macro, סמן ב-"ייתכן"
- vol_ratio>2 עם ירידה = לחץ מכירה חריג — חשוב לציין
- RSI<25 = oversold קיצוני, RSI>75 = overbought — פרש את המשמעות
- earnings_days קיים — תמיד אזהרה
- אל תחזור על המספרים, תפרש אותם
- אסור מירכאות כפולות בתוך strings

פורמט: ["תובנה 1", "תובנה 2", "תובנה 3"]"""

    try:
        import requests as _req
        resp = _req.post(
            GROQ_URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type':  'application/json',
            },
            json={
                'model':       GROQ_MODEL,
                'messages':    [
                    {'role': 'system', 'content': system},
                    {'role': 'user',   'content': context},
                ],
                'max_tokens':  600,
                'temperature': 0.3,
            },
            timeout=45,
        )
        resp.raise_for_status()
        raw = resp.json()['choices'][0]['message']['content'].strip()
        start = raw.find('[')
        end   = raw.rfind(']')
        if start == -1 or end == -1:
            return []
        raw = raw[start:end+1]
        raw = re.sub(r'(?<=[^\s,:{"\[])\"(?=[^\s,}:\]\[])', '', raw)
        results = json.loads(raw)
        if isinstance(results, list):
            return [str(r) for r in results if r]
        return []
    except Exception as e:
        print(f'[daily] Groq שגיאה: {e}')
        return []


# ── בניית הודעה ───────────────────────────────────────────────────────────────

def build_message(portfolio: dict, all_data: list, insights: list) -> str:
    today    = datetime.now().strftime('%d/%m/%Y')
    holdings = portfolio.get('holdings', [])

    lines     = [f'דוח בוקר {today}', '']
    any_alert = False

    for h in holdings:
        ticker = h.get('symbol') or h.get('ticker', '')
        if not ticker:
            continue

        # מצא נתוני טיקר
        d = next((x for x in all_data if x.get('ticker') == ticker), {})
        q = d.get('quote', {})
        t = d.get('target52', {})

        price   = q.get('price')
        chg_pct = q.get('chg_pct')
        vol_r   = q.get('vol_ratio')
        rsi     = q.get('rsi')

        if price is None:
            lines.append(f'{ticker:<6} ---')
            continue

        chg_str = f'{chg_pct:+.1f}%' if chg_pct is not None else '?'
        line    = f'{ticker:<6} ${price:<9.2f} {chg_str:<7}'

        # נפח
        if vol_r is not None:
            line += f' | x{vol_r} נפח'

        # RSI
        if rsi is not None:
            line += f' | RSI {int(rsi)}'

        # יעד אנליסטים
        target = t.get('target')
        if target and price:
            upside = round((target / price - 1) * 100, 0)
            if abs(upside) < 200:
                line += f' | יעד {upside:+.0f}%'

        # 52w position
        w52 = t.get('w52_range')
        if w52 and price:
            hi, lo = w52
            if hi > lo:
                pct = round((price - lo) / (hi - lo) * 100, 0)
                line += f' | 52w {int(pct)}%'

        # רווחים קרובים
        ne = t.get('next_earnings')
        if ne is not None:
            line += f' | רווחים: {ne}ד'

        # kill switch בדיקה מ-reviews קיימים
        reviews = d.get('reviews', {})
        kill_hit = any(
            isinstance(rv, dict) and rv.get('verdict') in ('SELL', 'EXIT', 'REVIEW')
            for rv in reviews.values()
        )
        if kill_hit:
            line += ' !! REVIEW'
            any_alert = True

        lines.append(line)

    # watchlist
    watchlist = portfolio.get('watchlist', [])
    wl_lines  = []
    for w in watchlist:
        ticker  = w.get('symbol') or w.get('ticker', '')
        trigger = w.get('trigger_price') or w.get('entry_trigger')
        if not ticker or not trigger:
            continue
        d = next((x for x in all_data if x.get('ticker') == ticker), {})
        price = d.get('quote', {}).get('price')
        if price and abs(price - float(trigger)) / float(trigger) < 0.03:
            wl_lines.append(f'WATCHLIST: {ticker} קרוב לטריגר ${trigger} (כעת ${price:.2f})')

    if any_alert:
        lines.insert(2, 'ALERT: יש אחזקות לבדיקה')

    if insights:
        lines.append('')
        lines.append('תובנות:')
        for ins in insights:
            lines.append(f'- {ins}')

    if wl_lines:
        lines.append('')
        lines.extend(wl_lines)

    return '\n'.join(lines)


# ── ריצה ─────────────────────────────────────────────────────────────────────

def main():
    print('[daily_report] מתחיל...')
    with open(PORTFOLIO_JSON, encoding='utf-8') as f:
        portfolio = json.load(f)

    holdings  = portfolio.get('holdings', [])
    watchlist = portfolio.get('watchlist', [])
    all_tickers = list({
        h.get('symbol') or h.get('ticker', '')
        for h in holdings + watchlist
        if h.get('symbol') or h.get('ticker')
    })

    print(f'[daily_report] שולף נתונים ל-{len(all_tickers)} טיקרים...')

    all_data = []
    for ticker in all_tickers:
        print(f'[daily_report] {ticker}...')
        quote   = get_enriched_quote(ticker)
        t52     = get_target_and_52w(ticker)
        reviews = load_reviews(ticker)

        # חדשות רק אם חריג
        chg = abs(quote.get('chg_pct') or 0)
        vol = quote.get('vol_ratio') or 1.0
        news = get_news_headlines(ticker) if (chg > 1.5 or vol > 1.4) else []

        # חדשות מתחרות אם חריג
        competitor_news = {}
        if chg > 1.5 or vol > 1.4:
            for comp in COMPETITORS.get(ticker, []):
                comp_news = get_news_headlines(comp, max_items=2)
                if comp_news:
                    competitor_news[comp] = comp_news

        all_data.append({
            'ticker':           ticker,
            'quote':            quote,
            'target52':         t52,
            'reviews':          reviews,
            'news':             news,
            'competitor_news':  competitor_news,
        })

    # הכן context ל-Groq (ללא reviews, רק מספרים + חדשות)
    groq_context = []
    for d in all_data:
        q = d['quote']
        t = d['target52']
        entry = {
            'ticker':      d['ticker'],
            'chg_pct':     q.get('chg_pct'),
            'vol_ratio':   q.get('vol_ratio'),
            'rsi':         q.get('rsi'),
            'target_upside': (
                round((t.get('target', 0) / q.get('price', 1) - 1) * 100, 1)
                if t.get('target') and q.get('price') else None
            ),
            'earnings_days': t.get('next_earnings'),
            'news':          d['news'],
            'competitor_news': d['competitor_news'],
        }
        groq_context.append(entry)

    print('[daily_report] מריץ Groq insights...')
    insights = run_groq_insights(groq_context)
    print(f'[daily_report] Groq החזיר {len(insights)} תובנות')

    msg    = build_message(portfolio, all_data, insights)
    result = send_notification(msg, title='דוח בוקר', tags=['sun'])
    print(f'[daily_report] נשלח: {result}')


if __name__ == '__main__':
    main()
