"""ספק נתוני 13F (החזקות מוסדיות של משקיעי-על) מ-SEC EDGAR.

זרימה: לכל CIK של מנהל השקעות -> submissions API -> דיווח 13F-HR אחרון ->
מאתרים את ה-information table (קובץ ה-XML שאינו primary_doc) -> מפרסרים את
ההחזקות (issuer, cusip, value, shares). מקור רשמי, auditable.

הערה על יחידות: החל מ-2023 שדה value מדווח בדולרים מלאים (לא באלפים).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Optional

from ..config import SEC_USER_AGENT, logger
from .base import ProviderError
from .cache import cache_get, cache_set, http_get_json

_HEADERS = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
_FOLDER = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/"

# רשימת משקיעי-על ידועים לפי CIK רשמי ב-SEC. השם נשלף דינמית מ-submissions
# (entityName) כדי שהשיוך תמיד יהיה נכון, גם אם הרשימה הזו תתיישן.
SUPER_INVESTORS: dict[str, str] = {
    "0001067983": "Berkshire Hathaway (Warren Buffett)",
    "0001649339": "Scion Asset Management (Michael Burry)",
    "0001336528": "Pershing Square (Bill Ackman)",
    "0001350694": "Bridgewater Associates (Ray Dalio)",
    "0001037389": "Renaissance Technologies",
    "0001656456": "Appaloosa (David Tepper)",
    "0001536411": "Duquesne Family Office (Stanley Druckenmiller)",
    "0001061768": "Baupost Group (Seth Klarman)",
    "0001040273": "Third Point (Dan Loeb)",
    "0001079114": "Greenlight Capital (David Einhorn)",
}


def _norm_cik(cik: str) -> str:
    """מנרמל ל-10 ספרות עם אפסים מובילים."""
    return str(int(cik)).zfill(10)


def _text(node: Optional[ET.Element]) -> Optional[str]:
    return node.text.strip() if node is not None and node.text else None


def _tag(elem: ET.Element) -> str:
    """מסיר namespace מתגית XML."""
    return re.sub(r"\{.*\}", "", elem.tag)


def _latest_13f(cik10: str) -> Optional[dict]:
    """מאתר את דיווח ה-13F-HR האחרון: accession, תאריך דיווח, תקופת הדיווח, שם הישות."""
    data = http_get_json(
        _SUBMISSIONS.format(cik=cik10),
        _HEADERS,
        cache_key=f"sec_subs_{cik10}",
        ttl=60 * 60 * 6,
        is_sec=True,
    )
    name = data.get("name") or data.get("entityName") or cik10
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    for i, form in enumerate(forms):
        if form != "13F-HR":
            continue
        return {
            "entity_name": name,
            "accession": recent["accessionNumber"][i],
            "filing_date": recent["filingDate"][i],
            "period": recent.get("reportDate", [""] * len(forms))[i],
        }
    return None


def _info_table_url(cik_int: str, accession: str) -> Optional[str]:
    """מאתר את קובץ ה-information table בתיקיית הדיווח (ה-XML שאינו primary_doc)."""
    acc = accession.replace("-", "")
    folder = _FOLDER.format(cik_int=cik_int, acc=acc)
    index = http_get_json(
        folder + "index.json",
        _HEADERS,
        cache_key=f"f13_idx_{acc}",
        ttl=60 * 60 * 24 * 30,
        is_sec=True,
    )
    for item in index.get("directory", {}).get("item", []):
        name = item.get("name", "")
        if name.endswith(".xml") and "primary_doc" not in name:
            return folder + name
    return None


def _parse_info_table(url: str, cache_key: str) -> list[dict]:
    """מוריד ומפרסר את ה-information table. מחזיר רשימת החזקות."""
    cached = cache_get(cache_key, ttl=60 * 60 * 24 * 30)
    if cached is not None:
        return cached

    import requests
    from .cache import _throttle_sec

    _throttle_sec()
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=25)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning("כשל בפירסור 13F info table %s: %s", url, exc)
        return []

    holdings = []
    for info in (e for e in root.iter() if _tag(e) == "infoTable"):
        rec: dict = {}
        for c in info.iter():
            t = _tag(c)
            if t in ("nameOfIssuer", "cusip", "value", "sshPrnamt", "titleOfClass"):
                rec.setdefault(t, (c.text or "").strip())
        issuer = rec.get("nameOfIssuer")
        value = rec.get("value")
        if not issuer or not value:
            continue
        holdings.append({
            "issuer": issuer,
            "cusip": rec.get("cusip", ""),
            "value": float(value),  # דולרים מלאים (post-2022)
            "shares": float(rec.get("sshPrnamt") or 0),
        })
    cache_set(cache_key, holdings)
    return holdings


def get_manager_holdings(cik: str) -> Optional[dict]:
    """מחזיר את ההחזקות העדכניות של מנהל לפי CIK, או None אם אין דיווח 13F."""
    cik10 = _norm_cik(cik)
    latest = _latest_13f(cik10)
    if not latest:
        return None
    cik_int = str(int(cik10))
    table_url = _info_table_url(cik_int, latest["accession"])
    if not table_url:
        return None
    acc = latest["accession"].replace("-", "")
    raw = _parse_info_table(table_url, cache_key=f"f13_tbl_{acc}")
    # ב-13F החזקה גדולה מפוצלת לעיתים למספר שורות (לפי סמכות הצבעה / מנהל משנה).
    # מאחדים לפי CUSIP כדי לקבל את השווי האמיתי של כל פוזיציה.
    agg: dict[str, dict] = {}
    for h in raw:
        key = h["cusip"] or h["issuer"]
        if key in agg:
            agg[key]["value"] += h["value"]
            agg[key]["shares"] += h["shares"]
        else:
            agg[key] = dict(h)
    holdings = list(agg.values())
    total = sum(h["value"] for h in holdings)
    return {
        "cik": cik10,
        "manager": SUPER_INVESTORS.get(cik10, latest["entity_name"]),
        "entity_name": latest["entity_name"],
        "filing_date": latest["filing_date"],
        "period": latest["period"],
        "total_value": total,
        "holdings": holdings,
        "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik10}&type=13F-HR",
    }


def get_super_investors() -> list[dict]:
    """מחזיר את ההחזקות של כל משקיעי-העל ברשימה. מדלג בעמידות על מי שאין לו 13F."""
    out = []
    for cik in SUPER_INVESTORS:
        try:
            rec = get_manager_holdings(cik)
        except ProviderError as exc:
            logger.warning("כשל בשליפת 13F עבור CIK %s: %s", cik, exc)
            rec = None
        if rec and rec["holdings"]:
            out.append(rec)
    return out
