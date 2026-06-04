"""Review layer, שכבת קריאה בלבד לסקירת מניות.

מקבילה ל-obsidian_layer.py בכיוון הקריאה. אסור:
  * לקרוא קבצי handoff שלמים
  * לבצע listing של תיקיות
  * לקרוא קבצי append-only במלואם
  * לחרוג מ-5 שאילתות NotebookLM

אכיפת תקציב היא תנאי הכרחי לדטרמיניזם.
"""
import json
import os
import re
from collections import Counter
from datetime import datetime

import obsidian_layer

# תקציבי retrieval קשיחים, נאכפים בכל פונקציה
MAX_HUB_BYTES        = 16384   # קובץ hub שלם, hub אמור להיות קטן
MAX_USER_SECTION_LEN = 3000    # תווים בסעיף USER (אחרי חיתוך)
MAX_TAIL_BYTES       = 32768   # קריאת זנב מקובץ append-only
MAX_TAIL_LINES       = 80      # שורות מסעיף יחיד אחרון
MAX_KEYWORDS         = 8
MAX_QUERIES          = 5       # קשיח, אסור להגדיל
MAX_THESIS_CHARS     = 600     # קטיעת thesis לפני הזרקה ל-prompts

ROOT = os.path.dirname(os.path.abspath(__file__))


def _vault() -> str | None:
    """החזרת נתיב הכספת או None אם לא מוגדרת."""
    return obsidian_layer.get_vault_path()


def _hub_path(ticker: str) -> str | None:
    v = _vault()
    if not v:
        return None
    return os.path.join(v, 'Tickers', f'{ticker.upper().strip()}.md')


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """חילוץ frontmatter פשוט. מחזיר (dict, גוף ללא frontmatter).
    מינימליסטי, ללא תלות חיצונית. ערכי מחרוזת בלבד."""
    if not text.startswith('---'):
        return {}, text
    end = text.find('\n---', 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4:].lstrip('\n')
    fm = {}
    for line in fm_raw.splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, body


def read_hub(ticker: str) -> dict:
    """קריאת קובץ ה-hub של הטיקר. מחזיר:
      {exists, frontmatter, user_section, truncated}
    אם לא קיים, exists=False וכל היתר ריקים. תקציב: MAX_HUB_BYTES."""
    p = _hub_path(ticker)
    if not p or not os.path.exists(p):
        return {'exists': False, 'frontmatter': {}, 'user_section': '', 'truncated': False}
    size = os.path.getsize(p)
    with open(p, 'r', encoding='utf-8') as f:
        text = f.read(MAX_HUB_BYTES)
    truncated_hub = size > MAX_HUB_BYTES
    fm, body = _parse_frontmatter(text)

    # חילוץ סעיף USER, הכל מתחת ל-USER_MARKER, חתוך לאורך מקסימלי
    user_marker = obsidian_layer.USER_MARKER
    idx = body.find(user_marker)
    if idx == -1:
        user_section = ''
        truncated_user = False
    else:
        user_section = body[idx + len(user_marker):].strip()
        if len(user_section) > MAX_USER_SECTION_LEN:
            user_section = user_section[:MAX_USER_SECTION_LEN] + '\n[truncated by retrieval budget]'
            truncated_user = True
        else:
            truncated_user = False

    return {
        'exists': True,
        'frontmatter': fm,
        'user_section': user_section,
        'truncated': truncated_hub or truncated_user,
    }


def _tail_last_section(path: str) -> dict:
    """קריאת ה-`## ` האחרון מקובץ markdown ללא טעינת הקובץ כולו.
    תקציב: MAX_TAIL_BYTES מהזנב, MAX_TAIL_LINES שורות.
    מחזיר {exists, section, truncated} או exists=False."""
    if not os.path.exists(path):
        return {'exists': False, 'section': '', 'truncated': False}
    size = os.path.getsize(path)
    read_size = min(size, MAX_TAIL_BYTES)
    with open(path, 'rb') as f:
        f.seek(max(0, size - read_size))
        tail_bytes = f.read()

    # פענוח UTF-8 בטוח, ייתכן שהתחלנו באמצע תו רב-בייטי
    tail = None
    for skip in range(0, 5):
        try:
            tail = tail_bytes[skip:].decode('utf-8')
            break
        except UnicodeDecodeError:
            continue
    if tail is None:
        return {'exists': True, 'section': '', 'truncated': True}

    # מציאת המופע האחרון של "\n## "
    idx = tail.rfind('\n## ')
    if idx >= 0:
        section = tail[idx + 1:]
    elif tail.startswith('## '):
        section = tail
    else:
        # לא נמצאה כותרת בזנב, התקציב לא הספיק
        return {'exists': True, 'section': '', 'truncated': True}

    lines = section.splitlines()
    truncated = False
    if len(lines) > MAX_TAIL_LINES:
        lines = lines[:MAX_TAIL_LINES]
        lines.append('[truncated by retrieval budget]')
        truncated = True

    return {'exists': True, 'section': '\n'.join(lines).strip(), 'truncated': truncated}


def tail_decision(ticker: str) -> dict:
    """ההחלטה האחרונה מ-Decision History.md, ללא קריאת הקובץ כולו."""
    v = _vault()
    if not v:
        return {'exists': False, 'section': '', 'truncated': False}
    p = os.path.join(v, 'Tickers', ticker.upper().strip(), 'Decision History.md')
    return _tail_last_section(p)


def tail_thesis_evolution(ticker: str) -> dict:
    """שינוי ה-thesis האחרון, ללא קריאת הקובץ כולו."""
    v = _vault()
    if not v:
        return {'exists': False, 'section': '', 'truncated': False}
    p = os.path.join(v, 'Tickers', ticker.upper().strip(), 'Thesis Evolution.md')
    return _tail_last_section(p)


def latest_ic_dash(ticker: str) -> dict | None:
    """קריאת analyses/<T>/_reviews/ic.json אם קיים. ללא חיפושים נוספים."""
    p = os.path.join(ROOT, 'analyses', ticker.upper().strip(), '_reviews', 'ic.json')
    if not os.path.exists(p):
        return None
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


# חילוץ מילות מפתח דטרמיניסטי, ללא LLM
_KW_UPPER  = re.compile(r'\b[A-Z]{3,}(?:[A-Z0-9_]*)\b')
_KW_QUOTED = re.compile(r'"([^"\n]{3,60})"')
_KW_BOLD   = re.compile(r'\*\*([^*\n]{3,60})\*\*')
_KW_TITLE  = re.compile(r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b')

# הסרת stopwords מצומצמת לרעש שכיח
_STOP = {'The', 'And', 'But', 'For', 'With', 'This', 'That', 'From',
         'Have', 'Has', 'Was', 'Were', 'YES', 'NO', 'NA', 'IC', 'CEO'}


def extract_thesis_keywords(text: str, max_n: int = MAX_KEYWORDS) -> list[str]:
    """חילוץ מילות מפתח דטרמיניסטי מתוך טקסט thesis/hub.
    מקורות: UPPERCASE, "ציטוטים", **bold**, Title Case.
    ללא LLM, ללא קריאה לרשת."""
    if not text:
        return []
    found = []
    found += _KW_UPPER.findall(text)
    found += _KW_QUOTED.findall(text)
    found += _KW_BOLD.findall(text)
    found += _KW_TITLE.findall(text)
    cleaned = []
    seen_lower = set()
    for k in found:
        k = k.strip()
        if not k or k in _STOP:
            continue
        kl = k.lower()
        if kl in seen_lower:
            continue
        seen_lower.add(kl)
        cleaned.append(k)
    # דירוג לפי תדירות הופעה במקור
    freq = Counter(found)
    cleaned.sort(key=lambda x: -freq.get(x, 0))
    return cleaned[:max_n]


def build_query_pack(ticker: str, thesis_text: str, keywords: list[str],
                     last_review_date: str | None) -> dict:
    """בניית חבילת 5 שאילתות דטרמיניסטית ל-NotebookLM.
    קשיח: 5 שאילתות בדיוק, ללא חריגה.

    מבנה ה-prompts thesis-aware: keywords מוזרקים לתבניות קבועות.
    אם keywords ריק, נופלים חזרה ל-thesis_text מקוצר.
    אם גם הוא ריק, השאילתות מסומנות כ-NO_THESIS וה-skill חייב לעצור."""
    tk = ticker.upper().strip()
    thesis_short = (thesis_text or '').strip()[:MAX_THESIS_CHARS]
    if keywords:
        subject = ', '.join(keywords)
    elif thesis_short:
        subject = f'the documented thesis: "{thesis_short}"'
    else:
        subject = 'NO_THESIS'

    since = last_review_date or 'the previous review'

    pack = {
        'support': (
            f'For {tk}: cite specific evidence in the source documents that '
            f'directly SUPPORTS the following thesis components: {subject}. '
            f'For each point, quote a short phrase and name the source document '
            f'(filing, transcript, presentation). If no supporting evidence exists, reply N/A.'
        ),
        'contradict': (
            f'For {tk}: cite specific evidence in the source documents that '
            f'CONTRADICTS or WEAKENS the following thesis components: {subject}. '
            f'For each point, quote a short phrase and name the source document. '
            f'If none, reply N/A. Do not infer beyond the documents.'
        ),
        'changes_since': (
            f'For {tk}: list MATERIAL CHANGES since {since} that affect: {subject}. '
            f'Earnings beats/misses, revenue trajectory, margin shifts, leadership commentary, '
            f'customer wins/losses. Each item: short factual statement + source document name. '
            f'If none, reply N/A.'
        ),
        'risks_delta': (
            f'For {tk}: list NEW or ESCALATING RISK FACTORS in the latest filings/transcripts '
            f'that relate to: {subject}. Each item: short statement + source document. '
            f'Exclude boilerplate risks unchanged from prior filings. If none, reply N/A.'
        ),
        'guidance_delta': (
            f'For {tk}: list any FORWARD GUIDANCE updates (revenue, margins, capex, units) '
            f'affecting: {subject}. Each item: short factual statement + source document name '
            f'+ direction (raised/lowered/reaffirmed). If none, reply N/A.'
        ),
    }
    assert len(pack) == MAX_QUERIES, 'חריגה מתקציב השאילתות'
    return pack


def _format_evidence_items(items) -> list[str]:
    """פורמט פריטי evidence עם attribution חובה.
    כל פריט: {claim, source, strength?}.
    מחרוזת ריקה או רשימה ריקה → ['- N/A'].
    פריט ללא source → מסומן [no-source] (חולשה דיווח).
    strength='weak' או 'conflicting' → סימון אי-ודאות."""
    if not items:
        return ['- N/A']
    if isinstance(items, str):
        s = items.strip()
        if not s or s.upper() == 'N/A':
            return ['- N/A']
        return [f'- {s} [no-source]']
    out = []
    for it in items:
        if isinstance(it, str):
            s = it.strip()
            if not s or s.upper() == 'N/A':
                continue
            out.append(f'- {s} [no-source]')
            continue
        claim = (it.get('claim') or '').strip()
        source = (it.get('source') or '').strip()
        strength = (it.get('strength') or '').strip().lower()
        if not claim:
            continue
        line = f'- {claim}'
        if source:
            line += f' ({source})'
        else:
            line += ' [no-source]'
        if strength in ('weak', 'conflicting', 'uncertain'):
            line += f' [{strength}]'
        out.append(line)
    return out or ['- N/A']


def _confidence(evidence: dict, memory: dict) -> int:
    """חישוב confidence דטרמיניסטי 1-10.
    בסיס 6, מורידים על סתירות, מוסיפים על תמיכה ועדכניות.
    שום ניחוש סובייקטיבי."""
    score = 6
    support = evidence.get('support') or []
    contradict = evidence.get('contradict') or []
    risks = evidence.get('risks_delta') or []
    n_support    = len(support) if isinstance(support, list) else (0 if not support else 1)
    n_contradict = len(contradict) if isinstance(contradict, list) else (0 if not contradict else 1)
    n_risks      = len(risks) if isinstance(risks, list) else (0 if not risks else 1)
    score += min(2, n_support)
    score -= min(4, n_contradict)
    score -= min(2, n_risks)
    if not memory.get('hub_exists'):
        score -= 2
    if not memory.get('notebooklm_available'):
        score -= 2
    return max(1, min(10, score))


def _suggest_action(confidence: int, evidence: dict) -> str:
    """המלצה דטרמיניסטית. ללא חופש שיפוט."""
    contradict = evidence.get('contradict') or []
    n_contradict = len(contradict) if isinstance(contradict, list) else (1 if contradict else 0)
    if confidence >= 8 and n_contradict == 0:
        return 'Add'
    if confidence >= 6 and n_contradict <= 1:
        return 'Hold'
    if confidence >= 4:
        return 'Watch'
    return 'Reduce'


def synthesize(ticker: str, memory: dict, evidence: dict) -> str:
    """בניית output במבנה הקבוע. כל טענה מ-NotebookLM חייבת attribution.
    טענות ללא source מסומנות [no-source]. evidence חלקי → N/A מפורש."""
    tk = ticker.upper().strip()
    fm = memory.get('frontmatter') or {}
    user = memory.get('user_section') or ''
    last_decision = memory.get('last_decision') or ''
    last_thesis_evo = memory.get('last_thesis_evolution') or ''
    ic_dash = memory.get('ic_dash') or {}

    # current thesis: מקור 1 = IC dash thesis, מקור 2 = USER section, אחרת N/A
    current_thesis = (ic_dash.get('thesis') or '').strip()
    if not current_thesis and user:
        current_thesis = user[:400].strip()
    if not current_thesis:
        current_thesis = 'N/A'

    what_changed = last_thesis_evo.strip() if last_thesis_evo else 'N/A'

    conf = _confidence(evidence, memory)
    action = _suggest_action(conf, evidence)

    lines = []
    lines.append(f'Ticker: {tk}')
    lines.append('')
    lines.append('Current Thesis:')
    lines.append(current_thesis if current_thesis != 'N/A' else 'N/A')
    lines.append('')
    lines.append('What Changed:')
    lines.append(what_changed if what_changed != 'N/A' else 'N/A')
    lines.append('')
    lines.append('Evidence From NotebookLM:')
    lines.extend(_format_evidence_items(evidence.get('support')))
    lines.append('')
    lines.append('Material Changes:')
    lines.extend(_format_evidence_items(evidence.get('changes_since')))
    lines.append('')
    lines.append('Guidance Updates:')
    lines.extend(_format_evidence_items(evidence.get('guidance_delta')))
    lines.append('')
    lines.append('Contradictions:')
    lines.extend(_format_evidence_items(evidence.get('contradict')))
    lines.append('')
    lines.append('Thesis Break Signals:')
    contradict = evidence.get('contradict') or []
    risks = evidence.get('risks_delta') or []
    n_contradict = len(contradict) if isinstance(contradict, list) else (1 if contradict else 0)
    n_risks = len(risks) if isinstance(risks, list) else (1 if risks else 0)
    if n_contradict == 0 and n_risks == 0:
        lines.append('- None detected.')
    else:
        lines.append(f'- {n_contradict} contradiction(s), {n_risks} new/escalating risk(s).')
        lines.extend(_format_evidence_items(risks))
    lines.append('')
    lines.append(f'Suggested Action:')
    lines.append(action)
    lines.append('')
    lines.append(f'Confidence:')
    lines.append(f'{conf}/10')
    lines.append('')
    lines.append('---')
    lines.append('Notes:')
    if not memory.get('notebooklm_available'):
        lines.append('- NotebookLM notebook missing. Evidence sections are N/A by policy.')
    if not memory.get('hub_exists'):
        lines.append('- Vault hub missing. Memory sections are limited.')
    if memory.get('truncated'):
        lines.append('- Some memory sections were truncated by retrieval budget.')
    last_verdict = fm.get('verdict')
    if last_verdict:
        lines.append(f'- Last vault verdict: {last_verdict} ({fm.get("verdict_date", "?")}).')

    return '\n'.join(lines).rstrip() + '\n'


def append_review(ticker: str, output_text: str) -> dict:
    """append-only ל-Tickers/<T>/Reviews.md דרך obsidian_layer.
    שום rewriting. שום מחיקה. fail-soft."""
    tk = ticker.upper().strip()
    today = datetime.now().strftime('%Y-%m-%d')
    rel = f'Tickers/{tk}/Reviews.md'
    entry = f'## {today} - Review\n\n{output_text.strip()}\n'
    header = f'# {tk} - Reviews\n\n*Append-only log of /review runs. NotebookLM evidence + Obsidian memory synthesis.*'
    return obsidian_layer.append_only_write(rel, entry, header_if_new=header)


# נקודת כניסה אחת לסקיל, מצמצמת קריאות subprocess
def load_memory(ticker: str, notebooklm_available: bool) -> dict:
    """אגרגציה של כל מקורות הזיכרון בקריאה אחת. תקציב נאכף בתוך כל helper.
    מחזיר מבנה שמועבר ישירות ל-synthesize ול-build_query_pack."""
    hub = read_hub(ticker)
    decision = tail_decision(ticker)
    thesis_evo = tail_thesis_evolution(ticker)
    ic_dash = latest_ic_dash(ticker)

    # רצף טקסט לחילוץ keywords: USER section + thesis מ-IC dash
    kw_source = (hub.get('user_section') or '')
    if ic_dash and ic_dash.get('thesis'):
        kw_source += '\n' + str(ic_dash.get('thesis'))
    keywords = extract_thesis_keywords(kw_source)

    # תאריך הסקירה האחרונה לבניית changes_since
    last_review_date = (ic_dash or {}).get('date') or (hub.get('frontmatter') or {}).get('verdict_date')

    return {
        'hub_exists': hub['exists'],
        'frontmatter': hub.get('frontmatter') or {},
        'user_section': hub.get('user_section') or '',
        'last_decision': decision.get('section') or '',
        'last_thesis_evolution': thesis_evo.get('section') or '',
        'ic_dash': ic_dash,
        'keywords': keywords,
        'last_review_date': last_review_date,
        'notebooklm_available': notebooklm_available,
        'truncated': hub.get('truncated') or decision.get('truncated') or thesis_evo.get('truncated'),
    }
