"""
סקנר שבתי — שבת 5:00.
מריץ את סוכן הסקנר ושולח 3 ההזדמנויות הטובות ביותר.
אם הסשן מקומי — קורא ל-Flask API.
אם GitHub Actions — מריץ ישירות דרך Anthropic SDK.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from notifications import send_both

SCANNER_RESULTS  = os.path.join(ROOT, 'scanner-results.json')
SUNDAY_TARGET    = os.path.join(ROOT, 'sunday-analysis-target.json')
SCANNER_ARCHIVE  = os.path.join(ROOT, 'analyses', '_monthly', '_scanner_archive')
MONTHLY_DIR      = os.path.join(ROOT, 'analyses', '_monthly')
FLASK_BASE       = os.environ.get('FLASK_BASE', 'http://127.0.0.1:5000')


# ── ארכיב + calibration ──────────────────────────────────────────────────────

def archive_scanner_results() -> None:
    """ארכב את תוצאות הסורק הקודמות לפני דריסה."""
    if not os.path.exists(SCANNER_RESULTS):
        return
    os.makedirs(SCANNER_ARCHIVE, exist_ok=True)
    date_str  = datetime.now().strftime('%Y-%m-%d')
    dest_path = os.path.join(SCANNER_ARCHIVE, f'scanner-{date_str}.json')
    try:
        with open(SCANNER_RESULTS, encoding='utf-8') as f:
            data = f.read()
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(data)
        print(f'[scanner] ארכב תוצאות ל-{dest_path}')
        # נקה ארכיב ישן מעבר ל-16 שבועות
        from glob import glob as _glob
        archives = sorted(_glob(os.path.join(SCANNER_ARCHIVE, 'scanner-*.json')))
        for old in archives[:-16]:
            os.remove(old)
    except Exception as e:
        print(f'[scanner] שגיאת ארכיב: {e}')


def load_calibration_context() -> str:
    """
    מחזיר בלוק טקסט עם ביצועי הסורק מהחודש האחרון.
    מוזרק ל-prompt הסורק כ-~300 טוקנים.
    """
    from glob import glob as _glob
    monthly_dirs = sorted(_glob(os.path.join(MONTHLY_DIR, '????-??')), reverse=True)
    for d in monthly_dirs:
        cal_path = os.path.join(d, 'scanner_calibration.json')
        if os.path.exists(cal_path):
            try:
                with open(cal_path, encoding='utf-8') as f:
                    cal = json.load(f)
                stats = cal.get('stats', {})
                period = cal.get('period', '')
                recs   = cal.get('recommendations', [])
                successes = [r['ticker'] for r in recs if r.get('outcome') == 'SUCCESS']
                failures  = [r['ticker'] for r in recs if r.get('outcome') == 'FAIL']
                lines = [
                    f'## כיול סורק — {period}',
                    f'Hit Rate: {stats.get("hit_rate_pct", "N/A")}% ({stats.get("successes", 0)}/{stats.get("evaluated", 0)} המלצות)',
                    f'תשואה ממוצעת: {stats.get("avg_return_pct", "N/A")}%',
                ]
                if successes:
                    lines.append(f'הצלחות: {", ".join(successes[:5])}')
                if failures:
                    lines.append(f'כישלונות: {", ".join(failures[:5])}')
                by_conv = stats.get('by_conviction', {})
                if by_conv:
                    conv_str = ' | '.join(f'conviction {k}: {v}%' for k, v in sorted(by_conv.items()))
                    lines.append(f'דיוק לפי conviction: {conv_str}')
                lines.append('התאם את ה-conviction שלך בהתאם לתוצאות אלה.')
                return '\n'.join(lines) + '\n\n'
            except Exception:
                pass
    return ''


# ── הפעלת סקנר ───────────────────────────────────────────────────────────────

def run_scanner_via_flask() -> list:
    """מריץ סקנר דרך Flask API (כשהשרת רץ מקומית)."""
    try:
        req = urllib.request.Request(
            f'{FLASK_BASE}/api/scanner/run',
            data=b'{}',
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.load(r)
        run_id = resp.get('run_id')
        if not run_id:
            return []
        print(f'[scanner] run_id={run_id} — ממתין לסיום...')
        # סקנר timeout 480 שניות — בדוק כל 30 שניות
        for _ in range(20):
            time.sleep(30)
            try:
                with urllib.request.urlopen(
                    f'{FLASK_BASE}/api/run-status/{run_id}', timeout=10
                ) as sr:
                    status = json.load(sr)
                if status.get('status') == 'done':
                    break
            except Exception:
                pass
        # קרא תוצאות
        with open(SCANNER_RESULTS, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'[scanner] Flask לא נגיש: {e}')
        return []


def run_scanner_via_sdk() -> list:
    """מריץ סקנר דרך Anthropic SDK (GitHub Actions / כשאין Flask)."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print('[scanner] אין ANTHROPIC_API_KEY — דלג על סקנר')
        return []
    try:
        import anthropic
        prompt_path = os.path.join(ROOT, 'מערכת תיק ההשקעות', 'Scanner_Agent.md')
        with open(prompt_path, encoding='utf-8') as f:
            system_prompt = f.read()

        portfolio_path = os.path.join(ROOT, 'portfolio.json')
        with open(portfolio_path, encoding='utf-8') as f:
            pf = json.load(f)
        holdings = [h.get('symbol') or h.get('ticker','') for h in pf.get('holdings', [])]
        calibration_ctx = load_calibration_context()
        context = (calibration_ctx
                   + f'תיק נוכחי (אל תמליץ על אלה): {", ".join(holdings)}\n'
                   + f'תאריך: {datetime.now().strftime("%Y-%m-%d")}')

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=2048,
            system=system_prompt,
            messages=[{'role': 'user', 'content': context}],
        )
        raw = msg.content[0].text.strip()
        # נקה backticks אם יש
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1]
        if raw.endswith('```'):
            raw = raw.rsplit('```', 1)[0]
        results = json.loads(raw)
        with open(SCANNER_RESULTS, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        return results
    except Exception as e:
        print(f'[scanner] SDK שגיאה: {e}')
        return []


def get_scanner_results() -> list:
    """נסה Flask קודם, אחר-כך SDK, לבסוף קרא קובץ קיים."""
    # נסה Flask
    results = run_scanner_via_flask()
    if results:
        return results
    # נסה SDK
    results = run_scanner_via_sdk()
    if results:
        return results
    # קרא קובץ קיים
    if os.path.exists(SCANNER_RESULTS):
        print('[scanner] משתמש בתוצאות קיימות')
        with open(SCANNER_RESULTS, encoding='utf-8') as f:
            return json.load(f)
    return []


# ── עיצוב הודעה ──────────────────────────────────────────────────────────────

def format_scanner_message(results: list) -> tuple[str, str]:
    today = datetime.now().strftime('%d/%m/%Y')
    # מיון לפי conviction יורד
    sorted_r = sorted(results, key=lambda x: x.get('conviction', 0), reverse=True)
    top3 = sorted_r[:3]

    # שמור top-1 לניתוח ראשון ביום ראשון
    if top3:
        with open(SUNDAY_TARGET, 'w', encoding='utf-8') as f:
            json.dump(top3[0], f, ensure_ascii=False, indent=2)
        print(f'[scanner] top pick לניתוח ראשון: {top3[0].get("ticker")}')

    lines_tg = [f'*סקנר שבתי — {today}*\n*3 ההזדמנויות לשבוע הקרוב:*\n']
    lines_wa = [f'סקנר שבתי {today}\n']

    for i, opp in enumerate(top3, 1):
        tk  = opp.get('ticker', '?')
        co  = opp.get('company', '')
        cat = opp.get('catalyst', '')
        con = opp.get('conviction', '?')
        up  = opp.get('upside_pct', '?')
        dn  = opp.get('downside_pct', '?')
        tf  = opp.get('timeframe', '')
        src = opp.get('source', '')

        lines_tg.append(
            f'*{i}. {tk}* ({co})\n'
            f'קטליסט: {cat}\n'
            f'Conviction: {con}/5 | Upside: {up}% | Downside: {dn}% | {tf}\n'
            f'מקור: {src}\n'
        )
        lines_wa.append(f'{i}. {tk} — {cat[:80]} (conviction {con}/5)')

    if not top3:
        lines_tg.append('לא נמצאו הזדמנויות ברמת conviction >= 3 השבוע.')
        lines_wa.append('לא נמצאו הזדמנויות השבוע.')

    return '\n'.join(lines_tg), '\n'.join(lines_wa)


# ── ריצה ─────────────────────────────────────────────────────────────────────

def main():
    print('[saturday_scanner] מתחיל...')
    archive_scanner_results()
    results = get_scanner_results()
    print(f'[saturday_scanner] נמצאו {len(results)} הזדמנויות')
    full_tg, short_wa = format_scanner_message(results)
    result = send_both(short_text=short_wa, full_text=full_tg)
    print(f'[saturday_scanner] נשלח: {result}')


if __name__ == '__main__':
    main()
