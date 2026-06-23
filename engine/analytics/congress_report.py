"""שכבת אנליטיקה לדיווחי מסחר של הקונגרס (Phase 6).

עוטף את המקור הרשמי ומוסיף מטא-דאטה של מקור והבהרת כיסוי. אפס LLM.
"""
from __future__ import annotations

from ..providers import congress


def recent_congress_trades(year: int | None = None, limit: int = 50) -> dict:
    """דיווחי PTR אחרונים מבית הנבחרים, עם מקור והבהרת כיסוי שקופה."""
    data = congress.get_ptr_filings(year=year, limit=limit)
    filings = data["filings"]
    return {
        "year": data["year"],
        "filings": filings,
        "total": data["total"],
        "shown": len(filings),
        "source": {
            "name": "U.S. House Clerk - Financial Disclosures",
            "url": "https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure",
            "as_of": filings[0]["filing_date"] if filings else None,
        },
        "note": ("מוצגים דיווחי עסקה תקופתיים (PTR) רשמיים: מי הגיש ומתי, עם קישור ל-PDF הרשמי. "
                 "פירוט העסקאות (טיקר, סכום, כיוון) נמצא בתוך ה-PDF. "
                 "מקורות צד-שלישי החינמיים לנתונים ברמת-עסקה חסומים כעת, ולכן לא נבנה עליהם."),
    }
