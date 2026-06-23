"""סכמות נתונים מרכזיות.

עיקרון העל: כל מספר במערכת עטוף ב-DataPoint עם מקור ותאריך, כך שהוא ניתן לאימות.
שכבת ה-LLM מקבלת רק DataPoint-ים מחושבים, ולעולם אינה ממציאה מספרים.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """מקור נתון בודד - לצורך auditability."""

    name: str = Field(..., description="שם המקור, למשל 'SEC EDGAR' או 'Yahoo Finance'")
    url: Optional[str] = Field(None, description="קישור ישיר למקור כשרלוונטי")
    as_of: Optional[str] = Field(None, description="תאריך הנתון בפורמט ISO (YYYY-MM-DD)")


class DataPoint(BaseModel):
    """ערך מספרי בודד הניתן לאימות מול מקורו. הליבה של עקרון ה-auditability."""

    label: str = Field(..., description="תווית קריאה, למשל 'הכנסות שנתיות'")
    value: Optional[float] = Field(None, description="הערך המספרי")
    unit: Optional[str] = Field(None, description="יחידה: USD, %, x, shares וכו'")
    source: Source
    note: Optional[str] = Field(None, description="הערה/הסבר קצר על אופן החישוב")


class CompanyFacts(BaseModel):
    """עובדות חברה מ-SEC EDGAR (XBRL companyfacts)."""

    ticker: str
    cik: str
    name: str
    facts: dict = Field(default_factory=dict, description="עובדות XBRL גולמיות")
    source: Source


class PriceQuote(BaseModel):
    """ציטוט מחיר נוכחי."""

    ticker: str
    price: DataPoint
    change_pct: Optional[DataPoint] = None
    currency: str = "USD"


class FundamentalReport(BaseModel):
    """דוח ניתוח פונדמנטלי - כל שדה מספרי הוא DataPoint עם מקור (או None אם חסר)."""

    ticker: str
    name: str
    revenue: Optional[DataPoint] = None
    revenue_growth: Optional[DataPoint] = None
    gross_margin: Optional[DataPoint] = None
    operating_margin: Optional[DataPoint] = None
    net_margin: Optional[DataPoint] = None
    fcf: Optional[DataPoint] = None
    roic: Optional[DataPoint] = None
    market_cap: Optional[DataPoint] = None
    pe: Optional[DataPoint] = None
    ps: Optional[DataPoint] = None
    ev_ebitda: Optional[DataPoint] = None
    assumptions: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)


class TechnicalReport(BaseModel):
    """דוח ניתוח טכני - כל הערכים מחושבים אלגוריתמית מהיסטוריית מחירים."""

    ticker: str
    last_price: Optional[DataPoint] = None
    sma50: Optional[DataPoint] = None
    sma200: Optional[DataPoint] = None
    rsi14: Optional[DataPoint] = None
    macd: Optional[DataPoint] = None
    macd_signal: Optional[DataPoint] = None
    atr14: Optional[DataPoint] = None
    trend: Optional[str] = None
    support: list[float] = Field(default_factory=list)
    resistance: list[float] = Field(default_factory=list)
    entry_zone: Optional[list[float]] = None
    exit_zone: Optional[list[float]] = None
    stop_loss: Optional[DataPoint] = None
    sources: list[Source] = Field(default_factory=list)


class ResearchAnswer(BaseModel):
    """תשובת מחקר מסונתזת - הפלט הסופי של ה-Research Terminal."""

    question: str
    ticker: str
    summary: str = Field(..., description="תשובה מוסברת בשפה טבעית")
    data_points: list[DataPoint] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    reasoning: list[str] = Field(
        default_factory=list, description="שרשרת ההיגיון - שקיפות מלאה"
    )
