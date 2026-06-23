"""שכבת cache + rate limiting + retry לבקשות HTTP חיצוניות.

מטרה: לעמוד במגבלות הקצב של SEC, להפחית קריאות חוזרות, ולספק עמידות לתקלות רשת.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Optional

import requests

from ..config import CACHE_DIR, CACHE_TTL_DEFAULT, SEC_MIN_INTERVAL, logger

# נעילה גלובלית לוויסות קצב מול sec.gov
_sec_lock = threading.Lock()
_last_sec_call = 0.0


def _cache_path(key: str) -> Path:
    """ממפה מפתח cache לקובץ JSON על הדיסק."""
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
    return CACHE_DIR / f"{safe}.json"


def cache_get(key: str, ttl: int = CACHE_TTL_DEFAULT) -> Optional[Any]:
    """מחזיר ערך מה-cache אם קיים ולא פג. אחרת None."""
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if time.time() - payload.get("_ts", 0) > ttl:
        return None
    return payload.get("data")


def cache_set(key: str, data: Any) -> None:
    """שומר ערך ב-cache עם חותמת זמן."""
    path = _cache_path(key)
    try:
        path.write_text(
            json.dumps({"_ts": time.time(), "data": data}, ensure_ascii=False),
            encoding="utf-8",
        )
    except (OSError, TypeError) as exc:
        logger.warning("cache_set נכשל עבור %s: %s", key, exc)


def _throttle_sec() -> None:
    """וויסות קצב מול SEC: לפחות SEC_MIN_INTERVAL שניות בין בקשות."""
    global _last_sec_call
    with _sec_lock:
        delta = time.time() - _last_sec_call
        if delta < SEC_MIN_INTERVAL:
            time.sleep(SEC_MIN_INTERVAL - delta)
        _last_sec_call = time.time()


def http_get_json(
    url: str,
    headers: dict[str, str],
    *,
    cache_key: Optional[str] = None,
    ttl: int = CACHE_TTL_DEFAULT,
    is_sec: bool = False,
    retries: int = 3,
) -> Any:
    """בקשת GET שמחזירה JSON, עם cache, retry ו-throttle אופציונלי ל-SEC.

    זורק requests.HTTPError אם כל הניסיונות נכשלו.
    """
    if cache_key:
        cached = cache_get(cache_key, ttl)
        if cached is not None:
            return cached

    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        if is_sec:
            _throttle_sec()
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if cache_key:
                cache_set(cache_key, data)
            return data
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            wait = min(2 ** attempt, 8)
            logger.warning(
                "בקשה נכשלה (%d/%d) %s: %s - ממתין %ds",
                attempt,
                retries,
                url,
                exc,
                wait,
            )
            time.sleep(wait)

    raise requests.HTTPError(f"כל הניסיונות נכשלו עבור {url}: {last_exc}")
