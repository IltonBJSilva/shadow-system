"""Regras do calendário interno e API pública do módulo."""
import calendar as stdlib_calendar
from dataclasses import dataclass, field
from datetime import date, datetime, time as dtime, timedelta

from sqlalchemy import select

from app.core import time
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.quests import services as quest_services

from .models import CalendarEvent

KINDS: dict[str, str] = {
    "personal": "Pessoal",
    "study": "Estudos",
    "university": "Faculdade",
    "workout": "Treino",
    "work": "Trabalho",
    "quest": "Quest",
    "content": "Conteúdo",
    "other": "Outro",
}
SOURCES = ("local", "google")


@dataclass
class EventInput:
    title: str
    start_at: datetime
    end_at: datetime | None = None  # None = 1 hora depois do início (ou o dia todo)
    all_day: bool = False
    kind: str = "personal"
    description: str = ""
    location: str = ""
    quest_id: int | None = None


@dataclass
class CalendarDay:
    day: date
    in_month: bool
    is_today: bool
    events: list[CalendarEvent] = field(default_factory=list)
    quests: list[quest_services.QuestView] = field(default_factory=list)


# ---------- Leitura ----------

def get_event(event_id: int) -> CalendarEvent:
    event = db.session.get(CalendarEvent, event_id)
    if event is None:
        raise NotFoundError("Evento não encontrado.")
    return event


def events_between(start: datetime, end: datetime) -> list[CalendarEvent]:
    """Eventos que se sobrepõem ao intervalo [start, end)."""
    return list(db.session.scalars(
        select(CalendarEvent)
        .where(CalendarEvent.start_at < end, CalendarEvent.end_at >= start)
        .order_by(CalendarEvent.start_at)
    ))


def upcoming_events(days: int = 7, limit: int = 8) -> list[CalendarEvent]:
    now = time.now()
    return events_between(now, now + timedelta(days=days))[:limit]


def find_conflicts(start: datetime, end: datetime, exclude_id: int | None = None) -> list[CalendarEvent]:
    """Eventos com horário que bate com [start, end). Eventos de dia inteiro não contam como conflito."""
    rows = db.session.scalars(
        select(CalendarEvent).where(
            CalendarEvent.start_at < end,
            CalendarEvent.end_at > start,
            CalendarEvent.all_day.is_(False),
            CalendarEvent.id != (exclude_id or 0),
        )
    )
    return list(rows)


def month_grid(year: int, month: int) -> list[list[CalendarDay]]:
    """Semanas (segunda a domingo) do mês, com eventos e quests com prazo em cada dia."""
    today = time.today()
    weeks = stdlib_calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    first, last = weeks[0][0], weeks[-1][-1]
    by_day: dict[date, CalendarDay] = {
        d: CalendarDay(d, d.month == month, d == today) for week in weeks for d in week
    }
    for event in events_between(datetime.combine(first, dtime.min), datetime.combine(last + timedelta(days=1), dtime.min)):
        day = max(event.start_at.date(), first)
        while day <= min(event.end_at.date(), last):
            by_day[day].events.append(event)
            day += timedelta(days=1)
    for quest in quest_services.quests_due_between(first, last):
        by_day[quest.due_date].quests.append(quest)
    return [[by_day[d] for d in week] for week in weeks]


def local_events_to_push() -> list[CalendarEvent]:
    """Eventos locais ainda não enviados ao Google (usado pela integração)."""
    return list(db.session.scalars(
        select(CalendarEvent).where(CalendarEvent.source == "local", CalendarEvent.google_event_id.is_(None))
    ))


# ---------- Escrita ----------

def save_event(data: EventInput, event_id: int | None = None) -> tuple[CalendarEvent, list[CalendarEvent]]:
    """Cria ou edita. Retorna o evento e os conflitos de horário (aviso, não bloqueia)."""
    start, end = _normalize_times(data)
    if not data.title.strip():
        raise DomainError("O evento precisa de um título.")
    if data.kind not in KINDS:
        raise DomainError("Tipo de evento inválido.")
    event = get_event(event_id) if event_id else CalendarEvent(source="local")
    event.title = data.title.strip()
    event.description = data.description.strip()
    event.location = data.location.strip()
    event.kind = data.kind
    event.start_at, event.end_at, event.all_day = start, end, data.all_day
    event.quest_id = data.quest_id or None
    db.session.add(event)
    db.session.commit()
    conflicts = [] if data.all_day else find_conflicts(start, end, exclude_id=event.id)
    return event, conflicts


def delete_event(event_id: int) -> None:
    db.session.delete(get_event(event_id))
    db.session.commit()


def upsert_google_event(google_event_id: str, data: EventInput) -> tuple[CalendarEvent, bool]:
    """Importa ou atualiza um evento vindo do Google. Retorna (evento, criado?).

    A busca pelo google_event_id é o que evita duplicar eventos ao sincronizar várias vezes.
    """
    event = db.session.scalar(select(CalendarEvent).where(CalendarEvent.google_event_id == google_event_id))
    created = event is None
    if created:
        event = CalendarEvent(source="google", google_event_id=google_event_id, kind=data.kind)
        db.session.add(event)
    start, end = _normalize_times(data)
    event.title = data.title.strip() or "(sem título)"
    event.description = data.description
    event.location = data.location
    event.start_at, event.end_at, event.all_day = start, end, data.all_day
    return event, created


def mark_pushed(event_id: int, google_event_id: str) -> None:
    get_event(event_id).google_event_id = google_event_id


def delete_google_events_not_in(google_ids: set[str], start: datetime, end: datetime) -> int:
    """Remove eventos importados do Google no intervalo que não existem mais lá."""
    stale = [e for e in events_between(start, end) if e.source == "google" and e.google_event_id not in google_ids]
    for event in stale:
        db.session.delete(event)
    return len(stale)


def _normalize_times(data: EventInput) -> tuple[datetime, datetime]:
    if data.all_day:
        start = datetime.combine(data.start_at.date(), dtime.min)
        end_day = data.end_at.date() if data.end_at else start.date()
        end = datetime.combine(end_day, dtime(23, 59))
    else:
        start = data.start_at
        end = data.end_at or start + timedelta(hours=1)
    if end < start:
        raise DomainError("O fim do evento precisa ser depois do início.")
    return start, end
