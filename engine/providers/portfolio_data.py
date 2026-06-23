"""ספק נתוני התיק האישי. קורא את portfolio.json הקיים של מערכת ה-portfolio.

מקור הנתונים הוא קובץ מקומי שבבעלות המשתמש, ולכן הוא מקור אמת מלא ו-auditable.
נתיב ברירת מחדל: ~/portfolio/portfolio.json. ניתן לעקוף עם משתנה סביבה BAREBONE_PORTFOLIO.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .base import ProviderError

_DEFAULT = Path.home() / "portfolio" / "portfolio.json"


def _path() -> Path:
    override = os.environ.get("BAREBONE_PORTFOLIO")
    return Path(override) if override else _DEFAULT


def load_portfolio() -> dict:
    """טוען את קובץ התיק. זורק ProviderError אם חסר או לא תקין."""
    p = _path()
    if not p.exists():
        raise ProviderError(f"קובץ התיק לא נמצא: {p}")
    try:
        with p.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderError(f"כשל בקריאת קובץ התיק: {exc}") from exc
    if "holdings" not in data:
        raise ProviderError("מבנה קובץ התיק לא תקין (חסר holdings)")
    return data


def portfolio_source() -> dict:
    """מתאר את מקור נתוני התיק עבור תג ה-auditability."""
    return {"name": "portfolio.json (מקומי)", "url": None, "as_of": str(_path())}
