"""חילוץ סדרות נתונים מעובדות XBRL של EDGAR.

מרכז את מיפוי המושגים (concept tags) ואת הלוגיקה של בחירת ערכים שנתיים, כדי
ששאר שכבת ה-analytics תעבוד מול ממשק נקי ולא מול מבנה ה-JSON הגולמי של SEC.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..models import CompanyFacts

# מיפוי מושג -> רשימת tags אפשריים (לפי סדר עדיפות). חברות שונות משתמשות ב-tags שונים.
CONCEPT_TAGS: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "cogs": [
        "CostOfGoodsAndServicesSold",
        "CostOfRevenue",
        "CostOfGoodsSold",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "ocf": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "da": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
        "DepreciationAndAmortization",
    ],
    "assets": ["Assets"],
    "equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "lt_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "st_debt": ["LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings"],
    "current_liab": ["LiabilitiesCurrent"],
    "eps_diluted": ["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted"],
}

# יחידות ברירת מחדל לכל מושג
CONCEPT_UNIT: dict[str, str] = {
    "eps_diluted": "USD/shares",
}


def _units_for(facts: CompanyFacts, key: str) -> tuple[Optional[str], list[dict]]:
    """מחזיר (tag שנבחר, רשימת רשומות units) עבור מושג נתון, לפי סדר העדיפות."""
    unit = CONCEPT_UNIT.get(key, "USD")
    for tag in CONCEPT_TAGS.get(key, []):
        concept = facts.facts.get("us-gaap", {}).get(tag)
        if not concept:
            continue
        units = concept.get("units", {}).get(unit)
        if units:
            return tag, units
    return None, []


def annual_series(facts: CompanyFacts, key: str) -> list[dict]:
    """מחזיר סדרה שנתית עולה לפי תאריך עבור מושג.

    כל איבר: {end, val, fy, form, tag}. עבור פריטי תזרים/רווח (flows) נבחרים רק
    מקטעים שנתיים (משך > 300 ימים). עבור פריטי מאזן (instant) נבחרים כל הצילומים.
    כפילויות לפי תאריך סיום נפתרות לטובת הרשומה המאוחרת (תיקונים).
    """
    tag, units = _units_for(facts, key)
    if not tag:
        return []
    by_end: dict[str, dict] = {}
    for u in units:
        end = u.get("end")
        val = u.get("val")
        if not end or val is None:
            continue
        start = u.get("start")
        if start:  # flow: דורש משך שנתי
            try:
                days = (date.fromisoformat(end) - date.fromisoformat(start)).days
            except ValueError:
                continue
            if days < 300:
                continue
        by_end[end] = {
            "end": end,
            "val": float(val),
            "fy": u.get("fy"),
            "form": u.get("form"),
            "tag": tag,
        }
    return [by_end[e] for e in sorted(by_end)]


def quarterly_series(facts: CompanyFacts, key: str) -> list[dict]:
    """מחזיר סדרה רבעונית עולה לפי תאריך עבור מושג.

    עבור flows (הכנסות/רווח) נבחרים מקטעים של רבעון בלבד (משך 60-100 ימים),
    כדי לא לערבב נתוני רבעון עם נתוני שנה/חצי. כפילויות נפתרות לטובת המאוחר.
    """
    tag, units = _units_for(facts, key)
    if not tag:
        return []
    by_end: dict[str, dict] = {}
    for u in units:
        end = u.get("end")
        val = u.get("val")
        start = u.get("start")
        if not end or val is None or not start:
            continue
        try:
            days = (date.fromisoformat(end) - date.fromisoformat(start)).days
        except ValueError:
            continue
        if not (60 <= days <= 100):  # רבעון בלבד
            continue
        by_end[end] = {
            "end": end,
            "val": float(val),
            "fy": u.get("fy"),
            "fp": u.get("fp"),
            "form": u.get("form"),
            "tag": tag,
        }
    return [by_end[e] for e in sorted(by_end)]


def latest_annual(facts: CompanyFacts, key: str) -> Optional[dict]:
    """מחזיר את הרשומה השנתית האחרונה עבור מושג, או None."""
    series = annual_series(facts, key)
    return series[-1] if series else None


def shares_outstanding(facts: CompanyFacts) -> Optional[dict]:
    """מספר המניות במחזור (instant) מתוך dei או us-gaap."""
    candidates = [
        ("dei", "EntityCommonStockSharesOutstanding"),
        ("us-gaap", "CommonStockSharesOutstanding"),
        ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"),
    ]
    for taxonomy, tag in candidates:
        concept = facts.facts.get(taxonomy, {}).get(tag)
        if not concept:
            continue
        units = concept.get("units", {}).get("shares")
        if not units:
            continue
        valid = [u for u in units if u.get("end") and u.get("val")]
        if valid:
            latest = max(valid, key=lambda u: u["end"])
            return {"end": latest["end"], "val": float(latest["val"]), "tag": tag}
    return None
