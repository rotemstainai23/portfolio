"""ניתוח טכני דטרמיניסטי - pandas/numpy בלבד, אפס LLM.

כל האינדיקטורים מחושבים בנוסחאות סטנדרטיות (RSI/ATR בשיטת Wilder, MACD ב-EMA).
שכבת ה-LLM, אם פעילה, רק מסבירה את המשמעות. היא לעולם אינה מחשבת את המספרים.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd

from ..models import DataPoint, Source, TechnicalReport
from ..providers import market


# ---------- אינדיקטורים (פונקציות טהורות על Series/DataFrame) ----------

def sma(close: pd.Series, n: int) -> pd.Series:
    """ממוצע נע פשוט."""
    return close.rolling(n).mean()


def ema(close: pd.Series, n: int) -> pd.Series:
    """ממוצע נע מעריכי."""
    return close.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    """RSI בשיטת Wilder. ערכים בטווח 0..100."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / n, min_periods=n, adjust=False).mean()
    rs = avg_gain / avg_loss
    out = 100.0 - 100.0 / (1.0 + rs)
    # כשאין הפסדים כלל RSI=100; כשאין רווחים כלל RSI=0
    out = out.where(avg_loss != 0, 100.0)
    out = out.where(avg_gain != 0, out.where(avg_loss == 0, 0.0))
    return out


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """מחזיר (קו MACD, קו אות, היסטוגרמה)."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line, macd_line - signal_line


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Average True Range בשיטת Wilder. דורש עמודות High/Low/Close."""
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / n, min_periods=n, adjust=False).mean()


def swing_levels(df: pd.DataFrame, k: int = 5) -> tuple[list[float], list[float]]:
    """מזהה swing highs/lows: נקודה היא קיצון אם היא המקסימום/מינימום בחלון +-k.

    מחזיר (highs, lows) מתוך ~6 החודשים האחרונים.
    """
    recent = df.tail(130)  # כ-6 חודשי מסחר
    highs, lows = [], []
    h, low = recent["High"].values, recent["Low"].values
    for i in range(k, len(recent) - k):
        window_h = h[i - k : i + k + 1]
        window_l = low[i - k : i + k + 1]
        if h[i] == window_h.max():
            highs.append(round(float(h[i]), 2))
        if low[i] == window_l.min():
            lows.append(round(float(low[i]), 2))
    return highs, lows


# ---------- אורקסטרציה ----------

def _last(series: pd.Series) -> Optional[float]:
    s = series.dropna()
    return round(float(s.iloc[-1]), 2) if not s.empty else None


def get_technical(ticker: str, period: str = "1y") -> TechnicalReport:
    """מחשב דוח טכני מלא עבור טיקר מהיסטוריית מחירים."""
    df = market.get_price_history(ticker, period=period)
    as_of = df.index[-1].date().isoformat() if hasattr(df.index[-1], "date") else date.today().isoformat()
    src = Source(name="Yahoo Finance", url=f"https://finance.yahoo.com/quote/{ticker.upper()}", as_of=as_of)
    close = df["Close"]
    last_price = _last(close)

    report = TechnicalReport(ticker=ticker.upper())
    report.last_price = DataPoint(label="מחיר אחרון", value=last_price, unit="USD", source=src)
    report.sma50 = DataPoint(label="ממוצע נע 50", value=_last(sma(close, 50)), unit="USD", source=src)
    report.sma200 = DataPoint(label="ממוצע נע 200", value=_last(sma(close, 200)), unit="USD", source=src)
    report.rsi14 = DataPoint(label="RSI(14)", value=_last(rsi(close)), unit="", source=src,
                             note="מעל 70 = קניית יתר, מתחת 30 = מכירת יתר")
    macd_line, signal_line, _ = macd(close)
    report.macd = DataPoint(label="MACD", value=_last(macd_line), unit="", source=src)
    report.macd_signal = DataPoint(label="קו אות MACD", value=_last(signal_line), unit="", source=src)
    atr_val = _last(atr(df))
    report.atr14 = DataPoint(label="ATR(14)", value=atr_val, unit="USD", source=src,
                             note="תנודתיות ממוצעת יומית")

    # מגמה לפי יחס מחיר לממוצעים
    s50, s200 = report.sma50.value, report.sma200.value
    if last_price and s50 and s200:
        if last_price > s50 > s200:
            report.trend = "עולה (uptrend)"
        elif last_price < s50 < s200:
            report.trend = "יורד (downtrend)"
        else:
            report.trend = "מעורב (sideways)"

    # תמיכות/התנגדויות לפי swing levels ביחס למחיר הנוכחי
    highs, lows = swing_levels(df)
    if last_price:
        supports = sorted({lv for lv in lows + highs if lv < last_price}, reverse=True)[:3]
        resistances = sorted({lv for lv in highs + lows if lv > last_price})[:3]
        report.support = supports
        report.resistance = resistances

        # אזורי כניסה/יציאה והצעת stop loss (מבוססי ATR)
        if supports:
            near_sup = supports[0]
            report.entry_zone = [round(near_sup, 2), round(near_sup * 1.01, 2)]
            if atr_val:
                report.stop_loss = DataPoint(
                    label="הצעת Stop Loss", value=round(near_sup - atr_val, 2), unit="USD", source=src,
                    note="תמיכה קרובה פחות ATR אחד",
                )
        if resistances:
            near_res = resistances[0]
            report.exit_zone = [round(near_res * 0.99, 2), round(near_res, 2)]

    report.sources = [src]
    return report
