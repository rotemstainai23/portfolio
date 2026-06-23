"""בדיקות Phase 0.

בדיקות יחידה (ללא רשת): cache ו-latest_fact.
בדיקות חיות (רשת, מסומנות network): EDGAR ו-yfinance.
הרצה ללא רשת:  pytest -m "not network"
"""
from __future__ import annotations

import pytest

from engine.models import CompanyFacts, Source
from engine.providers import edgar
from engine.providers.cache import cache_get, cache_set


# ---------- בדיקות יחידה (ללא רשת) ----------

def test_cache_roundtrip():
    """ערך שנשמר ב-cache נשלף חזרה זהה."""
    cache_set("test_key_unit", {"a": 1, "b": "שלום"})
    assert cache_get("test_key_unit", ttl=3600) == {"a": 1, "b": "שלום"}


def test_cache_expiry():
    """ttl=0 גורם לכל ערך להיחשב פג."""
    cache_set("test_key_expiry", {"x": 1})
    assert cache_get("test_key_expiry", ttl=0) is None


def test_latest_fact_extraction():
    """latest_fact בוחר את הרשומה עם תאריך הסיום המאוחר ביותר ועוטף ב-DataPoint עם מקור."""
    facts = CompanyFacts(
        ticker="TEST",
        cik="0000000000",
        name="Test Co",
        facts={
            "us-gaap": {
                "Revenues": {
                    "label": "Revenues",
                    "units": {
                        "USD": [
                            {"end": "2023-12-31", "val": 100, "form": "10-K", "fy": 2023},
                            {"end": "2024-12-31", "val": 150, "form": "10-K", "fy": 2024},
                        ]
                    },
                }
            }
        },
        source=Source(name="SEC EDGAR", url="http://x", as_of="2025-01-01"),
    )
    dp = edgar.latest_fact(facts, "Revenues")
    assert dp is not None
    assert dp.value == 150.0
    assert dp.source.as_of == "2024-12-31"
    assert dp.source.name.startswith("SEC EDGAR")


def test_latest_fact_missing():
    """מושג שלא קיים מחזיר None."""
    facts = CompanyFacts(
        ticker="TEST",
        cik="0000000000",
        name="Test Co",
        facts={"us-gaap": {}},
        source=Source(name="SEC EDGAR"),
    )
    assert edgar.latest_fact(facts, "Revenues") is None


# ---------- בדיקות חיות (רשת) ----------

@pytest.mark.network
def test_edgar_live_aapl():
    """שליפת עובדות AAPL מ-EDGAR מחזירה הכנסות עם מקור ותאריך."""
    facts = edgar.get_company_facts("AAPL")
    assert facts.cik == "0000320193"
    rev = edgar.latest_fact(
        facts, "RevenueFromContractWithCustomerExcludingAssessedTax", label="הכנסות"
    )
    assert rev is not None and rev.value and rev.value > 0
    assert rev.source.as_of  # תאריך קיים -> auditable


@pytest.mark.network
def test_market_live_quote():
    """שליפת מחיר חי מחזירה ערך חיובי עם מקור."""
    from engine.providers import market

    q = market.get_quote("AAPL")
    assert q.price.value and q.price.value > 0
    assert q.price.source.name == "Yahoo Finance"
