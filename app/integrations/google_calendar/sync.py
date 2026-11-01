"""Sincronização entre o calendário interno e o Google Calendar.

- Importar: eventos do Google entram no calendário interno (source="google"). Usa o id do Google
  como chave, então importar de novo atualiza em vez de duplicar. Eventos apagados no Google somem daqui.
- Enviar: eventos locais vão para o Google com a marca `shadowEventId`. Antes de criar, procuramos a
  marca no Google: se o evento já existe (ex.: o app caiu antes de salvar o id), só vinculamos.
"""
from dataclasses import dataclass
from datetime import date, datetime, time as dtime, timedelta

from app.core import time
from app.extensions import db
from app.modules.calendar import services as calendar
from app.modules.calendar.services import EventInput

from .client import SHADOW_PROPERTY, GoogleCalendarClient, GoogleNotFoundError

IMPORT_DAYS_BACK = 7
IMPORT_DAYS_AHEAD = 60


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    removed: int = 0
    pushed: int = 0
    linked: int = 0


def import_events(client: GoogleCalendarClient, today: date | None = None) -> SyncResult:
    today = today or time.today()
    start = datetime.combine(today - timedelta(days=IMPORT_DAYS_BACK), dtime.min)
    end = datetime.combine(today + timedelta(days=IMPORT_DAYS_AHEAD), dtime.min)
    result = SyncResult()
    seen: set[str] = set()
    for item in client.list_events(start, end):
        if item.get("status") == "cancelled":
            continue
        if _shadow_id(item) is not None:
            seen.add(item["id"])  # evento nosso, enviado daqui: já existe localmente
            continue
        data = google_to_input(item)
        if data is None:
            continue
        seen.add(item["id"])
        _, created = calendar.upsert_google_event(item["id"], data)
        if created:
            result.created += 1
        else:
            result.updated += 1
    result.removed = calendar.delete_google_events_not_in(seen, start, end)
    db.session.commit()
    return result


def push_event(client: GoogleCalendarClient, event) -> str:
    """Envia ou atualiza um evento local no Google. Retorna o id do Google."""
    body = local_to_google(event)
    if event.google_event_id:
        try:
            client.patch_event(event.google_event_id, body)
            return event.google_event_id
        except GoogleNotFoundError:
            pass  # foi apagado no Google: cria de novo abaixo
    existing = client.find_by_shadow_id(event.id)
    remote = client.patch_event(existing["id"], body) if existing else client.insert_event(body)
    calendar.mark_pushed(event.id, remote["id"])
    db.session.commit()
    return remote["id"]


def push_pending(client: GoogleCalendarClient) -> SyncResult:
    result = SyncResult()
    for event in calendar.local_events_to_push():
        push_event(client, event)
        result.pushed += 1
    return result


def google_to_input(item: dict) -> EventInput | None:
    start, end = item.get("start", {}), item.get("end", {})
    if "date" in start:  # dia inteiro; no Google o "end.date" é exclusivo (dia seguinte)
        first = date.fromisoformat(start["date"])
        last = date.fromisoformat(end.get("date", start["date"])) - timedelta(days=1)
        return EventInput(
            title=item.get("summary", ""), start_at=datetime.combine(first, dtime.min),
            end_at=datetime.combine(max(first, last), dtime.min), all_day=True, kind="other",
            description=item.get("description", ""), location=item.get("location", ""),
        )
    if "dateTime" not in start:
        return None
    return EventInput(
        title=item.get("summary", ""),
        start_at=_parse(start["dateTime"]),
        end_at=_parse(end.get("dateTime", start["dateTime"])),
        kind="other",
        description=item.get("description", ""),
        location=item.get("location", ""),
    )


def local_to_google(event) -> dict:
    body = {
        "summary": event.title,
        "description": event.description,
        "location": event.location,
        "extendedProperties": {"private": {SHADOW_PROPERTY: str(event.id)}},
    }
    if event.all_day:
        body["start"] = {"date": event.start_at.date().isoformat()}
        body["end"] = {"date": (event.end_at.date() + timedelta(days=1)).isoformat()}
    else:
        tz = str(time.local_tz())
        body["start"] = {"dateTime": event.start_at.isoformat(), "timeZone": tz}
        body["end"] = {"dateTime": event.end_at.isoformat(), "timeZone": tz}
    return body


def _shadow_id(item: dict) -> str | None:
    return item.get("extendedProperties", {}).get("private", {}).get(SHADOW_PROPERTY)


def _parse(value: str) -> datetime:
    return time.to_local_naive(datetime.fromisoformat(value.replace("Z", "+00:00")))
