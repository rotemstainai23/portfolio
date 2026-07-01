# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Global rules: `~/CLAUDE.md` · Living memory: `~/CLAUDE MEMORY/Projects/portfolio/`

## Operator Context
Primary account: `rotemstainai23@gmail.com`. Irreversible/external actions need per-action confirmation.

## Prime Directive
Do not break working systems. Priority: correctness > stability > agent-compatibility > minimal-diff.
SSOT is `portfolio.json` — never invent state, always validate against JSON/API.

## Repo Map
`app.py` Flask API (24+ endpoints — see docs/API.md) + Yahoo proxy + agent runner · `portfolio.json` SSOT · `decision_log.json` · `portfolio.html` dashboard · `obsidian_layer.py` fail-soft vault · `review_layer.py` read-only retrieval · `config.json` runtime flags · `qa_test_suite.py` · `templates/` reports · `analyses/<TICKER>/` (_handoffs/, _reviews/, *.js per agent) · `מערכת תיק ההשקעות/` agent prompts · `docs/` detailed docs · `serve.ps1` legacy stub (9 endpoints only).

**מנוע ענן (GitHub Actions + Pages — ללא תלות ב-app.py):**
`engine/` מנוע מוסדי: providers (EDGAR/Yahoo/insider/13F) + analytics + agents (Groq LLM) · `scripts/daily_report.py|sunday_report.py|saturday_scanner.py` כותבים JSON סטטי ל-`analyses/` · `.github/workflows/` daily/sunday/saturday (cron 02:00 UTC) + research.yml (workflow_dispatch) · `templates/research.html` PWA on-demand · `index.html` PWA ראשי עם bottom-nav (5 tabs כולל מחקר) · `analyses/_research/index.json` אינדקס מחקרים.

## Decision Router (read first, every task)
| Task | Read first | Plan Mode | Sub-agent |
|------|-----------|-----------|-----------|
| UI / styling | docs/STYLE_GUIDE.md | no | - |
| Backend / API | docs/API.md | high-risk → yes | - |
| JSON / serialization | docs/JSON_SCHEMAS.md | no | - |
| Agent chain / handoff schema | docs/AGENT_CHAIN.md | yes (+approval) | Plan |
| Broad code search (>3 queries) | - | no | Explore |
| Multi-file change / research | relevant only | yes | general-purpose |
| Recurring bug / weird behavior | docs/PITFALLS.md | no | - |
| Review a ticker | - | no | /review skill |
| Variance / attribution analysis | scripts/variance.py + monthly_close.js | no | /variance-analysis skill |
| שאלה כללית / ניתוב מניה/תיק | Oracle_Agent.md | no | Oracle |

Never `glob **/*.md` from home; never scan the repo or vault broadly.

## Core Workflow
- Investigate relevant files only → explain current behavior → propose smallest safe diff.
- Confidence <90%: stop and ask. High-risk (app.py, routes, agent schemas): approval required before implementing.
- Verify: server starts, dashboard renders, no console errors, JSON intact, API + chain compatible.
- Anti-refactor: change only what the task needs. Ask "what can break?" before editing multiple subsystems.

## Efficiency
Plan Mode before heavy/architectural work; spawn sub-agents per router; don't re-read files in context.

## Run / Test
```powershell
cd portfolio
python app.py                    # http://127.0.0.1:5000  (or start.bat)
pip install -r requirements.txt  # flask, yfinance, requests, truststore
python qa_test_suite.py          # synthetic-only, _QA_ prefix, exit 0=pass / 1=fail
```
Run from inside `portfolio/`. Never `python portfolio\app.py` from elsewhere.
Never hand-edit `portfolio.json` while server runs — use the API (POST/DELETE reset price cache).

## Multi-Agent Safety
Chain: Unified_Analyst → DevilsAdvocate → CEO_Agent → Executor → InvestmentCommittee (TradeRecorder post-buy).
**Oracle** (`מערכת תיק ההשקעות/Oracle_Agent.md`) — יועץ שיחתי. לא חלק מהשרשרת. במסלול הענן (cloudflare/worker.js `/oracle`) יש לו כלי add/update לאחזקות בלבד, מאומתים בטוקן GitHub של המשתמש; מחיקה רק מה-UI (טאב אחזקות), לא מהצ'אט — הגנה מהזרקת פרומפט.
- Never change a handoff schema unilaterally; verify downstream first.
- Persisted artifacts are canonical: `analyses/<TICKER>/_handoffs/` and `analyses/<TICKER>/<agent>.js`.
- `מערכת תיק ההשקעות/` is the canonical prompt dir; preserve agent boundaries. Details: docs/AGENT_CHAIN.md.
- **IC is the only agent that writes to portfolio/watchlist.** All others write handoffs only.
- **Numbers come only from `dashboard-json` blocks** in handoff markdown — never infer from prose.
- **Quick check** (mode: quick): 180s timeout → `_quick_check.js` + `_reviews/quick.json`. Not a full chain substitute.
- Agent timeouts: Analyst 1500s, others 600s, quick 180s.
- `_reviews/<agent>.json` drives consensus matrix + freshness chips (mtime: <14d green, 14-45d yellow, >45d red).
- Decision journal (kill switches, original thesis, conviction) is injected into every agent run — anti-drift anchor.

## Presentation Rule
Route all analysis data to `templates/<agent>.html?ticker=<TICKER>`; never expose raw `.js`/JSON.
UI: RTL, Heebo font, offline, CSS-native only (no Chart.js, no CDN). See docs/STYLE_GUIDE.md.

## Obsidian (fail-soft)
Writes only inside AUTO region; USER_MARKER section is user-owned, never touched.
Vault failures log only, never block the chain. Repo + JSON are authoritative; vault is derived.
After every chain run and significant session, vault auto-updates — no manual recall needed.

## Review System
`/review TICKER` is read-first, isolated from runtime. NotebookLM: ≤5 queries per run. Changes outside review outputs need approval.

## Investment Context
Thematic concentration may be intentional strategy; do not auto-treat as a flaw.

## Path Safety
Wrap Hebrew paths in quotes in shell: `"portfolio/מערכת תיק ההשקעות/"`. Prefer Glob/Read/Edit over shell.

## Communication
Hebrew + code comments; no em-dashes. Per change: what / why / risk / affected files / rollback. ≤5 bullets.
