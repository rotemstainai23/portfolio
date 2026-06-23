"""שכבת DB מינימלית מעל sqlite3 (ספריית התקן, ללא תלות).

ב-Phase 0 מוגדרות הטבלאות הבסיסיות: פרופיל ידע המשתמש והיסטוריית שאלות.
נתיב מיגרציה עתידי ל-Postgres ישמור על אותו ממשק.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    knowledge_level TEXT NOT NULL DEFAULT 'beginner',
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS research_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    question TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS learned_concepts (
    concept TEXT PRIMARY KEY,
    learned_at TEXT DEFAULT (datetime('now'))
);
"""


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """מנהל הקשר לחיבור SQLite עם row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """יוצר את הטבלאות ושורת פרופיל ברירת מחדל."""
    with get_conn() as conn:
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT OR IGNORE INTO user_profile (id, knowledge_level) VALUES (1, 'beginner')"
        )


def get_knowledge_level() -> str:
    """מחזיר את רמת הידע הנוכחית של המשתמש."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT knowledge_level FROM user_profile WHERE id = 1"
        ).fetchone()
        return row["knowledge_level"] if row else "beginner"


def set_knowledge_level(level: str) -> None:
    """מעדכן את רמת הידע (beginner/intermediate/advanced)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE user_profile SET knowledge_level = ?, updated_at = datetime('now') WHERE id = 1",
            (level,),
        )


def get_learned_concepts() -> list[str]:
    """מחזיר את רשימת המושגים שהמשתמש כבר למד."""
    with get_conn() as conn:
        rows = conn.execute("SELECT concept FROM learned_concepts").fetchall()
        return [r["concept"] for r in rows]


def mark_concept_learned(concept: str) -> None:
    """מסמן מושג כנלמד (מעקב התקדמות)."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO learned_concepts (concept) VALUES (?)", (concept,)
        )


def log_research(ticker: str, question: str) -> None:
    """רושם שאלת מחקר בהיסטוריה."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO research_history (ticker, question) VALUES (?, ?)",
            (ticker.upper(), question),
        )
