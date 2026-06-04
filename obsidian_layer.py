"""Obsidian integration — Phase 1: vault_writer foundations.

Architecture (5 modules; Phase 1 implements vault_writer only, rest are stubs):
  - vault_writer        — atomic UTF-8 writes, AUTO/USER marker preservation,
                          dry-run mode, fail-soft logging, append-only helpers
  - wiki_linker         — Phase 2 (stub)
  - dataview_schema     — Phase 3 (stub)
  - dashboard_builder   — Phase 4 (stub)
  - maintenance         — Phase 5 (stub)

Guardrails (Phase 1):
  * Additive only — no destructive ops, no renames, no moves
  * AUTO/USER markers — code touches AUTO region only
  * Append-only — Decision History + Thesis Evolution never overwritten
  * Fail-soft — vault write errors logged but never block main chain
  * UTF-8 + atomic writes (tmp + os.replace) for all files
  * Dry-run mode — first run logs to portfolio/obsidian_dry_run.log only
"""
import json
import os
import re
import shutil
import tempfile
import time
from datetime import datetime

# ── Constants ───────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(ROOT, 'config.json')

# Marker pair: text BETWEEN markers is owned by code (replaced on every update).
# Text BELOW USER_MARKER is preserved verbatim across runs.
AUTO_MARKER = '<!-- AUTO-GENERATED: DO NOT EDIT ABOVE -->'
USER_MARKER = '<!-- USER SECTION BELOW: NEVER TOUCH -->'

# Used by Phase 5 maintenance to detect append-only files (refuse line deletions)
APPEND_ONLY_MARKER = '<!-- APPEND-ONLY HISTORY: never delete past entries -->'

# Dry-run log path (outside vault, never deleted by rollback)
DRY_RUN_LOG = os.path.join(ROOT, 'obsidian_dry_run.log')


# ── Config + enablement ─────────────────────────────────────────────────────
def _load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def get_vault_path() -> str | None:
    cfg = _load_config()
    p = cfg.get('obsidian_vault')
    if not p or not os.path.isdir(p):
        return None
    return p


def is_enabled() -> bool:
    return bool(_load_config().get('obsidian_enabled')) and get_vault_path() is not None


def is_dry_run() -> bool:
    """When True, no vault writes happen — all writes are logged to DRY_RUN_LOG."""
    return bool(_load_config().get('obsidian_dry_run', True))  # default True for safety


# ── Filename safety ─────────────────────────────────────────────────────────
_UNSAFE_FN_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')

def safe_filename(name: str, max_len: int = 200) -> str:
    """Replace unsafe Windows chars + control chars. Preserves Hebrew + spaces.
    Max length 200 to stay well below MAX_PATH = 260 even with nested folders."""
    s = _UNSAFE_FN_CHARS.sub('_', name).strip()
    # Don't allow trailing dots or spaces on Windows
    s = s.rstrip('. ')
    return s[:max_len]


def ascii_only(name: str) -> str:
    """For auto-generated artifact filenames — strictly ASCII + safe."""
    s = re.sub(r'[^A-Za-z0-9_\- ]', '_', name).strip().rstrip('. ')
    return s[:200]


# ── Atomic write + marker handling ──────────────────────────────────────────
def _atomic_write(path: str, content: str) -> int:
    """Write text to path atomically (temp + os.replace). Creates parent dirs.
    Returns bytes written. Raises on failure (caller is fail-soft)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    parent = os.path.dirname(path) or '.'
    # tempfile in same dir → os.replace is guaranteed atomic on same filesystem
    fd, tmp_path = tempfile.mkstemp(suffix='.tmp', dir=parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        os.replace(tmp_path, path)
        return len(content.encode('utf-8'))
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise


def _split_user_section(existing: str) -> tuple[str, str]:
    """Returns (everything BEFORE USER_MARKER, USER_MARKER + everything AFTER).
    If USER_MARKER absent, returns (existing, '')."""
    idx = existing.find(USER_MARKER)
    if idx == -1:
        return existing, ''
    return existing[:idx], existing[idx:]  # second part STARTS with USER_MARKER


def _build_managed_content(frontmatter_yaml: str, auto_body: str,
                           preserved_user: str = '') -> str:
    """Compose the full note content with marker pair.
    Layout:
        ---
        frontmatter
        ---

        <!-- AUTO-GENERATED: DO NOT EDIT ABOVE -->

        [auto_body — replaced on every update]

        <!-- USER SECTION BELOW: NEVER TOUCH -->

        [user content — preserved]
    """
    parts = []
    if frontmatter_yaml:
        fm = frontmatter_yaml.strip()
        if not fm.startswith('---'):
            fm = f'---\n{fm}\n---'
        parts.append(fm)
    parts.append('')
    parts.append(AUTO_MARKER)
    parts.append('')
    parts.append(auto_body.strip())
    parts.append('')
    if preserved_user:
        # preserved_user already starts with USER_MARKER (from _split_user_section)
        parts.append(preserved_user.lstrip())
    else:
        parts.append(USER_MARKER)
        parts.append('')
        parts.append('*<!-- כאן אתה יכול להוסיף הערות/הקשרים אישיים. הקוד לא יגע במה שמתחת לקו הזה. -->*')
        parts.append('')
    return '\n'.join(parts).rstrip() + '\n'


# ── Logging ────────────────────────────────────────────────────────────────
def log_event(message: str, kind: str = 'INFO') -> None:
    """Append one line to log. In dry-run → portfolio/obsidian_dry_run.log.
    Otherwise → vault Meta/Research Logs.md (also append-only)."""
    ts = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    line = f'{ts} [{kind}] {message}\n'
    if is_dry_run():
        try:
            with open(DRY_RUN_LOG, 'a', encoding='utf-8') as f:
                f.write(line)
        except Exception:
            pass
        return
    vault = get_vault_path()
    if not vault:
        return
    log_path = os.path.join(vault, 'Meta', 'Research Logs.md')
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        if not os.path.exists(log_path):
            header = (f'# Research Logs\n\n{APPEND_ONLY_MARKER}\n\n'
                      f'יומן אירועי כתיבה אוטומטיים מהמערכת. כל שורה היא event יחיד.\n\n'
                      f'| תאריך | סוג | הודעה |\n|---|---|---|\n')
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(header)
        # append as table row
        _msg_safe = message.replace('|', '\\|')
        row = f'| {ts} | {kind} | {_msg_safe} |\n'
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(row)
    except Exception as e:
        # log to dry-run log as fallback so we never lose visibility
        try:
            with open(DRY_RUN_LOG, 'a', encoding='utf-8') as f:
                f.write(f'{ts} [LOG_FAIL] {message} (reason: {e})\n')
        except Exception:
            pass


# ── Core writers ────────────────────────────────────────────────────────────
def write_managed_note(rel_path: str, frontmatter_yaml: str, auto_body: str) -> dict:
    """Write a marker-wrapped note. Preserves USER section if file exists.
    Returns {written, path, bytes, mode}. Fail-soft on errors."""
    vault = get_vault_path()
    if not vault:
        return {'written': False, 'reason': 'vault not configured'}

    full_path = os.path.join(vault, rel_path)
    # Read existing (preserve user section)
    preserved_user = ''
    existed = os.path.exists(full_path)
    if existed:
        try:
            with open(full_path, encoding='utf-8') as f:
                existing = f.read()
            _, preserved_user = _split_user_section(existing)
        except Exception as e:
            log_event(f'read failed for {rel_path}: {e}', 'WARN')

    new_content = _build_managed_content(frontmatter_yaml, auto_body, preserved_user)

    if is_dry_run():
        size = len(new_content.encode('utf-8'))
        preserved_size = len(preserved_user.encode('utf-8'))
        log_event(f'DRY-RUN would write: {rel_path}  ({size}B, '
                  f'{"UPDATE" if existed else "CREATE"}, preserved_user={preserved_size}B)', 'DRY')
        return {'written': False, 'dry_run': True, 'path': rel_path,
                'bytes': size, 'mode': 'UPDATE' if existed else 'CREATE',
                'preserved_user_bytes': preserved_size}

    try:
        bytes_written = _atomic_write(full_path, new_content)
        log_event(f'wrote {rel_path} ({bytes_written}B, '
                  f'{"UPDATE" if existed else "CREATE"})', 'WRITE')
        return {'written': True, 'path': rel_path, 'bytes': bytes_written,
                'mode': 'UPDATE' if existed else 'CREATE'}
    except Exception as e:
        log_event(f'write FAILED for {rel_path}: {e}', 'ERROR')
        return {'written': False, 'error': str(e), 'path': rel_path}


def append_only_write(rel_path: str, entry: str, header_if_new: str = '') -> dict:
    """For Decision History / Thesis Evolution. Never overwrites; only appends.
    `entry` should include any date heading like '## 2026-05-28'.
    `header_if_new` is the file header used only on first creation."""
    vault = get_vault_path()
    if not vault:
        return {'written': False, 'reason': 'vault not configured'}
    full_path = os.path.join(vault, rel_path)
    existed = os.path.exists(full_path)

    if is_dry_run():
        size = len(entry.encode('utf-8'))
        log_event(f'DRY-RUN would APPEND to {rel_path}  ({size}B added, '
                  f'{"to existing" if existed else "creating new"})', 'DRY')
        return {'written': False, 'dry_run': True, 'path': rel_path, 'bytes_added': size}

    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if not existed:
            initial = f'{header_if_new}\n\n{APPEND_ONLY_MARKER}\n\n' if header_if_new else f'{APPEND_ONLY_MARKER}\n\n'
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(initial)
        with open(full_path, 'a', encoding='utf-8') as f:
            f.write('\n' + entry.rstrip() + '\n')
        log_event(f'appended to {rel_path} (+{len(entry)}B)', 'APPEND')
        return {'written': True, 'path': rel_path, 'bytes_added': len(entry)}
    except Exception as e:
        log_event(f'append FAILED for {rel_path}: {e}', 'ERROR')
        return {'written': False, 'error': str(e), 'path': rel_path}


# ── YAML frontmatter (minimal, no external dep) ─────────────────────────────
def _yaml_escape(v) -> str:
    """Minimal YAML scalar serializer — handles str/num/bool/None/list."""
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return '[' + ', '.join(_yaml_escape(x) for x in v) + ']'
    s = str(v)
    # Quote if contains special chars
    if any(c in s for c in ':#\n"\'[]{}|>') or s != s.strip():
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    return s


def make_frontmatter(fields: dict) -> str:
    """Build YAML frontmatter block from a flat dict. Skips None values."""
    lines = ['---']
    for k, v in fields.items():
        if v is None or v == '':
            continue
        lines.append(f'{k}: {_yaml_escape(v)}')
    lines.append('---')
    return '\n'.join(lines)


# ── High-level archivers (Phase 1 set) ──────────────────────────────────────
def _date_today() -> str:
    return datetime.now().strftime('%Y-%m-%d')


def write_ticker_hub(ticker: str, dash: dict) -> dict:
    """Tickers/<TICKER>.md — entity hub. Idempotent (preserves USER section)."""
    tk = ticker.upper().strip()
    fm = make_frontmatter({
        'ticker':            tk,
        'sector':            dash.get('sector'),
        'verdict':           dash.get('verdict'),
        'verdict_date':      dash.get('date') or _date_today(),
        'score':             dash.get('score'),
        'position_size_pct': dash.get('position_size_pct'),
        'valuation_summary': dash.get('valuation_summary'),
        'last_chain_run':    _date_today(),
        'note_type':         'ticker-hub',
    })
    body = []
    body.append(f'# {tk}')
    body.append('')
    if dash.get('company'):
        body.append(f'**Company:** {dash["company"]}')
    if dash.get('thesis'):
        body.append(f'**Thesis:** {dash["thesis"]}')
    if dash.get('valuation_summary'):
        body.append(f'**Valuation:** {dash["valuation_summary"]}')
    if dash.get('entry_exit_plan'):
        body.append(f'**Entry/Exit:** {dash["entry_exit_plan"]}')
    body.append('')
    body.append(f'**Latest verdict:** {dash.get("verdict", "—")} · ציון {dash.get("score", "—")}/100 · גודל {dash.get("position_size_pct", "—")}%')
    body.append('')
    if dash.get('key_risks'):
        body.append('## Key Risks')
        for r in dash['key_risks'][:6]:
            body.append(f'- {r}')
        body.append('')
    body.append('## Research Index')
    body.append('*Phase 1: links to artifacts written below. Phase 3 will add live Dataview tables here.*')
    body.append('')
    body.append(f'- 📊 **Full Chains:** `Tickers/{tk}/Full Chain/`')
    body.append(f'- ⚡ **Quick Checks:** `Tickers/{tk}/Quick Checks/`')
    body.append(f'- 🔄 **Re-checks:** `Tickers/{tk}/Re-checks/`')
    body.append(f'- ⚖️ **Committee:** `Tickers/{tk}/Committee/`')
    body.append(f'- 📜 **Decision History:** [[{tk}/Decision History]]')
    body.append(f'- 🧬 **Thesis Evolution:** [[{tk}/Thesis Evolution]]')
    body.append(f'- 📁 **All Handoffs:** `Tickers/{tk}/Handoffs/`')

    rel = f'Tickers/{tk}.md'
    return write_managed_note(rel, fm, '\n'.join(body))


def archive_handoff(ticker: str, agent: str, date: str, content: str) -> dict:
    """Mirror a per-agent handoff into vault. Whole file is auto (no user section)."""
    tk = ticker.upper().strip()
    ag = ascii_only(agent.lower())
    d  = ascii_only(date)
    rel = f'Tickers/{tk}/Handoffs/{ag}/{d}_{ag}.md'
    fm = make_frontmatter({
        'ticker': tk, 'agent': ag, 'date': d, 'note_type': 'handoff',
    })
    return write_managed_note(rel, fm, content)


def archive_full_chain(ticker: str, run_date: str, handoffs_map: dict, dash_by_agent: dict = None) -> dict:
    """Bundle all 5 agent handoffs from one chain run into ONE consolidated note.
    handoffs_map: {agent_name: raw_handoff_markdown}
    dash_by_agent: optional {agent: dashboard-json dict} for summary headers."""
    tk = ticker.upper().strip()
    d  = ascii_only(run_date)
    rel = f'Tickers/{tk}/Full Chain/{d}_full-chain.md'

    fm = make_frontmatter({
        'ticker': tk, 'date': d, 'note_type': 'full-chain',
        'agents': list(handoffs_map.keys()),
    })

    body = [f'# {tk} — Full Chain · {d}', '']
    body.append(f'**Run date:** {d}')
    body.append(f'**Agents completed:** {len(handoffs_map)} of 5')
    body.append('')
    body.append('## Summary per agent')
    for ag in ('analyst', 'devils', 'ceo', 'executor', 'ic'):
        if dash_by_agent and ag in dash_by_agent:
            d2 = dash_by_agent[ag]
            verdict = d2.get('verdict', '—')
            score = d2.get('score', '—')
            body.append(f'- **{ag}:** verdict={verdict}, score={score}/100')
        elif ag in handoffs_map:
            body.append(f'- **{ag}:** completed (no dashboard-json)')
        else:
            body.append(f'- **{ag}:** *(missing)*')
    body.append('')
    body.append('## Handoffs (raw)')
    for ag, content in handoffs_map.items():
        body.append('')
        body.append(f'### {ag}')
        body.append('')
        body.append(content.strip())
        body.append('')
    body.append('---')
    body.append(f'**Cross-links:** [[{tk}]] · [[{tk}/Decision History]] · [[{tk}/Thesis Evolution]]')

    return write_managed_note(rel, fm, '\n'.join(body))


def archive_quick_check(ticker: str, dash: dict, content: str) -> dict:
    """Quick-mode artifact."""
    tk = ticker.upper().strip()
    d  = ascii_only(dash.get('date') or _date_today())
    rel = f'Tickers/{tk}/Quick Checks/{d}_quick-check.md'
    fm = make_frontmatter({
        'ticker': tk, 'date': d, 'note_type': 'quick-check',
        'verdict': dash.get('verdict'), 'score': dash.get('score'),
    })
    return write_managed_note(rel, fm, content)


def archive_committee(ticker: str, dash: dict, content: str) -> dict:
    """IC handoff as standalone committee snapshot."""
    tk = ticker.upper().strip()
    d  = ascii_only(dash.get('date') or _date_today())
    rel = f'Tickers/{tk}/Committee/{d}_committee.md'
    fm = make_frontmatter({
        'ticker': tk, 'date': d, 'note_type': 'committee',
        'verdict': dash.get('verdict'), 'score': dash.get('score'),
        'position_size_pct': dash.get('position_size_pct'),
    })
    return write_managed_note(rel, fm, content)


def append_decision(ticker: str, dash: dict, source_full_chain: str = None) -> dict:
    """Append-only Decision History entry. Idempotent: skips if the same heading
    line (## date — verdict · ציון N/100 · גודל P%) already exists in the file."""
    tk = ticker.upper().strip()
    d  = dash.get('date') or _date_today()
    verdict = dash.get('verdict', '—')
    score   = dash.get('score', '—')
    pos     = dash.get('position_size_pct', '—')
    plan    = dash.get('entry_exit_plan', '')

    heading = f'## {d} — {verdict} · ציון {score}/100 · גודל {pos}%'
    entry   = heading + '\n'
    if source_full_chain:
        entry += f'**מקור:** [[{source_full_chain}]]\n'
    if plan:
        entry += f'**Entry/Exit:** {plan}\n'
    if dash.get('handoff_summary'):
        entry += f'**Summary:** {dash["handoff_summary"][:400]}\n'

    rel = f'Tickers/{tk}/Decision History.md'
    # Dedup: if this exact heading already exists in the file, skip the append.
    vault = get_vault_path()
    if vault:
        full = os.path.join(vault, rel)
        if os.path.exists(full):
            try:
                with open(full, encoding='utf-8') as f:
                    existing = f.read()
                if heading in existing:
                    log_event(f'decision append skipped (duplicate): {tk} {d} {verdict}', 'SKIP')
                    return {'written': False, 'reason': 'duplicate heading — skipped',
                            'path': rel, 'heading': heading}
            except Exception:
                pass  # fall through to normal append

    header = f'# {tk} — Decision History\n\n*Append-only chronicle of every committee decision.*'
    return append_only_write(rel, entry, header_if_new=header)


def append_thesis_change(ticker: str, prev_thesis: str, new_thesis: str,
                         source: str = None) -> dict:
    """Append-only Thesis Evolution entry. Only writes if thesis actually changed."""
    if (prev_thesis or '').strip() == (new_thesis or '').strip():
        return {'written': False, 'reason': 'thesis unchanged — no append'}

    tk = ticker.upper().strip()
    d  = _date_today()

    entry = f'## {d}\n'
    if source:
        entry += f'**Source:** [[{source}]]\n'
    if prev_thesis:
        entry += f'\n**Previous:** {prev_thesis.strip()[:600]}\n'
    if new_thesis:
        entry += f'\n**New:** {new_thesis.strip()[:600]}\n'

    rel = f'Tickers/{tk}/Thesis Evolution.md'
    header = f'# {tk} — Thesis Evolution\n\n*Append-only diff log of thesis changes between runs.*'
    return append_only_write(rel, entry, header_if_new=header)


# ── Schema doc (one-time write to Meta/) ────────────────────────────────────
def write_schema_doc() -> dict:
    """Documents the frontmatter contract used across the vault. Phase 1 baseline."""
    rel = 'Meta/Schema.md'
    fm = make_frontmatter({'note_type': 'schema-doc'})
    body = """# Vault Schema

*תיעוד ה-frontmatter contract של המערכת. כל הקבצים האוטומטיים מצייתים לזה.*

## Common fields
- `ticker` (string, uppercase) — symbol
- `note_type` (enum) — one of: `ticker-hub`, `handoff`, `full-chain`, `quick-check`,
  `committee`, `decision-history`, `thesis-evolution`, `moc`, `dashboard`, `schema-doc`
- `date` (YYYY-MM-DD) — note date
- `agent` (enum) — `analyst | devils | ceo | executor | ic | quick`

## Hub-specific (Tickers/<T>.md)
- `verdict`, `verdict_date`, `score`, `position_size_pct`
- `valuation_summary`, `last_chain_run`
- (Phase 3 adds: `fair_value`, `trigger_price`, `themes`, `next_review`,
  `moat_score`, `ai_exposure`, `thesis_status`)

## Conventions
- All auto notes have an AUTO/USER marker pair. Code touches only AUTO region.
- Append-only files: `Decision History.md`, `Thesis Evolution.md`, `Meta/Research Logs.md`.
- Filenames for auto-generated artifacts are ASCII only (Hebrew breaks RTL on Windows).
"""
    return write_managed_note(rel, fm, body)


# ── Hook entry points (called from app.py) ──────────────────────────────────
def on_save_handoff(ticker: str, agent: str, content: str, dash: dict) -> dict:
    """Called by app._save_handoff after the .md/_reviews/.js are written.
    Fail-soft: any error logged, never re-raised."""
    if not is_enabled():
        return {'skipped': True, 'reason': 'obsidian disabled'}
    results = {}
    try:
        date = (dash or {}).get('date') or _date_today()
        # 1. mirror handoff
        results['handoff'] = archive_handoff(ticker, agent, date, content)
        # 2. agent-specific routing
        if agent == 'quick':
            results['quick'] = archive_quick_check(ticker, dash or {}, content)
        elif agent == 'ic':
            # committee snapshot + decision history + thesis evolution
            results['committee'] = archive_committee(ticker, dash or {}, content)
            results['decision']  = append_decision(ticker, dash or {})
            # thesis evolution: compare to previous IC dashboard if available
            try:
                prev_path = _previous_ic_review(ticker)
                if prev_path:
                    with open(prev_path, encoding='utf-8') as f:
                        prev = json.load(f)
                    results['thesis_evo'] = append_thesis_change(
                        ticker, prev.get('thesis', ''), (dash or {}).get('thesis', ''),
                        source=f'Tickers/{ticker.upper()}/Committee/{date}_committee',
                    )
            except Exception as e:
                log_event(f'thesis evolution skipped for {ticker}: {e}', 'WARN')
        # 3. always refresh hub note (uses latest dash regardless of agent)
        if agent == 'ic':
            results['hub'] = write_ticker_hub(ticker, dash or {})
        # תמיד מרענן את הדוסייה הדחוסה — rule-based, ללא טוקנים
        results['dossier'] = generate_compact_dossier(ticker)
    except Exception as e:
        log_event(f'on_save_handoff EXCEPTION for {ticker}/{agent}: {e}', 'ERROR')
        results['exception'] = str(e)
    return results


def save_health_report(report: dict) -> dict:
    """כותב דוח בריאות תיק לכספת Obsidian תחת Meta/Health Reports/. Fail-soft."""
    if not is_enabled():
        return {'skipped': True}
    cfg = _load_config()
    vault = cfg.get('obsidian_vault', '')
    if not vault or not os.path.isdir(vault):
        return {'skipped': True, 'reason': 'vault not found'}
    dry_run = cfg.get('obsidian_dry_run', True)

    now_str = f'{report.get("run_date","")} {report.get("run_time","")}'.strip()
    note_name = now_str.replace(' ', '_').replace(':', '')
    note_path = os.path.join(vault, 'Meta', 'Health Reports', f'{note_name}.md')

    STATUS_ICON = {'INTACT': '🟢', 'REVIEW': '🟡', 'RERUN': '🔴', 'URGENT': '🚨'}
    results = report.get('results', [])
    summary = report.get('summary', {})

    rows = []
    for r in results:
        icon = STATUS_ICON.get(r.get('status', ''), '⚪')
        ticker_link = f'[[{r["ticker"]}]]' if r.get('ticker') else '-'
        concern = r.get('concern') or '—'
        catalyst = r.get('next_catalyst') or '—'
        action = r.get('action', '-')
        rows.append(f'| {ticker_link} | {icon} {r.get("status","-")} | {concern} | {catalyst} | {action} |')

    table = (
        '| טיקר | סטטוס | חדשות/בעיה | קטליזטור קרוב | פעולה |\n'
        '|------|--------|------------|---------------|--------|\n' +
        '\n'.join(rows)
    )

    content = (
        f'---\n'
        f'note_type: health-report\n'
        f'date: {report.get("run_date","")}\n'
        f'intact: {summary.get("intact",0)}\n'
        f'review: {summary.get("review",0)}\n'
        f'rerun: {summary.get("rerun",0)}\n'
        f'urgent: {summary.get("urgent",0)}\n'
        f'---\n\n'
        f'{AUTO_MARKER}\n\n'
        f'# בדיקת בריאות תיק — {now_str}\n\n'
        f'**סיכום:** '
        f'🟢 {summary.get("intact",0)} INTACT | '
        f'🟡 {summary.get("review",0)} REVIEW | '
        f'🔴 {summary.get("rerun",0)} RERUN | '
        f'🚨 {summary.get("urgent",0)} URGENT\n\n'
        f'{table}\n\n'
        f'{USER_MARKER}\n'
        f'*<!-- הערות אישיות על הבדיקה הזו -->*\n'
    )

    try:
        if not dry_run:
            os.makedirs(os.path.dirname(note_path), exist_ok=True)
            _atomic_write(note_path, content)
        # עדכן Research Logs
        logs_path = os.path.join(vault, 'Meta', 'Research Logs.md')
        if os.path.isfile(logs_path) and not dry_run:
            with open(logs_path, encoding='utf-8') as f:
                logs = f.read()
            urgent_flag = ' 🚨' if summary.get('urgent', 0) > 0 else ''
            row = f'| {now_str} | health-check{urgent_flag} | [[{note_name}]] | {report.get("tickers_checked",0)} tickers checked |\n'
            _atomic_write(logs_path, logs + row)
        return {'ok': True, 'path': note_path, 'dry_run': dry_run}
    except Exception as e:
        log_event(f'save_health_report EXCEPTION: {e}', 'ERROR')
        return {'exception': str(e)}


def on_chain_complete(ticker: str, run_date: str, handoffs_map: dict,
                      dash_by_agent: dict = None) -> dict:
    """Called by app._run_agent_thread when chain status='done'.
    handoffs_map: {agent: raw_md_content}. dash_by_agent: {agent: dash dict}."""
    if not is_enabled():
        return {'skipped': True, 'reason': 'obsidian disabled'}
    try:
        result = archive_full_chain(ticker, run_date, handoffs_map, dash_by_agent)
    except Exception as e:
        log_event(f'on_chain_complete EXCEPTION for {ticker}: {e}', 'ERROR')
        return {'exception': str(e)}
    # Phase 3: wiki linking + MOC update (fail-soft)
    try:
        wiki_linker.scan_and_link()
    except Exception as e:
        print(f'[wiki_linker on_chain_complete] {e}')
    return result


# ── Helpers ─────────────────────────────────────────────────────────────────
def _previous_ic_review(ticker: str) -> str | None:
    """Return path to previous IC _reviews/ic.json (BEFORE the one we just wrote).
    Phase 1 simplification: just returns current ic.json path; thesis-change diff
    compares latest-saved vs in-memory dash. Refined in Phase 3."""
    p = os.path.join(ROOT, 'analyses', ticker.upper(), '_reviews', 'ic.json')
    return p if os.path.exists(p) else None


# ── Phase 2: vault_reader — compact context for agent injection ───────────────
class vault_reader:
    """Reads prior knowledge from vault and returns compact context strings.
    Goal: replace repeated heavy analysis with ~600-token summaries → saves tokens.
    Fail-soft: any error returns '' so agents always get at least empty context."""

    @staticmethod
    def _read_file(rel_path: str) -> str:
        vault = get_vault_path()
        if not vault:
            return ''
        full = os.path.join(vault, rel_path)
        if not os.path.exists(full):
            return ''
        try:
            with open(full, encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ''

    @staticmethod
    def _extract_frontmatter(content: str) -> dict:
        """Parse simple YAML frontmatter (--- block at top). Returns {} on fail."""
        if not content.startswith('---'):
            return {}
        end = content.find('\n---', 3)
        if end == -1:
            return {}
        block = content[3:end].strip()
        result = {}
        for line in block.splitlines():
            if ':' in line:
                k, _, v = line.partition(':')
                result[k.strip()] = v.strip().strip('"')
        return result

    @staticmethod
    def _last_n_entries(content: str, n: int = 3) -> str:
        """Extract last N ## sections from append-only files."""
        import re
        sections = re.split(r'\n(?=## )', content)
        real = [s for s in sections if s.strip().startswith('## ')]
        last = real[-n:] if len(real) >= n else real
        return '\n'.join(last).strip()

    @classmethod
    def load_ticker_context(cls, ticker: str, max_chars: int = 2400) -> str:
        """מחזיר בלוק ידע קומפקטי להזרקה לפרומפט הסוכן.
        מקור עדיפות: Compressed Dossier (AUTO section) → Hub note fallback.
        Fail-soft: שגיאה מחזירה ''."""
        if not is_enabled():
            return ''
        tk = ticker.upper().strip()
        try:
            # נסה קודם את הדוסייה הדחוסה — היא כבר מוכנה ומקיפה
            dossier = cls._read_file(f'Tickers/{tk}/Compressed Dossier.md')
            if dossier:
                # שלוף רק את ה-AUTO section (בין הmarkers)
                start = dossier.find(AUTO_MARKER)
                end   = dossier.find(USER_MARKER)
                if start != -1:
                    body = dossier[start + len(AUTO_MARKER):end if end != -1 else len(dossier)]
                    body = body.strip()
                    if body:
                        return body[:max_chars]

            # Fallback: hub note (גרסה ישנה לפני שנוצר הדוסייה)
            import re as _re
            hub = cls._read_file(f'Tickers/{tk}.md')
            if not hub:
                return ''
            fm = cls._extract_frontmatter(hub)
            lines = []

            verdict = fm.get('verdict', '—')
            score   = fm.get('score', '—')
            v_date  = fm.get('verdict_date') or fm.get('last_chain_run', '—')
            pos     = fm.get('position_size_pct', '—')
            lines.append(f'📋 פסיקה אחרונה: {verdict} | ציון {score}/100 | גודל {pos}% | תאריך {v_date}')

            thesis_m = _re.search(r'\*\*Thesis:\*\*\s*(.+?)(?=\n\*\*|\n##|\Z)', hub, _re.DOTALL)
            if thesis_m:
                lines.append(f'🧬 תזה: {thesis_m.group(1).strip().replace(chr(10), " ")[:500]}')

            val_m = _re.search(r'\*\*Valuation:\*\*\s*(.+?)(?=\n\*\*|\n##|\Z)', hub, _re.DOTALL)
            if val_m:
                lines.append(f'💰 שווי: {val_m.group(1).strip().replace(chr(10), " ")[:300]}')

            ee_m = _re.search(r'\*\*Entry/Exit:\*\*\s*(.+?)(?=\n\*\*|\n##|\Z)', hub, _re.DOTALL)
            if ee_m:
                lines.append(f'🎯 כניסה/יציאה: {ee_m.group(1).strip().replace(chr(10), " ")[:300]}')

            risks_m = _re.search(r'## Key Risks\n(.*?)(?=\n##|\n<!--|\Z)', hub, _re.DOTALL)
            if risks_m:
                risks = [r2.lstrip('- ').strip() for r2 in
                         risks_m.group(1).strip().splitlines()
                         if r2.strip().startswith('-')][:3]
                if risks:
                    lines.append('⚠️ סיכונים:')
                    for r2 in risks:
                        lines.append(f'  • {r2[:180]}')

            dec = cls._read_file(f'Tickers/{tk}/Decision History.md')
            if dec:
                last_dec = cls._last_n_entries(dec, 2)
                if last_dec:
                    lines.append('📜 החלטות אחרונות:')
                    lines.append(last_dec[:600])

            return '\n'.join(lines)[:max_chars]
        except Exception as e:
            log_event(f'vault_reader.load_ticker_context failed for {ticker}: {e}', 'WARN')
            return ''

    @classmethod
    def load_portfolio_context(cls, max_chars: int = 1500) -> str:
        """Return compact portfolio-level context from Portfolio Hub."""
        if not is_enabled():
            return ''
        try:
            hub = cls._read_file('Portfolio Hub.md')
            if hub:
                auto_start = hub.find(AUTO_MARKER)
                user_start = hub.find(USER_MARKER)
                if auto_start != -1:
                    end = user_start if user_start != -1 else len(hub)
                    return hub[auto_start + len(AUTO_MARKER):end].strip()[:max_chars]
            return ''
        except Exception as e:
            log_event(f'vault_reader.load_portfolio_context failed: {e}', 'WARN')
            return ''


# ── Portfolio Hub ─────────────────────────────────────────────────────────────
def write_portfolio_hub(holdings: list, cash: float = 0.0) -> dict:
    """Write/update Portfolio Hub.md — living master note with all holdings."""
    vault = get_vault_path()
    if not vault:
        return {'written': False, 'reason': 'vault not configured'}

    fm = make_frontmatter({
        'note_type': 'portfolio-hub',
        'updated':   _date_today(),
        'cash_usd':  cash,
        'holdings_count': len(holdings),
    })

    body = ['# Portfolio Hub', '', f'*עדכון אחרון: {_date_today()} | {len(holdings)} החזקות*', '']

    body.append('## החזקות')
    body.append('')
    body.append('| מניה | שם | Layer | Sector | קניה $ | ציון | פסיקה | קישור |')
    body.append('|---|---|---|---|---|---|---|---|')

    for h in sorted(holdings, key=lambda x: x.get('layer', '')):
        tk      = h.get('symbol', '').upper()
        name    = h.get('name', '')[:22]
        layer   = h.get('layer', '—')
        sector  = h.get('sector', '—')[:20]
        buy     = h.get('buy_price', 0)
        score   = str(h.get('analyst_score', '—'))

        hub_content = vault_reader._read_file(f'Tickers/{tk}.md')
        verdict = '—'
        if hub_content:
            fm_h = vault_reader._extract_frontmatter(hub_content)
            verdict = fm_h.get('verdict', '—')
            vault_score = fm_h.get('score')
            if vault_score:
                score = vault_score

        body.append(f'| **{tk}** | {name} | {layer} | {sector} | ${buy:,.2f} | {score} | {verdict} | [[Tickers/{tk}|{tk}]] |')

    body.append('')
    if cash:
        body.append(f'💵 **מזומן:** ${cash:,.2f}')
    body.append('')

    layers: dict = {}
    for h in holdings:
        l = h.get('layer', 'Other')
        layers[l] = layers.get(l, 0) + 1
    body.append('## הקצאה לפי Layer')
    body.append('')
    for l, cnt in sorted(layers.items()):
        pct = cnt / len(holdings) * 100
        body.append(f'- **{l}:** {cnt} ({pct:.0f}%)')
    body.append('')

    verdict_map: dict = {}
    for h in holdings:
        tk = h.get('symbol', '').upper()
        hc = vault_reader._read_file(f'Tickers/{tk}.md')
        if hc:
            fm_h = vault_reader._extract_frontmatter(hc)
            v = fm_h.get('verdict', 'לא נותח')
            verdict_map.setdefault(v, []).append(tk)
        else:
            verdict_map.setdefault('לא נותח', []).append(tk)

    body.append('## מבט מהיר על פסיקות')
    body.append('')
    for v, tks in sorted(verdict_map.items()):
        body.append(f'- **{v}:** {", ".join(tks)}')
    body.append('')
    body.append('*לינקים: ' + ' · '.join(f'[[Tickers/{h["symbol"].upper()}|{h["symbol"].upper()}]]' for h in holdings) + '*')

    return write_managed_note('Portfolio Hub.md', fm, '\n'.join(body))


# ── Backfill — sync existing analyses/ into vault ────────────────────────────
def backfill_from_analyses(analyses_dir: str = None, portfolio_json: str = None) -> dict:
    """Idempotent sync: reads every analyses/<TICKER>/ and writes vault notes.
    Safe to re-run — existing USER sections preserved, append-only files de-duped."""
    if not is_enabled():
        return {'skipped': True, 'reason': 'obsidian disabled'}

    if analyses_dir is None:
        analyses_dir = os.path.join(ROOT, 'analyses')
    if portfolio_json is None:
        portfolio_json = os.path.join(ROOT, 'portfolio.json')

    results: dict = {'tickers': {}, 'portfolio_hub': None, 'errors': []}

    if not os.path.isdir(analyses_dir):
        results['errors'].append(f'analyses_dir not found: {analyses_dir}')
    else:
        for tk in os.listdir(analyses_dir):
            tk_dir = os.path.join(analyses_dir, tk)
            if not os.path.isdir(tk_dir) or not tk.replace('.', '').replace('_', '').isalnum():
                continue
            if tk.endswith('.zip'):
                continue
            tk = tk.upper()
            r: dict = {}
            try:
                ic_dash = _load_review_json(tk_dir, 'ic')
                dash_by_agent: dict = {}
                for ag in ('analyst', 'devils', 'ceo', 'executor', 'ic', 'quick'):
                    d = _load_review_json(tk_dir, ag)
                    if d:
                        dash_by_agent[ag] = d

                if ic_dash:
                    r['hub'] = write_ticker_hub(tk, ic_dash)
                    r['decision'] = append_decision(tk, ic_dash)
                    thesis = ic_dash.get('thesis', '')
                    if thesis:
                        r['thesis_evo'] = append_thesis_change(
                            tk, '', thesis,
                            source=f'Tickers/{tk}/Committee/{ic_dash.get("date","backfill")}_committee')

                hd_dir = os.path.join(tk_dir, '_handoffs')
                handoffs_map: dict = {}
                if os.path.isdir(hd_dir):
                    for fname in sorted(os.listdir(hd_dir)):
                        if fname.endswith('.md'):
                            ag_name = fname.replace('.md', '').split('_')[-1]
                            try:
                                with open(os.path.join(hd_dir, fname), encoding='utf-8') as f:
                                    handoffs_map[ag_name] = f.read()
                            except Exception:
                                pass

                if handoffs_map and ic_dash:
                    run_date = ic_dash.get('date') or _date_today()
                    r['full_chain'] = archive_full_chain(tk, run_date, handoffs_map, dash_by_agent or None)
                elif ic_dash and dash_by_agent:
                    run_date = ic_dash.get('date') or _date_today()
                    synthetic: dict = {}
                    for ag2, d2 in dash_by_agent.items():
                        if d2:
                            synthetic[ag2] = (f'# {tk} — {ag2}\n\n'
                                f'Verdict: {d2.get("verdict","—")} | Score: {d2.get("score","—")}\n\n'
                                f'*Handoff text not on disk — dashboard data only.*')
                    if synthetic:
                        r['full_chain'] = archive_full_chain(tk, run_date, synthetic, dash_by_agent or None)

                # דוסייה דחוסה — תמיד אחרון כדי שיכלול את כל הJSON שנטענו
                r['dossier'] = generate_compact_dossier(tk, analyses_dir)
                results['tickers'][tk] = r
            except Exception as e:
                results['errors'].append(f'{tk}: {e}')
                log_event(f'backfill failed for {tk}: {e}', 'ERROR')

    if os.path.exists(portfolio_json):
        try:
            with open(portfolio_json, encoding='utf-8') as f:
                pdata = json.load(f)
            holdings = pdata.get('holdings', [])
            if isinstance(holdings, dict):
                holdings = list(holdings.values())
            cash_raw = pdata.get('cash', {})
            if isinstance(cash_raw, dict):
                cash_total = sum(float(v) for v in cash_raw.values()) if cash_raw else 0.0
            else:
                cash_total = float(cash_raw) if cash_raw else 0.0
            results['portfolio_hub'] = write_portfolio_hub(holdings, cash_total)
        except Exception as e:
            results['errors'].append(f'portfolio_hub: {e}')
            log_event(f'portfolio hub backfill failed: {e}', 'ERROR')

    written = sum(1 for r in results['tickers'].values() if r.get('hub', {}).get('written'))
    log_event(f'backfill complete: {written}/{len(results["tickers"])} tickers, '
              f'{len(results["errors"])} errors', 'INFO')
    return results


def _load_review_json(tk_dir: str, agent: str):
    """Load analyses/<TICKER>/_reviews/<agent>.json.
    אם חסר, מנסה fallback על קובץ ה-.js הישן. Returns None אם שניהם חסרים."""
    p = os.path.join(tk_dir, '_reviews', f'{agent}.json')
    if os.path.exists(p):
        try:
            with open(p, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    # fallback: קובץ .js ישן (window.AGENT_DATA = {...})
    js_p = os.path.join(tk_dir, f'{agent}.js')
    if os.path.exists(js_p):
        return _parse_js_dashboard(js_p, agent)
    return None


def _parse_js_dashboard(js_path: str, agent: str) -> dict | None:
    """שולף שדות מינימליים מקובץ .js ישן לצורך הדוסייה. Rule-based regex בלבד."""
    try:
        with open(js_path, encoding='utf-8') as f:
            src = f.read()

        import re as _re
        import html as _html

        def _extract(pattern, default=''):
            m = _re.search(pattern, src, _re.DOTALL)
            return _html.unescape(
                _re.sub(r'<[^>]+>', '', m.group(1)).strip()
            ) if m else default

        ticker  = _extract(r"ticker\s*:\s*'([^']+)'")
        date    = _extract(r"date\s*:\s*'([^']+)'")
        verdict_raw = _extract(r"verdict\s*:\s*\{[^}]*headline\s*:\s*'([^']+)'")
        handoff = _extract(r"handoff\s*:\s*'((?:[^'\\]|\\.)*)'")
        handoff = handoff.replace('\\n', ' ').replace("\\'", "'")

        # ציון מ-scoreboxes
        score = None
        sm = _re.search(r'scoreboxes\s*:\s*\[(.*?)\]', src, _re.DOTALL)
        if sm:
            nm = _re.search(r"lbl\s*:\s*'ציון'\s*,\s*val\s*:\s*'?(\d+)", sm.group(1))
            if nm:
                score = int(nm.group(1))

        if not ticker:
            return None
        return {
            'ticker':           ticker,
            'agent':            agent,
            'date':             date,
            'verdict':          verdict_raw.split('—')[0].strip().lstrip('✅ ').strip() or 'APPROVED',
            'score':            score,
            'handoff_summary':  handoff[:700] if handoff else '',
            '_source':          'js-fallback',
        }
    except Exception:
        return None


# ── Compact Dossier — rule-based, zero LLM tokens ────────────────────────────
_AGENT_ORDER = ('analyst', 'devils', 'ceo', 'executor', 'ic', 'quick')
_AGENT_LABEL = {
    'analyst':  'Analyst',
    'devils':   'Devils Advocate',
    'ceo':      'CEO',
    'executor': 'Executor',
    'ic':       'IC',
    'quick':    'Quick Check',
}


def generate_compact_dossier(ticker: str, analyses_dir: str = None) -> dict:
    """כותב Tickers/<TICKER>/Compressed Dossier.md — סיכום rule-based ללא LLM.
    נקרא מ-on_save_handoff() בכל שמירת סוכן + מ-backfill.
    Fail-soft: כל שגיאה מוחזרת כ-dict עם 'error', אף פעם לא raise."""
    if not is_enabled():
        return {'skipped': True, 'reason': 'obsidian disabled'}

    tk = ticker.upper().strip()
    if analyses_dir is None:
        analyses_dir = os.path.join(ROOT, 'analyses')
    tk_dir = os.path.join(analyses_dir, tk)

    try:
        reviews = {}
        for ag in _AGENT_ORDER:
            d = _load_review_json(tk_dir, ag)
            if d:
                reviews[ag] = d

        if not reviews:
            return {'written': False, 'reason': 'no review data'}

        ic    = reviews.get('ic', {})
        anal  = reviews.get('analyst', {})
        devs  = reviews.get('devils', {})
        exec_ = reviews.get('executor', {})

        last_agent = 'ic' if 'ic' in reviews else max(
            reviews, key=lambda a: reviews[a].get('date', ''))
        last_date  = reviews[last_agent].get('date', _date_today())

        lines = [
            f'# {tk} — Compressed Dossier',
            f'_עדכון: {_AGENT_LABEL.get(last_agent, last_agent)} | {last_date}_',
            '',
        ]

        # תזה
        thesis = (ic.get('thesis') or anal.get('thesis') or
                  next((reviews[a].get('thesis') for a in _AGENT_ORDER
                        if a in reviews and reviews[a].get('thesis')), ''))
        if thesis:
            lines += ['## תזה', thesis, '']

        # סנפשוט
        verdict = ic.get('verdict') or next(
            (reviews[a].get('verdict') for a in reversed(_AGENT_ORDER)
             if a in reviews), '—')
        score = (ic.get('score') if ic else
                 next((reviews[a].get('score') for a in reversed(_AGENT_ORDER)
                       if a in reviews), '—'))
        pos  = ic.get('position_size_pct', next(
            (reviews[a].get('position_size_pct', 0)
             for a in reversed(_AGENT_ORDER) if a in reviews), 0))
        val  = ic.get('valuation_summary') or anal.get('valuation_summary') or ''
        ee   = (ic.get('entry_exit_plan') or exec_.get('entry_exit_plan') or
                anal.get('entry_exit_plan') or '')

        lines += [
            '## סנפשוט',
            f'**פסיקה:** {verdict} | **ציון:** {score}/100 | **גודל:** {pos}%',
        ]
        if val:
            lines.append(f'**שווי:** {val}')
        if ee:
            lines.append(f'**כניסה/יציאה:** {ee}')
        lines.append('')

        # טבלת סוכנים
        lines += ['## לפי סוכן', '',
                  '| סוכן | פסיקה | ציון | ממצא |',
                  '|------|-------|------|------|']
        for ag in _AGENT_ORDER:
            if ag not in reviews:
                continue
            r  = reviews[ag]
            av = r.get('verdict', '—')
            as_ = str(r.get('score', '—'))
            sm = (r.get('handoff_summary') or
                  (r.get('key_risks') or [''])[0])
            sm = sm[:130].replace('|', '\\|').replace('\n', ' ')
            lines.append(
                f'| **{_AGENT_LABEL.get(ag, ag)}** | {av} | {as_} | {sm} |')
        lines.append('')

        # Kill Switches / סיכונים
        risks = (ic.get('key_risks') or devs.get('key_risks') or
                 anal.get('key_risks') or [])
        if risks:
            lines += ['## סיכונים / Kill Switches', '']
            for r2 in risks[:5]:
                lines.append(f'- {r2}')
            lines.append('')

        # IC Summary — הכי שמן לinjection
        ic_sm = ic.get('handoff_summary', '')
        if ic_sm:
            lines += ['## IC Summary', ic_sm[:700], '']

        body = '\n'.join(lines)
        rel  = f'Tickers/{tk}/Compressed Dossier.md'
        fm   = make_frontmatter({
            'ticker':     tk,
            'note_type':  'compressed-dossier',
            'updated':    last_date,
            'last_agent': last_agent,
            'verdict':    verdict,
            'score':      score,
        })
        result = write_managed_note(rel, fm, body)
        log_event(f'dossier {"written" if result.get("written") else "dry-run"} for {tk}', 'DOSSIER')
        return result

    except Exception as e:
        log_event(f'generate_compact_dossier FAILED for {ticker}: {e}', 'ERROR')
        return {'written': False, 'error': str(e)}


# ── Phase 3: wiki_linker ─────────────────────────────────────────────────────
def _phase_stub(name):
    raise NotImplementedError(f'{name} — implemented in a later phase')

class wiki_linker:
    @staticmethod
    def scan_and_link() -> dict:
        """Phase 3: סורק vault, מוסיף [[TICKER]] backlinks, כותב Meta/MOC.md.
        Fail-soft — שגיאות מוגרות ולא מבלוקות."""
        cfg = _load_config()
        if not cfg.get('obsidian_enabled', False):
            return {'skipped': True, 'reason': 'obsidian disabled'}
        vault = cfg.get('obsidian_vault', '')
        if not vault or not os.path.isdir(vault):
            return {'skipped': True, 'reason': 'vault not found'}
        dry_run = cfg.get('obsidian_dry_run', True)

        # tickers ידועים מתיקיית analyses
        analyses_dir = os.path.join(ROOT, 'analyses')
        known_tickers: set = set()
        if os.path.isdir(analyses_dir):
            for name in os.listdir(analyses_dir):
                if os.path.isdir(os.path.join(analyses_dir, name)) and re.match(r'^[A-Z]{1,6}$', name):
                    known_tickers.add(name)
        if not known_tickers:
            return {'skipped': True, 'reason': 'no known tickers'}

        files_updated = []
        # סריקת כל קבצי .md בכספת
        for root_dir, dirs, files in os.walk(vault):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                if not fname.endswith('.md'):
                    continue
                fpath = os.path.join(root_dir, fname)
                try:
                    with open(fpath, encoding='utf-8') as f:
                        raw = f.read()
                    # פצל AUTO/USER
                    if USER_MARKER in raw:
                        auto_part = raw[:raw.index(USER_MARKER)]
                        user_part = raw[raw.index(USER_MARKER):]
                    else:
                        auto_part, user_part = raw, ''
                    new_auto = auto_part
                    for ticker in sorted(known_tickers):
                        # אל תקשר ב-hub של ה-ticker עצמו
                        if fname == f'{ticker}.md':
                            continue
                        # רק הופעה ראשונה, ורק אם לא מקושרת כבר
                        new_auto = re.sub(
                            r'(?<!\[\[)\b' + re.escape(ticker) + r'\b(?!\]\])',
                            f'[[{ticker}]]',
                            new_auto, count=1
                        )
                    if new_auto != auto_part:
                        if not dry_run:
                            _atomic_write(fpath, new_auto + user_part)
                        files_updated.append(fname)
                except Exception as e:
                    print(f'[wiki_linker] skip {fname}: {e}')

        # כתיבת Meta/MOC.md
        try:
            moc_path = os.path.join(vault, 'Meta', 'MOC.md')
            os.makedirs(os.path.dirname(moc_path), exist_ok=True)
            lines = [
                f'---\nnote_type: moc\ndate: {datetime.now().strftime("%Y-%m-%d")}\n---\n\n',
                f'{AUTO_MARKER}\n\n',
                '# Map of Contents\n\n',
                '## Ticker Hubs\n',
            ]
            for t in sorted(known_tickers):
                lines.append(f'- [[{t}]]\n')
            lines.append('\n## Portfolio\n- [[Portfolio Hub]]\n')
            lines.append('\n## Meta\n- [[Schema]]\n- [[Research Logs]]\n')
            sessions_dir = os.path.join(vault, 'Meta', 'Sessions')
            if os.path.isdir(sessions_dir):
                recent = sorted(
                    [s for s in os.listdir(sessions_dir) if s.endswith('.md')],
                    reverse=True
                )[:10]
                if recent:
                    lines.append('\n## Recent Sessions\n')
                    for s in recent:
                        lines.append(f'- [[{s[:-3]}]]\n')
            if not dry_run:
                _atomic_write(moc_path, ''.join(lines))
        except Exception as e:
            print(f'[wiki_linker] MOC write failed: {e}')

        return {'ok': True, 'files_linked': len(files_updated), 'tickers': sorted(known_tickers), 'dry_run': dry_run}

class dataview_schema:
    @staticmethod
    def emit(*a, **kw): _phase_stub('dataview_schema.emit (Phase 3)')

class dashboard_builder:
    @staticmethod
    def build(*a, **kw): _phase_stub('dashboard_builder.build (Phase 4)')

class maintenance:
    @staticmethod
    def run(*a, **kw): _phase_stub('maintenance.run (Phase 5)')
