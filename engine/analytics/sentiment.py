"""שכבת אנליטיקה לסנטימנט חדשות (Phase 8). דירוג דטרמיניסטי מבוסס לקסיקון.

זוהי שיטה היוריסטית שקופה (ספירת מילות מפתח חיוביות/שליליות בכותרת), לא LLM.
היא מסומנת ככזו ב-UI. כשיתווסף מפתח LLM ניתן יהיה להעשיר בניתוח נרטיבי עמוק יותר.
"""
from __future__ import annotations

import re

from ..providers import news as news_provider

# לקסיקון פיננסי (אנגלית - הכותרות באנגלית). שקוף וניתן לעריכה.
_POS = {"beat", "beats", "surge", "surges", "rally", "rallies", "jump", "jumps",
        "gain", "gains", "upgrade", "upgraded", "record", "strong", "growth",
        "profit", "raises", "raised", "outperform", "soar", "soars", "top", "tops",
        "win", "wins", "bullish", "rises", "rise", "boost", "high", "highs", "buy"}
_NEG = {"miss", "misses", "fall", "falls", "drop", "drops", "plunge", "plunges",
        "cut", "cuts", "downgrade", "downgraded", "weak", "loss", "losses",
        "lawsuit", "decline", "declines", "slump", "warn", "warns", "warning",
        "sink", "sinks", "crash", "slash", "fraud", "probe", "bearish", "sell",
        "concern", "concerns", "risk", "risks", "low", "lows", "fears"}


def _score_text(text: str) -> int:
    """ציון כותרת בודדת: מספר מילים חיוביות פחות שליליות."""
    words = re.findall(r"[a-z]+", (text or "").lower())
    pos = sum(1 for w in words if w in _POS)
    neg = sum(1 for w in words if w in _NEG)
    return pos - neg


def _label(score: int) -> str:
    if score > 0:
        return "חיובי"
    if score < 0:
        return "שלילי"
    return "ניטרלי"


def news_sentiment(ticker: str, limit: int = 15) -> dict:
    """מחזיר חדשות אחרונות עם דירוג סנטימנט פר-כותרת וסיכום מצרפי."""
    items = news_provider.get_news(ticker, limit=limit)
    scored = []
    for it in items:
        sc = _score_text(it["title"] + " " + it["summary"])
        scored.append({**it, "sentiment_score": sc, "sentiment": _label(sc)})

    pos = sum(1 for s in scored if s["sentiment_score"] > 0)
    neg = sum(1 for s in scored if s["sentiment_score"] < 0)
    neutral = len(scored) - pos - neg
    net = pos - neg
    if not scored:
        verdict = "אין חדשות זמינות"
    elif net > 1:
        verdict = "סנטימנט חיובי נטו בכותרות האחרונות"
    elif net < -1:
        verdict = "סנטימנט שלילי נטו בכותרות האחרונות"
    else:
        verdict = "סנטימנט מעורב/ניטרלי בכותרות האחרונות"

    return {
        "ticker": ticker.upper(),
        "items": scored,
        "count": len(scored),
        "positive": pos,
        "negative": neg,
        "neutral": neutral,
        "net": net,
        "verdict": verdict,
        "source": {
            "name": "Yahoo Finance RSS",
            "url": f"https://finance.yahoo.com/quote/{ticker.upper()}/news",
            "as_of": scored[0]["date"] if scored else None,
        },
        "method": "דירוג היוריסטי שקוף מבוסס לקסיקון מילות מפתח (לא LLM).",
    }
