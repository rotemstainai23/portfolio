"""
sec_fetcher.py — שאיבה ממוקדת מ-SEC EDGAR ומ-earnings transcripts.

עיקרון: לא קוראים מסמכים שלמים. כל שאילתה מחזירה רק
את הסעיפים הרלוונטיים לפי KEYWORD_TAXONOMY.

מקורות (חינמיים, ללא API key):
  • SEC EDGAR full-text search  — efts.sec.gov
  • SEC EDGAR filing index      — data.sec.gov
  • Motley Fool transcripts     — scrape בסיסי
  • EDGAR HTML sections         — xbrl viewer / htm filing

תקציבי retrieval:
  MAX_SECTION_CHARS  = 1200   תווים לסעיף אחד
  MAX_SECTIONS       = 4      סעיפים מחזיר לבלוק אחד
  MAX_TRANSCRIPT_CHARS = 2000 תמליל מלא אחרי חיתוך
  MAX_TOTAL_CHARS    = 4000   סך הכל לכל הבלוק
"""
import re
import os
import json
import time
import requests
from datetime import datetime, timedelta

# ── תקציבים ────────────────────────────────────────────────────────────────
MAX_SECTION_CHARS   = 1200
MAX_SECTIONS        = 4
MAX_TRANSCRIPT_CHARS = 2000
MAX_TOTAL_CHARS     = 4000
REQUEST_TIMEOUT     = 12
RATE_SLEEP          = 0.35   # שניות בין בקשות EDGAR

HEADERS = {
    'User-Agent': 'PortfolioResearch/2.0 rotemstainai23@gmail.com',
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'application/json, text/html, */*',
}


# ══════════════════════════════════════════════════════════════════════════════
# KEYWORD TAXONOMY
# ══════════════════════════════════════════════════════════════════════════════
# כל entry מגדיר:
#   keywords  — מה לחפש בגוף המסמך (lowercase match)
#   sections  — שמות סעיפי 10-K/10-Q שמכילים מידע זה (לפי EDGAR structure)
#   weight    — עדיפות (גבוה = נבחר ראשון כשיש limit)
#   max_chars — חיתוך תוצאה לסעיף זה
#
# קטגוריות: revenue | margins | fcf | eps | guidance | segments |
#           balance_sheet | risks | buybacks | call_guidance | call_metrics
# ──────────────────────────────────────────────────────────────────────────

KEYWORD_TAXONOMY: dict = {

    # ── הכנסות וצמיחה ────────────────────────────────────────────────────
    'revenue': {
        'keywords': [
            'net revenue', 'total revenues', 'total net revenue',
            'revenue increased', 'revenue decreased', 'revenue grew',
            'year-over-year', 'yoy', 'organic growth', 'constant currency',
        ],
        'sections': [
            'Results of Operations', 'Revenue', 'Net Revenue',
            'Consolidated Statements of Operations',
        ],
        'weight': 10,
        'max_chars': MAX_SECTION_CHARS,
    },

    # ── רווחיות ──────────────────────────────────────────────────────────
    'margins': {
        'keywords': [
            'gross margin', 'gross profit', 'operating margin', 'operating income',
            'operating loss', 'adjusted ebitda', 'non-gaap', 'adjusted operating',
            'operating expenses', 'cost of revenue',
        ],
        'sections': [
            'Results of Operations', 'Operating Results',
            'Gross Profit', 'Operating Expenses',
        ],
        'weight': 9,
        'max_chars': MAX_SECTION_CHARS,
    },

    # ── תזרים מזומנים ו-CapEx ─────────────────────────────────────────────
    'fcf': {
        'keywords': [
            'free cash flow', 'capital expenditures', 'capex',
            'cash provided by operating', 'net cash used', 'investing activities',
            'cash from operations', 'cash used in investing',
            'property and equipment', 'datacenter',
        ],
        'sections': [
            'Liquidity and Capital Resources', 'Cash Flows',
            'Capital Expenditures', 'Investing Activities',
        ],
        'weight': 10,
        'max_chars': MAX_SECTION_CHARS,
    },

    # ── EPS ורווח נקי ─────────────────────────────────────────────────────
    'eps': {
        'keywords': [
            'earnings per share', 'diluted eps', 'net income', 'net loss',
            'diluted shares', 'weighted-average shares', 'basic and diluted',
            'income from operations',
        ],
        'sections': [
            'Results of Operations', 'Earnings Per Share',
            'Consolidated Statements of Operations',
        ],
        'weight': 8,
        'max_chars': 800,
    },

    # ── הנחיות עתידיות (Guidance) ─────────────────────────────────────────
    'guidance': {
        'keywords': [
            'outlook', 'guidance', 'we expect', 'we anticipate', 'we forecast',
            'full year', 'full-year', 'fiscal year 2026', 'fiscal 2027',
            'second quarter', 'third quarter', 'next quarter',
            'revenue guidance', 'eps guidance', 'raise guidance', 'lowered',
        ],
        'sections': [
            'Outlook', 'Guidance', 'Forward-Looking Statements',
            'Business Outlook', 'Financial Outlook',
        ],
        'weight': 10,
        'max_chars': MAX_SECTION_CHARS,
    },

    # ── נתוני מגזרים ──────────────────────────────────────────────────────
    'segments': {
        'keywords': [
            'segment revenue', 'reportable segment', 'operating segment',
            'cloud', 'aws', 'azure', 'google cloud', 'advertising',
            'subscription', 'services', 'hardware', 'licensing',
        ],
        'sections': [
            'Segment Information', 'Business Segments',
            'Reportable Segments', 'Note.*Segment',
        ],
        'weight': 7,
        'max_chars': MAX_SECTION_CHARS,
    },

    # ── מאזן / חוב ───────────────────────────────────────────────────────
    'balance_sheet': {
        'keywords': [
            'total debt', 'long-term debt', 'cash and cash equivalents',
            'total assets', 'stockholders equity', "shareholders' equity",
            'credit facility', 'revolving credit', 'notes payable',
        ],
        'sections': [
            'Financial Condition', 'Liquidity and Capital Resources',
            'Consolidated Balance Sheets', 'Balance Sheet',
        ],
        'weight': 6,
        'max_chars': 800,
    },

    # ── רכישה עצמית / החזר הון ────────────────────────────────────────────
    'buybacks': {
        'keywords': [
            'share repurchase', 'stock repurchase', 'buyback',
            'dividends', 'return of capital', 'repurchased shares',
            'authorization', 'shares outstanding',
        ],
        'sections': [
            'Share Repurchase', 'Capital Return', 'Stockholder Returns',
            'Dividends', 'Stock Repurchase Program',
        ],
        'weight': 5,
        'max_chars': 600,
    },

    # ── גורמי סיכון ───────────────────────────────────────────────────────
    'risks': {
        'keywords': [
            'risk factors', 'competition', 'regulatory', 'litigation',
            'macroeconomic', 'cybersecurity', 'customer concentration',
            'geopolitical', 'tariff', 'inflation',
        ],
        'sections': [
            'Risk Factors', 'Quantitative and Qualitative Disclosures',
            'Legal Proceedings',
        ],
        'weight': 4,
        'max_chars': 800,
    },

    # ── תמליל שיחת משקיעים — הנחיות ──────────────────────────────────────
    'call_guidance': {
        'keywords': [
            'next quarter', 'full year guidance', 'we expect', 'we anticipate',
            'revenue guidance', 'eps guidance', 'raise guidance', 'lower guidance',
            'macro environment', 'demand environment', 'backlog',
        ],
        'sections': ['Prepared Remarks', 'Guidance', 'Opening Remarks'],
        'weight': 10,
        'max_chars': MAX_SECTION_CHARS,
    },

    # ── תמליל — מדדי KPI ──────────────────────────────────────────────────
    'call_metrics': {
        'keywords': [
            'rpo', 'arr', 'nrr', 'net revenue retention', 'net retention rate',
            'churn', 'bookings', 'seat', 'logos', 'customers', 'win rate',
            'attach rate', 'renewal rate', 'net dollar retention',
        ],
        'sections': ['Q&A', 'Prepared Remarks', 'Metrics'],
        'weight': 8,
        'max_chars': MAX_SECTION_CHARS,
    },

    # ── תמליל — שאלות אנליסטים ────────────────────────────────────────────
    'call_qa': {
        'keywords': [
            'your question', 'analyst', 'morgan stanley', 'goldman sachs',
            'jp morgan', 'ubs', 'barclays', 'question.*?:', 'follow.?up',
        ],
        'sections': ['Q&A Session', 'Question-and-Answer'],
        'weight': 6,
        'max_chars': MAX_SECTION_CHARS,
    },
}

# ── מיפוי: שאילתה → categories רלוונטיות ───────────────────────────────────
QUERY_PROFILES: dict = {
    'full_analysis':    ['revenue', 'margins', 'fcf', 'eps', 'guidance', 'segments'],
    'earnings_check':   ['revenue', 'margins', 'eps', 'guidance', 'call_guidance'],
    'valuation':        ['revenue', 'fcf', 'eps', 'balance_sheet', 'buybacks'],
    'risks_deep':       ['risks', 'balance_sheet', 'fcf'],
    'guidance_only':    ['guidance', 'call_guidance'],
    'transcript_full':  ['call_guidance', 'call_metrics', 'call_qa'],
    'kpi_check':        ['call_metrics', 'segments', 'revenue'],
    'quick_check':      ['revenue', 'guidance', 'call_guidance'],
}


# ══════════════════════════════════════════════════════════════════════════════
# EDGAR CIK LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

_cik_cache: dict = {}

def get_cik(ticker: str) -> str | None:
    """מחזיר CIK (10-ספרות) עבור ticker. ממטמן בזיכרון."""
    tk = ticker.upper().strip()
    if tk in _cik_cache:
        return _cik_cache[tk]
    try:
        url = f'https://efts.sec.gov/LATEST/search-index?q=%22{tk}%22&dateRange=custom&startdt=2020-01-01&forms=10-K'
        # שיטה מהירה יותר: company tickers JSON
        url2 = 'https://www.sec.gov/files/company_tickers.json'
        r = requests.get(url2, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        for entry in data.values():
            if entry.get('ticker', '').upper() == tk:
                cik = str(entry['cik_str']).zfill(10)
                _cik_cache[tk] = cik
                return cik
        return None
    except Exception as e:
        print(f'[sec_fetcher] CIK lookup failed for {tk}: {e}')
        return None


# ══════════════════════════════════════════════════════════════════════════════
# EDGAR FILING INDEX
# ══════════════════════════════════════════════════════════════════════════════

def get_latest_filing(ticker: str, form_type: str = '10-Q') -> dict | None:
    """מחזיר {accession_number, filing_date, primary_document, index_url}
    עבור הדיווח האחרון מסוג form_type. None אם נכשל."""
    cik = get_cik(ticker)
    if not cik:
        return None
    time.sleep(RATE_SLEEP)
    try:
        url = f'https://data.sec.gov/submissions/CIK{cik}.json'
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        filings = data.get('filings', {}).get('recent', {})
        forms   = filings.get('form', [])
        dates   = filings.get('filingDate', [])
        accnums = filings.get('accessionNumber', [])
        docs    = filings.get('primaryDocument', [])

        for i, f in enumerate(forms):
            if f == form_type:
                acc = accnums[i].replace('-', '')
                idx_url = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/'
                return {
                    'ticker': ticker.upper(),
                    'form': form_type,
                    'accession': accnums[i],
                    'filing_date': dates[i],
                    'primary_doc': docs[i],
                    'index_url': idx_url,
                    'doc_url': idx_url + docs[i],
                }
        return None
    except Exception as e:
        print(f'[sec_fetcher] filing index failed for {ticker}/{form_type}: {e}')
        return None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION EXTRACTOR (HTML → text)
# ══════════════════════════════════════════════════════════════════════════════

def _strip_html(html: str) -> str:
    """הסרת HTML tags בסיסית, ניקוי רווחים."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'\s{3,}', '\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


def _find_keyword_windows(text: str, keywords: list, window: int = 600) -> list[str]:
    """מוצא חלונות טקסט סביב כל keyword. מחזיר רשימת snippets ייחודיים."""
    text_lower = text.lower()
    seen_positions = set()
    snippets = []
    for kw in keywords:
        idx = 0
        kw_lower = kw.lower()
        while True:
            pos = text_lower.find(kw_lower, idx)
            if pos == -1:
                break
            # בדיקה שהחלון לא חופף עם snippet קיים
            block_start = max(0, pos - 100)
            block_end   = min(len(text), pos + window)
            already = any(abs(p - pos) < window // 2 for p in seen_positions)
            if not already:
                snippet = text[block_start:block_end].strip()
                if len(snippet) > 60:
                    snippets.append(snippet)
                    seen_positions.add(pos)
            idx = pos + len(kw_lower)
            if len(snippets) >= MAX_SECTIONS:
                break
        if len(snippets) >= MAX_SECTIONS:
            break
    return snippets[:MAX_SECTIONS]


def fetch_filing_sections(ticker: str, form_type: str = '10-Q',
                          categories: list = None) -> dict:
    """מוריד את הדיווח האחרון ומחלץ רק את הסעיפים הרלוונטיים.
    categories: רשימה מ-KEYWORD_TAXONOMY (ברירת מחדל: full_analysis).
    מחזיר {ticker, form, date, sections: {category: [snippets]}, error?}."""
    if categories is None:
        categories = QUERY_PROFILES['full_analysis']

    result: dict = {
        'ticker':   ticker.upper(),
        'form':     form_type,
        'date':     None,
        'sections': {},
        'source':   None,
    }

    filing = get_latest_filing(ticker, form_type)
    if not filing:
        result['error'] = f'לא נמצא {form_type} עבור {ticker}'
        return result

    result['date']   = filing['filing_date']
    result['source'] = filing['doc_url']

    time.sleep(RATE_SLEEP)
    try:
        r = requests.get(filing['doc_url'], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        raw = r.text
    except Exception as e:
        result['error'] = f'הורדת מסמך נכשלה: {e}'
        return result

    # הסרת HTML → טקסט נקי
    text = _strip_html(raw)

    # חיפוש keyword windows לכל קטגוריה
    for cat in categories:
        if cat not in KEYWORD_TAXONOMY:
            continue
        entry    = KEYWORD_TAXONOMY[cat]
        snippets = _find_keyword_windows(text, entry['keywords'])
        if snippets:
            # חיתוך כל snippet
            clipped = [s[:entry['max_chars']] for s in snippets]
            result['sections'][cat] = clipped

    return result


# ══════════════════════════════════════════════════════════════════════════════
# EARNINGS TRANSCRIPT FETCHER
# ══════════════════════════════════════════════════════════════════════════════

def fetch_earnings_transcript(ticker: str) -> dict:
    """מחפש תמליל earnings call אחרון.
    מקורות: Motley Fool (חינם, ללא key).
    מחזיר {ticker, date, text_excerpt, source, error?}."""
    tk = ticker.upper().strip()
    result: dict = {'ticker': tk, 'date': None, 'text_excerpt': '', 'source': None}

    # Motley Fool — תבנית URL ידועה לתמליל
    try:
        # חיפוש באמצעות EDGAR 8-K earnings press release כ-fallback
        time.sleep(RATE_SLEEP)
        search_url = (
            f'https://efts.sec.gov/LATEST/search-index?q=%22earnings+call%22'
            f'&entity={tk}&forms=8-K&dateRange=custom'
            f'&startdt={(datetime.now()-timedelta(days=120)).strftime("%Y-%m-%d")}'
        )
        r = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        hits = r.json().get('hits', {}).get('hits', [])
        if hits:
            hit = hits[0]
            result['date']   = hit.get('_source', {}).get('file_date', '')
            result['source'] = 'SEC EDGAR 8-K'
    except Exception:
        pass

    # Motley Fool transcript scrape
    try:
        mf_url = f'https://www.fool.com/quote/nasdaq/{tk.lower()}/#quote-earnings-transcripts'
        time.sleep(RATE_SLEEP)
        r2 = requests.get(mf_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r2.status_code == 200:
            text = _strip_html(r2.text)
            # חיפוש שמות סעיפים ידועים בתמליל
            all_kws = []
            for cat in ['call_guidance', 'call_metrics', 'call_qa']:
                all_kws += KEYWORD_TAXONOMY[cat]['keywords']
            snippets = _find_keyword_windows(text, all_kws, window=500)
            if snippets:
                result['text_excerpt'] = '\n\n'.join(snippets)[:MAX_TRANSCRIPT_CHARS]
                result['source'] = mf_url
    except Exception:
        pass

    return result


# ══════════════════════════════════════════════════════════════════════════════
# MAIN BUILDER — מחזיר בלוק context מוכן להזרקה
# ══════════════════════════════════════════════════════════════════════════════

def build_sec_context(ticker: str, profile: str = 'full_analysis',
                      include_transcript: bool = True) -> str:
    """Entry point ראשי. מחזיר string מוכן להזרקה ל-agent prompt.
    profile: מפתח ב-QUERY_PROFILES.
    מוגבל ל-MAX_TOTAL_CHARS בסיכום."""
    cats = QUERY_PROFILES.get(profile, QUERY_PROFILES['full_analysis'])
    parts = []

    # 10-Q (ראשון; אם לא קיים — נסה 10-K)
    data = fetch_filing_sections(ticker, '10-Q', cats)
    if data.get('error') or not data['sections']:
        data = fetch_filing_sections(ticker, '10-K', cats)

    if not data.get('error') and data['sections']:
        parts.append(f"📄 {data['form']} ({data['date']}) — מקור: {data['source']}")
        for cat, snippets in data['sections'].items():
            label = cat.replace('_', ' ').upper()
            parts.append(f'\n[{label}]')
            for s in snippets[:2]:  # מקסימום 2 snippets לקטגוריה
                parts.append(s[:KEYWORD_TAXONOMY[cat]['max_chars']])
    elif data.get('error'):
        parts.append(f'⚠️ {data["error"]}')

    # Transcript
    if include_transcript:
        tr = fetch_earnings_transcript(ticker)
        if tr.get('text_excerpt'):
            parts.append(f'\n📞 Earnings Call ({tr.get("date","—")}):')
            parts.append(tr['text_excerpt'][:MAX_TRANSCRIPT_CHARS])

    result = '\n'.join(parts)
    return result[:MAX_TOTAL_CHARS]


# ══════════════════════════════════════════════════════════════════════════════
# KEYWORD HELPER — לשימוש מ-review_layer
# ══════════════════════════════════════════════════════════════════════════════

def keywords_for_ticker(ticker: str, thesis_keywords: list = None) -> list[str]:
    """מחזיר רשימת מילות מפתח ממוקדות ל-ticker.
    משלב: keywords בסיסיים + ticker-specific + thesis keywords."""
    base = [
        'revenue', 'gross margin', 'operating income', 'free cash flow',
        'guidance', 'outlook', 'earnings per share',
    ]
    ticker_specific = {
        'AMZN':  ['aws', 'advertising revenue', 'third-party seller', 'capex'],
        'NVDA':  ['data center', 'compute', 'gaming', 'automotive', 'blackwell'],
        'MSFT':  ['azure', 'commercial cloud', 'intelligent cloud', 'productivity'],
        'GOOG':  ['google cloud', 'search revenue', 'youtube', 'advertising'],
        'META':  ['family daily active people', 'ad impressions', 'reality labs'],
        'AVGO':  ['semiconductor solutions', 'networking', 'vmware'],
        'MU':    ['dram', 'nand', 'hbm', 'data center memory'],
        'SOFI':  ['net interest margin', 'nim', 'deposits', 'members', 'technology platform'],
        'NOW':   ['crpo', 'remaining performance obligation', 'subscription', 'agentic'],
        'RKLB':  ['neutron', 'launch services', 'space systems', 'backlog'],
        'VST':   ['capacity factor', 'nuclear', 'retail electricity', 'hedge'],
        'IBIT':  ['bitcoin', 'btc', 'net asset value', 'shares outstanding'],
        'OKLO':  ['aurora', 'microreactor', 'loan agreement', 'doe'],
        'APLD':  ['gpu', 'hpc', 'data center', 'hosting revenue'],
    }
    tk = ticker.upper().strip()
    result = list(base)
    result += ticker_specific.get(tk, [])
    if thesis_keywords:
        result += [kw.lower() for kw in thesis_keywords[:4]]
    # de-dup תוך שמירת סדר
    seen = set()
    deduped = []
    for k in result:
        if k not in seen:
            seen.add(k)
            deduped.append(k)
    return deduped[:16]  # מקסימום 16 מילות מפתח


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import sys
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else 'NVDA'
    profile = sys.argv[2] if len(sys.argv) > 2 else 'quick_check'
    print(f'\n=== sec_fetcher: {ticker} / {profile} ===\n')
    ctx = build_sec_context(ticker, profile, include_transcript=True)
    print(ctx or '(ריק)')
    print(f'\n=== סה"כ: {len(ctx)} תווים ===')
