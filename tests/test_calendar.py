from datetime import datetime, timedelta

import pytest

from app.core import time
from app.core.errors import DomainError
from app.modules.calendar import services
from app.modules.calendar.services import EventInput
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


def test_event_defaults_to_one_hour(app):
    event, conflicts = services.save_event(EventInput(title="Aula", start_at=datetime(2026, 3, 2, 19, 0)))
    assert event.end_at == datetime(2026, 3, 2, 20, 0)
    assert conflicts == []


def test_all_day_event_spans_whole_day(app):
    event, _ = services.save_event(EventInput(title="Prova", start_at=datetime(2026, 3, 2, 15, 0), all_day=True))
    assert event.start_at == datetime(2026, 3, 2, 0, 0)
    assert event.end_at.date() == event.start_at.date()


def test_end_before_start_is_rejected(app):
    with pytest.raises(DomainError):
        services.save_event(EventInput(title="X", start_at=datetime(2026, 3, 2, 10), end_at=datetime(2026, 3, 2, 9)))


def test_conflicts_are_reported(app):
    services.save_event(EventInput(title="Treino", start_at=datetime(2026, 3, 2, 18), end_at=datetime(2026, 3, 2, 19)))
    _, conflicts = services.save_event(EventInput(title="Estudo", start_at=datetime(2026, 3, 2, 18, 30)))
    assert [c.title for c in conflicts] == ["Treino"]
    _, none = services.save_event(EventInput(title="Depois", start_at=datetime(2026, 3, 2, 19)))
    assert [c.title for c in none] == ["Estudo"]  # 19h-20h bate só com o Estudo (18:30-19:30)


def test_month_grid_places_events_and_quests(app):
    services.save_event(EventInput(title="Viagem", start_at=datetime(2026, 3, 10), end_at=datetime(2026, 3, 12),
                                   all_day=True))
    quests.create_quest(QuestInput(title="Entregar trabalho", due_date=datetime(2026, 3, 11).date()))
    weeks = services.month_grid(2026, 3)
    days = {cell.day: cell for week in weeks for cell in week}
    assert all(len(week) == 7 for week in weeks)
    assert [e.title for e in days[datetime(2026, 3, 11).date()].events] == ["Viagem"]
    assert [e.title for e in days[datetime(2026, 3, 12).date()].events] == ["Viagem"]
    assert [q.title for q in days[datetime(2026, 3, 11).date()].quests] == ["Entregar trabalho"]


def test_upsert_google_event_does_not_duplicate(app):
    data = EventInput(title="Reunião", start_at=datetime(2026, 3, 5, 9))
    _, created = services.upsert_google_event("g-1", data)
    _, created_again = services.upsert_google_event("g-1", EventInput(title="Reunião (editada)",
                                                                      start_at=datetime(2026, 3, 5, 10)))
    assert created and not created_again
    events = services.events_between(datetime(2026, 3, 5), datetime(2026, 3, 6))
    assert len(events) == 1 and events[0].title == "Reunião (editada)"


def test_upcoming_events(app):
    soon = time.now() + timedelta(days=1)
    services.save_event(EventInput(title="Em breve", start_at=soon))
    services.save_event(EventInput(title="Longe", start_at=soon + timedelta(days=60)))
    assert [e.title for e in services.upcoming_events(days=7)] == ["Em breve"]


def test_routes(client):
    response = client.post("/calendar/events", data={
        "title": "Academia", "kind": "workout", "start_date": "2026-03-02", "start_time": "18:00",
        "quest_id": "0",
    })
    assert response.status_code == 302
    event = services.events_between(datetime(2026, 3, 2), datetime(2026, 3, 3))[0]
    assert client.get("/calendar/?month=2026-03").status_code == 200
    assert client.get(f"/calendar/events/{event.id}").status_code == 200
    assert client.get("/calendar/?month=lixo").status_code == 200


def test_time_is_required_unless_all_day(client):
    client.post("/calendar/events", data={"title": "Sem hora", "kind": "personal", "start_date": "2026-03-02",
                                          "quest_id": "0"})
    assert services.events_between(datetime(2026, 3, 2), datetime(2026, 3, 3)) == []
