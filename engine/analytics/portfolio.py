"""שכבת אנליטיקה לתיק האישי (Phase 9). חישובים דטרמיניסטיים בלבד, אפס LLM.

מחשב שווי נוכחי, רווח/הפסד, משקלים, ריכוז לפי סקטור ושכבה, סיכון משוקלל,
ומסמן דגלי ריכוז לפי ספים גלויים. כל מספר ניתן לאימות מול portfolio.json
והמחיר הנוכחי מ-yfinance.
"""
from __future__ import annotations

from ..providers import market, portfolio_data
from ..providers.base import ProviderError

# ספי דגלי ריכוז (גלויים, ניתנים לשינוי)
_POS_LIMIT = 20.0       # פוזיציה בודדת מעל 20% = ריכוז גבוה
_SECTOR_LIMIT = 35.0    # סקטור בודד מעל 35% = חשיפת סקטור גבוהה
_SPEC_LIMIT = 20.0      # שכבת ספקולציה מעל 20% = חשיפה ספקולטיבית גבוהה


def compute_portfolio(priced_holdings: list[dict], cash: float) -> dict:
    """חישוב טהור (testable): מקבל החזקות עם current_price ומזומן, מחזיר ניתוח מלא."""
    rows = []
    for h in priced_holdings:
        qty = float(h["quantity"])
        buy = float(h["buy_price"])
        price = h.get("current_price")
        cost = qty * buy
        value = qty * price if price is not None else None
        pnl = (value - cost) if value is not None else None
        pnl_pct = ((value / cost - 1) * 100.0) if (value is not None and cost) else None
        rows.append({
            "symbol": h["symbol"],
            "name": h.get("name", h["symbol"]),
            "layer": h.get("layer", "-"),
            "sector": h.get("sector", "-"),
            "quantity": qty,
            "buy_price": buy,
            "current_price": price,
            "cost": cost,
            "value": value,
            "pnl": pnl,
            "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
            "risk_score": h.get("risk_score"),
            "priced": price is not None,
        })

    invested = sum(r["value"] for r in rows if r["value"] is not None)
    total = invested + cash
    total_cost = sum(r["cost"] for r in rows)

    for r in rows:
        r["weight"] = round(r["value"] / total * 100, 2) if (r["value"] is not None and total) else None
    rows.sort(key=lambda r: (r["value"] is not None, r["value"] or 0), reverse=True)

    # ריכוז לפי סקטור ושכבה (רק על מה שתומחר)
    def _group(key: str) -> list[dict]:
        agg: dict[str, float] = {}
        for r in rows:
            if r["value"] is None:
                continue
            agg[r[key]] = agg.get(r[key], 0.0) + r["value"]
        out = [{"name": k, "value": v, "weight": round(v / invested * 100, 2) if invested else 0.0}
               for k, v in agg.items()]
        out.sort(key=lambda x: x["value"], reverse=True)
        return out

    by_sector = _group("sector")
    by_layer = _group("layer")

    # סיכון משוקלל לפי שווי (1-10)
    rk_num = sum((r["risk_score"] or 0) * r["value"] for r in rows if r["value"] is not None and r["risk_score"])
    weighted_risk = round(rk_num / invested, 2) if invested else None

    # דגלי ריכוז דטרמיניסטיים
    flags = []
    for r in rows:
        if r["weight"] and r["weight"] > _POS_LIMIT:
            flags.append(f"ריכוז גבוה: {r['symbol']} מהווה {r['weight']}% מהתיק (סף {_POS_LIMIT:.0f}%).")
    for s in by_sector:
        if s["weight"] > _SECTOR_LIMIT:
            flags.append(f"חשיפת סקטור גבוהה: {s['name']} {s['weight']}% מהמושקע (סף {_SECTOR_LIMIT:.0f}%).")
    spec = next((l for l in by_layer if l["name"] == "Speculation"), None)
    if spec and spec["weight"] > _SPEC_LIMIT:
        flags.append(f"חשיפה ספקולטיבית גבוהה: שכבת Speculation {spec['weight']}% (סף {_SPEC_LIMIT:.0f}%).")

    total_pnl = invested - total_cost
    return {
        "holdings": rows,
        "cash": cash,
        "total_value": total,
        "invested_value": invested,
        "total_cost": total_cost,
        "total_pnl": total_pnl,
        "total_pnl_pct": round(total_pnl / total_cost * 100, 2) if total_cost else None,
        "cash_weight": round(cash / total * 100, 2) if total else None,
        "by_sector": by_sector,
        "by_layer": by_layer,
        "weighted_risk": weighted_risk,
        "concentration_flags": flags,
        "thresholds": {"position": _POS_LIMIT, "sector": _SECTOR_LIMIT, "speculation": _SPEC_LIMIT},
    }


def analyze_portfolio() -> dict:
    """אורקסטרציה: טוען את התיק, מושך מחירים נוכחיים, ומריץ את החישוב הטהור."""
    data = portfolio_data.load_portfolio()
    holdings = data.get("holdings", [])
    priced = []
    for h in holdings:
        rec = dict(h)
        try:
            rec["current_price"] = market.get_quote(h["symbol"]).price.value
        except ProviderError:
            rec["current_price"] = None  # עמידות: מסומן כלא מתומחר
        priced.append(rec)

    result = compute_portfolio(priced, float(data.get("cash", 0)))
    result["source"] = portfolio_data.portfolio_source()
    result["unpriced"] = [r["symbol"] for r in result["holdings"] if not r["priced"]]
    return result
