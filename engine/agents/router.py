"""ניתוב כוונת שאלה (Research Terminal). דטרמיניסטי, מבוסס מילות מפתח.

מסווג שאלה בשפה טבעית לקטגוריות וקובע אילו ניתוחים להריץ. זהו הצומת שמחקה את
ה-router של Barebone שבוחר את 'השילוב הנכון' של ניתוחים לכל שאלה.
"""
from __future__ import annotations

# קטגוריית כוונה -> מילות מפתח (עברית + אנגלית)
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "valuation": ["יקר", "זול", "שווי", "valuation", "overvalued", "undervalued",
                  "מכפיל", "תמחור", "price", "worth", "expensive", "cheap"],
    "risk": ["סיכון", "סיכונים", "risk", "חוב", "debt", "מסוכן", "downside"],
    "quality": ["איכות", "איכותי", "quality", "חזק", "moat", "יתרון", "יתרונות",
                "advantage", "strong", "good"],
    "technical": ["טכני", "technical", "תמיכה", "התנגדות", "rsi", "macd", "כניסה",
                  "יציאה", "support", "resistance", "entry", "exit", "stop", "מגמה", "trend"],
    "analysts": ["אנליסט", "אנליסטים", "analyst", "יעד", "target", "המלצה", "consensus"],
    "growth": ["צמיחה", "growth", "גדל", "מתרחב", "revenue"],
}


def classify(question: str) -> dict:
    """מסווג שאלה. מחזיר {intents, needs_fundamental, needs_technical}."""
    q = question.lower()
    intents = [name for name, kws in _INTENT_KEYWORDS.items()
               if any(kw.lower() in q for kw in kws)]
    if not intents:
        intents = ["quality", "valuation"]  # ברירת מחדל: סקירה כללית
    needs_technical = "technical" in intents
    # פונדמנטלי נדרש כמעט תמיד (שווי/איכות/סיכון/צמיחה/אנליסטים)
    needs_fundamental = bool(set(intents) & {"valuation", "risk", "quality", "growth", "analysts"}) or not needs_technical
    return {
        "intents": intents,
        "needs_fundamental": needs_fundamental,
        "needs_technical": needs_technical,
    }
