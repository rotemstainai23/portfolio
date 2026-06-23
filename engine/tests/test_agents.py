"""בדיקות שכבת ה-agents: ניתוב, למידה, וסינתזה."""
from __future__ import annotations

import pytest

from engine import db
from engine.agents import education, router, synthesis


@pytest.fixture(autouse=True)
def _init_db():
    db.init_db()


# ---------- router ----------

def test_router_valuation_intent():
    plan = router.classify("האם המניה יקרה?")
    assert "valuation" in plan["intents"]
    assert plan["needs_fundamental"]


def test_router_technical_intent():
    plan = router.classify("מה רמות התמיכה וההתנגדות?")
    assert "technical" in plan["intents"]
    assert plan["needs_technical"]


def test_router_default_when_unknown():
    plan = router.classify("ספר לי על החברה")
    assert plan["intents"]  # תמיד מחזיר משהו
    assert plan["needs_fundamental"]


# ---------- education ----------

def test_education_levels_differ():
    beg = education.explain_concept("pe", "beginner")
    adv = education.explain_concept("pe", "advanced")
    assert beg["explanation"] != adv["explanation"]
    assert beg["term"] == adv["term"]


def test_education_unknown_concept():
    assert education.explain_concept("nope") is None


def test_learning_path_tracks_progress():
    db.set_knowledge_level("beginner")
    db.mark_concept_learned("pe")
    path = education.learning_path()
    assert path["level"] == "beginner"
    assert any(s["key"] == "pe" and s["learned"] for s in path["steps"])
    assert path["progress"]["done"] >= 1


# ---------- synthesis (רשת) ----------

@pytest.mark.network
def test_research_end_to_end():
    ans = synthesis.research("AAPL", "האם המניה יקרה ומה האיכות שלה?")
    assert ans.ticker == "AAPL"
    assert ans.summary
    assert len(ans.data_points) > 0
    # כל DataPoint חייב מקור (auditability)
    assert all(dp.source and dp.source.name for dp in ans.data_points)
    assert ans.reasoning  # שרשרת היגיון קיימת
