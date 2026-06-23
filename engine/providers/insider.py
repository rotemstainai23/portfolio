"""ספק נתוני עסקאות בעלי עניין (Insider, Form 4) מ-SEC EDGAR.

זרימה: submissions API מספק את רשימת הדיווחים -> מסננים form=='4' -> מורידים את
ה-XML הגולמי של כל דיווח ומפרסרים בעלים, תפקיד ועסקאות. מקור רשמי, auditable.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

from ..config import SEC_USER_AGENT
from .base import ProviderError
from .cache import cache_get, cache_set, http_get_json
from . import edgar

_HEADERS = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/{doc}"


def _text(node: Optional[ET.Element]) -> Optional[str]:
    return node.text.strip() if node is not None and node.text else None


def _recent_form4(cik10: str, limit: int) -> list[dict]:
    """מחזיר מטא-דאטה של דיווחי Form 4 אחרונים (תאריך, accession, primaryDocument)."""
    data = http_get_json(
        _SUBMISSIONS.format(cik=cik10),
        _HEADERS,
        cache_key=f"sec_subs_{cik10}",
        ttl=60 * 60 * 6,
        is_sec=True,
    )
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    out = []
    for i, form in enumerate(forms):
        if form != "4":
            continue
        out.append({
            "date": recent["filingDate"][i],
            "accession": recent["accessionNumber"][i],
            "doc": recent["primaryDocument"][i],
        })
        if len(out) >= limit:
            break
    return out


def _parse_form4(cik_int: str, accession: str, primary_doc: str) -> Optional[dict]:
    """מוריד ומפרסר Form 4 גולמי. מחזיר None אם הפירסור נכשל (עמידות)."""
    acc = accession.replace("-", "")
    filename = primary_doc.split("/")[-1]  # מסיר תיקיית xslF345.../
    raw_url = _ARCHIVE.format(cik_int=cik_int, acc=acc, doc=filename)
    view_url = _ARCHIVE.format(cik_int=cik_int, acc=acc, doc=primary_doc)

    cache_key = f"form4_{acc}"
    cached = cache_get(cache_key, ttl=60 * 60 * 24 * 30)
    if cached is not None:
        return cached

    import requests
    from .cache import _throttle_sec

    _throttle_sec()
    try:
        resp = requests.get(raw_url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (requests.RequestException, ET.ParseError):
        return None

    def find(path: str) -> Optional[str]:
        return _text(root.find(path))

    transactions = []
    for nd in root.findall(".//nonDerivativeTransaction"):
        code = _text(nd.find(".//transactionCode"))
        shares = _text(nd.find(".//transactionShares/value"))
        price = _text(nd.find(".//transactionPricePerShare/value"))
        ad = _text(nd.find(".//transactionAcquiredDisposedCode/value"))
        tdate = _text(nd.find(".//transactionDate/value"))
        if not code or not shares:
            continue
        transactions.append({
            "date": tdate,
            "code": code,
            "shares": float(shares),
            "price": float(price) if price else None,
            "ad": ad,  # A=רכישה D=מימוש/מכירה
        })

    parsed = {
        "owner": find(".//rptOwnerName"),
        "is_director": find(".//reportingOwnerRelationship/isDirector") in ("1", "true"),
        "is_officer": find(".//reportingOwnerRelationship/isOfficer") in ("1", "true"),
        "title": find(".//officerTitle"),
        "transactions": transactions,
        "url": view_url,
    }
    cache_set(cache_key, parsed)
    return parsed


def get_recent_form4(ticker: str, limit: int = 15) -> dict:
    """מחזיר את עסקאות בעלי העניין האחרונות עבור טיקר (גולמי, ללא דירוג)."""
    cik10, name = edgar.get_cik(ticker)
    cik_int = str(int(cik10))
    filings = _recent_form4(cik10, limit)
    parsed = []
    for f in filings:
        rec = _parse_form4(cik_int, f["accession"], f["doc"])
        if rec and rec["transactions"]:
            rec["filing_date"] = f["date"]
            parsed.append(rec)
    return {"ticker": ticker.upper(), "name": name, "filings": parsed}
