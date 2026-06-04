# PITFALLS.md

This document lists known repository traps, assumptions, and failure points.

Read when:

- behavior seems inconsistent
- modifying architecture
- editing prompts
- changing portfolio assumptions
- debugging unusual behavior

---

# Backend Components

## app.py — canonical

Status:

```text
CANONICAL
```

Flask backend. Implements all 24 endpoints required by the dashboard:
portfolio CRUD, agent runner (`/api/run` invoking `claude -p`), decision
journal, handoff persistence, review JSON extraction, Obsidian sync,
templates/* and analyses/* static serving.

Launch:

```powershell
cd portfolio
python app.py
```

`start.bat` performs the same launch.

---

## serve.ps1 — experimental / legacy

Status:

```text
EXPERIMENTAL — DO NOT DECLARE CANONICAL
```

PowerShell HttpListener proxy. Covers only 9 of the 24 endpoints:
portfolio CRUD (holdings/watchlist/trades/cash) + chart proxy + portfolio.html
serving.

Missing endpoints (the dashboard hits these and gets 404):

- `/api/run`, `/api/run-status/<id>` — agent runner
- `/api/decisions`, `/api/decisions/<ticker>` — decision journal
- `/api/handoffs/<ticker>`, `/handoffs/<ticker>/<file>` — handoff viewer
- `/api/latest-reviews`, `/api/latest-reviews/<ticker>` — dashboard cards
- `/api/analyses` — analyses index
- `/templates/<file>`, `/analyses/<file>` — visual report assets

Useful for portfolio-only edits when Python isn't available. The dashboard's
analyses/handoffs/decisions/reports views silently break under it.

Until parity is reached, app.py is the only correct primary server.

---

# Portfolio Philosophy

## AI Concentration

Important context:

High AI concentration is intentional.

This is:

```text
thematic concentration
```

not automatically:

```text
portfolio risk mismanagement
```

Do NOT automatically flag concentration as a flaw.

Evaluate concentration in context.

---

# Markdown Scanning Trap

Avoid broad repository scans.

Do NOT use:

```text
glob **/*.md
```

Reason:

May pull irrelevant markdown files.

Can create noisy context.

Can waste tokens.

Prefer targeted reads.

Example:

Read only:

```text
portfolio/מערכת תיק ההשקעות/
```

when working with prompts.

Avoid home-directory markdown scanning.

---

# Hebrew Path Handling

Paths containing Hebrew characters should be wrapped in quotes.

Example:

```bash
"portfolio/מערכת תיק ההשקעות/"
```

Reason:

Prevents CLI/Bash path parsing issues.

---

# Runtime Data Trap

When server is running:

Avoid manually editing:

```text
portfolio.json
```

Reason:

Live pricing cache may become stale.

Prefer REST API updates.

POST/DELETE reset cache automatically.

---

# Report Architecture Trap

Two report patterns exist.

## Legacy (Deprecated)

Standalone report files:

```text
*_report_*.html
```

Do NOT create new ones.

Avoid extending legacy pattern.

---

## Preferred Pattern

Use:

```text
templates/<agent>.html?ticker=<TICKER>
```

Data source:

```text
analyses/<TICKER>/<agent>.js
```

which populates:

```javascript
window.AGENT_DATA
```

Prefer reusable templates.

Do not create new standalone reports.

---

# Change Philosophy

Before major changes:

1. Verify architecture
2. Check downstream compatibility
3. Prefer minimal diffs
4. Preserve working behavior

Avoid unnecessary rewrites.