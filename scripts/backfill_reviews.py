"""
backfill_reviews.py
-------------------
מייצר _reviews/*.json עבור טיקרים שיש להם קבצי JS אבל חסרים _reviews.
מחלץ נתונים מ-handoff fields בקבצי JS.

שימוש:
    python scripts/backfill_reviews.py          # כל הטיקרים החסרים
    python scripts/backfill_reviews.py NOW RKLB  # טיקרים ספציפיים
"""
import sys, os, re, json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSES = os.path.join(ROOT, 'analyses')
AGENT_ORDER = ['analyst', 'devils', 'ceo', 'executor', 'ic']


def extract_text(content: str, pattern: str) -> str | None:
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return None
    raw = m.group(1)
    # נקה HTML tags
    raw = re.sub(r'<[^>]+>', '', raw)
    raw = raw.replace('\\n', ' ').replace('\n', ' ').strip()
    return raw[:400] if raw else None


def extract_from_js(ticker: str, agent: str, content: str) -> dict:
    """חלץ שדות קומפקטיים מקובץ JS."""
    # handoff text (הכי אמין)
    handoff = extract_text(content, r"handoff\s*:\s*'(.*?)'")
    if not handoff:
        handoff = extract_text(content, r'handoff\s*:\s*"(.*?)"')

    # verdict
    ver_m = re.search(r'(APPROVED|BUY|SELL|HOLD|WAIT|AVOID|REVIEW|INTACT)', content)
    verdict_raw = ver_m.group(1) if ver_m else None
    # מפה ל-verdict רשמי
    verdict_map = {'APPROVED': 'BUY', 'BUY': 'BUY', 'SELL': 'SELL',
                   'HOLD': 'HOLD', 'WAIT': 'WAIT', 'AVOID': 'AVOID',
                   'REVIEW': 'REVIEW', 'INTACT': 'INTACT'}
    verdict = verdict_map.get(verdict_raw)

    # position size
    pos_m = re.search(r'(\d+)%\s*[·\-]\s*(Growth|Stability|Speculation)', content)
    if not pos_m:
        # ניסיון נוסף: "גודל: 5%"
        pos_m2 = re.search(r'גודל.*?(\d+)%', content)
        pos_pct = int(pos_m2.group(1)) if pos_m2 else None
    else:
        pos_pct = int(pos_m.group(1))

    # date — ניסה כמה פורמטים
    date_m = re.search(r"date\s*:\s*'(\d{1,2}[./]\d{1,2}[./]\d{4})'", content)
    if date_m:
        raw_date = date_m.group(1)
        # המר DD.MM.YYYY → YYYY-MM-DD
        parts = re.split(r'[./]', raw_date)
        if len(parts) == 3 and len(parts[2]) == 4:
            date_str = f'{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}'
        else:
            date_str = raw_date
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    # score מספרי
    score_m = re.search(r'ציון\s+(?:איכות|סיכון|כולל)[^0-9]*(\d+)', content)
    score = int(score_m.group(1)) if score_m else None

    # thesis — שורה ראשונה של handoff
    thesis = handoff[:150] if handoff else None

    return {
        'ticker': ticker,
        'agent': agent,
        'date': date_str,
        'verdict': verdict,
        'score': score,
        'thesis': thesis,
        'key_risks': [],
        'position_size_pct': pos_pct,
        'valuation_summary': None,
        'entry_exit_plan': None,
        'handoff_summary': handoff,
        '_backfilled': True,  # סמן שזה backfill ולא פלט ישיר של סוכן
    }


def needs_backfill(ticker: str) -> list[str]:
    """החזר רשימת סוכנים שחסרים להם reviews."""
    adir = os.path.join(ANALYSES, ticker)
    rev_dir = os.path.join(adir, '_reviews')
    missing = []
    for agent in AGENT_ORDER:
        js_path = os.path.join(adir, f'{agent}.js')
        rev_path = os.path.join(rev_dir, f'{agent}.json')
        if os.path.exists(js_path) and not os.path.exists(rev_path):
            missing.append(agent)
    return missing


def backfill_ticker(ticker: str, dry_run=False) -> dict:
    adir = os.path.join(ANALYSES, ticker)
    rev_dir = os.path.join(adir, '_reviews')
    missing = needs_backfill(ticker)

    if not missing:
        print(f'  {ticker}: כל ה-reviews קיימים — מדלג')
        return {'ticker': ticker, 'created': []}

    created = []
    for agent in missing:
        js_path = os.path.join(adir, f'{agent}.js')
        with open(js_path, encoding='utf-8', errors='replace') as f:
            content = f.read()

        data = extract_from_js(ticker, agent, content)
        rev_path = os.path.join(rev_dir, f'{agent}.json')

        if dry_run:
            print(f'  [DRY] {ticker}/{agent}: verdict={data["verdict"]} score={data["score"]} pos={data["position_size_pct"]}%')
        else:
            os.makedirs(rev_dir, exist_ok=True)
            with open(rev_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f'  OK {ticker}/{agent}: {rev_path}')
        created.append(agent)

    return {'ticker': ticker, 'created': created}


def main():
    tickers = sys.argv[1:] if len(sys.argv) > 1 else None

    if not tickers:
        # גלה אוטומטית כל הטיקרים החסרים
        tickers = []
        for d in sorted(os.listdir(ANALYSES)):
            if d.startswith('_') or not os.path.isdir(os.path.join(ANALYSES, d)):
                continue
            if needs_backfill(d):
                tickers.append(d)

    if not tickers:
        print('אין טיקרים שצריכים backfill.')
        return

    print(f'Backfilling reviews for: {", ".join(tickers)}')
    print()

    for ticker in tickers:
        print(f'{ticker}:')
        result = backfill_ticker(ticker)
        if result['created']:
            print(f'  נוצרו {len(result["created"])} קבצים: {", ".join(result["created"])}')
        print()

    print('סיום backfill.')


if __name__ == '__main__':
    main()
