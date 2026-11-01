from datetime import date, timedelta

import pytest

from app.core import time
from app.core.errors import DomainError
from app.modules.hunter import services as hunter
from app.modules.quests import recurrence, services
from app.modules.quests.services import QuestInput


def _attr(key: str) -> int:
    return next(a.id for a in hunter.list_attributes() if a.key == key)


# ---------- recorrência (pura) ----------

def test_next_due_handles_month_end():
    assert recurrence.next_due(date(2026, 1, 31), "monthly") == date(2026, 2, 28)
    assert recurrence.next_due(date(2026, 12, 15), "monthly") == date(2027, 1, 15)
    assert recurrence.next_due(date(2026, 3, 1), "weekly") == date(2026, 3, 8)


def test_next_due_on_or_after_skips_missed_occurrences():
    assert recurrence.next_due_on_or_after(date(2026, 3, 1), "daily", date(2026, 3, 10)) == date(2026, 3, 10)


# ---------- criação ----------

def test_default_xp_comes_from_difficulty(app):
    quest = services.create_quest(QuestInput(title="Estudar Flask", difficulty=4))
    assert quest.xp_reward == 100
    assert quest.logs[0].action == "created"


def test_custom_xp_is_respected(app):
    assert services.create_quest(QuestInput(title="X", xp_reward=7)).xp_reward == 7


def test_invalid_input_is_rejected(app):
    with pytest.raises(DomainError):
        services.create_quest(QuestInput(title="  "))
    with pytest.raises(DomainError):
        services.create_quest(QuestInput(title="X", quest_type="boss"))


def test_quest_inherits_category_attributes(app):
    category = services.save_category("Treino", "#ff0000", [_attr("strength"), _attr("vitality")])
    quest = services.create_quest(QuestInput(title="Academia", category_id=category.id))
    assert set(services.attribute_names_for(quest)) == {"Strength", "Vitality"}


def test_recurring_quest_without_date_starts_today(app):
    quest = services.create_quest(QuestInput(title="Ler 10 páginas", quest_type="daily", recurrence="daily"))
    assert quest.due_date == time.today()
    assert quest.series_id == quest.id


# ---------- conclusão e recompensas ----------

def test_complete_awards_xp_and_attributes(app):
    quest = services.create_quest(QuestInput(title="Treino", difficulty=3, attribute_ids=[_attr("strength")]))
    result = services.complete_quest(quest.id)
    assert result.amount == 50
    assert hunter.get_hunter().total_xp == 50
    assert next(a for a in hunter.list_attributes() if a.key == "strength").points == 3
    assert services.get_quest(quest.id).status == "completed"


def test_cannot_complete_twice(app):
    quest = services.create_quest(QuestInput(title="Uma vez"))
    services.complete_quest(quest.id)
    with pytest.raises(DomainError):
        services.complete_quest(quest.id)
    assert hunter.get_hunter().total_xp == 50


def test_completing_recurring_quest_spawns_next(app):
    today = time.today()
    quest = services.create_quest(QuestInput(title="Daily", quest_type="daily", recurrence="daily", due_date=today))
    services.complete_quest(quest.id)
    active = services.list_quests("active")
    assert len(active) == 1
    assert active[0].due_date == today + timedelta(days=1)
    assert active[0].series_id == quest.id


def test_completing_overdue_daily_does_not_duplicate_today(app):
    today = time.today()
    quest = services.create_quest(QuestInput(title="Daily", recurrence="daily", due_date=today - timedelta(days=3)))
    services.complete_quest(quest.id)
    assert services.list_quests("active")[0].due_date == today + timedelta(days=1)


def test_rollover_marks_missed_without_penalty(app):
    today = time.today()
    services.create_quest(QuestInput(title="Daily", recurrence="daily", due_date=today - timedelta(days=2)))
    assert services.roll_over_recurring(today) == 1
    assert services.roll_over_recurring(today) == 0  # idempotente
    closed = services.list_quests("closed")
    assert closed[0].status == "missed"
    assert services.list_quests("active")[0].due_date == today
    assert hunter.get_hunter().total_xp == 0


def test_cancel_only_active(app):
    quest = services.create_quest(QuestInput(title="Talvez"))
    services.cancel_quest(quest.id)
    with pytest.raises(DomainError):
        services.cancel_quest(quest.id)


# ---------- consultas ----------

def test_quests_for_today_includes_overdue_and_undated_dailies(app):
    today = time.today()
    services.create_quest(QuestInput(title="Atrasada", due_date=today - timedelta(days=1)))
    services.create_quest(QuestInput(title="Daily sem data", quest_type="daily"))
    services.create_quest(QuestInput(title="Futura", due_date=today + timedelta(days=5)))
    titles = {q.title for q in services.quests_for_today(today)}
    assert titles == {"Atrasada", "Daily sem data"}


def test_stats_counts(app):
    quest = services.create_quest(QuestInput(title="A"))
    services.create_quest(QuestInput(title="B", due_date=time.today() - timedelta(days=1)))
    services.complete_quest(quest.id)
    assert services.stats() == {"completed": 1, "active": 1, "overdue": 1}


# ---------- rotas ----------

def test_create_and_complete_through_routes(client):
    response = client.post("/quests/", data={
        "title": "Revisar cálculo", "quest_type": "main", "category_id": "0", "priority": "high",
        "difficulty": "2", "recurrence": "none",
    })
    assert response.status_code == 302
    quest = services.list_quests("active")[0]
    assert quest.title == "Revisar cálculo" and quest.xp_reward == 25

    response = client.post(f"/quests/{quest.id}/complete", data={"next": "/hunter/"})
    assert response.headers["Location"] == "/hunter/"
    assert hunter.get_hunter().total_xp == 25


def test_redirect_back_ignores_external_next(client):
    quest = services.create_quest(QuestInput(title="Seguro"))
    response = client.post(f"/quests/{quest.id}/complete", data={"next": "https://evil.com"})
    assert response.headers["Location"] == "/quests/"


def test_pages_render(client):
    quest = services.create_quest(QuestInput(title="Página"))
    for url in ("/quests/", "/quests/?view=completed", f"/quests/{quest.id}", f"/quests/{quest.id}/edit",
                "/quests/categories"):
        assert client.get(url).status_code == 200, url
