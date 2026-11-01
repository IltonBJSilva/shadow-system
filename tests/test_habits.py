from datetime import date, timedelta

import pytest

from app.core import time
from app.core.errors import DomainError
from app.modules.habits import services, streaks
from app.modules.hunter import services as hunter


def _attr(key: str) -> int:
    return next(a.id for a in hunter.list_attributes() if a.key == key)


# ---------- streaks (puras) ----------

def test_current_streak_counts_until_yesterday_when_today_pending():
    today = date(2026, 5, 10)
    done = [date(2026, 5, 7), date(2026, 5, 8), date(2026, 5, 9)]
    assert streaks.current_streak(done, today) == 3
    assert streaks.current_streak(done + [today], today) == 4


def test_current_streak_breaks_after_a_gap():
    today = date(2026, 5, 10)
    assert streaks.current_streak([date(2026, 5, 7)], today) == 0


def test_best_streak():
    days = [date(2026, 1, d) for d in (1, 2, 3, 7, 8)]
    assert streaks.best_streak(days) == 3
    assert streaks.best_streak([]) == 0


# ---------- serviços ----------

def test_check_in_awards_xp_and_attribute(app):
    habit = services.save_habit("Ler", "", 15, [_attr("intelligence")])
    result = services.check_in(habit.id)
    assert result.amount == 15
    assert next(a for a in hunter.list_attributes() if a.key == "intelligence").points == 1
    view = services.list_habits()[0]
    assert view.done_today and view.current_streak == 1


def test_double_check_in_is_rejected(app):
    habit = services.save_habit("Água", "", 10, [])
    services.check_in(habit.id)
    with pytest.raises(DomainError):
        services.check_in(habit.id)
    assert hunter.get_hunter().total_xp == 10


def test_undo_refunds_the_original_xp(app):
    habit = services.save_habit("Meditar", "", 10, [_attr("spirituality")])
    services.check_in(habit.id)
    services.save_habit("Meditar", "", 50, [_attr("spirituality")], habit.id)  # XP mudou depois
    services.undo_check_in(habit.id)
    assert hunter.get_hunter().total_xp == 0
    assert next(a for a in hunter.list_attributes() if a.key == "spirituality").points == 0


def test_backfill_limits(app):
    habit = services.save_habit("Alongar", "", 5, [])
    today = time.today()
    services.check_in(habit.id, today - timedelta(days=2))
    with pytest.raises(DomainError):
        services.check_in(habit.id, today + timedelta(days=1))
    with pytest.raises(DomainError):
        services.check_in(habit.id, today - timedelta(days=30))


def test_archived_habit_cannot_be_checked(app):
    habit = services.save_habit("Antigo", "", 5, [])
    services.set_active(habit.id, False)
    with pytest.raises(DomainError):
        services.check_in(habit.id)
    assert services.list_habits(active=False)[0].name == "Antigo"


def test_best_current_streak(app):
    a = services.save_habit("A", "", 5, [])
    services.save_habit("B", "", 5, [])
    today = time.today()
    for offset in range(3):
        services.check_in(a.id, today - timedelta(days=offset))
    assert services.best_current_streak() == 3


# ---------- rotas ----------

def test_check_and_uncheck_routes(client):
    habit = services.save_habit("Treinar", "", 20, [])
    client.post(f"/habits/{habit.id}/check")
    assert hunter.get_hunter().total_xp == 20
    client.post(f"/habits/{habit.id}/uncheck")
    assert hunter.get_hunter().total_xp == 0


def test_invalid_day_shows_error(client):
    habit = services.save_habit("Treinar", "", 20, [])
    response = client.post(f"/habits/{habit.id}/check", data={"day": "ontem"})
    assert response.status_code == 302
    assert hunter.get_hunter().total_xp == 0


def test_pages_render(client):
    habit = services.save_habit("Página", "", 5, [])
    assert client.get("/habits/").status_code == 200
    assert client.get(f"/habits/{habit.id}/edit").status_code == 200
