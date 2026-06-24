"""שרשרת 5 סוכנים בענן דרך Groq — ללא תלות ב-Flask או Claude CLI.

Analyst → Devil's Advocate → CEO → Executor → Investment Committee

כותב:
  analyses/_chain/<TICKER>/chain.json         — תוצאות כל הסוכנים + מטא
  analyses/<TICKER>/_reviews/<agent>.json     — כרטיסי ביקורת (תואם dashboard)
  analyses/_reviews_index.json                — עדכון אינדקס כרטיסים
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..analytics import fundamentals, technical
from ..config import logger
from ..providers import market
from . import llm

ROOT       = Path(__file__).resolve().parent.parent.parent
PROMPTS    = ROOT / "מערכת תיק ההשקעות"
ANALYSES   = ROOT / "analyses"
CHAIN_DIR  = ANALYSES / "_chain"

AGENT_ORDER = ["analyst", "devils", "ceo", "executor", "ic"]

PROMPT_FILES = {
    "analyst":  "Unified_Analyst.md",
    "devils":   "DevilsAdvocate_Updated.md",
    "ceo":      "CEO_Agent_Updated.md",
    "executor": "Executor_Updated.md",
    "ic":       "InvestmentCommittee_Updated.md",
}

# ponytail: קצר את הפרומפטים לGROQ_PROMPT_LINES שורות בלבד
# הפרומפטים המלאים מיועדים לClaude+בראוזר. Groq צריך רק את הRole.
# Groq free: 6k TPM. 80 שורות × ~10 טוקנים = ~800 in + 2000 out = 2800/קריאה.
GROQ_PROMPT_LINES = 80

MAX_TOKENS = {
    "analyst":  2000,
    "devils":   2000,
    "ceo":      2000,
    "executor": 2000,
    "ic":       2000,
}

# שניות המתנה בין קריאות Groq — מניעת rate-limit (6k TPM)
INTER_AGENT_SLEEP = 10


def _load_prompt(agent: str) -> str:
    """טוען את הRole בלבד (GROQ_PROMPT_LINES שורות ראשונות).

    הפרומפטים המלאים כוללים הוראות גלישה לClaude; Groq צריך רק את הRole.
    """
    path = PROMPTS / PROMPT_FILES[agent]
    try:
        full = path.read_text(encoding="utf-8")
        lines = full.splitlines()[:GROQ_PROMPT_LINES]
        return "\n".join(lines)
    except Exception as exc:
        logger.warning("לא ניתן לטעון פרומפט %s: %s", agent, exc)
        return f"אתה סוכן {agent} לניתוח השקעות. נתח את המניה ובצע את תפקידך."


def _market_context(ticker: str) -> dict[str, Any]:
    """מביא נתוני שוק בסיסיים — fail-soft לכל מקור."""
    ctx: dict[str, Any] = {"ticker": ticker}
    try:
        q = market.get_quote(ticker)
        ctx["quote"] = q.model_dump() if hasattr(q, "model_dump") else dict(q)
    except Exception as exc:
        ctx["quote_error"] = str(exc)
    try:
        f = fundamentals.get_fundamentals(ticker)
        ctx["fundamentals"] = f.model_dump() if hasattr(f, "model_dump") else {}
        ctx["company"] = getattr(f, "name", ticker)
    except Exception as exc:
        ctx["fund_error"] = str(exc)
    try:
        t = technical.get_technical(ticker)
        ctx["technical"] = t.model_dump() if hasattr(t, "model_dump") else {}
    except Exception as exc:
        ctx["tech_error"] = str(exc)
    return ctx


def _portfolio_snapshot() -> str:
    """תמצית תיק קומפקטית לסוכן CEO ומעלה."""
    try:
        p = json.loads((ROOT / "portfolio.json").read_text(encoding="utf-8"))
        holdings = [f"{h['symbol']} ({h.get('layer','?')})" for h in p.get("holdings", [])]
        wl = [w["symbol"] for w in p.get("watchlist", [])]
        cash = p.get("cash", 0)
        return f"אחזקות: {', '.join(holdings)}\nווצ'ליסט: {', '.join(wl)}\nמזומן: ${cash:,.0f}"
    except Exception:
        return "נתוני תיק לא זמינים"


def _build_user_msg(ticker: str, agent: str, mkt: dict, prev: dict[str, str]) -> str:
    """בונה הודעת משתמש לסוכן: הקשר שוק + פלטי סוכנים קודמים."""
    lines = [f"## מניה לניתוח: {ticker}"]

    quote = mkt.get("quote", {})
    if quote:
        price  = quote.get("price") or quote.get("regularMarketPrice")
        cap    = quote.get("marketCap")
        name   = mkt.get("company", ticker)
        lines += [
            f"חברה: {name}",
            f"מחיר: ${price}" if price else "",
            f"שווי שוק: ${cap/1e9:.1f}B" if cap else "",
        ]

    fund = mkt.get("fundamentals", {})
    if fund:
        fields = []
        for k in ["revenue", "net_margin", "roic", "pe", "ev_ebitda"]:
            dp = fund.get(k, {})
            v  = dp.get("value") if isinstance(dp, dict) else None
            u  = dp.get("unit", "") if isinstance(dp, dict) else ""
            if v is not None:
                fields.append(f"{k}={v:.1f}{u}")
        if fields:
            lines.append("פונדמנטלים: " + ", ".join(fields))

    tech = mkt.get("technical", {})
    if tech:
        rsi = (tech.get("rsi14") or {}).get("value")
        trend = tech.get("trend")
        if rsi or trend:
            lines.append(f"טכני: trend={trend}, RSI={rsi:.0f}" if rsi and trend else "")

    if agent in ("ceo", "executor", "ic"):
        lines += ["", "## תמצית תיק", _portfolio_snapshot()]

    if prev:
        lines.append("\n## פלטי סוכנים קודמים")
        for ag, out in prev.items():
            # שלח רק 800 תווים ראשונים מכל סוכן
            lines.append(f"### {ag}\n{out[:800]}{'...' if len(out) > 800 else ''}")

    lines.append(
        "\n## הוראה\nבצע את תפקידך. פלט מובנה ומפורט בעברית."
        " כלול verdict ברור (BUY/WATCHLIST/PASS/NO_ACTION) וציון 1-10."
    )
    return "\n".join(l for l in lines if l)


def _extract_review(ticker: str, agent: str, output: str) -> dict:
    """מחלץ verdict וציון מהפלט הגולמי של הסוכן."""
    verdict_map = {
        "buy": "BUY", "קנה": "BUY", "קניה": "BUY",
        "sell": "SELL", "מכור": "SELL",
        "pass": "PASS", "לא לקנות": "PASS", "skip": "PASS",
        "watchlist": "WATCHLIST", "מעקב": "WATCHLIST",
        "no.action": "NO_ACTION", "no action": "NO_ACTION", "ללא פעולה": "NO_ACTION",
        "danger": "DANGER",
    }
    text_lower = output.lower()
    verdict = None
    for kw, v in verdict_map.items():
        if kw in text_lower:
            verdict = v
            break

    score = None
    m = re.search(r'(?:ציון|score)[:\s]+(\d+(?:\.\d+)?)\s*/?\s*10', output, re.IGNORECASE)
    if m:
        score = float(m.group(1))

    # תמצית: 3 שורות ראשונות שיש בהן תוכן
    lines = [l.strip() for l in output.split("\n") if l.strip()]
    thesis = " ".join(lines[:3])[:300]

    return {
        "ticker": ticker.upper(),
        "agent": agent,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "verdict": verdict,
        "score": score,
        "thesis": thesis,
        "key_risks": [],
        "position_size_pct": None,
        "_cloud": True,
    }


def _write_review(ticker: str, agent: str, review: dict) -> None:
    rv_dir = ANALYSES / ticker.upper() / "_reviews"
    rv_dir.mkdir(parents=True, exist_ok=True)
    (rv_dir / f"{agent}.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _update_reviews_index(ticker: str, reviews: dict[str, dict]) -> None:
    index_path = ANALYSES / "_reviews_index.json"
    try:
        idx = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"reviews": []}
        existing = [r for r in idx.get("reviews", []) if r.get("ticker") != ticker.upper()]
        ic = reviews.get("ic", {})
        existing.insert(0, {
            "ticker": ticker.upper(),
            "verdict": ic.get("verdict"),
            "score": ic.get("score"),
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": ic.get("thesis", ""),
        })
        idx["reviews"] = existing[:50]
        idx["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        index_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("עדכון _reviews_index נכשל: %s", exc)


def run_chain(ticker: str) -> dict[str, Any]:
    """מריץ את שרשרת 5 הסוכנים. מחזיר dict עם כל הפלטים."""
    ticker = ticker.upper().strip()
    logger.info("שרשרת ענן: מתחיל %s", ticker)

    mkt = _market_context(ticker)
    outputs: dict[str, str] = {}
    reviews: dict[str, dict] = {}

    for i, agent in enumerate(AGENT_ORDER):
        if i > 0:
            logger.info("  המתנה %ds לפני %s (rate-limit)", INTER_AGENT_SLEEP, agent)
            time.sleep(INTER_AGENT_SLEEP)
        logger.info("  סוכן: %s", agent)
        system  = _load_prompt(agent)
        user    = _build_user_msg(ticker, agent, mkt, outputs)
        result  = llm.explain(user, system=system, max_tokens=MAX_TOKENS[agent])
        if not result:
            result = f"[{agent}: לא התקבל פלט מ-Groq]"
            logger.warning("  %s: פלט ריק", agent)
        outputs[agent] = result
        reviews[agent] = _extract_review(ticker, agent, result)
        _write_review(ticker, agent, reviews[agent])

    # כתיבת chain.json
    chain_out = CHAIN_DIR / ticker
    chain_out.mkdir(parents=True, exist_ok=True)
    payload = {
        "ticker":    ticker,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "company":   mkt.get("company", ticker),
        "agents":    outputs,
        "reviews":   reviews,
        "ic_verdict": reviews.get("ic", {}).get("verdict"),
        "ic_score":   reviews.get("ic", {}).get("score"),
    }
    (chain_out / "chain.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (chain_out / "chain.js").write_text(
        f"window.CHAIN_DATA = {json.dumps(payload, ensure_ascii=False)};\n",
        encoding="utf-8",
    )

    _update_reviews_index(ticker, reviews)
    logger.info("שרשרת ענן: הסתיים %s | IC=%s score=%s",
                ticker, payload["ic_verdict"], payload["ic_score"])
    return payload
