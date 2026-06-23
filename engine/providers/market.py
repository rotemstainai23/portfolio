"""ספק נתוני שוק מ-yfinance (מחירים, היסטוריה, יעדי אנליסטים).

yfinance אינו רשמי ועלול להישבר; לכן מבודד מאחורי הממשק. נתיב גיבוי עתידי: Stooq.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf

from ..models import DataPoint, PriceQuote, Source
from .base import ProviderError

_SOURCE_NAME = "Yahoo Finance"
_YF_URL = "https://finance.yahoo.com/quote/{ticker}"


def _src(ticker: str) -> Source:
    return Source(
        name=_SOURCE_NAME,
        url=_YF_URL.format(ticker=ticker.upper()),
        as_of=date.today().isoformat(),
    )


def get_quote(ticker: str) -> PriceQuote:
    """מחזיר ציטוט מחיר נוכחי + שינוי יומי באחוזים."""
    try:
        tk = yf.Ticker(ticker)
        info = tk.fast_info
        price = float(info["last_price"])
        prev = float(info.get("previous_close") or price)
    except Exception as exc:  # yfinance זורק חריגות מגוונות
        raise ProviderError(f"כשל בשליפת מחיר עבור {ticker}: {exc}") from exc

    change_pct = ((price - prev) / prev * 100.0) if prev else None
    return PriceQuote(
        ticker=ticker.upper(),
        price=DataPoint(label="מחיר נוכחי", value=price, unit="USD", source=_src(ticker)),
        change_pct=DataPoint(
            label="שינוי יומי",
            value=round(change_pct, 2) if change_pct is not None else None,
            unit="%",
            source=_src(ticker),
        ),
    )


def get_price_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """מחזיר DataFrame היסטורי (OHLCV). משמש את שכבת ה-analytics הטכנית.

    זורק ProviderError אם אין נתונים.
    """
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
    except Exception as exc:
        raise ProviderError(f"כשל בשליפת היסטוריה עבור {ticker}: {exc}") from exc
    if df is None or df.empty:
        raise ProviderError(f"אין נתוני היסטוריה עבור {ticker}")
    return df


def get_analyst_targets(ticker: str) -> Optional[DataPoint]:
    """מחזיר יעד מחיר ממוצע של אנליסטים אם זמין."""
    try:
        info = yf.Ticker(ticker).info
        target = info.get("targetMeanPrice")
    except Exception:
        return None
    if target is None:
        return None
    return DataPoint(
        label="יעד מחיר ממוצע (אנליסטים)",
        value=float(target),
        unit="USD",
        source=_src(ticker),
    )
