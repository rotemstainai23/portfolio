"""
build_reviews_index.py
בונה analyses/_reviews_index.json מכל קבצי ic.json בתיקיות הסקירות.
מופעל אוטומטית מ-daily.yml לאחר הרצת הדוח היומי.
"""
import json
import os
import glob
import datetime

reviews = []
for path in sorted(glob.glob('analyses/*/_reviews/ic.json')):
    try:
        parts = path.replace('\\', '/').split('/')
        ticker = parts[1] if len(parts) > 1 else None
        if not ticker or ticker.startswith('_'):
            continue
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        summary = d.get('summary') or d.get('thesis') or d.get('investment_thesis') or d.get('rationale', '')
        if len(summary) > 300:
            summary = summary[:300]
        reviews.append({
            'ticker':    ticker,
            'verdict':   d.get('verdict', d.get('final_verdict', '')),
            'score':     d.get('score', d.get('final_score')),
            'generated': d.get('generated', d.get('date', '')),
            'summary':   summary,
        })
    except Exception as e:
        print(f'Skip {path}: {e}')

out = {
    'generated': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'reviews':   reviews,
}
os.makedirs('analyses', exist_ok=True)
with open('analyses/_reviews_index.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f'Reviews index: {len(reviews)} tickers')
