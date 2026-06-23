"""ספק נתונים מ-SEC EDGAR (חינמי, רשמי, auditable).

מקורות:
- מיפוי טיקר->CIK: https://www.sec.gov/files/company_tickers.json
- עובדות XBRL: https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..config import SEC_USER_AGENT
from ..models import CompanyFacts, DataPoint, Source
from .base import TickerNotFound
from .cache import http_get_json

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

_HEADERS = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}

# קאש בזיכרון למיפוי הטיקרים (גדול יחסית, נטען פעם אחת)
_ticker_map: Optional[dict[str, tuple[str, str]]] = None


def _load_ticker_map() -> dict[str, tuple[str, str]]:
    """טוען וממפה ticker -> (cik10, company_name)."""
    global _ticker_map
    if _ticker_map is not None:
        return _ticker_map
    raw = http_get_json(
        _TICKERS_URL,
        _HEADERS,
        cache_key="sec_company_tickers",
        ttl=60 * 60 * 24 * 7,  # שבוע
        is_sec=True,
    )
    mapping: dict[str, tuple[str, str]] = {}
    # המבנה: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
    for row in raw.values():
        ticker = str(row.get("ticker", "")).upper()
        cik = str(row.get("cik_str", "")).zfill(10)
        title = row.get("title", "")
        if ticker:
            mapping[ticker] = (cik, title)
    _ticker_map = mapping
    return mapping


def get_cik(ticker: str) -> tuple[str, str]:
    """מחזיר (cik10, company_name) עבור טיקר. זורק TickerNotFound אם לא קיים."""
    mapping = _load_ticker_map()
    key = ticker.upper().strip()
    if key not in mapping:
        raise TickerNotFound(f"הטיקר {ticker} לא נמצא במיפוי SEC")
    return mapping[key]


def get_company_facts(ticker: str) -> CompanyFacts:
    """שולף את כל עובדות ה-XBRL של החברה מ-EDGAR."""
    cik, name = get_cik(ticker)
    url = _FACTS_URL.format(cik=cik)
    raw = http_get_json(
        url,
        _HEADERS,
        cache_key=f"sec_facts_{cik}",
        is_sec=True,
    )
    return CompanyFacts(
        ticker=ticker.upper(),
        cik=cik,
        name=raw.get("entityName", name),
        facts=raw.get("facts", {}),
        source=Source(
            name="SEC EDGAR",
            url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}",
            as_of=date.today().isoformat(),
        ),
    )


def latest_fact(
    facts: CompanyFacts,
    tag: str,
    *,
    taxonomy: str = "us-gaap",
    unit: str = "USD",
    label: Optional[str] = None,
) -> Optional[DataPoint]:
    """מחלץ את הערך העדכני ביותר של מושג XBRL נתון, עטוף ב-DataPoint.

    מחזיר None אם המושג לא קיים בדוחות.
    """
    concept = facts.facts.get(taxonomy, {}).get(tag)
    if not concept:
        return None
    units = concept.get("units", {}).get(unit)
    if not units:
        return None
    # בוחרים את הרשומה עם תאריך הסיום המאוחר ביותר (end)
    valid = [u for u in units if u.get("end") and u.get("val") is not None]
    if not valid:
        return None
    latest = max(valid, key=lambda u: u["end"])
    return DataPoint(
        label=label or concept.get("label") or tag,
        value=float(latest["val"]),
        unit=unit,
        source=Source(
            name="SEC EDGAR (XBRL)",
            url=facts.source.url,
            as_of=latest["end"],
        ),
        note=f"XBRL {taxonomy}:{tag}, form={latest.get('form', '?')}, fy={latest.get('fy', '?')}",
    )
