"""בדיקות Phase 4 - Earnings Intelligence (חישוב YoY לפי תאריך)."""
from __future__ import annotations

import pytest

from engine.analytics import earnings


def test_yoy_matches_by_date_not_position():
    # סדרה שמדלגת על רבעון (כמו דילוג Q4 פיסקלי). YoY חייב להתאים לפי תאריך.
    series = [
        {"end": "2025-03-29", "val": 100.0},
        {"end": "2025-06-28", "val": 110.0},
        {"end": "2025-12-27", "val": 140.0},  # דילוג על ספטמבר
        {"end": "2026-03-28", "val": 120.0},  # אחרון, שנה אחרי 2025-03-29
    ]
    # 120 מול 100 = +20%, ולא מול הרשומה במיקום -? )
    assert earnings._yoy(series) == 20.0


def test_yoy_returns_none_without_year_ago_match():
    series = [{"end": "2026-03-28", "val": 120.0}, {"end": "2025-12-27", "val": 140.0}]
    # אין רשומה בערך שנה אחורה -> None
    assert earnings._yoy(series) is None


@pytest.mark.network
def test_earnings_live_apple_official_source():
    e = earnings.get_earnings("AAPL")
    assert e["quarterly_revenue"] and e["quarterly_eps"]
    assert "EDGAR" in e["source"]["name"]
    # צמיחת ההכנסות חיובית ובטווח סביר (לא באג ההיסט הישן)
    assert e["revenue_yoy"] is not None and e["revenue_yoy"] > 0
