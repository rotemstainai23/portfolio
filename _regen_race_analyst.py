"""סקריפט חד-פעמי: מייצר מחדש את analyst.js עבור RACE מה-handoff הקיים."""
import sys, os
os.chdir(r'c:\Users\רותם\portfolio')
sys.path.insert(0, r'c:\Users\רותם\portfolio')

from app import _write_visual_js, _extract_dashboard_json, _extract_visual_scores

hf = r'c:\Users\רותם\portfolio\analyses\RACE\_handoffs\2026-06-01_analyst.md'
with open(hf, encoding='utf-8') as f:
    content = f.read()

dash = _extract_dashboard_json(content)
if not dash:
    print('ERROR: לא נמצא dashboard-json בקובץ')
    sys.exit(1)

vs = _extract_visual_scores(content)
if vs:
    dash['visual_scores'] = vs
    print(f'visual_scores נטענו: {list(vs.keys())}')
else:
    print('WARN: אין visual-scores — נמשיך ללא enrichment מספרי')

result = _write_visual_js('RACE', 'analyst', dash)
print('OK:', result)
