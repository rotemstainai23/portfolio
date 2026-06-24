"""בונה analyses/_research/index.json מכל report.json קיים."""
import json, glob, os

items = []
for p in glob.glob('analyses/_research/*/report.json'):
    try:
        ticker = p.replace('\\', '/').split('/')[2]
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        items.append({'ticker': ticker, 'generated': d.get('generated', '')})
    except Exception as e:
        print(f'skip {p}: {e}')

items.sort(key=lambda x: x['generated'], reverse=True)
with open('analyses/_research/index.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False)
print(f'research index: {len(items)} entries')
