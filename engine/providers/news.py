"""ספק חדשות מ-Yahoo Finance RSS (חינמי). מקור לכותרות עדכניות לפי טיקר.

מחזיר כותרות גולמיות (title, link, date, summary). דירוג הסנטימנט נעשה בשכבת
ה-analytics, לא כאן. RSS אינו רשמי אך יציב; מבודד מאחורי הממשק.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from .base import ProviderError
from .cache import cache_get, cache_set

_RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
_UA = {"User-Agent": "Mozilla/5.0 Barebone.AI research"}


def _clean(text: str) -> str:
    """מסיר תגי HTML מתקציר."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _parse_date(raw: str) -> str:
    """ממיר תאריך RSS (RFC822) ל-ISO. נופל בעמידות לטקסט המקורי."""
    if not raw:
        return ""
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(raw, fmt).astimezone(timezone.utc).date().isoformat()
        except ValueError:
            continue
    return raw


def get_news(ticker: str, limit: int = 15) -> list[dict]:
    """מחזיר כותרות חדשות אחרונות עבור טיקר. ריק אם אין/כשל (עמידות)."""
    ticker = ticker.upper()
    cache_key = f"news_{ticker}"
    cached = cache_get(cache_key, ttl=60 * 30)  # רענון כל חצי שעה
    if cached is not None:
        return cached[:limit]

    import requests

    try:
        resp = requests.get(_RSS.format(ticker=ticker), headers=_UA, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (requests.RequestException, ET.ParseError) as exc:
        raise ProviderError(f"כשל בשליפת חדשות עבור {ticker}: {exc}") from exc

    items = []
    for it in root.findall(".//item"):
        title = it.findtext("title")
        if not title:
            continue
        items.append({
            "title": title.strip(),
            "url": (it.findtext("link") or "").strip(),
            "date": _parse_date(it.findtext("pubDate") or ""),
            "summary": _clean(it.findtext("description") or "")[:300],
        })
    cache_set(cache_key, items)
    return items[:limit]
