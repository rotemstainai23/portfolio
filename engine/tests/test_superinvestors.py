"""בדיקות Phase 7 - 13F Super Investors."""
from __future__ import annotations

import pytest

from engine.analytics import superinvestors as si
from engine.providers import thirteenf


def test_norm_token_strips_generics():
    # מילים גנריות (INC/CORP) לא נבחרות כטוקן מזהה
    assert si._norm_token("APPLE INC") == "APPLE"
    assert si._norm_token("NVIDIA CORP") == "NVIDIA"
    assert si._norm_token("The Coca Cola Co") == "COCA"


def test_super_investors_list_valid_ciks():
    # כל CIK מנורמל ל-10 ספרות
    for cik in thirteenf.SUPER_INVESTORS:
        assert len(cik) == 10 and cik.isdigit()


@pytest.mark.network
def test_berkshire_holdings_aggregated():
    m = thirteenf.get_manager_holdings("0001067983")
    assert m is not None
    assert m["total_value"] > 1e11  # תיק ברקשייר > 100 מיליארד
    # אין כפילויות CUSIP אחרי האיחוד
    cusips = [h["cusip"] for h in m["holdings"] if h["cusip"]]
    assert len(cusips) == len(set(cusips))


@pytest.mark.network
def test_holders_of_ticker_apple():
    r = si.holders_of_ticker("AAPL")
    assert r["matched_on"] == "APPLE"
    # ברקשייר מחזיקה אפל - חייבת להופיע, וכל מחזיק עם מקור
    managers = [h["manager"] for h in r["holders"]]
    assert any("Berkshire" in m for m in managers)
    for h in r["holders"]:
        assert h["value"] > 0 and "sec.gov" in h["url"]
