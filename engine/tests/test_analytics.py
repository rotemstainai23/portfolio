"""בדיקות שכבת ה-analytics הדטרמיניסטית (ללא רשת).

מאמתות את נכונות האינדיקטורים הטכניים, מודל ה-DCF, וחישובי הפונדמנטלים מול
ערכים ידועים ותכונות מתמטיות. בדיקות חיות (רשת) מסומנות network.
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from engine.analytics import dcf, fundamentals, technical
from engine.models import CompanyFacts, Source


# ---------- אינדיקטורים טכניים ----------

def test_sma_known_value():
    close = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
    assert technical.sma(close, 3).iloc[-1] == pytest.approx((8 + 9 + 10) / 3)


def test_rsi_rising_series_is_100():
    close = pd.Series(range(1, 40), dtype=float)
    assert technical.rsi(close).iloc[-1] == pytest.approx(100.0)


def test_rsi_falling_series_is_0():
    close = pd.Series(range(40, 1, -1), dtype=float)
    assert technical.rsi(close).iloc[-1] == pytest.approx(0.0)


def test_rsi_bounds():
    # סדרה מעורבת - RSI חייב להישאר בטווח 0..100
    import random

    random.seed(7)
    close = pd.Series([100 + random.uniform(-5, 5) for _ in range(100)])
    r = technical.rsi(close).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_macd_constant_series_is_zero():
    close = pd.Series([5.0] * 60)
    macd_line, signal_line, hist = technical.macd(close)
    assert macd_line.iloc[-1] == pytest.approx(0.0)
    assert hist.iloc[-1] == pytest.approx(0.0)


def test_atr_constant_range():
    # טווח יומי קבוע של 2 -> ATR מתכנס ל-2
    df = pd.DataFrame({"High": [10.0] * 30, "Low": [8.0] * 30, "Close": [9.0] * 30})
    assert technical.atr(df, 14).iloc[-1] == pytest.approx(2.0, abs=1e-6)


# ---------- DCF ----------

def test_dcf_known_value():
    # fcf0=100, growth=0, wacc=10%, terminal_growth=0, year=1:
    # שווי = (100+1000)/1.1 = 1000 בדיוק
    res = dcf.intrinsic_value(100.0, 0.0, 0.10, 0.0, years=1)
    assert res["ev"] == pytest.approx(1000.0, rel=1e-9)


def test_dcf_invalid_wacc_raises():
    with pytest.raises(ValueError):
        dcf.intrinsic_value(100.0, 0.05, 0.02, 0.03)


def test_dcf_higher_growth_higher_value():
    low = dcf.intrinsic_value(100, 0.03, 0.10, 0.02)["ev"]
    high = dcf.intrinsic_value(100, 0.08, 0.10, 0.02)["ev"]
    assert high > low


# ---------- פונדמנטלים (על עובדות סינתטיות) ----------

def _synthetic_facts() -> CompanyFacts:
    return CompanyFacts(
        ticker="TEST",
        cik="0000000000",
        name="Test Co",
        facts={
            "us-gaap": {
                "Revenues": {"units": {"USD": [
                    {"start": "2023-01-01", "end": "2023-12-31", "val": 1000, "fy": 2023, "form": "10-K"},
                    {"start": "2024-01-01", "end": "2024-12-31", "val": 1200, "fy": 2024, "form": "10-K"},
                ]}},
                "NetIncomeLoss": {"units": {"USD": [
                    {"start": "2024-01-01", "end": "2024-12-31", "val": 240, "fy": 2024, "form": "10-K"},
                ]}},
                "OperatingIncomeLoss": {"units": {"USD": [
                    {"start": "2024-01-01", "end": "2024-12-31", "val": 300, "fy": 2024, "form": "10-K"},
                ]}},
                "StockholdersEquity": {"units": {"USD": [
                    {"end": "2024-12-31", "val": 2000, "fy": 2024, "form": "10-K"},
                ]}},
            }
        },
        source=Source(name="SEC EDGAR", url="http://x", as_of="2025-01-01"),
    )


def test_fundamentals_growth_and_margins():
    rep = fundamentals.compute_fundamentals(_synthetic_facts(), price=None)
    assert rep.revenue.value == 1200
    assert rep.revenue_growth.value == pytest.approx(20.0)  # 1000 -> 1200
    assert rep.net_margin.value == pytest.approx(20.0)  # 240/1200
    assert rep.operating_margin.value == pytest.approx(25.0)  # 300/1200


def test_fundamentals_roic_present():
    rep = fundamentals.compute_fundamentals(_synthetic_facts(), price=None)
    # NOPAT = 300*0.79 = 237; invested = 2000 (אין חוב/מזומן) -> ROIC ~ 11.85%
    assert rep.roic is not None
    assert rep.roic.value == pytest.approx(11.85, abs=0.05)


def test_fundamentals_missing_data_is_none():
    empty = CompanyFacts(ticker="X", cik="0", name="X", facts={"us-gaap": {}},
                         source=Source(name="SEC EDGAR"))
    rep = fundamentals.compute_fundamentals(empty, price=None)
    assert rep.revenue is None and rep.pe is None


# ---------- בדיקות חיות ----------

@pytest.mark.network
def test_get_technical_live():
    rep = technical.get_technical("AAPL", period="1y")
    assert rep.last_price.value and rep.last_price.value > 0
    assert rep.rsi14.value is None or 0 <= rep.rsi14.value <= 100


@pytest.mark.network
def test_get_fundamentals_live():
    rep = fundamentals.get_fundamentals("AAPL")
    assert rep.revenue and rep.revenue.value > 0
    assert rep.net_margin is not None
