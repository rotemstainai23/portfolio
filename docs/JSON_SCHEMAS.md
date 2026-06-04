# JSON_SCHEMAS.md

This document defines JSON structures used in the portfolio system.

Critical rule:

`portfolio.json` is the single source of truth (SSOT).

Never invent structure.
Never rename fields without verifying compatibility.

When changing schemas:

1. Verify API compatibility
2. Verify frontend compatibility
3. Verify agent compatibility
4. Preserve backwards compatibility

---

# portfolio.json

Purpose:
Primary portfolio state storage.

Structure:

```json
{
  "cash": 71,
  "holdings": [
    {
      "symbol": "AAPL",
      "name": "Apple",
      "quantity": 10,
      "buy_price": 180,
      "layer": "Stability",
      "sector": "Technology",
      "analyst_score": 8,
      "risk_score": 4,
      "notes": "Long-term position"
    }
  ],
  "trades": [
    {
      "trade_id": "TRD-001",
      "date": "2026-01-01",
      "ticker": "AAPL",
      "action": "BUY",
      "verdict": "APPROVED",
      "price": 180,
      "size_pct": 5,
      "layer": "Growth",
      "analyst_score": 8,
      "risk_score": 4,
      "confidence": 9,
      "fair_value": 210,
      "upside_pct": 16,
      "thesis": "Strong AI tailwinds"
    }
  ],
  "watchlist": [
    {
      "symbol": "NVDA",
      "company": "NVIDIA",
      "date_added": "2026-01-01",
      "verdict": "WATCH",
      "layer": "Growth",
      "analyst_score": 9,
      "risk_score": 5,
      "confidence": 8,
      "fair_value": 170,
      "trigger_price": 140,
      "trigger_direction": "below",
      "thesis": "Wait for pullback",
      "fragile_assumption": "AI capex remains strong",
      "kill_switch": "Cloud spending weakens",
      "next_review": "2026-04-01",
      "notes": ""
    }
  ]
}
```

Important notes:

## holdings

Required concepts:

- `symbol`
- `quantity`
- `buy_price`
- `layer`

Valid layers:

```text
Stability
Growth
Speculation
```

Optional metadata:

- sector
- analyst_score
- risk_score
- notes

---

## trades

Trade IDs auto-generated:

```text
TRD-001
TRD-002
TRD-003
```

Common fields:

- ticker
- action
- verdict
- confidence
- fair_value
- upside_pct
- thesis

---

## watchlist

Supports trigger logic.

Valid trigger directions:

```text
below
above
```

Common investment fields:

- verdict
- analyst_score
- risk_score
- confidence
- thesis
- kill_switch
- next_review

---

# decision_log.json

Purpose:
Investment decision archive.

Structure:

```json
{
  "decisions": [
    {
      "id": "DEC-001",
      "ticker": "AAPL",
      "date": "2026-01-01",
      "decision": "BUY",
      "position_size_pct": 5,
      "why": "Strong fundamentals",
      "biggest_risk": "Valuation compression",
      "kill_switch": "Revenue growth breaks",
      "conviction": 8,
      "original_thesis": "AI-driven growth"
    }
  ]
}
```

Important:

- Not API-driven
- Manual edit or Claude-managed
- IDs follow:

```text
DEC-001
DEC-002
DEC-003
```

---

# analyses/<TICKER>/_reviews/quick.json

Purpose:
Fast committee review between major reviews.

Structure:

```json
{
  "ticker": "AAPL",
  "agent": "quick",
  "date": "2026-01-01",
  "verdict": "INTACT",
  "score": 8,
  "thesis": "Business remains strong",
  "key_risks": [],
  "position_size_pct": 5,
  "valuation_summary": "Still attractive",
  "entry_exit_plan": "Hold",
  "handoff_summary": "No major thesis changes"
}
```

Valid verdicts:

```text
INTACT
DETERIORATING
EXIT
```

---

# Runtime Safety

When server is running:

Avoid manual edits to:

```text
portfolio.json
```

Use REST API instead.

Reason:
Cache reset behavior is automatic through API operations.