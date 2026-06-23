"""CLI יחיד למנוע engine: מחקר מניה on-demand -> JSON סטטי ל-PWA.

הרצה (משורש portfolio):
    python -m engine.run --mode research --ticker AAPL

כותב ל-analyses/_research/<TICKER>/report.json + report.js (window.RESEARCH_DATA).
כל מקטע fail-soft: כשל במקור אחד לא מפיל את הדוח, רק מסומן. כך הפערים גלויים
ולא מסתתרים מאחורי קריסה.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import db
from .agents import synthesis
from .analytics import dcf as dcf_mod
from .analytics import earnings, fundamentals, sentiment, smartmoney, superinvestors, technical
from .config import logger
from .providers import market
from .providers.base import ProviderError, TickerNotFound

ROOT = Path(__file__).resolve().parent.parent  # portfolio/
RESEARCH_DIR = ROOT / "analyses" / "_research"


def _safe(label: str, fn: Callable[[], Any]) -> Any:
    """מריץ fn, מחזיר את תוצאתו או מילון שגיאה. מקטע אחד לא מפיל את הדוח."""
    try:
        return fn()
    except (TickerNotFound, ProviderError) as exc:
        logger.warning("מקטע %s נכשל: %s", label, exc)
        return {"error": str(exc), "section": label}
    except Exception as exc:  # ponytail: fail-soft מכוון - מקור חיצוני אחד לא מפיל הכל
        logger.warning("מקטע %s שגיאה לא צפויה: %s", label, exc)
        return {"error": str(exc), "section": label}


def _dump(obj: Any) -> Any:
    """ממיר pydantic ל-dict אם צריך."""
    return obj.model_dump() if hasattr(obj, "model_dump") else obj


def research(ticker: str) -> dict:
    """אוסף סקירת מחקר מלאה לטיקר מכל שכבות ה-analytics. כל מקטע fail-soft."""
    db.init_db()
    t = ticker.upper().strip()
    logger.info("מחקר on-demand: %s", t)

    return {
        "ticker": t,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot": _safe("snapshot", lambda: _dump(market.get_quote(t))),
        "summary": _safe("summary", lambda: _dump(synthesis.research(t, "תן סקירת השקעה מלאה ומאוזנת"))),
        "fundamental": _safe("fundamental", lambda: _dump(fundamentals.get_fundamentals(t))),
        "technical": _safe("technical", lambda: _dump(technical.get_technical(t, period="1y"))),
        "dcf": _safe("dcf", lambda: dcf_mod.get_dcf(t)),
        "earnings": _safe("earnings", lambda: earnings.get_earnings(t)),
        "insider": _safe("insider", lambda: smartmoney.insider_report(t)),
        "news": _safe("news", lambda: sentiment.news_sentiment(t)),
        "superinvestors": _safe("superinvestors", lambda: superinvestors.holders_of_ticker(t)),
    }


def _write(ticker: str, payload: dict) -> Path:
    """כותב report.json + report.js (window.RESEARCH_DATA) ל-analyses/_research/<TICKER>/."""
    out_dir = RESEARCH_DIR / ticker.upper()
    out_dir.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, ensure_ascii=False, indent=2)
    (out_dir / "report.json").write_text(blob, encoding="utf-8")
    (out_dir / "report.js").write_text(f"window.RESEARCH_DATA = {blob};\n", encoding="utf-8")
    return out_dir


def _notify(ticker: str) -> None:
    """ntfy push כשהמחקר מוכן (fail-soft). נשען על notifications.py של portfolio."""
    try:
        sys.path.append(str(ROOT))  # append ולא insert(0) - לא מסתיר stdlib
        from notifications import send_notification

        url = os.environ.get("DASHBOARD_URL", "").rstrip("/")
        click = f"{url}/templates/research.html?ticker={ticker.upper()}" if url else ""
        send_notification(
            f"מחקר {ticker.upper()} מוכן", title="מחקר מניה הושלם",
            tags=["mag", "chart_increasing"], click_url=click,
        )
    except Exception as exc:  # ponytail: התראה היא נחמדה-שתהיה, לא מפילה ריצה
        logger.info("ntfy דולג: %s", exc)


def _validate_ticker(raw: str) -> str:
    """אותיות, ספרות ונקודה בלבד, מקסימום 10 תווים. מונע path traversal."""
    t = raw.upper().strip()
    if not re.match(r'^[A-Z][A-Z0-9.]{0,9}$', t):
        raise SystemExit(f"טיקר לא חוקי: {raw!r}")
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description="מנוע engine - CLI")
    ap.add_argument("--mode", default="research", choices=["research"])
    ap.add_argument("--ticker", required=True)
    args = ap.parse_args()

    ticker = _validate_ticker(args.ticker)
    payload = research(ticker)
    out_dir = _write(ticker, payload)
    logger.info("נכתב: %s", out_dir / "report.json")
    _notify(args.ticker)


if __name__ == "__main__":
    main()
