"""שכבת הלמידה (Phase 10) - החלק החשוב ביותר: להפוך את המשתמש למשקיע עצמאי.

מילון מושגים עם הסבר בשלוש רמות (מתחיל/בינוני/מתקדם), מסלול למידה, ומעקב
התקדמות. ההסברים דטרמיניסטיים (כתובים מראש) כך שהלמידה אמינה ואינה תלויה ב-LLM,
ו-ה-LLM יכול להעשיר אותם כשהוא זמין.
"""
from __future__ import annotations

from typing import Optional

from .. import db

# מילון המושגים. כל מושג בשלוש רמות עומק.
CONCEPTS: dict[str, dict] = {
    "pe": {
        "term": "מכפיל רווח (P/E)",
        "beginner": "כמה שנים של רווח נוכחי צריך כדי 'להחזיר' את מחיר המניה. מכפיל גבוה = המשקיעים מצפים לצמיחה, או שהמניה יקרה.",
        "intermediate": "מחיר המניה חלקי הרווח למניה. משווים אותו לעמיתים ולממוצע ההיסטורי של החברה כדי להעריך אם התמחור סביר.",
        "advanced": "P/E רגיש לרווח חד-פעמי ולמבנה הון. עדיף להשוות forward P/E, ולשקלל מול קצב צמיחה (PEG) ואיכות הרווח.",
    },
    "ps": {
        "term": "מכפיל מכירות (P/S)",
        "beginner": "שווי החברה חלקי ההכנסות. שימושי לחברות צעירות שעדיין לא רווחיות.",
        "intermediate": "שווי שוק חלקי הכנסות שנתיות. פחות תלוי בהנהלת רווח מ-P/E, אבל מתעלם מרווחיות.",
        "advanced": "יש לקרוא P/S יחד עם מרג'ין: אותו P/S משמעותו שונה לחלוטין בחברה עם מרג'ין 10% מול 40%.",
    },
    "ev_ebitda": {
        "term": "EV/EBITDA",
        "beginner": "מודד תמחור שמנטרל הבדלי חוב ומיסוי בין חברות.",
        "intermediate": "שווי תאגידי (שווי שוק + חוב - מזומן) חלקי רווח תפעולי לפני פחת. טוב להשוואה בין חברות עם מבני הון שונים.",
        "advanced": "EBITDA מתעלם מ-capex ומשינויי הון חוזר, ולכן מטעה בענפים עתירי הון. השוו ל-EV/FCF.",
    },
    "roic": {
        "term": "תשואה על הון מושקע (ROIC)",
        "beginner": "כמה רווח החברה מייצרת על כל שקל שהושקע בה. גבוה = עסק יעיל.",
        "intermediate": "NOPAT חלקי הון מושקע. ROIC עקבי מעל עלות ההון (WACC) הוא סימן ליתרון תחרותי.",
        "advanced": "המפתח הוא ROIC מול WACC לאורך זמן ומגמת ה-ROIC. הגדרת ההון המושקע משפיעה מהותית, יש לעקביות.",
    },
    "fcf": {
        "term": "תזרים מזומנים חופשי (FCF)",
        "beginner": "המזומן שנשאר לחברה אחרי שהשקיעה בתפעול ובציוד. זה הכסף ה'אמיתי' שאפשר לחלק או להשקיע.",
        "intermediate": "תזרים תפעולי פחות השקעות הון (capex). בסיס להערכת שווי DCF ולחלוקת דיבידנד/באייבק.",
        "advanced": "הבחינו בין FCF לבעלי המניות לבין FCFF, ושימו לב ל-stock-based compensation ולהון חוזר שמעוותים את התמונה.",
    },
    "dcf": {
        "term": "היוון תזרימים (DCF)",
        "beginner": "מחשבים כמה שווים כל המזומנים שהחברה תייצר בעתיד, במונחי היום.",
        "intermediate": "מהוונים FCF עתידי בשיעור WACC ומוסיפים ערך שיורי. רגיש מאוד להנחות הצמיחה וההיוון.",
        "advanced": "DCF הוא תרגיל ברגישות: בנו תרחישים (שמרני/בסיס/אופטימי) ובדקו את משתני המפתח במקום מספר בודד.",
    },
    "margin": {
        "term": "מרג'ינים (רווחיות)",
        "beginner": "איזה אחוז מההכנסות נשאר כרווח. ככל שגבוה יותר, החברה רווחית יותר.",
        "intermediate": "מרג'ין גולמי/תפעולי/נקי מראים רווחיות בשכבות שונות. מגמת המרג'ין חשובה כמו הרמה.",
        "advanced": "פירוק המרג'ין (תמחור מול מבנה עלויות) ומינוף תפעולי מסבירים את הרגישות לצמיחה ולמחזוריות.",
    },
    "rsi": {
        "term": "RSI (מדד עוצמה יחסית)",
        "beginner": "מד מ-0 עד 100 שמראה אם המניה 'נמתחה' למעלה (מעל 70) או למטה (מתחת 30).",
        "intermediate": "מודד את עוצמת התנועה האחרונה. מעל 70 קניית יתר, מתחת 30 מכירת יתר, אבל יכול להישאר קיצוני במגמה חזקה.",
        "advanced": "דיברגנס בין RSI למחיר הוא אות מוקדם להיחלשות מגמה. כיילו את התקופה לאופי הנכס.",
    },
    "macd": {
        "term": "MACD",
        "beginner": "כלי שמשווה שני ממוצעים נעים כדי לזהות שינוי מומנטום.",
        "intermediate": "הפרש EMA12 ו-EMA26, עם קו אות EMA9. חציית קו האות מסמנת שינוי מומנטום.",
        "advanced": "ההיסטוגרמה מקדימה את החציות. שלבו עם מבנה מחיר ונפח כדי לסנן אותות שווא.",
    },
    "atr": {
        "term": "ATR (טווח אמיתי ממוצע)",
        "beginner": "כמה המניה זזה בממוצע ביום. עוזר לקבוע מרחק סטופ הגיוני.",
        "intermediate": "מודד תנודתיות. סטופ במרחק כפולת ATR נותן 'אוויר' מותאם לתנודתיות הנכס.",
        "advanced": "ATR אינו כיווני. שמשו בו לגודל פוזיציה ולניהול סיכון, לא לחיזוי כיוון.",
    },
    "support_resistance": {
        "term": "תמיכה והתנגדות",
        "beginner": "מחירים שבהם המניה נוטה 'לעצור': תמיכה מלמטה, התנגדות מלמעלה.",
        "intermediate": "אזורים שבהם היצע/ביקוש התרכזו בעבר. שבירה שלהם בנפח גבוה משמעותית.",
        "advanced": "רמות הן אזורים ולא קווים. ערכו לפי מספר נגיעות, נפח, וקרבה לממוצעים נעים מרכזיים.",
    },
}

# מסלול למידה מומלץ לפי רמה (סדר המושגים)
_PATHS: dict[str, list[str]] = {
    "beginner": ["margin", "pe", "fcf", "rsi", "support_resistance"],
    "intermediate": ["ps", "ev_ebitda", "roic", "macd", "atr", "dcf"],
    "advanced": ["roic", "dcf", "ev_ebitda", "macd"],
}


def list_concepts() -> list[dict]:
    """רשימת כל המושגים (key + term)."""
    return [{"key": k, "term": v["term"]} for k, v in CONCEPTS.items()]


def explain_concept(key: str, level: Optional[str] = None) -> Optional[dict]:
    """הסבר מושג ברמה נתונה (ברירת מחדל: רמת המשתמש מה-DB)."""
    concept = CONCEPTS.get(key)
    if not concept:
        return None
    level = level or db.get_knowledge_level()
    if level not in ("beginner", "intermediate", "advanced"):
        level = "beginner"
    return {
        "key": key,
        "term": concept["term"],
        "level": level,
        "explanation": concept[level],
    }


def learning_path(level: Optional[str] = None) -> dict:
    """מסלול למידה אישי + סימון אילו מושגים כבר נלמדו."""
    level = level or db.get_knowledge_level()
    path_keys = _PATHS.get(level, _PATHS["beginner"])
    learned = set(db.get_learned_concepts())
    steps = [
        {"key": k, "term": CONCEPTS[k]["term"], "learned": k in learned}
        for k in path_keys
        if k in CONCEPTS
    ]
    done = sum(1 for s in steps if s["learned"])
    return {"level": level, "steps": steps, "progress": {"done": done, "total": len(steps)}}
