"""בדיקות Phase 9 - Portfolio Intelligence (חישוב טהור)."""
from __future__ import annotations

from engine.analytics import portfolio as pf


def _sample():
    return [
        {"symbol": "AAA", "name": "A", "quantity": 10, "buy_price": 10,
         "current_price": 15, "sector": "Tech", "layer": "Growth", "risk_score": 4},
        {"symbol": "BBB", "name": "B", "quantity": 5, "buy_price": 20,
         "current_price": 16, "sector": "Energy", "layer": "Speculation", "risk_score": 8},
    ]


def test_pnl_and_weights():
    r = pf.compute_portfolio(_sample(), cash=20.0)
    # AAA: 10*15=150 שווי, עלות 100, רווח 50 (+50%)
    aaa = next(h for h in r["holdings"] if h["symbol"] == "AAA")
    assert aaa["value"] == 150 and aaa["pnl"] == 50 and aaa["pnl_pct"] == 50.0
    # BBB: 5*16=80 שווי, עלות 100, הפסד -20 (-20%)
    bbb = next(h for h in r["holdings"] if h["symbol"] == "BBB")
    assert bbb["value"] == 80 and bbb["pnl_pct"] == -20.0
    # סך הכל: מושקע 230 + מזומן 20 = 250
    assert r["invested_value"] == 230 and r["total_value"] == 250


def test_concentration_flags():
    r = pf.compute_portfolio(_sample(), cash=20.0)
    # AAA = 150/250 = 60% > 20% => דגל ריכוז
    assert any("AAA" in f for f in r["concentration_flags"])
    # Speculation = 80/230 = 34.8% > 20% => דגל ספקולציה
    assert any("ספקולטיבית" in f for f in r["concentration_flags"])


def test_unpriced_holding_is_robust():
    holds = _sample()
    holds[0]["current_price"] = None  # מחיר חסר
    r = pf.compute_portfolio(holds, cash=0.0)
    aaa = next(h for h in r["holdings"] if h["symbol"] == "AAA")
    assert aaa["value"] is None and aaa["priced"] is False
    # החישוב הכולל לא נופל, מתבסס על מה שתומחר בלבד
    assert r["invested_value"] == 80


def test_weighted_risk():
    r = pf.compute_portfolio(_sample(), cash=0.0)
    # סיכון משוקלל: (4*150 + 8*80)/230 = 1240/230 = 5.39
    assert r["weighted_risk"] == 5.39
