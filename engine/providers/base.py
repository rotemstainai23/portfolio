"""ממשק בסיס לספקי נתונים + חריגות משותפות.

ההפשטה הזו מאפשרת להחליף מקור חינמי במקור בתשלום (למשל FMP) בלי לגעת
בשכבות analytics/agents - הן תלויות בממשק, לא במימוש.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import CompanyFacts, PriceQuote


class ProviderError(Exception):
    """תקלה כללית בשכבת הספקים (רשת, פרסור, נתון חסר)."""


class TickerNotFound(ProviderError):
    """טיקר לא נמצא במיפוי SEC."""


@runtime_checkable
class FundamentalsProvider(Protocol):
    """ספק נתונים פונדמנטליים (דוחות כספיים)."""

    def get_company_facts(self, ticker: str) -> CompanyFacts: ...


@runtime_checkable
class MarketProvider(Protocol):
    """ספק נתוני שוק (מחירים, היסטוריה)."""

    def get_quote(self, ticker: str) -> PriceQuote: ...
