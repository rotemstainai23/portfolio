"""בדיקות Phase 8 - News & Sentiment (דירוג דטרמיניסטי)."""
from __future__ import annotations

import pytest

from engine.analytics import sentiment


def test_score_positive_negative_neutral():
    assert sentiment._score_text("Apple beats earnings, shares surge") > 0
    assert sentiment._score_text("Stock plunges on weak guidance and lawsuit") < 0
    assert sentiment._score_text("Company holds annual meeting") == 0


def test_label_mapping():
    assert sentiment._label(2) == "חיובי"
    assert sentiment._label(-1) == "שלילי"
    assert sentiment._label(0) == "ניטרלי"


@pytest.mark.network
def test_news_sentiment_live_has_sources():
    r = sentiment.news_sentiment("AAPL", limit=10)
    assert r["count"] > 0
    assert r["positive"] + r["negative"] + r["neutral"] == r["count"]
    for it in r["items"]:
        assert it["title"] and it["sentiment"] in ("חיובי", "שלילי", "ניטרלי")
