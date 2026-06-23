"""ספק דיווחי מסחר של חברי הקונגרס (בית הנבחרים) מהמקור הרשמי.

מקור: House Clerk Financial Disclosures (ZIP שנתי, נתונים ממשלתיים רשמיים).
https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip

החלטת תכן (חשובה): מקורות צד-שלישי החינמיים שמספקים נתונים ברמת-עסקה (טיקר/סכום/כיוון)
נחסמו (house-stock-watcher S3 מחזיר 403). במקום לבנות על מקור שבור או לפרסר PDF באופן
שביר, המערכת נשענת על המקור הרשמי האמין ברמת-הדיווח: מי הגיש דיווח עסקה תקופתי (PTR),
מתי, עם קישור ישיר ל-PDF הרשמי. פרטי העסקה עצמם נמצאים ב-PDF ולכן מקושרים, לא מומצאים.
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import date, datetime

from .base import ProviderError
from .cache import cache_get, cache_set

_ZIP = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
_PDF = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc}.pdf"
_UA = {"User-Agent": "Mozilla/5.0 Barebone.AI research rotemstain23@gmail.com"}


def _iso(d: str) -> str:
    """ממיר M/D/YYYY ל-ISO. נופל בעמידות למחרוזת המקורית."""
    for fmt in ("%m/%d/%Y", "%-m/%-d/%Y"):
        try:
            return datetime.strptime(d, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.strptime(d.strip(), "%m/%d/%Y").date().isoformat()
    except ValueError:
        return d


def get_ptr_filings(year: int | None = None, limit: int = 50) -> dict:
    """מחזיר דיווחי עסקה תקופתיים (PTR) אחרונים של חברי בית הנבחרים, ממוין יורד לפי תאריך."""
    year = year or date.today().year
    cache_key = f"house_fd_{year}"
    rows = cache_get(cache_key, ttl=60 * 60 * 12)  # רענון פעמיים ביום
    if rows is None:
        import requests
        try:
            resp = requests.get(_ZIP.format(year=year), headers=_UA, timeout=30)
            resp.raise_for_status()
            zf = zipfile.ZipFile(io.BytesIO(resp.content))
            txt = zf.read(f"{year}FD.txt").decode("utf-8", "replace")
        except (requests.RequestException, zipfile.BadZipFile, KeyError) as exc:
            raise ProviderError(f"כשל בשליפת דיווחי קונגרס לשנת {year}: {exc}") from exc
        rows = list(csv.DictReader(io.StringIO(txt), delimiter="\t"))
        cache_set(cache_key, rows)

    ptr = []
    for r in rows:
        if r.get("FilingType") != "P":  # P = Periodic Transaction Report (דיווח עסקאות)
            continue
        doc = (r.get("DocID") or "").strip()
        name = " ".join(p for p in [r.get("Prefix", "").strip(), r.get("First", "").strip(),
                                    r.get("Last", "").strip(), r.get("Suffix", "").strip()] if p)
        statedst = (r.get("StateDst") or "").strip()
        ptr.append({
            "member": name,
            "state": statedst[:2],
            "district": statedst[2:],
            "filing_date": _iso(r.get("FilingDate", "")),
            "doc_id": doc,
            "pdf_url": _PDF.format(year=year, doc=doc) if doc else None,
        })
    ptr.sort(key=lambda x: x["filing_date"], reverse=True)
    return {
        "year": year,
        "filings": ptr[:limit],
        "total": len(ptr),
    }
