"""מודל DCF (Discounted Cash Flow) דטרמיניסטי עם הנחות גלויות וניתנות לכוונון.

intrinsic_value היא פונקציה טהורה (קלה לבדיקה). get_dcf מושך את הקלטים מ-EDGAR
(FCF בסיס, חוב נטו, מניות) ומחשב שווי הוגן למניה.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..models import CompanyFacts, DataPoint, Source
from ..providers import edgar
from . import xbrl


def intrinsic_value(
    fcf0: float,
    growth: float,
    wacc: float,
    terminal_growth: float,
    years: int = 5,
) -> dict:
    """מחשב שווי תאגידי (EV) לפי היוון תזרימים עתידיים + ערך שיורי (Gordon).

    growth/wacc/terminal_growth בשברים (0.10 = עשרה אחוז). זורק ValueError אם
    wacc <= terminal_growth (הנוסחה מתבדרת).
    """
    if wacc <= terminal_growth:
        raise ValueError("WACC חייב להיות גדול מצמיחת הטרמינל")
    pv_flows = 0.0
    fcf = fcf0
    projection = []
    for t in range(1, years + 1):
        fcf = fcf * (1 + growth)
        discounted = fcf / (1 + wacc) ** t
        pv_flows += discounted
        projection.append({"year": t, "fcf": round(fcf, 2), "pv": round(discounted, 2)})
    terminal = fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_terminal = terminal / (1 + wacc) ** years
    ev = pv_flows + pv_terminal
    return {
        "ev": ev,
        "pv_flows": pv_flows,
        "pv_terminal": pv_terminal,
        "projection": projection,
    }


def get_dcf(
    ticker: str,
    *,
    growth: float = 0.08,
    wacc: float = 0.09,
    terminal_growth: float = 0.025,
    years: int = 5,
) -> dict:
    """DCF מלא לטיקר עם שווי הוגן למניה. כל ההנחות מוחזרות לשקיפות."""
    facts: CompanyFacts = edgar.get_company_facts(ticker)
    ocf = xbrl.latest_annual(facts, "ocf")
    capex = xbrl.latest_annual(facts, "capex")
    if not ocf or not capex:
        return {"ticker": ticker.upper(), "error": "אין מספיק נתוני תזרים ב-EDGAR ל-DCF"}
    fcf0 = ocf["val"] - abs(capex["val"])

    cash = xbrl.latest_annual(facts, "cash")
    lt_debt = xbrl.latest_annual(facts, "lt_debt")
    st_debt = xbrl.latest_annual(facts, "st_debt")
    shares = xbrl.shares_outstanding(facts)
    net_debt = (
        (lt_debt["val"] if lt_debt else 0.0)
        + (st_debt["val"] if st_debt else 0.0)
        - (cash["val"] if cash else 0.0)
    )

    result = intrinsic_value(fcf0, growth, wacc, terminal_growth, years)
    equity_value = result["ev"] - net_debt
    src = Source(name="SEC EDGAR (XBRL) + מודל DCF", url=facts.source.url, as_of=ocf["end"])

    per_share = None
    if shares and shares["val"]:
        per_share = DataPoint(
            label="שווי הוגן למניה (DCF)",
            value=round(equity_value / shares["val"], 2),
            unit="USD",
            source=src,
            note="ערך הון עצמי חלקי מספר מניות",
        )

    return {
        "ticker": ticker.upper(),
        "fcf_base": DataPoint(label="FCF בסיס", value=round(fcf0, 2), unit="USD", source=src).model_dump(),
        "enterprise_value": round(result["ev"], 2),
        "equity_value": round(equity_value, 2),
        "fair_value_per_share": per_share.model_dump() if per_share else None,
        "assumptions": {
            "growth": growth,
            "wacc": wacc,
            "terminal_growth": terminal_growth,
            "years": years,
            "net_debt": round(net_debt, 2),
            "note": "הנחות ברירת מחדל ניתנות לכוונון. שווי הוגן רגיש מאוד להנחות.",
        },
        "projection": result["projection"],
        "source": src.model_dump(),
    }
