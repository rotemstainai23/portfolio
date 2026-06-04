"""vault_session_hook.py — Stop hook של Claude Code.
קורא את תמליל השיחה (CLAUDE_TRANSCRIPT_PATH), מחלץ סיכום,
וכותב note לכספת Obsidian תחת Meta/Sessions/.
מוגדר ב-.claude/settings.local.json תחת hooks.Stop.
"""
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))


def _load_config() -> dict:
    try:
        with open(os.path.join(ROOT, 'config.json'), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _atomic_write(path: str, content: str) -> None:
    import tempfile
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                    dir=os.path.dirname(path), suffix='.tmp') as t:
        t.write(content)
        tmp = t.name
    os.replace(tmp, path)


def _extract_summary(transcript_tail: str) -> dict:
    """מחלץ מידע בסיסי מסוף התמליל ללא קריאת Claude."""
    # קבצים שנשתנו
    changed = list(dict.fromkeys(re.findall(
        r'(?:Edit|Write|created|updated)\s+(?:successfully\s+)?(?:at\s+)?[`"]?([^\s`"\']+\.(?:py|html|json|md|js|txt))[`"]?',
        transcript_tail
    )))[:8]

    # tickers שהוזכרו
    tickers = list(dict.fromkeys(re.findall(r'\b([A-Z]{2,6})\b', transcript_tail)))
    tickers = [t for t in tickers if len(t) >= 2 and t not in
               {'OK', 'API', 'RTL', 'CSS', 'SQL', 'UI', 'UX', 'IC', 'CEO', 'MOC', 'AWS', 'YOY',
                'SSOT', 'LLM', 'CDN', 'WARN', 'POST', 'GET', 'PUT', 'NEW', 'OLD', 'ANY',
                'TRUE', 'FALSE', 'NULL', 'NOT', 'AND', 'FOR', 'THE', 'IS', 'IN', 'TO', 'AS'}
               ][:5]

    # נושא — שורה ראשונה לא ריקה מהמשתמש
    topic_match = re.search(r'"role":\s*"user"[^}]*"content":\s*"([^"]{10,120})"', transcript_tail)
    topic = topic_match.group(1)[:100] if topic_match else 'עדכון מערכת'

    return {'topic': topic, 'changed_files': changed, 'tickers': tickers}


def main():
    cfg = _load_config()
    if not cfg.get('obsidian_enabled', False) or cfg.get('obsidian_dry_run', True):
        return

    vault = cfg.get('obsidian_vault', '')
    if not vault or not os.path.isdir(vault):
        return

    transcript_path = os.environ.get('CLAUDE_TRANSCRIPT_PATH', '')
    if not transcript_path or not os.path.isfile(transcript_path):
        return

    try:
        with open(transcript_path, encoding='utf-8', errors='ignore') as f:
            raw = f.read()
    except Exception:
        return

    # קרא רק 4000 תו אחרון — מספיק לסיכום, לא שורף זיכרון
    tail = raw[-4000:]

    summary = _extract_summary(tail)
    if not summary['changed_files'] and not summary['tickers']:
        return  # שיחה ריקה / תצוגה בלבד — לא כותבים

    now = datetime.now()
    note_name = now.strftime('%Y-%m-%d_%H%M')
    note_path = os.path.join(vault, 'Meta', 'Sessions', f'{note_name}.md')

    # אל תדרוס session קיים (למקרה שהhook נקרא פעמיים)
    if os.path.exists(note_path):
        return

    ticker_links = ' '.join(f'[[{t}]]' for t in summary['tickers']) if summary['tickers'] else 'אין'
    files_list = '\n'.join(f'- `{f}`' for f in summary['changed_files']) if summary['changed_files'] else '- אין שינויים'

    content = (
        f'---\n'
        f'note_type: session\n'
        f'date: {now.strftime("%Y-%m-%d")}\n'
        f'time: {now.strftime("%H:%M")}\n'
        f'tickers: [{", ".join(summary["tickers"])}]\n'
        f'---\n\n'
        f'<!-- AUTO-GENERATED: DO NOT EDIT ABOVE -->\n\n'
        f'# Session {note_name}\n\n'
        f'**נושא:** {summary["topic"]}\n\n'
        f'**מניות שהוזכרו:** {ticker_links}\n\n'
        f'**קבצים שהשתנו:**\n{files_list}\n\n'
        f'<!-- USER SECTION BELOW: NEVER TOUCH -->\n'
        f'*<!-- הערות אישיות כאן -->*\n'
    )

    try:
        _atomic_write(note_path, content)
        # עדכן Research Logs
        logs_path = os.path.join(vault, 'Meta', 'Research Logs.md')
        if os.path.isfile(logs_path):
            with open(logs_path, encoding='utf-8') as f:
                logs = f.read()
            row = f'| {now.strftime("%Y-%m-%d %H:%M")} | session | [[{note_name}]] | {summary["topic"][:60]} |\n'
            _atomic_write(logs_path, logs + row)
    except Exception as e:
        print(f'[vault_session_hook] {e}', file=sys.stderr)


if __name__ == '__main__':
    main()
