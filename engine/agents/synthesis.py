"""סינתזת תשובת מחקר (Research Terminal core, Phase 1).

אוסף נתונים מ-analytics, בונה תשובה מוסברת עם שרשרת היגיון ומקורות. הסיכום
נבנה דטרמיניסטית מהמספרים, וה-LLM (אם זמין) מעשיר אותו - אך לעולם אינו מחליף
את המספרים עצמם.
"""
from __future__ import annotations

from typing import Optional

from .. import db
from ..analytics import fundamentals, technical
from ..models import DataPoint, FundamentalReport, ResearchAnswer, Source, TechnicalReport
from . import llm, router


def _collect_points(report) -> list[DataPoint]:
    """אוסף את כל ה-DataPoint הלא-ריקים מתוך דוח."""
    points = []
    for field in type(report).model_fields:
        dp = getattr(report, field, None)
        if isinstance(dp, DataPoint) and dp.value is not None:
            points.append(dp)
    return points


def _fmt(dp: Optional[DataPoint]) -> str:
    """ייצוג טקסטואלי קצר של DataPoint לסיכום."""
    if not dp or dp.value is None:
        return "לא זמין"
    v = dp.value
    if dp.unit == "USD":
        av = abs(v)
        if av >= 1e9:
            return f"{v/1e9:.2f}B$"
        if av >= 1e6:
            return f"{v/1e6:.2f}M$"
        return f"{v:.2f}$"
    if dp.unit == "%":
        return f"{v:.1f}%"
    if dp.unit == "x":
        return f"{v:.2f}x"
    return f"{v:.2f}"


def _deterministic_summary(
    name: str, intents: list[str], fund: Optional[FundamentalReport], tech: Optional[TechnicalReport]
) -> tuple[str, list[str]]:
    """בונה סיכום והיגיון דטרמיניסטיים מהמספרים בלבד."""
    parts: list[str] = []
    reasoning: list[str] = []

    if fund:
        bits = []
        if fund.revenue:
            bits.append(f"הכנסות {_fmt(fund.revenue)}")
        if fund.revenue_growth:
            bits.append(f"צמיחה {_fmt(fund.revenue_growth)}")
        if fund.net_margin:
            bits.append(f"מרג'ין נקי {_fmt(fund.net_margin)}")
        if fund.roic:
            bits.append(f"ROIC {_fmt(fund.roic)}")
        if bits:
            parts.append(f"{name}: " + ", ".join(bits) + ".")
            reasoning.append("נשלפו דוחות כספיים מ-SEC EDGAR וחושבו צמיחה, מרג'ינים ו-ROIC.")

        # תמחור
        if "valuation" in intents or "quality" in intents:
            valbits = []
            if fund.pe:
                valbits.append(f"מכפיל רווח {_fmt(fund.pe)}")
            if fund.ps:
                valbits.append(f"מכפיל מכירות {_fmt(fund.ps)}")
            if fund.ev_ebitda:
                valbits.append(f"EV/EBITDA {_fmt(fund.ev_ebitda)}")
            if valbits:
                parts.append("תמחור: " + ", ".join(valbits) + ". יש להשוות לעמיתים ולממוצע ההיסטורי כדי לקבוע אם זה יקר.")
                reasoning.append("חושבו מכפילי תמחור משילוב מחיר השוק (Yahoo) ונתוני EDGAR.")

        # איכות
        if "quality" in intents and fund.roic and fund.net_margin:
            qual = "סימני איכות חיוביים" if (fund.roic.value or 0) > 10 and (fund.net_margin.value or 0) > 10 else "איכות מעורבת לפי המדדים"
            parts.append(f"איכות: {qual} (ROIC ומרג'ין נקי).")
            reasoning.append("איכות הוערכה לפי רמת ה-ROIC והמרג'ין הנקי (סף מקובל ~10%).")

    if tech:
        tbits = []
        if tech.trend:
            tbits.append(f"מגמה {tech.trend}")
        if tech.rsi14 and tech.rsi14.value is not None:
            tbits.append(f"RSI {tech.rsi14.value:.0f}")
        if tech.support:
            tbits.append(f"תמיכה קרובה {tech.support[0]}")
        if tech.resistance:
            tbits.append(f"התנגדות קרובה {tech.resistance[0]}")
        if tbits:
            parts.append("טכני: " + ", ".join(tbits) + ".")
            reasoning.append("חושבו אינדיקטורים טכניים (RSI/MACD/ATR) ורמות תמיכה/התנגדות מהיסטוריית המחירים.")

    if not parts:
        parts.append(f"לא נמצאו מספיק נתונים עבור {name} כדי לבנות תשובה מבוססת.")
    parts.append("הערה: זהו מידע מחקרי בלבד, לא ייעוץ השקעות אישי.")
    return " ".join(parts), reasoning


def _llm_prompt(question: str, summary: str, level: str) -> str:
    return (
        f"רמת הידע של המשתמש: {level}.\n"
        f"שאלת המשתמש: {question}\n\n"
        f"הנתונים המחושבים (אל תשנה מספרים אלה):\n{summary}\n\n"
        "כתוב תשובה מוסברת בעברית המותאמת לרמת הידע, עם שרשרת היגיון קצרה, "
        "יתרון וחיסרון מרכזי, ובלי להמציא מספרים חדשים."
    )


def research(ticker: str, question: str) -> ResearchAnswer:
    """ליבת ה-Research Terminal: שאלה בשפה טבעית -> תשובה מוסברת ומאומתת."""
    ticker = ticker.upper().strip()
    plan = router.classify(question)
    db.log_research(ticker, question)

    fund: Optional[FundamentalReport] = None
    tech: Optional[TechnicalReport] = None
    data_points: list[DataPoint] = []
    sources: list[Source] = []
    reasoning: list[str] = [f"סווגה כוונת השאלה: {', '.join(plan['intents'])}."]
    name = ticker

    if plan["needs_fundamental"]:
        try:
            fund = fundamentals.get_fundamentals(ticker)
            name = fund.name
            data_points += _collect_points(fund)
            sources += fund.sources
        except Exception as exc:
            reasoning.append(f"שליפת נתונים פונדמנטליים נכשלה: {exc}")

    if plan["needs_technical"]:
        try:
            tech = technical.get_technical(ticker)
            data_points += _collect_points(tech)
            sources += tech.sources
        except Exception as exc:
            reasoning.append(f"שליפת נתונים טכניים נכשלה: {exc}")

    summary, more_reasoning = _deterministic_summary(name, plan["intents"], fund, tech)
    reasoning += more_reasoning

    # העשרת LLM אופציונלית (לא מחליפה מספרים)
    level = db.get_knowledge_level()
    llm_text = llm.explain(_llm_prompt(question, summary, level), heavy=True)
    if llm_text:
        summary = llm_text
        reasoning.append("ההסבר נוסח על ידי שכבת ה-LLM על בסיס המספרים המחושבים בלבד.")
    else:
        reasoning.append("הסבר דטרמיניסטי (שכבת LLM אינה פעילה).")

    # ניקוי מקורות כפולים לפי שם
    seen = set()
    unique_sources = []
    for s in sources:
        if s.name not in seen:
            seen.add(s.name)
            unique_sources.append(s)

    return ResearchAnswer(
        question=question,
        ticker=ticker,
        summary=summary,
        data_points=data_points,
        sources=unique_sources,
        reasoning=reasoning,
    )
