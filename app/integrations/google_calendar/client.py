"""Cliente da Google Calendar API v3, pela biblioteca oficial google-api-python-client.

Métodos usados (todos documentados em https://developers.google.com/calendar/api/v3/reference):
    calendarList.list, events.list, events.insert, events.patch, events.delete, freebusy.query

O cliente recebe o objeto `service` pronto, para que os testes passem um objeto falso.
"""
from datetime import datetime
from typing import Any

from googleapiclient.errors import HttpError

from app.core import time

# Marca que colocamos nos eventos criados pelo Shadow System (extendedProperties.private).
# Serve para reconhecer nossos eventos e não duplicá-los.
SHADOW_PROPERTY = "shadowEventId"


class GoogleCalendarError(Exception):
    """Erro da API do Google. A mensagem é mostrada ao usuário."""


class GoogleNotFoundError(GoogleCalendarError):
    """Evento ou calendário não existe (mais) no Google."""


def build_service(credentials) -> Any:
    from googleapiclient.discovery import build

    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


class GoogleCalendarClient:
    def __init__(self, service: Any, calendar_id: str = "primary"):
        self._service = service
        self.calendar_id = calendar_id

    def calendars(self) -> list[dict]:
        data = self._run(self._service.calendarList().list())
        return [{"id": c["id"], "summary": c.get("summary", c["id"]), "primary": c.get("primary", False)}
                for c in data.get("items", [])]

    def list_events(self, start: datetime, end: datetime) -> list[dict]:
        """Eventos no intervalo, com recorrentes já expandidos (singleEvents=True). Pagina sozinho."""
        events: list[dict] = []
        page_token = None
        while True:
            data = self._run(self._service.events().list(
                calendarId=self.calendar_id,
                timeMin=_rfc3339(start),
                timeMax=_rfc3339(end),
                singleEvents=True,
                orderBy="startTime",
                maxResults=250,
                pageToken=page_token,
            ))
            events.extend(data.get("items", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                return events

    def find_by_shadow_id(self, shadow_id: int) -> dict | None:
        data = self._run(self._service.events().list(
            calendarId=self.calendar_id,
            privateExtendedProperty=f"{SHADOW_PROPERTY}={shadow_id}",
            maxResults=1,
        ))
        items = data.get("items", [])
        return items[0] if items else None

    def insert_event(self, body: dict) -> dict:
        return self._run(self._service.events().insert(calendarId=self.calendar_id, body=body))

    def patch_event(self, event_id: str, body: dict) -> dict:
        return self._run(self._service.events().patch(calendarId=self.calendar_id, eventId=event_id, body=body))

    def delete_event(self, event_id: str) -> None:
        self._run(self._service.events().delete(calendarId=self.calendar_id, eventId=event_id))

    def busy_periods(self, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
        """Períodos ocupados (consulta de disponibilidade), em horário local."""
        data = self._run(self._service.freebusy().query(body={
            "timeMin": _rfc3339(start), "timeMax": _rfc3339(end), "items": [{"id": self.calendar_id}],
        }))
        busy = data.get("calendars", {}).get(self.calendar_id, {}).get("busy", [])
        return [(_parse_dt(b["start"]), _parse_dt(b["end"])) for b in busy]

    @staticmethod
    def _run(request) -> dict:
        try:
            return request.execute() or {}
        except HttpError as exc:
            status = getattr(exc.resp, "status", "?")
            if str(status) == "404":
                raise GoogleNotFoundError("Calendário ou evento não encontrado no Google.") from exc
            if str(status) in ("401", "403"):
                raise GoogleCalendarError("Sem permissão no Google Calendar. Conecte a conta de novo.") from exc
            raise GoogleCalendarError(f"Google Calendar respondeu com erro {status}.") from exc


def _rfc3339(value: datetime) -> str:
    return time.to_aware(value).isoformat()


def _parse_dt(value: str) -> datetime:
    return time.to_local_naive(datetime.fromisoformat(value.replace("Z", "+00:00")))
