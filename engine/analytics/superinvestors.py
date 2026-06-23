"""שכבת אנליטיקה ל-13F: סקירת תיקי משקיעי-על ואיתור מי מחזיק בטיקר נתון.

חישובים דטרמיניסטיים בלבד (משקלים, מיון, התאמת שם). אפס LLM.
התאמת טיקר->החזקה נעשית לפי שם המנפיק (13F אינו כולל טיקר, רק CUSIP ושם),
ולכן מסומנת במפורש כהיוריסטיקה מבוססת-שם.
"""
from __future__ import annotations

import re

from ..providers import edgar, thirteenf
from ..providers.base import ProviderError

# מילים גנריות שאינן מסייעות בזיהוי המנפיק
_STOP = {"INC", "CORP", "CORPORATION", "CO", "COMPANY", "LTD", "LLC", "PLC",
         "THE", "GROUP", "HOLDINGS", "HOLDING", "CLASS", "COM", "NEW"}


def _norm_token(name: str) -> str:
    """המילה המשמעותית הראשונה בשם, באותיות גדולות וללא תווים מיוחדים."""
    words = re.sub(r"[^A-Za-z ]", " ", (name or "").upper()).split()
    for w in words:
        if w not in _STOP and len(w) >= 3:
            return w
    return words[0] if words else ""


def super_investor_overview(top_n: int = 10) -> dict:
    """סקירת תיקי כל משקיעי-העל: לכל מנהל top_n החזקות לפי שווי."""
    managers = thirteenf.get_super_investors()
    result = []
    for m in managers:
        holdings = sorted(m["holdings"], key=lambda h: h["value"], reverse=True)
        top = holdings[:top_n]
        for h in top:
            h["weight"] = round(h["value"] / m["total_value"] * 100, 2) if m["total_value"] else 0.0
        result.append({
            "manager": m["manager"],
            "cik": m["cik"],
            "period": m["period"],
            "filing_date": m["filing_date"],
            "total_value": m["total_value"],
            "positions": len(m["holdings"]),
            "top_holdings": top,
            "url": m["url"],
        })
    result.sort(key=lambda x: x["total_value"], reverse=True)
    return {
        "managers": result,
        "count": len(result),
        "source": {
            "name": "SEC EDGAR 13F-HR",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=13F-HR",
            "as_of": result[0]["filing_date"] if result else None,
        },
        "note": "עיכוב רגולטורי מובנה של עד 45 יום מתום הרבעון. שווי בדולרים מלאים.",
    }


def holders_of_ticker(ticker: str) -> dict:
    """אילו ממשקיעי-העל מחזיקים בטיקר נתון. התאמה לפי שם המנפיק (היוריסטיקה)."""
    try:
        _cik, company = edgar.get_cik(ticker)
    except ProviderError:
        company = ticker.upper()
    target = _norm_token(company)

    managers = thirteenf.get_super_investors()
    holders = []
    for m in managers:
        for h in m["holdings"]:
            if _norm_token(h["issuer"]) == target and target:
                weight = round(h["value"] / m["total_value"] * 100, 2) if m["total_value"] else 0.0
                holders.append({
                    "manager": m["manager"],
                    "issuer": h["issuer"],
                    "value": h["value"],
                    "shares": h["shares"],
                    "weight": weight,
                    "period": m["period"],
                    "url": m["url"],
                })
                break  # החזקה אחת למנהל
    holders.sort(key=lambda x: x["value"], reverse=True)
    total = sum(h["value"] for h in holders)
    return {
        "ticker": ticker.upper(),
        "company": company,
        "matched_on": target,
        "holders": holders,
        "holder_count": len(holders),
        "total_value": total,
        "source": {
            "name": "SEC EDGAR 13F-HR",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=13F-HR",
            "as_of": holders[0]["period"] if holders else None,
        },
        "note": ("התאמה לפי שם המנפיק (13F אינו כולל טיקר). "
                 + ("נמצאו מחזיקים." if holders else "אף אחד ממשקיעי-העל ברשימה לא מחזיק, או שהשם לא הותאם.")),
    }
