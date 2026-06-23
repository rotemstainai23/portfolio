"""שכבת אנליטיקה לדוחות רווחים (Phase 4). מבוסס נתונים רשמיים מ-EDGAR XBRL.

החלטת תכן: אין מקור חינמי רשמי מלא לתמלילי שיחות ועידה ולתחזיות אנליסטים, ולכן
המערכת מתמקדת במה שכן רשמי ו-auditable: EPS מדולל והכנסות רבעוניים מדוחות 10-Q/10-K,
כולל צמיחה שנתית (YoY) מול אותו רבעון אשתקד. תאריך הדוח הבא נשלף מ-yfinance (best-effort).
חישובים דטרמיניסטיים בלבד, אפס LLM.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..providers import edgar
from ..providers.base import ProviderError, TickerNotFound
from . import xbrl


def _yoy(series: list[dict]) -> Optional[float]:
    """צמיחה שנתית: הרבעון האחרון מול הרבעון שהסתיים לפני כ-שנה.

    מתאים לפי תאריך (כ-365 ימים אחורה) ולא לפי היסט מיקום, כי הסדרה הרבעונית
    מדלגת על הרבעון הפיסקלי הרביעי (הוא מופיע רק בתוך הדוח השנתי, לא כמקטע 90 יום).
    """
    if len(series) < 2:
        return None
    latest = series[-1]
    try:
        latest_end = date.fromisoformat(latest["end"])
    except ValueError:
        return None
    best = None
    best_gap = None
    for s in series[:-1]:
        try:
            gap = abs((latest_end - date.fromisoformat(s["end"])).days - 365)
        except ValueError:
            continue
        if gap <= 25 and (best_gap is None or gap < best_gap):  # חלון של +-25 יום סביב שנה
            best, best_gap = s, gap
    if not best or not best["val"]:
        return None
    return round((latest["val"] / best["val"] - 1) * 100, 1)


def _next_earnings_date(ticker: str) -> Optional[str]:
    """תאריך הדוח הבא מ-yfinance (best-effort, לא חוסם אם נכשל)."""
    try:
        import yfinance as yf
        cal = yf.Ticker(ticker).calendar
        dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
        if dates:
            d = dates[0]
            return d.isoformat() if hasattr(d, "isoformat") else str(d)
    except Exception:
        return None
    return None


def get_earnings(ticker: str, quarters: int = 8) -> dict:
    """מחזיר היסטוריית רווחים רבעונית רשמית + צמיחה שנתית + תאריך דוח הבא."""
    facts = edgar.get_company_facts(ticker)

    rev = xbrl.quarterly_series(facts, "revenue")
    eps = xbrl.quarterly_series(facts, "eps_diluted")
    ni = xbrl.quarterly_series(facts, "net_income")

    def _fmt(series: list[dict]) -> list[dict]:
        return [{"end": s["end"], "fy": s.get("fy"), "fp": s.get("fp"),
                 "value": s["val"], "form": s.get("form")} for s in series[-quarters:]]

    src = {"name": "SEC EDGAR (XBRL)", "url": facts.source.url,
           "as_of": rev[-1]["end"] if rev else (eps[-1]["end"] if eps else None)}

    return {
        "ticker": ticker.upper(),
        "name": facts.name,
        "quarterly_revenue": _fmt(rev),
        "quarterly_eps": _fmt(eps),
        "quarterly_net_income": _fmt(ni),
        "revenue_yoy": _yoy(rev),
        "eps_yoy": _yoy(eps),
        "latest_quarter": rev[-1]["end"] if rev else (eps[-1]["end"] if eps else None),
        "next_earnings_date": _next_earnings_date(ticker),
        "source": src,
        "note": ("נתוני EPS מדולל והכנסות רבעוניים מדוחות 10-Q/10-K רשמיים. "
                 "תמלילים ותחזיות אנליסטים אינם זמינים במקור חינמי רשמי ולכן אינם כלולים."),
    }


def get_earnings_safe(ticker: str) -> dict:
    """עטיפה שמחזירה שגיאה מובנית במקום לזרוק (לשימוש ה-frontend)."""
    try:
        return get_earnings(ticker)
    except (TickerNotFound, ProviderError) as exc:
        return {"ticker": ticker.upper(), "error": str(exc)}
