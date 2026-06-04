"""
gather_research.py - Pre-analysis research gatherer.

כותב analyses/<TICKER>/research_data.txt עם 4 בלוקי מחקר:
  1. השוואת מתחרים (yfinance)
  2. חדשות (yfinance + Google News RSS)
  3. תוכניות עתיד (SEC EDGAR 8-K)
  4. אותות אלפא (short interest, insiders, institutional, analyst targets)

כל המקורות חינמיים ללא מפתח API.
שימוש: python gather_research.py TICKER [--dry-run]
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os
import time
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

try:
    import yfinance as yf
    _HAS_YF = True
except ImportError:
    _HAS_YF = False
    print("[warn] yfinance לא מותקן — חלק מהנתונים יידלגו")

try:
    from pytrends.request import TrendReq
    _HAS_PYTRENDS = True
except ImportError:
    _HAS_PYTRENDS = False

ANALYSES_DIR = os.path.join(os.path.dirname(__file__), 'analyses')
OUTPUT_FILE = 'research_data.txt'

HEADERS = {
    'User-Agent': 'PortfolioResearch/1.0 rotemstainai23@gmail.com',
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'application/json, text/xml, */*',
}

# מפת עמיתים לפי טיקר ידוע + fallback לפי sector
PEER_MAP = {
    'NOW':   ['CRM', 'WDAY', 'SNOW', 'DDOG', 'MDB'],
    'CRM':   ['NOW', 'WDAY', 'SAP', 'ORCL', 'MSFT'],
    'WDAY':  ['NOW', 'CRM', 'SAP', 'INTU', 'ORCL'],
    'SNOW':  ['DDOG', 'MDB', 'ESTC', 'NOW', 'CRM'],
    'MDB':   ['SNOW', 'DDOG', 'ESTC', 'ORCL', 'MSFT'],
    'DDOG':  ['SNOW', 'ESTC', 'SPLK', 'NOW', 'DYNT'],
    'SOFI':  ['AFRM', 'UPST', 'LC', 'OPFI', 'NU'],
    'AFRM':  ['SOFI', 'UPST', 'LC', 'PYPL', 'SQ'],
    'UPST':  ['SOFI', 'AFRM', 'LC', 'OPFI', 'NRDS'],
    'RKLB':  ['SPCE', 'LMT', 'RTX', 'NOC', 'BA'],
    'SPCE':  ['RKLB', 'LMT', 'RTX', 'NOC', 'BA'],
    'AMZN':  ['SHOP', 'WMT', 'TGT', 'BABA', 'EBAY'],
    'SHOP':  ['AMZN', 'WIX', 'BIGC', 'SQSP', 'ETSY'],
    'NVDA':  ['AMD', 'INTC', 'QCOM', 'AVGO', 'MRVL'],
    'AMD':   ['NVDA', 'INTC', 'QCOM', 'AVGO', 'MRVL'],
    'META':  ['GOOGL', 'SNAP', 'PINS', 'RDDT', 'TWTR'],
    'GOOGL': ['META', 'MSFT', 'AMZN', 'SNAP', 'TTD'],
    'MSFT':  ['GOOGL', 'AMZN', 'ORCL', 'SAP', 'NOW'],
    'TSLA':  ['RIVN', 'LCID', 'GM', 'F', 'STLA'],
}

SECTOR_PEERS = {
    'Technology':        ['MSFT', 'AAPL', 'GOOGL', 'META', 'NVDA'],
    'Financial Services':['JPM', 'BAC', 'GS', 'MS', 'WFC'],
    'Healthcare':        ['JNJ', 'PFE', 'ABBV', 'UNH', 'MRK'],
    'Consumer Cyclical': ['AMZN', 'TSLA', 'HD', 'NKE', 'MCD'],
    'Consumer Defensive':['WMT', 'PG', 'KO', 'PEP', 'COST'],
    'Energy':            ['XOM', 'CVX', 'COP', 'EOG', 'SLB'],
    'Industrials':       ['CAT', 'DE', 'GE', 'HON', 'MMM'],
    'Communication Services': ['META', 'GOOGL', 'NFLX', 'DIS', 'T'],
    'Real Estate':       ['AMT', 'PLD', 'CCI', 'EQIX', 'SPG'],
    'Utilities':         ['NEE', 'DUK', 'AEP', 'SO', 'D'],
}


def fmt_num(val, is_pct=False, dec=1):
    if val is None:
        return 'N/A'
    try:
        v = float(val)
        if is_pct:
            return f"{v * 100:.{dec}f}%"
        if abs(v) >= 1e12:
            return f"${v/1e12:.{dec}f}T"
        if abs(v) >= 1e9:
            return f"${v/1e9:.{dec}f}B"
        if abs(v) >= 1e6:
            return f"${v/1e6:.{dec}f}M"
        return f"{v:.{dec}f}"
    except (TypeError, ValueError):
        return 'N/A'


def fetch(url, timeout=15, xml=False):
    try:
        h = dict(HEADERS)
        if xml:
            h['Accept'] = 'application/atom+xml, text/xml, */*'
        r = requests.get(url, headers=h, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  [warn] {url[:60]}... => {e}")
        return None


# ── בלוק 1: השוואת מתחרים ────────────────────────────────────────────────

def gather_competitors(ticker):
    print("[1/4] מחקר מתחרים...")

    if not _HAS_YF:
        return "(yfinance לא זמין — דלג)"

    ticker = ticker.upper()
    peers = PEER_MAP.get(ticker)
    if not peers:
        try:
            sector = yf.Ticker(ticker).info.get('sector', '')
            peers = SECTOR_PEERS.get(sector, ['MSFT', 'GOOGL', 'AMZN', 'META', 'AAPL'])
        except Exception:
            peers = ['MSFT', 'GOOGL', 'AMZN', 'META', 'AAPL']

    peers = [p for p in peers if p != ticker][:5]
    all_tickers = [ticker] + peers

    rows = []
    for sym in all_tickers:
        try:
            info = yf.Ticker(sym).info
            rows.append({
                'ticker':    sym,
                'name':      (info.get('shortName') or info.get('longName') or sym)[:24],
                'mcap':      info.get('marketCap'),
                'pe':        info.get('trailingPE') or info.get('forwardPE'),
                'ps':        info.get('priceToSalesTrailing12Months'),
                'rev_gr':    info.get('revenueGrowth'),
                'gm':        info.get('grossMargins'),
                'op_margin': info.get('operatingMargins'),
                'is_main':   sym == ticker,
            })
            time.sleep(0.35)
        except Exception as e:
            print(f"  [warn] {sym}: {e}")

    if not rows:
        return "לא נמצאו נתוני מתחרים."

    lines = [
        "| טיקר | חברה | שווי שוק | P/E | P/S | צמיחה | מרווח גולמי | מרווח תפעולי |",
        "|------|------|----------|-----|-----|-------|-------------|--------------|",
    ]
    for r in rows:
        marker = " ◄" if r['is_main'] else ""
        lines.append(
            f"| **{r['ticker']}**{marker} | {r['name']} | {fmt_num(r['mcap'])} | "
            f"{fmt_num(r['pe'], dec=1) if r['pe'] else 'N/A'} | "
            f"{fmt_num(r['ps'], dec=1) if r['ps'] else 'N/A'} | "
            f"{fmt_num(r['rev_gr'], is_pct=True) if r['rev_gr'] is not None else 'N/A'} | "
            f"{fmt_num(r['gm'], is_pct=True) if r['gm'] is not None else 'N/A'} | "
            f"{fmt_num(r['op_margin'], is_pct=True) if r['op_margin'] is not None else 'N/A'} |"
        )

    # מיצוב יחסי
    main = next((r for r in rows if r['is_main']), None)
    peer_rows = [r for r in rows if not r['is_main']]
    notes = []
    if main:
        avg_pe = [r['pe'] for r in peer_rows if r['pe']]
        avg_ps = [r['ps'] for r in peer_rows if r['ps']]
        avg_gm = [r['gm'] for r in peer_rows if r['gm']]
        if avg_pe and main['pe']:
            avg = sum(avg_pe) / len(avg_pe)
            diff = (main['pe'] / avg - 1) * 100
            label = f"P/E {'גבוה' if diff > 0 else 'נמוך'} ב-{abs(diff):.0f}% מממוצע עמיתים"
            notes.append(label)
        if avg_ps and main['ps']:
            avg = sum(avg_ps) / len(avg_ps)
            diff = (main['ps'] / avg - 1) * 100
            notes.append(f"P/S {'גבוה' if diff > 0 else 'נמוך'} ב-{abs(diff):.0f}% מממוצע")
        if avg_gm and main['gm']:
            avg = sum(avg_gm) / len(avg_gm)
            diff = (main['gm'] / avg - 1) * 100
            notes.append(f"מרווח גולמי {'גבוה' if diff > 0 else 'נמוך'} ב-{abs(diff):.0f}% מממוצע")

    if notes:
        lines.append("")
        lines.append("**מיצוב יחסי:** " + " | ".join(notes))

    return "\n".join(lines)


# ── בלוק 2: חדשות ────────────────────────────────────────────────────────

def gather_news(ticker, company_name=None):
    print("[2/4] מחקר חדשות...")

    cutoff = datetime.now() - timedelta(days=60)
    items = []
    seen = set()

    # מקור 1: yfinance
    if _HAS_YF:
        try:
            for art in (yf.Ticker(ticker).news or [])[:25]:
                title = (art.get('title') or '').strip()
                if not title or title in seen:
                    continue
                ts = art.get('providerPublishTime', 0)
                dt = datetime.fromtimestamp(ts) if ts else datetime.now()
                if dt >= cutoff:
                    items.append({
                        'date': dt.strftime('%Y-%m-%d'),
                        'title': title,
                        'src': art.get('publisher', 'Yahoo Finance'),
                    })
                    seen.add(title)
        except Exception as e:
            print(f"  [warn] yfinance news: {e}")

    # מקור 2 + 3: Google News RSS
    queries = [f"{ticker} stock earnings"]
    if company_name:
        queries.append(company_name)
    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-US&gl=US&ceid=US:en"
            r = fetch(url, xml=True)
            if not r:
                continue
            root = ET.fromstring(r.content)
            for item in root.findall('.//item')[:15]:
                title = (item.findtext('title') or '').strip()
                if not title or title in seen:
                    continue
                pub = item.findtext('pubDate') or ''
                try:
                    dt = datetime.strptime(pub[:16], '%a, %d %b %Y')
                except Exception:
                    dt = datetime.now()
                if dt >= cutoff:
                    items.append({
                        'date': dt.strftime('%Y-%m-%d'),
                        'title': title,
                        'src': item.findtext('source') or 'Google News',
                    })
                    seen.add(title)
        except Exception as e:
            print(f"  [warn] Google News RSS: {e}")

    if not items:
        return "לא נמצאו חדשות (60 יום אחרונים)."

    items.sort(key=lambda x: x['date'], reverse=True)
    return "\n".join(
        f"- **{i['date']}** | {i['title']} ({i['src']})"
        for i in items[:30]
    )


# ── בלוק 3: תוכניות עתיד (SEC EDGAR 8-K) ────────────────────────────────

def gather_future_plans(ticker):
    print("[3/4] מחקר תוכניות עתיד (SEC EDGAR)...")

    lines = []

    # 8-K filings via EDGAR company ATOM feed
    try:
        url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={ticker}&type=8-K"
            f"&dateb=&owner=include&count=10&search_text=&output=atom"
        )
        r = fetch(url, xml=True)
        if r:
            ns = '{http://www.w3.org/2005/Atom}'
            root = ET.fromstring(r.content)
            entries = root.findall(f'{ns}entry')
            if entries:
                lines.append("**הגשות 8-K אחרונות (אירועים מהותיים, SEC EDGAR):**")
                for entry in entries[:8]:
                    title = (entry.findtext(f'{ns}title') or '').strip()
                    updated = (entry.findtext(f'{ns}updated') or '')[:10]
                    summary = entry.find(f'{ns}summary')
                    sumtext = ''
                    if summary is not None and summary.text:
                        sumtext = summary.text.strip()[:180]
                    if title:
                        lines.append(f"- **{updated}** | {title}")
                        if sumtext and len(sumtext) > 20:
                            lines.append(f"  _{sumtext}_")
            else:
                lines.append("לא נמצאו הגשות 8-K ב-EDGAR.")
        else:
            lines.append("EDGAR לא נגיש כרגע.")
    except Exception as e:
        lines.append(f"שגיאה בשליפת 8-K: {e}")

    lines.append("")

    # אחזקות מרכזיות + מוסדיות מ-yfinance
    if _HAS_YF:
        try:
            t = yf.Ticker(ticker)
            major = t.major_holders
            if major is not None and not major.empty:
                lines.append("**אחזקות מרכזיות:**")
                for _, row in major.iterrows():
                    lines.append(f"- {row.iloc[1]}: {row.iloc[0]}")
                lines.append("")
            inst = t.institutional_holders
            if inst is not None and not inst.empty:
                lines.append("**מחזיקים מוסדיים (top 5):**")
                for _, row in inst.head(5).iterrows():
                    holder = str(row.iloc[0])
                    shares = row.iloc[1] if len(row) > 1 else ''
                    pct = row.iloc[3] if len(row) > 3 else ''
                    pct_str = f" ({float(pct)*100:.1f}%)" if pct != '' else ''
                    lines.append(f"- {holder}: {fmt_num(shares, dec=0)} מניות{pct_str}")
                lines.append("")
        except Exception as e:
            print(f"  [warn] yfinance holders: {e}")

    return "\n".join(lines) if lines else "לא נמצאו נתוני תוכניות עתיד."


# ── בלוק 4: אותות אלפא ──────────────────────────────────────────────────

def gather_alpha_signals(ticker):
    print("[4/4] מחקר אותות אלפא...")

    lines = []

    if _HAS_YF:
        try:
            info = yf.Ticker(ticker).info

            # שורט אינטרסט
            short_pct   = info.get('shortPercentOfFloat')
            short_ratio = info.get('shortRatio')
            shares_short = info.get('sharesShort')
            lines.append("**שורט אינטרסט:**")
            if short_pct is not None:
                pct = short_pct * 100
                lvl = ("גבוה מאוד — פוטנציאל לסחיטת שורטים" if pct > 15
                       else "גבוה" if pct > 8
                       else "מתון" if pct > 4
                       else "נמוך")
                lines.append(f"- Float בשורט: **{pct:.1f}%** ({lvl})")
            if short_ratio is not None:
                lines.append(f"- ימי כיסוי (Days to Cover): **{short_ratio:.1f}**")
            if shares_short is not None:
                lines.append(f"- מניות בשורט: {fmt_num(shares_short, dec=0)}")
            if short_pct and short_pct > 0.10:
                lines.append("- ⚡ short float גבוה + שיפור פונדמנטלי = אסימטריה חיובית אפשרית")
            lines.append("")

            # מבנה אחזקות
            insider_pct = info.get('heldPercentInsiders')
            inst_pct    = info.get('heldPercentInstitutions')
            lines.append("**מבנה אחזקות:**")
            if insider_pct is not None:
                lvl = ("גבוה — מנהלים מאמינים בחברה" if insider_pct > 0.10
                       else "מתון" if insider_pct > 0.03
                       else "נמוך")
                lines.append(f"- אחזקות פנים (insiders): **{insider_pct*100:.1f}%** — {lvl}")
            if inst_pct is not None:
                lines.append(f"- אחזקות מוסדיות: **{inst_pct*100:.1f}%**")
            lines.append("")

            # יעדי מחיר אנליסטים
            target_mean = info.get('targetMeanPrice')
            target_high = info.get('targetHighPrice')
            target_low  = info.get('targetLowPrice')
            current     = info.get('currentPrice') or info.get('regularMarketPrice')
            rec_key     = info.get('recommendationKey', '')
            n_analysts  = info.get('numberOfAnalystOpinions', 0)
            if target_mean and current:
                upside = (target_mean / current - 1) * 100
                lines.append("**קונצנזוס אנליסטים:**")
                lines.append(
                    f"- יעד ממוצע: ${target_mean:.2f} | גבוה: ${target_high:.2f} | "
                    f"נמוך: ${target_low:.2f} | נוכחי: ${current:.2f}"
                )
                lines.append(f"- פוטנציאל לממוצע: **{upside:+.1f}%**")
                if rec_key:
                    lines.append(f"- המלצה: {rec_key.upper()} ({n_analysts} אנליסטים)")
                if upside > 30:
                    lines.append("- ⚡ אפסייד גבוה — השוק מחמיר מהקונצנזוס, בדוק אם מוצדק")
                elif upside < 0:
                    lines.append("- ⚠️ נסחר מעל יעד ממוצע — מחיר מחייב הצדקה גבוהה")
                lines.append("")
        except Exception as e:
            print(f"  [warn] yfinance alpha signals: {e}")

    # עסקאות פנים (Form 4) מ-EDGAR
    try:
        ninety_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        url = (
            f"https://efts.sec.gov/LATEST/search-index"
            f"?q=%22{ticker}%22&forms=4"
            f"&dateRange=custom&startdt={ninety_ago}&enddt={today}"
        )
        r = fetch(url)
        if r:
            data = r.json()
            hits = data.get('hits', {}).get('hits', [])
            lines.append("**עסקאות פנים (Form 4 — 90 יום, EDGAR):**")
            if hits:
                lines.append(f"- נמצאו {len(hits)} הגשות Form 4")
                for h in hits[:4]:
                    src = h.get('_source', {})
                    entity = src.get('entity_name', ticker)
                    period = src.get('period_of_report', '')
                    form_type = src.get('form_type', '4')
                    lines.append(f"  - {entity} | טופס: {form_type} | תקופה: {period}")
                edgar_link = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=4&count=20"
                lines.append(f"- קישור EDGAR מלא: {edgar_link}")
            else:
                lines.append("- לא נמצאו הגשות Form 4 ב-90 יום האחרונים")
            lines.append("")
    except Exception as e:
        print(f"  [warn] EDGAR Form 4: {e}")

    # Google Trends (אם pytrends מותקן)
    if _HAS_PYTRENDS and _HAS_YF:
        try:
            info = yf.Ticker(ticker).info
            company_kw = (info.get('shortName') or ticker).split()[0]
            pytrends = TrendReq(hl='en-US', tz=180)
            pytrends.build_payload([company_kw], timeframe='today 3-m', geo='US')
            df = pytrends.interest_over_time()
            if not df.empty and company_kw in df.columns:
                vals = df[company_kw].tolist()
                if len(vals) >= 8:
                    recent = sum(vals[-4:]) / 4
                    earlier = sum(vals[:4]) / 4
                    trend = "עולה ⬆" if recent > earlier * 1.1 else "יורד ⬇" if recent < earlier * 0.9 else "יציב →"
                    lines.append("**Google Trends (3 חודשים, ארה\"ב):**")
                    lines.append(f"- עניין חיפוש: {trend} ({earlier:.0f} → {recent:.0f} / 100)")
                    lines.append("")
        except Exception as e:
            print(f"  [warn] pytrends: {e}")

    return "\n".join(lines) if lines else "לא נמצאו אותות אלפא."


# ── Main ───────────────────────────────────────────────────────────────────

def run(ticker, save=True):
    ticker = ticker.upper().strip()
    print(f"\n{'═'*52}")
    print(f"  מחקר מקדים: {ticker}  [{datetime.now().strftime('%Y-%m-%d %H:%M')}]")
    print(f"{'═'*52}\n")

    company_name = None
    if _HAS_YF:
        try:
            company_name = yf.Ticker(ticker).info.get('shortName')
        except Exception:
            pass

    # ── SEC filings + earnings transcript (sec_fetcher) ──────────────────
    sec_context = ''
    try:
        import sec_fetcher as _sf
        # בחר profile לפי הקשר: full_analysis כברירת מחדל
        sec_context = _sf.build_sec_context(ticker, profile='full_analysis', include_transcript=True)
        if sec_context:
            print(f"  ✓ SEC context: {len(sec_context)} תווים")
    except Exception as _e:
        print(f"  [warn] sec_fetcher: {_e}")

    sections = [
        ("COMPETITOR COMPARISON",            gather_competitors(ticker)),
        ("NEWS COVERAGE (last 60 days)",      gather_news(ticker, company_name)),
        ("FUTURE PLANS & STRATEGIC SIGNALS",  gather_future_plans(ticker)),
        ("ALPHA SIGNALS",                     gather_alpha_signals(ticker)),
    ]
    if sec_context:
        sections.insert(0, ("SEC FILING — 10-Q/10-K + EARNINGS CALL (ממוקד)", sec_context))

    body = "\n\n".join(
        f"━━━ {header} ━━━\n{content}"
        for header, content in sections
    )
    output = body + f"\n\n[Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Ticker: {ticker}]"

    if save:
        out_dir = os.path.join(ANALYSES_DIR, ticker)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, OUTPUT_FILE)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n✓ נשמר: {out_path}")
    else:
        print("\n" + output)

    return output


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("שימוש: python gather_research.py TICKER [--dry-run]")
        sys.exit(1)
    ticker_arg = sys.argv[1]
    dry = '--dry-run' in sys.argv
    run(ticker_arg, save=not dry)
