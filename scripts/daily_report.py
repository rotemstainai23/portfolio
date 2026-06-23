"""
דוח בוקר יומי — שני עד שישי, 5:00.
נפח חריג + RSI + יעד אנליסטים + רווחים קרובים + חדשות + Groq insights.
ללא קריאות Claude API. מקורות: Yahoo Finance RSS/v8/v10 + Groq (חינם).
"""
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from glob import glob as _glob

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# curl_cffi CA bundle לyfinance
try:
    import certifi
    import os as _os
    _os.environ['CURL_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from notifications import send_notification
from yahoo_client import get_chart_result, extract_closes, rsi_14
from groq_client import call_groq, extract_json_array

PORTFOLIO_JSON = os.path.join(ROOT, 'portfolio.json')
ANALYSES_DIR   = os.path.join(ROOT, 'analyses')
DAILY_DIR      = os.path.join(ANALYSES_DIR, '_daily')
DAILY_JS       = os.path.join(DAILY_DIR, 'daily_latest.js')
DAILY_JSON     = os.path.join(DAILY_DIR, 'daily_latest.json')

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
    """wrapper מקומי — משמש רק ל-RSS ו-yfinance. Yahoo v8 דרך yahoo_client."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception:
        return ''


def get_enriched_quote(ticker: str) -> dict:
    """מחיר + שינוי יומי + נפח_ratio + RSI מ-Yahoo Finance v8 (חודש אחרון)."""
    result = get_chart_result(ticker, period='1mo')
    if not result:
        return {}
    try:
        meta    = result.get('meta', {})
        quote   = result.get('indicators', {}).get('quote', [{}])[0]
        closes  = extract_closes(result)
        volumes = [v for v in quote.get('volume', []) if v is not None]

        if len(closes) < 2:
            return {}

        price   = closes[-1]
        prev    = closes[-2]
        chg_pct = round((price / prev - 1) * 100, 2) if prev else 0

        vol_today = volumes[-1] if volumes else None
        vol_hist  = [v for v in volumes[:-1] if v]
        avg_vol   = sum(vol_hist) / len(vol_hist) if vol_hist else None
        vol_ratio = round(vol_today / avg_vol, 1) if (vol_today and avg_vol) else None

        return {
            'price':     round(price, 2),
            'chg_pct':   chg_pct,
            'vol_ratio': vol_ratio,
            'rsi':       rsi_14(closes),
            'currency':  meta.get('currency', 'USD'),
            'w52_high':  meta.get('fiftyTwoWeekHigh'),
            'w52_low':   meta.get('fiftyTwoWeekLow'),
        }
    except Exception as e:
        print(f'[daily] quote שגיאה {ticker}: {e}')
        return {}


# ETFs שאין להם יעד אנליסטים / תאריך רווחים
_ETF_TICKERS = {'IBIT', 'GLDM', 'SPY', 'QQQ', 'GLD', 'SLV'}


def get_target_and_earnings(ticker: str) -> dict:
    """יעד אנליסטים + תאריך רווחים דרך yfinance (מטפל ב-auth אוטומטית)."""
    if ticker.upper() in _ETF_TICKERS:
        return {}
    try:
        import yfinance as _yf
        info = _yf.Ticker(ticker).info
        target     = info.get('targetMeanPrice')
        earnings_ts = info.get('earningsTimestamp')
        next_earnings = None
        if earnings_ts:
            dt = datetime.fromtimestamp(int(earnings_ts), tz=timezone.utc)
            days_away = (dt.date() - datetime.now(tz=timezone.utc).date()).days
            if 0 <= days_away <= 21:
                next_earnings = days_away
        return {
            'target':        round(float(target), 2) if target else None,
            'next_earnings': next_earnings,
        }
    except Exception as e:
        print(f'[daily] yfinance שגיאה {ticker}: {e}')
        return {}


def get_news_headlines(ticker: str, max_items: int = 3) -> list:
    """כותרות חדשות + URLs מ-Yahoo Finance RSS. מחזיר [{title, url}]."""
    url  = f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US'
    html = _fetch(url, timeout=8)
    if not html:
        return []
    try:
        root = ET.fromstring(html)
        items = []
        for item in root.findall('.//item')[:max_items]:
            title = item.findtext('title', '').strip()
            if not title:
                continue
            link = item.findtext('link', '').strip() or item.findtext('guid', '').strip()
            items.append({'title': title, 'url': link})
        return items
    except Exception:
        return []


def translate_headlines_batch(news_items: list) -> dict:
    """מתרגם כותרות חדשות לעברית ב-Groq call אחד. מחזיר {original_title: he_title}."""
    if not news_items or not os.environ.get('GROQ_API_KEY'):
        return {}

    unique_titles = list(dict.fromkeys(item['title'] for item in news_items if item.get('title')))
    if not unique_titles:
        return {}

    system = 'תרגם כותרות חדשות פיננסיות לעברית. החזר JSON array של strings מתורגמים באותו סדר. כותרת אחת לכל string.'
    user   = json.dumps(unique_titles, ensure_ascii=False)
    raw    = call_groq(system, user, max_tokens=800, temperature=0.1, timeout=30)
    translated = extract_json_array(raw)

    if len(translated) != len(unique_titles):
        print(f'[daily] תרגום: קיבלתי {len(translated)} במקום {len(unique_titles)} — מחזיר מקור')
        return {}

    return {orig: str(he) for orig, he in zip(unique_titles, translated)}


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
    if not os.environ.get('GROQ_API_KEY'):
        return []

    system = """אתה אנליסט תיק השקעות מנוסה. קיבלת נתוני בוקר על תיק מניות.

ענה ב-JSON בלבד — מערך של 3 עד 4 strings בעברית.
כל string: משפט אחד שנותן פרשנות ממשית, לא תיאור של הנתון.

דוגמאות טובות:
- "OKLO -11%: ייתכן תגובה לאחור לאחר העליות החדות בגזרת הגרעין, או חשש מבדיקות רגולטוריות של SMR"
- "IBIT oversold RSI 14 בשילוב עם 52w שפל 5%: Bitcoin בלחץ חזק, כדאי לעקוב אחר מחיר BTC"
- "META +4.2% עם נפח גבוה: ייתכן הכרזה על שות AI או תוצאות Reels חזקות — בדוק חדשות"

דוגמאות רעות (אל תשתמש בסגנון הזה):
- "OKLO חוותה ירידה חדה" (תיאור, לא פרשנות)
- "RSI נמוך מרמז על oversold" (כולם יודעים)

כללים:
- earnings_days≤7 — תמיד אזהרה עם שם הסקטור
- השוואה בין מניות בסקטור דומה (NVDA+AVGO שתיהן down = מגמת סקטור)
- חדשות מתחרות שקיבלת — שלב לתוך הניתוח
- אסור מירכאות כפולות בתוך strings

פורמט: ["תובנה 1", "תובנה 2", "תובנה 3"]"""

    context = json.dumps(holdings_data, ensure_ascii=False, separators=(',', ':'))
    raw     = call_groq(system, context, max_tokens=600, timeout=45)
    results = [str(r) for r in extract_json_array(raw) if r]
    if not results and raw:
        print(f'[daily] Groq: לא נמצא JSON. raw={raw[:100]}')
    return results


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

        # 52w position — מ-v8 meta (ישיר בתוך quote)
        w52_high = q.get('w52_high')
        w52_low  = q.get('w52_low')
        if w52_high and w52_low and w52_high > w52_low and price:
            pct = round((price - w52_low) / (w52_high - w52_low) * 100, 0)
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


# ── שמירת DAILY_DATA ─────────────────────────────────────────────────────────

def archive_daily_js():
    """מעתיק daily_latest.js לארכיון תאריך — שומר 30 ימי מסחר אחרונים."""
    if not os.path.exists(DAILY_JS):
        return
    os.makedirs(DAILY_DIR, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    dest = os.path.join(DAILY_DIR, f'daily_{date_str}.js')
    try:
        with open(DAILY_JS, encoding='utf-8') as f:
            content = f.read()
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(content)
        archives = sorted(_glob(os.path.join(DAILY_DIR, 'daily_2*.js')))
        for old in archives[:-30]:
            os.remove(old)
        print(f'[daily] ארכב ל-{dest}')
    except Exception as e:
        print(f'[daily] שגיאת ארכיב: {e}')


def build_sector_summary(portfolio: dict, all_data: list) -> list:
    """ממוצע שינוי יומי לכל סקטור מהאחזקות."""
    sectors: dict = {}
    for h in portfolio.get('holdings', []):
        ticker = h.get('symbol') or h.get('ticker', '')
        sector = h.get('sector', 'אחר')
        d = next((x for x in all_data if x.get('ticker') == ticker), {})
        chg = d.get('quote', {}).get('chg_pct')
        if chg is not None:
            if sector not in sectors:
                sectors[sector] = {'tickers': [], 'chg_sum': 0.0, 'count': 0}
            sectors[sector]['tickers'].append(ticker)
            sectors[sector]['chg_sum'] += chg
            sectors[sector]['count'] += 1
    return [
        {
            'sector': s,
            'avg_chg_pct': round(v['chg_sum'] / v['count'], 2),
            'tickers': v['tickers'],
        }
        for s, v in sectors.items() if v['count'] > 0
    ]


def write_daily_js(data: dict):
    """כותב daily_latest.js (window.DAILY_DATA) ו-daily_latest.json."""
    os.makedirs(DAILY_DIR, exist_ok=True)
    js = f'window.DAILY_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n'
    with open(DAILY_JS, 'w', encoding='utf-8') as f:
        f.write(js)
    with open(DAILY_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'[daily] כתב {DAILY_JS} + {DAILY_JSON}')


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
        t52     = get_target_and_earnings(ticker)
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

    # תרגום בלוק — כל הכותרות בקריאה אחת לפני insights
    all_news_items = [item for d in all_data for item in d.get('news', []) if isinstance(item, dict)]
    print(f'[daily_report] מתרגם {len(all_news_items)} כותרות חדשות...')
    translations = translate_headlines_batch(all_news_items)
    for d in all_data:
        for item in d.get('news', []):
            if isinstance(item, dict) and item.get('title') in translations:
                item['title_he'] = translations[item['title']]

    print('[daily_report] מריץ Groq insights...')
    insights = run_groq_insights(groq_context)
    print(f'[daily_report] Groq החזיר {len(insights)} תובנות')

    # ── בניית DAILY_DATA ────────────────────────────────────────────────────
    now = datetime.now()
    holdings_data_out = []
    alert_tickers = []

    for h in holdings:
        ticker = h.get('symbol') or h.get('ticker', '')
        if not ticker:
            continue
        d        = next((x for x in all_data if x.get('ticker') == ticker), {})
        q        = d.get('quote', {})
        t        = d.get('target52', {})
        reviews  = d.get('reviews', {})

        price    = q.get('price')
        chg_pct  = q.get('chg_pct')
        w52_high = q.get('w52_high')
        w52_low  = q.get('w52_low')
        w52_pos  = None
        if w52_high and w52_low and w52_high > w52_low and price:
            w52_pos = int(round((price - w52_low) / (w52_high - w52_low) * 100))

        target = t.get('target')
        upside = None
        if target and price:
            raw = (target / price - 1) * 100
            if abs(raw) < 200:
                upside = round(raw, 1)

        verdict = None
        for rv in reviews.values():
            if isinstance(rv, dict) and rv.get('verdict') in ('SELL', 'EXIT', 'REVIEW'):
                verdict = rv.get('verdict')
                alert_tickers.append(ticker)
                break

        holdings_data_out.append({
            'ticker':             ticker,
            'sector':             h.get('sector', ''),
            'layer':              h.get('layer', ''),
            'price':              price,
            'chg_pct':            chg_pct,
            'vol_ratio':          q.get('vol_ratio'),
            'rsi':                q.get('rsi'),
            'w52_pos_pct':        w52_pos,
            'analyst_target':     target,
            'analyst_upside_pct': upside,
            'days_to_earnings':   t.get('next_earnings'),
            'verdict':            verdict,
            'news':               d.get('news', []),
        })

    wl_triggers = []
    for w in watchlist:
        wt     = w.get('symbol') or w.get('ticker', '')
        trig   = w.get('trigger_price') or w.get('entry_trigger')
        if not wt or not trig:
            continue
        d = next((x for x in all_data if x.get('ticker') == wt), {})
        cur = d.get('quote', {}).get('price')
        if cur and abs(cur - float(trig)) / float(trig) < 0.03:
            wl_triggers.append({
                'ticker':        wt,
                'trigger_price': float(trig),
                'current_price': cur,
                'distance_pct':  round((cur - float(trig)) / float(trig) * 100, 2),
            })

    # ── insider enrichment מה-engine (fail-soft) ─────────────────────────────
    insider_alerts = {}
    try:
        from engine.analytics.smartmoney import insider_report as _ir
        holding_tickers = [h.get('symbol') or h.get('ticker', '') for h in holdings if h.get('symbol') or h.get('ticker')]
        for _t in holding_tickers:
            try:
                rep = _ir(_t, limit=10)
                summary = rep.get('summary', {})
                if summary.get('open_market_buy_value', 0) > 10000:
                    insider_alerts[_t] = {
                        'buy_val': summary['open_market_buy_value'],
                        'sell_val': summary.get('open_market_sell_value', 0),
                        'net': summary.get('net_value', 0),
                        'verdict': summary.get('verdict', ''),
                    }
                    print(f'[daily] insider: {_t} - {summary.get("verdict", "")}')
            except Exception:
                pass
    except ImportError:
        pass

    # מאקרו: SPY/QQQ דרך אותו מקור Yahoo v8 שכבר בשימוש
    _spy = get_enriched_quote('SPY')
    _qqq = get_enriched_quote('QQQ')
    macro = {'spy_chg_pct': _spy.get('chg_pct'), 'qqq_chg_pct': _qqq.get('chg_pct'), 'vix': None}  # ponytail: VIX צריך טיפול בסימבול ^, נוסיף אם הפאנל דורש

    daily_payload = {
        'generated':          now.strftime('%Y-%m-%d'),
        'generated_time':     now.strftime('%H:%M'),
        'market_date':        now.strftime('%Y-%m-%d'),
        'has_alerts':         len(alert_tickers) > 0,
        'alert_tickers':      list(set(alert_tickers)),
        'macro':              macro,
        'holdings':           holdings_data_out,
        'watchlist_triggers': wl_triggers,
        'groq_insights':      insights,
        'sector_summary':     build_sector_summary(portfolio, all_data),
        'insider_alerts':     insider_alerts,
    }
    write_daily_js(daily_payload)
    archive_daily_js()  # ponytail: אחרי הכתיבה — מארכב את נתוני היום, לא של אתמול

    # ── שליחת התראה קצרה עם קישור לדשבורד ────────────────────────────────
    up_count = sum(1 for h in holdings_data_out if (h.get('chg_pct') or 0) > 0)
    dn_count = sum(1 for h in holdings_data_out if (h.get('chg_pct') or 0) < 0)
    alert_line = f'🔴 {", ".join(set(alert_tickers))} לבדיקה\n' if alert_tickers else ''
    summary_line = f'{len(holdings_data_out)} אחזקות | {up_count} עולות / {dn_count} יורדות'
    notification_body = f'{alert_line}{summary_line}\n\n' + '\n'.join(f'• {i}' for i in insights[:2])

    dashboard_url = os.environ.get('DASHBOARD_URL', '').rstrip('/')
    report_url = f'{dashboard_url}/templates/daily.html' if dashboard_url else ''
    result = send_notification(notification_body, title='הדוח היומי מוכן',
                               tags=['sun', 'chart_increasing'], click_url=report_url)
    print(f'[daily_report] נשלח: {result}')


if __name__ == '__main__':
    main()
