"""בדיקת חילוץ verdict וציון מפלטי סוכנים — הבאגים שנמצאו ב-2026-07-08."""
from engine.agents.chain import _extract_review


def test_watchlist_not_hijacked_by_maskana():
    # "מסקנה" מכילה "קנה" — אסור שזה ייתפס כ-BUY
    out = "אני מגיע למסקנה הבאה: אני ממליץ **WATCHLIST**. ציון 6 מתוך 10."
    r = _extract_review("CCJ", "executor", out)
    assert r["verdict"] == "WATCHLIST", r["verdict"]
    assert r["score"] == 6.0, r["score"]


def test_markdown_bold_score():
    out = "**המלצה**: WATCHLIST\n\n**ציון**: 7/10"
    r = _extract_review("CCJ", "analyst", out)
    assert r["verdict"] == "WATCHLIST"
    assert r["score"] == 7.0


def test_explicit_verdict_score_lines():
    out = "טקסט כלשהו עם המילה מעקב באמצע.\nVERDICT: BUY\nSCORE: 8"
    r = _extract_review("AAPL", "ic", out)
    assert r["verdict"] == "BUY"
    assert r["score"] == 8.0


def test_buy_price_not_matched():
    out = "הנתון buy_price אינו ורדיקט. ההחלטה: מעקב."
    r = _extract_review("MU", "ceo", out)
    assert r["verdict"] == "WATCHLIST"


def test_score_out_of_range_rejected():
    out = "VERDICT: PASS\nSCORE: 95"
    r = _extract_review("IBM", "devils", out)
    assert r["verdict"] == "PASS"
    assert r["score"] is None
