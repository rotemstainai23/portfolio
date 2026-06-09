"""
סקנר שבתי — שבת 5:00.
שולף חדשות + פונדמנטלי מ-Yahoo Finance ומנתח עם Groq (Llama 3.3 70B) חינמי.
"""
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from notifications import send_notification
from yahoo_client import get_chart_result, extract_closes, fetch_url, rsi_14
from groq_client import call_groq, extract_json_array

SCANNER_RESULTS = os.path.join(ROOT, 'scanner-results.json')
SUNDAY_TARGET   = os.path.join(ROOT, 'sunday-analysis-target.json')
SCANNER_ARCHIVE = os.path.join(ROOT, 'analyses', '_monthly', '_scanner_archive')

# יקום מניות לסריקה — מגוון סקטורים
SCAN_UNIVERSE = [
    # טכנולוגיה
    'NVDA','META','GOOGL','MSFT','AAPL','AMD','AVGO','CRM','SNOW','PLTR',
    'UBER','LYFT','SHOP','MELI','SE','GRAB','NET','DDOG','ZS','CRWD',
    # AI + ענן
    'AI','SOUN','BBAI','IREN','CORZ','MSTR','PATH','UiPath',
    # ביומד + בריאות
    'LLY','NVO','MRNA','BNTX','REGN','VRTX','ISRG',
    # פיננסים
    'COIN','HOOD','SQ','AFRM','UPST','NU',
    # ישראל-ארה"ב
    'CHKP','NICE','CYBR','WIX','MNDY','GLBE','CEVA',
    # אנרגיה + מניות ערך
    'XOM','CVX','NEE','FSLR','ENPH',
    # ספייס + הגנה
    'RKLB','LUNR','RDW','KTOS','HII',
]


# ── שליפת נתונים ─────────────────────────────────────────────────────────────

def get_news_headlines(ticker: str, max_items: int = 5) -> list[str]:
    """חדשות מ-Yahoo Finance RSS."""
    url  = f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US'
    html = fetch_url(url)
    if not html:
        return []
    try:
        root  = ET.fromstring(html)
        items = root.findall('.//item')
        cutoff = datetime.utcnow() - timedelta(days=7)
        headlines = []
        for item in items[:max_items]:
            title = item.findtext('title', '')
            if title:
                headlines.append(title.strip())
        return headlines
    except Exception:
        return []


def get_yahoo_quote(ticker: str) -> dict:
    """מחיר + momentum + RSI מ-Yahoo v8 (3 חודשים) — עם dual-host fallback."""
    result = get_chart_result(ticker, period='3mo')
    if not result:
        return {}
    try:
        meta   = result.get('meta', {})
        closes = extract_closes(result)
        if len(closes) < 5:
            return {}
        price    = closes[-1]
        price_1m = closes[-21] if len(closes) >= 21 else closes[0]
        price_3m = closes[0]
        mom_1m   = round((price / price_1m - 1) * 100, 1) if price_1m else 0
        mom_3m   = round((price / price_3m - 1) * 100, 1) if price_3m else 0
        return {
            'price':    round(price, 2),
            'mom_1m':   mom_1m,
            'mom_3m':   mom_3m,
            'rsi':      rsi_14(closes) or 50,
            'currency': meta.get('currency', 'USD'),
        }
    except Exception:
        return {}


def get_yahoo_fundamentals(ticker: str) -> dict:
    """נתונים פונדמנטליים מ-Yahoo Finance v10."""
    import urllib.parse
    url  = (f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/'
            f'{urllib.parse.quote(ticker)}?modules=summaryDetail,financialData,defaultKeyStatistics')
    html = fetch_url(url, timeout=12)
    if not html:
        return {}
    try:
        data    = json.loads(html)
        summary = data.get('quoteSummary', {}).get('result', [{}])[0]
        detail  = summary.get('summaryDetail', {})
        fin     = summary.get('financialData', {})
        stats   = summary.get('defaultKeyStatistics', {})

        def val(d, k):
            v = d.get(k, {})
            return v.get('fmt') or v.get('raw')

        return {
            'pe':             val(detail, 'trailingPE'),
            'fwd_pe':         val(detail, 'forwardPE'),
            'revenue_growth': val(fin, 'revenueGrowth'),
            'gross_margin':   val(fin, 'grossMargins'),
            'earnings_growth':val(fin, 'earningsGrowth'),
            'target_price':   val(fin, 'targetMeanPrice'),
            'short_ratio':    val(stats, 'shortRatio'),
            'beta':           val(detail, 'beta'),
            'market_cap':     val(detail, 'marketCap'),
        }
    except Exception:
        return {}


# ── בניית context לסקנר ───────────────────────────────────────────────────────

def build_scan_context(holdings: list[str]) -> str:
    """בנה context מלא — מסרוק את כל היקום ומעביר רק Top 25 לGroq."""
    exclude    = set(h.upper() for h in holdings)
    candidates = [t for t in SCAN_UNIVERSE if t.upper() not in exclude]

    # שלב 1: סרוק את כולם, אסוף נתונים
    raw_data = []
    for i, ticker in enumerate(candidates):
        quote = get_yahoo_quote(ticker)
        if not quote:
            continue
        news  = get_news_headlines(ticker, max_items=3)
        score = abs(quote['mom_1m']) + abs(quote['mom_3m']) * 0.5 + len(news) * 2
        raw_data.append({'ticker': ticker, 'quote': quote, 'news': news, 'score': score})
        print(f'[scanner] נסרק {ticker} ({i+1}/{len(candidates)})')

    # שלב 2: מיין לפי score, קח Top 25
    raw_data.sort(key=lambda x: x['score'], reverse=True)
    top25 = raw_data[:25]
    print(f'[scanner] נבחרו {len(top25)} מניות לניתוח Groq')

    # שלב 3: הוסף פונדמנטלי רק ל-Top 25
    lines = [f'## סריקת שוק — {datetime.now().strftime("%Y-%m-%d")}']
    lines.append(f'תיק נוכחי (אל תמליץ על אלה): {", ".join(sorted(exclude))}\n')

    for item in top25:
        ticker = item['ticker']
        quote  = item['quote']
        news   = item['news']
        fund   = get_yahoo_fundamentals(ticker)

        block = [f'### {ticker}']
        block.append(f'מחיר: ${quote["price"]} | 1M: {quote["mom_1m"]}% | 3M: {quote["mom_3m"]}% | RSI: {quote["rsi"]}')
        if fund:
            f_parts = []
            if fund.get('fwd_pe'):          f_parts.append(f'P/E: {fund["fwd_pe"]}')
            if fund.get('revenue_growth'):  f_parts.append(f'צמיחה: {fund["revenue_growth"]}')
            if fund.get('earnings_growth'): f_parts.append(f'רווח: {fund["earnings_growth"]}')
            if fund.get('target_price'):    f_parts.append(f'יעד: ${fund["target_price"]}')
            if f_parts:
                block.append(' | '.join(f_parts))
        if news:
            block.append('חדשות: ' + ' | '.join(news))
        lines.append('\n'.join(block))

    return '\n\n'.join(lines)


# ── Groq AI ───────────────────────────────────────────────────────────────────

def run_groq_analysis(context: str) -> list:
    """שלח נתונים ל-Groq וקבל Top 3 בJSON."""
    if not os.environ.get('GROQ_API_KEY'):
        print('[scanner] אין GROQ_API_KEY')
        return []

    system = """אתה סוכן סקנר מניות מקצועי. בהינתן נתוני שוק, פונדמנטלי וחדשות לרשימת מניות, זהה את 3 ההזדמנויות הטובות ביותר לשבוע הקרוב.

ענה אך ורק ב-JSON תקין, ללא הסברים, בפורמט הבא:
[
  {
    "ticker": "XXXX",
    "company": "שם החברה",
    "catalyst": "קטליסט ספציפי לשבוע הקרוב (30-60 מילים)",
    "conviction": 4,
    "upside_pct": 12,
    "downside_pct": 5,
    "timeframe": "1-2 שבועות",
    "source": "מקור: חדשות / טכני / פונדמנטלי / כולם",
    "thesis": "תזה קצרה (2-3 משפטים) מבוססת על הנתונים שסופקו"
  }
]

קריטריוני בחירה:
- קטליסט ברור: רווחים קרובים, חדשות מוצר, שינוי רגולטורי, momentum חזק
- לא לכלול מניות מהתיק הנוכחי
- conviction 4-5 רק למניות עם עדות חזקה מהנתונים
- upside/downside ריאליסטי לטווח הקצר

חשוב: אסור להשתמש במירכאות כפולות בתוך ערכי JSON. במקום "דו"ח" כתוב "דוח"."""

    raw     = call_groq(system, context, max_tokens=1500, timeout=60)
    results = extract_json_array(raw)
    if not results and raw:
        print(f'[scanner] לא נמצא JSON array. raw={raw[:300]}')
    return [r for r in results if isinstance(r, dict)]


# ── ארכיב ────────────────────────────────────────────────────────────────────

def archive_previous() -> None:
    if not os.path.exists(SCANNER_RESULTS):
        return
    os.makedirs(SCANNER_ARCHIVE, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    dest     = os.path.join(SCANNER_ARCHIVE, f'scanner-{date_str}.json')
    try:
        with open(SCANNER_RESULTS, encoding='utf-8') as f:
            data = f.read()
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(data)
        from glob import glob as _glob
        archives = sorted(_glob(os.path.join(SCANNER_ARCHIVE, 'scanner-*.json')))
        for old in archives[:-16]:
            os.remove(old)
    except Exception as e:
        print(f'[scanner] שגיאת ארכיב: {e}')


# ── עיצוב הודעה ──────────────────────────────────────────────────────────────

def format_message(results: list) -> str:
    today   = datetime.now().strftime('%d/%m/%Y')
    sorted_r = sorted(results, key=lambda x: x.get('conviction', 0), reverse=True)
    top3     = sorted_r[:3]

    if top3:
        with open(SUNDAY_TARGET, 'w', encoding='utf-8') as f:
            json.dump(top3[0], f, ensure_ascii=False, indent=2)
        print(f'[scanner] top pick: {top3[0].get("ticker")}')

    lines = [f'סקנר שבתי {today} — 3 הזדמנויות לשבוע:']
    for i, opp in enumerate(top3, 1):
        lines.append(
            f'{i}. {opp.get("ticker")} ({opp.get("company","")})\n'
            f'   קטליסט: {opp.get("catalyst","")}\n'
            f'   Conviction: {opp.get("conviction")}/5 | '
            f'Upside: +{opp.get("upside_pct")}% | Downside: -{opp.get("downside_pct")}%\n'
            f'   {opp.get("thesis","")}'
        )
    if not top3:
        lines.append('לא נמצאו הזדמנויות ברמת conviction מספקת השבוע.')
    return '\n\n'.join(lines)


# ── ריצה ─────────────────────────────────────────────────────────────────────

def main():
    print('[saturday_scanner] מתחיל...')
    archive_previous()

    # טען תיק נוכחי
    pf_path  = os.path.join(ROOT, 'portfolio.json')
    holdings = []
    if os.path.exists(pf_path):
        with open(pf_path, encoding='utf-8') as f:
            pf = json.load(f)
        holdings = [h.get('symbol') or h.get('ticker', '') for h in pf.get('holdings', [])]

    # בנה context וסרוק
    context = build_scan_context(holdings)

    # הרץ Groq
    results = run_groq_analysis(context)
    print(f'[scanner] Groq החזיר {len(results)} הזדמנויות')

    # fallback — קרא קובץ קיים
    if not results and os.path.exists(SCANNER_RESULTS):
        print('[scanner] Groq נכשל — משתמש בתוצאות קיימות')
        with open(SCANNER_RESULTS, encoding='utf-8') as f:
            results = json.load(f)

    # שמור תוצאות
    if results:
        with open(SCANNER_RESULTS, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    # שלח התראה
    msg    = format_message(results)
    result = send_notification(msg, title='סקנר שבתי', tags=['mag'])
    print(f'[scanner] נשלח: {result}')


if __name__ == '__main__':
    main()
