"""בדיקות Phase 6 - Congress Trading (מקור רשמי House Clerk)."""
from __future__ import annotations

import pytest

from engine.providers import congress
from engine.analytics import congress_report


def test_iso_date_parsing():
    assert congress._iso("3/31/2026") == "2026-03-31"
    assert congress._iso("12/5/2025") == "2025-12-05"


@pytest.mark.network
def test_congress_ptr_filings_have_official_pdf():
    r = congress_report.recent_congress_trades(year=2026, limit=20)
    assert r["total"] > 0 and r["shown"] > 0
    assert "House Clerk" in r["source"]["name"]
    for f in r["filings"]:
        assert f["member"]
        assert f["pdf_url"] and "disclosures-clerk.house.gov" in f["pdf_url"]
    # ממוין יורד לפי תאריך
    dates = [f["filing_date"] for f in r["filings"]]
    assert dates == sorted(dates, reverse=True)
