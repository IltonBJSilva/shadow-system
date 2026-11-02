"""A API do Google nunca é chamada: FakeService imita o objeto do google-api-python-client."""
import json
from datetime import date, datetime, timedelta

import pytest

from app import create_app
from app.core import time
from app.extensions import db
from app.integrations import google_calendar
from app.integrations.google_calendar import oauth, sync
from app.integrations.google_calendar.client import SHADOW_PROPERTY, GoogleCalendarClient
from app.modules.calendar import services as calendar
from app.modules.calendar.services import EventInput


class _Request:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class FakeEvents:
    """Guarda eventos em memória como o Google faria."""

    def __init__(self):
        self.items: dict[str, dict] = {}
        self.inserted = 0

    def list(self, **kwargs):
        prop = kwargs.get("privateExtendedProperty")
        items = list(self.items.values())
        if prop:
            key, value = prop.split("=")
            items = [i for i in items if i.get("extendedProperties", {}).get("private", {}).get(key) == value]
        return _Request({"items": items})

    def insert(self, calendarId, body):
        self.inserted += 1
        event = {**body, "id": f"g{self.inserted}"}
        self.items[event["id"]] = event
        return _Request(event)

    def patch(self, calendarId, eventId, body):
        self.items[eventId].update(body)
        return _Request(self.items[eventId])

    def delete(self, calendarId, eventId):
        self.items.pop(eventId)
        return _Request({})


class FakeService:
    def __init__(self):
        self.fake_events = FakeEvents()

    def events(self):
        return self.fake_events

    def calendarList(self):
        return type("L", (), {"list": lambda self: _Request({"items": [{"id": "primary", "summary": "Eu", "primary": True}]})})()

    def freebusy(self):
        return type("F", (), {"query": lambda self, body: _Request({"calendars": {"primary": {"busy": [
            {"start": "2026-11-02T13:00:00Z", "end": "2026-11-02T14:00:00Z"}]}}})})()


@pytest.fixture
def fake():
    service = FakeService()
    return service, GoogleCalendarClient(service, "primary")


def _google_event(event_id, summary, start, end, **extra):
    return {"id": event_id, "summary": summary, "status": "confirmed", "start": start, "end": end, **extra}


# ---------- conversões ----------

def test_google_all_day_end_is_exclusive(app):
    data = sync.google_to_input(_google_event("1", "Feriado", {"date": "2026-11-02"}, {"date": "2026-11-03"}))
    assert data.all_day and data.start_at.date() == date(2026, 11, 2) and data.end_at.date() == date(2026, 11, 2)


def test_google_datetime_is_converted_to_local(app):
    data = sync.google_to_input(_google_event(
        "1", "Call", {"dateTime": "2026-11-02T15:00:00Z"}, {"dateTime": "2026-11-02T16:00:00Z"}))
    assert data.start_at == datetime(2026, 11, 2, 12, 0)


def test_local_to_google_marks_shadow_id(app):
    event, _ = calendar.save_event(EventInput(title="Treino", start_at=datetime(2026, 11, 2, 18)))
    body = sync.local_to_google(event)
    assert body["extendedProperties"]["private"][SHADOW_PROPERTY] == str(event.id)
    assert body["start"] == {"dateTime": "2026-11-02T18:00:00", "timeZone": "America/Sao_Paulo"}


# ---------- importação ----------

def test_import_creates_updates_and_removes(app, fake):
    service, client = fake
    today = time.today()
    start = f"{today + timedelta(days=1)}T10:00:00-03:00"
    end = f"{today + timedelta(days=1)}T11:00:00-03:00"
    service.fake_events.items["a"] = _google_event("a", "Dentista", {"dateTime": start}, {"dateTime": end})
    service.fake_events.items["b"] = _google_event("b", "Cancelado", {"dateTime": start}, {"dateTime": end},
                                                   status="cancelled")
    assert sync.import_events(client, today).created == 1

    service.fake_events.items["a"]["summary"] = "Dentista (remarcado)"
    second = sync.import_events(client, today)
    assert (second.created, second.updated) == (0, 1)
    titles = [e.title for e in calendar.upcoming_events(days=3)]
    assert titles == ["Dentista (remarcado)"]

    del service.fake_events.items["a"]
    assert sync.import_events(client, today).removed == 1
    assert calendar.upcoming_events(days=3) == []


def test_import_skips_events_created_by_shadow_system(app, fake):
    service, client = fake
    event, _ = calendar.save_event(EventInput(title="Meu evento", start_at=time.now() + timedelta(hours=2)))
    sync.push_event(client, event)
    result = sync.import_events(client)
    assert result.created == 0
    assert len(calendar.upcoming_events(days=1)) == 1


# ---------- envio ----------

def test_push_does_not_duplicate(app, fake):
    service, client = fake
    event, _ = calendar.save_event(EventInput(title="Estudar", start_at=datetime(2026, 11, 5, 9)))
    google_id = sync.push_event(client, event)
    sync.push_event(client, event)  # já tem google_event_id: só atualiza
    assert service.fake_events.inserted == 1
    assert calendar.get_event(event.id).google_event_id == google_id


def test_push_links_existing_remote_event_when_local_id_was_lost(app, fake):
    service, client = fake
    event, _ = calendar.save_event(EventInput(title="Estudar", start_at=datetime(2026, 11, 5, 9)))
    sync.push_event(client, event)
    calendar.get_event(event.id).google_event_id = None  # simula falha antes de salvar o id
    db.session.commit()
    sync.push_event(client, calendar.get_event(event.id))
    assert service.fake_events.inserted == 1


def test_push_pending_only_sends_unsent_local_events(app, fake):
    service, client = fake
    calendar.save_event(EventInput(title="A", start_at=datetime(2026, 11, 5, 9)))
    calendar.save_event(EventInput(title="B", start_at=datetime(2026, 11, 6, 9)))
    assert sync.push_pending(client).pushed == 2
    assert sync.push_pending(client).pushed == 0


def test_busy_periods_are_local(app, fake):
    _, client = fake
    assert client.busy_periods(datetime(2026, 11, 2), datetime(2026, 11, 3)) == [
        (datetime(2026, 11, 2, 10, 0), datetime(2026, 11, 2, 11, 0))]


# ---------- OAuth e telas ----------

def test_status_without_configuration(app):
    assert google_calendar.status().state == "not_configured"


def test_status_with_secrets_and_token(tmp_path):
    secrets = tmp_path / "client.json"
    secrets.write_text(json.dumps({"web": {
        "client_id": "id", "client_secret": "secret", "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token", "redirect_uris": ["http://localhost:5050/x"]}}))
    token = tmp_path / "token.json"
    app = create_app("testing", {"GOOGLE_CLIENT_SECRETS_FILE": str(secrets), "GOOGLE_TOKEN_FILE": str(token)})
    with app.app_context():
        db.create_all()
        assert google_calendar.status().state == "configured"
        url, state, _ = oauth.authorization_url()
        assert url.startswith("https://accounts.google.com/") and "calendar.events" in url and state
        token.write_text("{}")
        assert google_calendar.status().state == "connected"
        oauth.disconnect()
        assert not token.exists()


def test_callback_rejects_wrong_state(tmp_path):
    app = create_app("testing", {"GOOGLE_TOKEN_FILE": str(tmp_path / "t.json")})
    client = app.test_client()
    with client.session_transaction() as session:
        session["google_oauth_state"] = "expected"
    assert client.get("/integrations/google/callback?state=forged&code=x").status_code == 400


def test_google_page_renders_setup_instructions(client):
    html = client.get("/integrations/google/").get_data(as_text=True)
    assert "GOOGLE_CLIENT_SECRETS_FILE" in html


def test_sync_without_connection_shows_error(client):
    response = client.post("/integrations/google/sync")
    assert response.status_code == 302
