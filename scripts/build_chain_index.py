"""בונה analyses/_chain/index.json מכל chain.json קיים."""
import json, glob, os

items = []
for p in glob.glob('analyses/_chain/*/chain.json'):
    try:
        ticker = p.replace('\\', '/').split('/')[2]
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        items.append({
            'ticker': ticker,
            'generated': d.get('generated', ''),
            'ic_verdict': d.get('ic_verdict'),
            'ic_score': d.get('ic_score'),
        })
    except Exception as e:
        print(f'skip {p}: {e}')

items.sort(key=lambda x: x['generated'], reverse=True)
os.makedirs('analyses/_chain', exist_ok=True)
with open('analyses/_chain/index.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f'chain index: {len(items)} entries')
