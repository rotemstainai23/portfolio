---
name: review
description: One-command stock review combining NotebookLM evidence (facts) with Obsidian memory (thesis history). Triggered by `/review TICKER` or natural language like "review NVDA". Token-efficient, deterministic, append-only memory. Use when the user asks to review, re-check, or re-evaluate a specific ticker.
---

# /review TICKER

Targeted stock review. NotebookLM = facts only. Obsidian memory = thesis only.

## Trigger
- `/review NVDA`
- `/review NVDA --update` (also appends synthesis to vault)
- Natural language: "review NVDA", "re-check META", "is the thesis still valid for MSFT"

## Hard rules (non-negotiable)

1. **NotebookLM = facts only.** Use it for SEC filings, earnings transcripts, investor presentations, analyst materials. Never ask it for opinions, conviction, or portfolio decisions.
2. **Obsidian memory = thesis only.** Read only the targeted sections listed below. Never load entire vault, never read full handoff files, never list ticker directories.
3. **Maximum 5 NotebookLM queries per run.** No retries, no follow-ups, no clarifying queries, no "summarize the notebook" fallback. The 5 queries come from `review_layer.build_query_pack` and are deterministic.
4. **Every NotebookLM-derived claim must cite a source document.** If NotebookLM returns a claim without a source, mark it `[no-source]`. If evidence is weak or conflicting, mark `[weak]` or `[conflicting]`.
5. **If required info is missing, output `N/A`.** Never expand scope to compensate.
6. **No edits outside the isolated scope.** Do not touch `app.py`, agent prompts, handoff schemas, `portfolio.json`, or the dashboard. The only vault write allowed is append-only to `Tickers/<T>/Reviews.md` and only when the user passed `--update`.

## Deterministic flow

Execute exactly these steps in order. Skip none, add none.

### Step 1 — Validate inputs
- Parse `TICKER` (uppercase, A-Z 1-6 chars). If invalid, stop with message `Invalid ticker`.
- Detect `--update` flag in user message.

### Step 2 — Check NotebookLM availability
Use the `notebooklm` skill to verify a notebook for this ticker exists. Match by notebook title containing the ticker (case-insensitive). Set `notebooklm_available = True/False`.

If `notebooklm_available = False`: continue with memory-only review. Evidence sections will be `N/A` by policy. Do NOT create a notebook automatically.

### Step 3 — Load memory (one Bash call, fixed budget)

```
cd C:/Users/רותם/portfolio
python -c "
import json, sys
import review_layer as r
mem = r.load_memory(sys.argv[1], notebooklm_available=(sys.argv[2]=='1'))
print(json.dumps(mem, ensure_ascii=False, default=str))
" TICKER 1_or_0
```

Replace `TICKER` with the actual ticker and `1_or_0` with `1` if NotebookLM is available, else `0`.

Hard limits enforced inside `load_memory`:
- Hub file: read at most 16KB. USER section truncated to 3000 chars.
- Decision History.md: read last 32KB only, return only the last `##` section, max 80 lines.
- Thesis Evolution.md: same budget.
- IC dash JSON: full read (small file).
- Keyword extraction: max 8 keywords, deterministic regex, no LLM.

If the hub does not exist (`hub_exists == False`) and there is also no IC dash, stop:
> No memory for $TICKER. Run the analyst chain first (see [docs/AGENT_CHAIN.md](docs/AGENT_CHAIN.md)).

### Step 4 — Build the deterministic query pack

```
python -c "
import json, sys
import review_layer as r
mem = json.loads(sys.stdin.read())
pack = r.build_query_pack(sys.argv[1], mem.get('user_section',''), mem.get('keywords',[]), mem.get('last_review_date'))
print(json.dumps(pack, ensure_ascii=False))
" TICKER <<< 'MEM_JSON'
```

Result is a dict with exactly 5 fixed keys: `support`, `contradict`, `changes_since`, `risks_delta`, `guidance_delta`.

If `notebooklm_available == False`: skip to Step 6 with all 5 evidence categories set to `[]`.

### Step 5 — Run the 5 queries against NotebookLM
For each of the 5 prompts, call the `notebooklm` skill against the ticker notebook. One query per category. Do not chain follow-up queries. Do not summarize. Do not let NotebookLM autonomously explore.

Parse each response into a list of items with attribution:
```json
[{"claim": "...", "source": "Q1 2026 Earnings Transcript", "strength": "strong"}, ...]
```

If NotebookLM returns text without a source citation, set `"source": ""` (the layer will tag it `[no-source]`).
If the response is `N/A` or empty, set the list to `[]`.

Strength markers:
- `strong` — direct quote from primary document
- `moderate` — paraphrased but sourced
- `weak` — uncertain, ambiguous, or single weak data point
- `conflicting` — multiple sources disagree

### Step 6 — Synthesize the output

```
python -c "
import json, sys
import review_layer as r
mem = json.loads(sys.argv[1])
ev  = json.loads(sys.argv[2])
print(r.synthesize(sys.argv[3], mem, ev))
" 'MEM_JSON' 'EVIDENCE_JSON' TICKER
```

Output is the fixed template. Print it to the user verbatim. Do not add commentary.

### Step 7 — Optional memory append
Only if the user passed `--update`:

```
python -c "
import sys, review_layer as r
out = sys.stdin.read()
print(r.append_review(sys.argv[1], out))
" TICKER <<< 'SYNTHESIZED_OUTPUT'
```

This appends one new `## YYYY-MM-DD - Review` entry to `Tickers/<T>/Reviews.md`. Never rewrites prior entries. Fail-soft (any error is logged, no exception raised).

## Output template (always identical structure)

```
Ticker: NVDA

Current Thesis:
<from IC dash or USER section, or N/A>

What Changed:
<last Thesis Evolution entry, or N/A>

Evidence From NotebookLM:
- <claim> (<source>) [strength?]
- ...

Material Changes:
- ...

Guidance Updates:
- ...

Contradictions:
- ...

Thesis Break Signals:
- None detected.  OR  - N contradictions, M new/escalating risks. + list.

Suggested Action:
Hold | Add | Reduce | Watch

Confidence:
X/10

---
Notes:
- (any structural notes about missing notebooks, truncation, etc.)
```

## Token budget self-check

Before finishing, verify:
- You ran exactly 5 NotebookLM queries (or 0 if unavailable).
- You read the hub file at most once.
- You did not read any handoff file.
- You did not list any directory.
- Total Bash subprocess calls: 3 (load_memory, build_query_pack, synthesize) plus optional 1 for append_review.

If any of these is violated, you escaped the budget. Stop and report it.

## When NOT to use this skill
- User asks to run the full agent chain (`/run`, "analyze NVDA from scratch"). Use the existing chain.
- User asks to edit handoffs, portfolio.json, or dashboard. This skill is read-only on those.
- User asks for a deep-dive forensic analysis. That is the Unified_Analyst agent's job, not this skill.

## Related files
- [review_layer.py](review_layer.py) — the read-only retrieval library
- [obsidian_layer.py](obsidian_layer.py) — vault write primitives (used only for `append_review`)
- [docs/AGENT_CHAIN.md](docs/AGENT_CHAIN.md) — the existing agent workflow this skill complements
