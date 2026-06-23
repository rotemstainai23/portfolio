"""ניתוח Smart Money - דירוג משמעות עסקאות בעלי עניין (Phase 5).

מקבל עסקאות Form 4 גולמיות מהספק ומדרג אותן: עסקאות שוק פתוח (קנייה P / מכירה S)
משמעותיות, ואילו מענקים ומימושי אופציות (A/M/F) שגרתיים. הכל דטרמיניסטי.
"""
from __future__ import annotations

from ..providers import insider

# קודי עסקה של Form 4 ומשמעותם
_CODE_LABEL = {
    "P": ("קנייה בשוק הפתוח", "buy"),
    "S": ("מכירה בשוק הפתוח", "sell"),
    "A": ("מענק/הקצאה", "routine"),
    "M": ("מימוש אופציה", "routine"),
    "F": ("ניכוי מס במניות", "routine"),
    "G": ("מתנה", "routine"),
    "C": ("המרה", "routine"),
    "X": ("מימוש אופציה", "routine"),
}


def _role(rec: dict) -> str:
    if rec.get("is_officer") and rec.get("title"):
        return rec["title"]
    if rec.get("is_director"):
        return "דירקטור"
    if rec.get("is_officer"):
        return "נושא משרה"
    return "בעל עניין"


def insider_report(ticker: str, limit: int = 20) -> dict:
    """דוח insider מדורג + סיכום אגרגטיבי (קניות מול מכירות בשוק הפתוח)."""
    raw = insider.get_recent_form4(ticker, limit=limit)
    rows = []
    for filing in raw["filings"]:
        role = _role(filing)
        for tx in filing["transactions"]:
            label, direction = _CODE_LABEL.get(tx["code"], (tx["code"], "routine"))
            value = (tx["shares"] * tx["price"]) if tx["price"] else None
            # ציון משמעות: עסקאות שוק פתוח גבוהות, שגרתיות נמוכות
            base = value or 0.0
            significance = base * (2.0 if direction in ("buy", "sell") else 0.2)
            rows.append({
                "owner": filing["owner"],
                "role": role,
                "date": tx["date"] or filing["filing_date"],
                "code": tx["code"],
                "action": label,
                "direction": direction,
                "shares": tx["shares"],
                "price": tx["price"],
                "value": round(value, 2) if value else None,
                "significance": significance,
                "url": filing["url"],
            })

    rows.sort(key=lambda r: r["significance"], reverse=True)

    buys = [r for r in rows if r["direction"] == "buy" and r["value"]]
    sells = [r for r in rows if r["direction"] == "sell" and r["value"]]
    buy_val = round(sum(r["value"] for r in buys), 2)
    sell_val = round(sum(r["value"] for r in sells), 2)
    net = round(buy_val - sell_val, 2)

    if buys and not sells:
        verdict = "אות חיובי: קניות בשוק הפתוח ללא מכירות"
    elif buy_val > sell_val and buys:
        verdict = "נטו קנייה בשוק הפתוח"
    elif sells and not buys:
        verdict = "מכירות בשוק הפתוח (לרוב שגרתי אצל מנהלים, אך ראוי לתשומת לב)"
    elif sell_val > buy_val:
        verdict = "נטו מכירה בשוק הפתוח"
    else:
        verdict = "פעילות מעורבת / שגרתית"

    return {
        "ticker": raw["ticker"],
        "name": raw["name"],
        "summary": {
            "open_market_buys": len(buys),
            "open_market_buy_value": buy_val,
            "open_market_sells": len(sells),
            "open_market_sell_value": sell_val,
            "net_value": net,
            "verdict": verdict,
        },
        "transactions": rows[:25],
        "source": {
            "name": "SEC EDGAR (Form 4)",
            "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=4&company={ticker.upper()}",
            "as_of": rows[0]["date"] if rows else None,
        },
        "note": "עסקאות שוק פתוח (קנייה P / מכירה S) משמעותיות יותר ממענקים ומימושי אופציות.",
    }
