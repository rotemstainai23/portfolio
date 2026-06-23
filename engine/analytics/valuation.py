"""השוואת עמיתים (peer comparison) - השוואת מכפילים מול חברות דומות.

מקבל רשימת טיקרים של עמיתים ומשווה P/E, P/S, מרג'ין תפעולי. כל ערך מגיע משכבת
ה-fundamentals (כלומר מ-EDGAR + מחיר), כך שההשוואה auditable.
"""
from __future__ import annotations

from . import fundamentals


def _num(dp) -> float | None:
    return dp.value if dp is not None else None


def compare_peers(ticker: str, peers: list[str]) -> dict:
    """משווה את הטיקר מול עמיתים לפי מכפילים עיקריים.

    מחזיר שורה לכל חברה + ממוצע העמיתים, לצורך הקשר יחסי.
    """
    all_tickers = [ticker.upper()] + [p.upper() for p in peers if p.upper() != ticker.upper()]
    rows = []
    for tk in all_tickers:
        try:
            f = fundamentals.get_fundamentals(tk)
            rows.append({
                "ticker": tk,
                "name": f.name,
                "pe": _num(f.pe),
                "ps": _num(f.ps),
                "ev_ebitda": _num(f.ev_ebitda),
                "operating_margin": _num(f.operating_margin),
                "revenue_growth": _num(f.revenue_growth),
            })
        except Exception as exc:
            rows.append({"ticker": tk, "error": str(exc)})

    # ממוצע עמיתים (ללא חברת היעד), מתעלם מ-None
    peer_rows = [r for r in rows[1:] if "error" not in r]
    def avg(field: str):
        vals = [r[field] for r in peer_rows if r.get(field) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    peer_avg = {
        "pe": avg("pe"),
        "ps": avg("ps"),
        "ev_ebitda": avg("ev_ebitda"),
        "operating_margin": avg("operating_margin"),
        "revenue_growth": avg("revenue_growth"),
    }
    return {"target": ticker.upper(), "rows": rows, "peer_average": peer_avg}
