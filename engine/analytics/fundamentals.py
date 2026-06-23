"""ניתוח פונדמנטלי דטרמיניסטי מתוך עובדות EDGAR + מחיר שוק.

כל המספרים מחושבים כאן (לא ב-LLM) ומוחזרים כ-DataPoint עם מקור. הנחות חישוב
(שיעור מס, הון מושקע) מתועדות במפורש בשדה assumptions ובהערות.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..models import CompanyFacts, DataPoint, FundamentalReport, Source
from ..providers import edgar, market
from . import xbrl

_TAX_RATE = 0.21  # שיעור מס אפקטיבי מונח לחישוב NOPAT


def _edgar_dp(label: str, value: Optional[float], unit: str, facts: CompanyFacts,
              as_of: Optional[str], note: Optional[str] = None) -> Optional[DataPoint]:
    """בונה DataPoint ממקור EDGAR. מחזיר None אם אין ערך."""
    if value is None:
        return None
    return DataPoint(
        label=label,
        value=value,
        unit=unit,
        source=Source(name="SEC EDGAR (XBRL)", url=facts.source.url, as_of=as_of),
        note=note,
    )


def _val(rec: Optional[dict]) -> Optional[float]:
    return rec["val"] if rec else None


def get_fundamentals(ticker: str) -> FundamentalReport:
    """מחשב דוח פונדמנטלי מלא עבור טיקר (שליפה + חישוב)."""
    facts = edgar.get_company_facts(ticker)
    price = None
    try:
        price = market.get_quote(ticker).price.value
    except Exception:  # מחיר חסר לא יפיל את הדוח הפונדמנטלי
        price = None
    return compute_fundamentals(facts, price)


def compute_fundamentals(facts: CompanyFacts, price: Optional[float] = None) -> FundamentalReport:
    """החישוב הטהור על עובדות נתונות (ללא רשת). שדות חסרים מוחזרים None."""
    ticker = facts.ticker
    url = facts.source.url
    assumptions: list[str] = []

    # סדרות שנתיות
    rev_series = xbrl.annual_series(facts, "revenue")
    revenue = rev_series[-1] if rev_series else None
    rev_prior = rev_series[-2] if len(rev_series) >= 2 else None

    gross = xbrl.latest_annual(facts, "gross_profit")
    cogs = xbrl.latest_annual(facts, "cogs")
    op_income = xbrl.latest_annual(facts, "operating_income")
    net_income = xbrl.latest_annual(facts, "net_income")
    ocf = xbrl.latest_annual(facts, "ocf")
    capex = xbrl.latest_annual(facts, "capex")
    da = xbrl.latest_annual(facts, "da")
    equity = xbrl.latest_annual(facts, "equity")
    cash = xbrl.latest_annual(facts, "cash")
    lt_debt = xbrl.latest_annual(facts, "lt_debt")
    st_debt = xbrl.latest_annual(facts, "st_debt")
    eps = xbrl.latest_annual(facts, "eps_diluted")
    shares = xbrl.shares_outstanding(facts)

    report = FundamentalReport(ticker=ticker.upper(), name=facts.name)

    # הכנסות + צמיחה
    report.revenue = _edgar_dp(
        "הכנסות שנתיות", _val(revenue), "USD", facts,
        revenue["end"] if revenue else None,
        note=f"XBRL {revenue['tag']}, fy={revenue['fy']}" if revenue else None,
    )
    if revenue and rev_prior and rev_prior["val"]:
        growth = (revenue["val"] - rev_prior["val"]) / abs(rev_prior["val"]) * 100.0
        report.revenue_growth = DataPoint(
            label="צמיחת הכנסות (שנה/שנה)",
            value=round(growth, 1),
            unit="%",
            source=Source(name="SEC EDGAR (XBRL)", url=url, as_of=revenue["end"]),
            note=f"{rev_prior['end']} -> {revenue['end']}",
        )

    # מרג'ינים (כל אחד יחסית להכנסות אותה שנה)
    rev_val = _val(revenue)
    if rev_val:
        gross_val = _val(gross)
        if gross_val is None and cogs and rev_val:
            gross_val = rev_val - cogs["val"]  # נגזר אם GrossProfit חסר
        if gross_val is not None:
            report.gross_margin = DataPoint(
                label="מרג'ין גולמי", value=round(gross_val / rev_val * 100, 1), unit="%",
                source=Source(name="SEC EDGAR (XBRL)", url=url, as_of=revenue["end"]),
                note="(הכנסות פחות עלות המכר) חלקי הכנסות",
            )
        if op_income:
            report.operating_margin = DataPoint(
                label="מרג'ין תפעולי", value=round(op_income["val"] / rev_val * 100, 1), unit="%",
                source=Source(name="SEC EDGAR (XBRL)", url=url, as_of=revenue["end"]),
                note="רווח תפעולי חלקי הכנסות",
            )
        if net_income:
            report.net_margin = DataPoint(
                label="מרג'ין נקי", value=round(net_income["val"] / rev_val * 100, 1), unit="%",
                source=Source(name="SEC EDGAR (XBRL)", url=url, as_of=revenue["end"]),
                note="רווח נקי חלקי הכנסות",
            )

    # תזרים חופשי (FCF = תזרים תפעולי פחות השקעות הון)
    if ocf and capex:
        fcf_val = ocf["val"] - abs(capex["val"])
        report.fcf = DataPoint(
            label="תזרים מזומנים חופשי", value=fcf_val, unit="USD",
            source=Source(name="SEC EDGAR (XBRL)", url=url, as_of=ocf["end"]),
            note="תזרים תפעולי פחות capex",
        )

    # ROIC משוערך (NOPAT חלקי הון מושקע). הנחות מתועדות.
    total_debt = (_val(lt_debt) or 0.0) + (_val(st_debt) or 0.0)
    if op_income and equity:
        nopat = op_income["val"] * (1 - _TAX_RATE)
        invested = equity["val"] + total_debt - (_val(cash) or 0.0)
        if invested > 0:
            report.roic = DataPoint(
                label="ROIC (משוערך)", value=round(nopat / invested * 100, 1), unit="%",
                source=Source(name="SEC EDGAR (XBRL)", url=url, as_of=op_income["end"]),
                note="NOPAT חלקי (הון עצמי ועוד חוב פחות מזומן)",
            )
            assumptions.append(f"ROIC: שיעור מס מונח {int(_TAX_RATE*100)}%, הון מושקע = הון עצמי + חוב - מזומן")

    # מכפילים - דורשים מחיר שוק (פרמטר) ומספר מניות
    if price and shares:
        mcap = price * shares["val"]
        report.market_cap = DataPoint(
            label="שווי שוק", value=mcap, unit="USD",
            source=Source(name="Yahoo Finance + SEC EDGAR", url=facts.source.url, as_of=date.today().isoformat()),
            note=f"מחיר ({price}) כפול מניות במחזור ({shares['val']:.0f})",
        )
        if rev_val:
            report.ps = DataPoint(
                label="מכפיל מכירות (P/S)", value=round(mcap / rev_val, 2), unit="x",
                source=Source(name="Yahoo Finance + SEC EDGAR", url=url, as_of=date.today().isoformat()),
            )
        if eps and eps["val"] and eps["val"] > 0:
            report.pe = DataPoint(
                label="מכפיל רווח (P/E)", value=round(price / eps["val"], 2), unit="x",
                source=Source(name="Yahoo Finance + SEC EDGAR", url=url, as_of=date.today().isoformat()),
                note=f"מחיר חלקי רווח מדולל למניה ({eps['val']})",
            )
        if op_income and da:
            ebitda = op_income["val"] + da["val"]
            ev = mcap + total_debt - (_val(cash) or 0.0)
            if ebitda > 0:
                report.ev_ebitda = DataPoint(
                    label="EV/EBITDA", value=round(ev / ebitda, 2), unit="x",
                    source=Source(name="Yahoo Finance + SEC EDGAR", url=url, as_of=date.today().isoformat()),
                    note="שווי תאגידי חלקי EBITDA (רווח תפעולי + פחת והפחתות)",
                )

    # איסוף מקורות ייחודיים
    seen = set()
    for field in type(report).model_fields:
        dp = getattr(report, field, None)
        if isinstance(dp, DataPoint) and dp.source.name not in seen:
            seen.add(dp.source.name)
            report.sources.append(dp.source)
    report.assumptions = assumptions
    return report
