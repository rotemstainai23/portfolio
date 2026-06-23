"""בדיקות Phase 5 - Insider Intelligence."""
from __future__ import annotations

import pytest

from engine.analytics import smartmoney


@pytest.mark.network
def test_insider_report_live():
    rep = smartmoney.insider_report("AAPL", limit=10)
    assert rep["ticker"] == "AAPL"
    assert "summary" in rep and "verdict" in rep["summary"]
    # אם יש עסקאות, לכל אחת מקור (url דיווח) -> auditability
    for tx in rep["transactions"]:
        assert tx["url"] and "sec.gov" in tx["url"]
        assert tx["direction"] in ("buy", "sell", "routine")


@pytest.mark.network
def test_insider_significance_ordering():
    rep = smartmoney.insider_report("MSFT", limit=12)
    sig = [t["significance"] for t in rep["transactions"]]
    assert sig == sorted(sig, reverse=True)  # מדורג יורד לפי משמעות
