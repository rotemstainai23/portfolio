"""
לקוח Yahoo Finance משותף לכל סקריפטי הדיווח.
dual-host fallback (query1→query2) + retry מרכזיים כאן.
"""
import json
import time
import urllib.parse
import urllib.request


def fetch_url(url, timeout=12):
    """HTTP GET פשוט עם User-Agent. מחזיר string ריק בכישלון."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception:
        return ''


def get_chart_result(ticker, period='1mo', interval='1d', retries=0):
    """
    שולף chart.result[0] מ-Yahoo v8 עם dual-host fallback.
    retries=0 כברירת מחדל — query1→query2 מספיק ומונע rate-limit amplification.
    """
    encoded = urllib.parse.quote(ticker)
    for attempt in range(retries + 1):
        for host in ('query1', 'query2'):
            url = (f'https://{host}.finance.yahoo.com/v8/finance/chart/'
                   f'{encoded}?interval={interval}&range={period}')
            raw = fetch_url(url)
            if not raw:
                continue
            try:
                data    = json.loads(raw)
                results = data.get('chart', {}).get('result') or []
                if results:
                    return results[0]
            except Exception:
                continue
        if attempt < retries:
            time.sleep(1.0)
    return {}


def extract_closes(result):
    """מחלץ רשימת close prices תקינות (ללא None) מ-chart result."""
    closes = (result.get('indicators', {})
                    .get('quote', [{}])[0]
                    .get('close', []))
    return [c for c in closes if c is not None]


def rsi_14(closes):
    """מחשב RSI 14 יום. מחזיר float או None אם אין מספיק נקודות."""
    if len(closes) < 15:
        return None
    diffs  = [closes[i] - closes[i-1] for i in range(len(closes)-14, len(closes))]
    gains  = [max(d, 0) for d in diffs]
    losses = [max(-d, 0) for d in diffs]
    ag = sum(gains) / 14
    al = sum(losses) / 14
    if al == 0:
        return 100.0
    return round(100 - 100 / (1 + ag / al), 1)
