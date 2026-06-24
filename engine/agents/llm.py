"""עטיפת LLM (Groq, llama-3.3-70b) להסבר/סינתזה. נפילה בחן כשאין מפתח.

עיקרון: ה-LLM מקבל אך ורק נתונים מחושבים (DataPoint) ומתבקש להסביר, לעולם לא
להמציא או לחשב מספרים. כל קריאה מגבילה את המודל למסגרת הזו דרך ה-system prompt.
"""
from __future__ import annotations

from typing import Optional

import requests

from ..config import GROQ_API_KEY, GROQ_MODEL, logger

_SYSTEM_GUARD = (
    "אתה עוזר מחקר השקעות. כל המספרים שתקבל כבר חושבו ממקורות רשמיים. "
    "אסור לך להמציא, לשנות או לחשב מספרים חדשים. תפקידך להסביר בעברית ברורה, "
    "להציג שרשרת היגיון, יתרונות וחסרונות, ולהתאים את ההסבר לרמת הידע שצוינה. "
    "אינך נותן ייעוץ השקעות אישי."
)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def llm_available() -> bool:
    """האם שכבת ה-LLM פעילה (קיים מפתח Groq)."""
    return bool(GROQ_API_KEY)


def explain(prompt: str, *, heavy: bool = False, system: Optional[str] = None, max_tokens: int = 1200) -> Optional[str]:
    """מבקש הסבר מה-LLM (Groq). מחזיר None אם אין מפתח או אם הקריאה נכשלה.

    הפרמטר heavy נשמר לתאימות חתימה; Groq משתמש במודל יחיד.  # ponytail
    """
    if not GROQ_API_KEY:
        return None
    try:
        resp = requests.post(
            _GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system or _SYSTEM_GUARD},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # רשת/מפתח/מכסה - לא מפיל את הבקשה
        logger.warning("קריאת Groq נכשלה, נופל להסבר דטרמיניסטי: %s", exc)
        return None
