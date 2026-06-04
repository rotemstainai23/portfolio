# AGENT_CHAIN.md

This document defines the investment multi-agent workflow.

Critical principle:

**Output of one agent becomes input of the next.**

Never change handoff structure unilaterally.

If changing:

- output format
- markdown sections
- expected fields
- naming conventions
- decision structure

You MUST verify downstream compatibility.

Breaking handoffs may break the entire investment workflow.

---

# Agent Chain

```text
Unified_Analyst
→ DevilsAdvocate
→ CEO_Agent
→ Executor
→ InvestmentCommittee
                   ↑
          TradeRecorder (post-buy)
```

Execution order matters.

Do not reorder agents without explicit instruction.

---

# Unified_Analyst

Role:

Deep forensic stock analysis.

Primary responsibilities:

- Business quality analysis
- Financial analysis
- Competitive moat evaluation
- Valuation analysis
- Thesis construction
- Risk identification
- Investment case building

Output:

Creates handoff files inside:

```text
analyses/<TICKER>/_handoffs/
```

Example:

```text
2026-05-26_analyst.md
```

Critical rule:

Analyst output becomes input for downstream agents.

Preserve compatibility.

---

# DevilsAdvocate

Role:

Attack the investment thesis.

Purpose:

Challenge optimism.

Primary responsibilities:

- Identify thesis weaknesses
- Surface hidden risks
- Stress-test assumptions
- Position sizing skepticism
- Failure scenario analysis

Outputs:

- risk score
- thesis objections
- fragile assumptions
- kill switches
- maximum position sizing guidance

Critical rule:

Do not soften criticism artificially.

Devil's Advocate exists to challenge conviction.

---

# CEO_Agent

Role:

Portfolio architect.

Primary responsibility:

Portfolio-level decision making.

Required inputs:

1. Analyst handoff
2. Devil handoff
3. Current portfolio state

Portfolio context matters.

Never evaluate opportunity in isolation.

Target allocation framework:

```text
Stability: 25–35%
Growth: 55–65%
Speculation: 5–10%
Cash: 5–10%
```

Responsibilities:

- Portfolio fit
- Position sizing
- Allocation logic
- Concentration management
- Opportunity cost evaluation

Critical rule:

AI concentration may be intentional.

Do not automatically treat concentration as a flaw.

---

# Executor

Role:

Trade structure and execution planning.

Primary responsibilities:

- Entry planning
- Tranche structure
- Limit order planning
- ATR-based stop planning
- Risk/reward evaluation

Outputs:

Execution-ready trade plan.

Focus:

Execution quality.

Not thesis creation.

---

# InvestmentCommittee

Role:

Final approval layer.

Purpose:

Final challenge before capital allocation.

Responsibilities:

- Evaluate all prior outputs
- Validate conviction
- Confirm sizing logic
- Approve or reject

Possible outcomes:

```text
APPROVED
REJECTED
WATCHLIST
```

Critical rule:

Committee reviews prior work.

Does not replace prior agents.

---

# TradeRecorder

Role:

Post-purchase documentation.

Triggered:

After approved investment action.

Responsibilities:

- Record trade
- Update logs
- Preserve historical reasoning
- Maintain investment memory

Used for:

Long-term accountability.

---

# Handoff Safety Rules

Never change handoff schemas without checking downstream consumers.

Before changing handoff format:

1. Identify downstream agents
2. Verify expected structure
3. Maintain backwards compatibility
4. Update all dependent prompts if necessary

Rule:

**No unilateral schema changes.**

---

# Repository Locations

Master prompts:

```text
portfolio/מערכת תיק ההשקעות/
```

Includes:

```text
Unified_Analyst.md
CEO_Agent_Updated.md
DevilsAdvocate_Updated.md
Executor_Updated.md
InvestmentCommittee_Updated.md
TradeRecorder_Updated.md
```

Analysis data:

```text
analyses/<TICKER>/
```

Handoffs:

```text
analyses/<TICKER>/_handoffs/
```

Quick reviews:

```text
analyses/<TICKER>/_reviews/
```

---

# Change Philosophy

When editing prompts:

Prefer:

small, compatible changes.

Avoid:

large rewrites that alter downstream behavior.

Preserve chain integrity.