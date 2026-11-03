"""API pública do módulo de treinos.

Criar um plano (de uma rotina pronta, de texto colado ou de um documento) e ativá-lo gera, conforme
as opções do plano:
- uma quest semanal recorrente por dia de treino (Daily Quest, com Strength e Vitality);
- eventos no calendário interno nas próximas semanas (dá para enviar ao Google pela tela do Google);
- um hábito "Treinar" que conta só os dias do plano (folga não quebra a sequência);
- sugestão de progressão de carga quando uma semana inteira é concluída.

Concluir a quest de um dia registra o treino (WorkoutSession) via evento "quest.completed".
Depende de: quests.services, habits.services, calendar.services, hunter.services.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import func, select

from app.core import time
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.calendar import services as calendar
from app.modules.habits import services as habits
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput

from . import parser, progression
from .models import WorkoutDay, WorkoutExercise, WorkoutPlan, WorkoutSession

CALENDAR_WEEKS = 4          # eventos criados à frente; renovados a cada treino concluído
HABIT_XP = 5                # o XP principal vem da quest; o hábito só conta a sequência
EVENT_MARK = "[Shadow System · treino #{plan_id}]"


@dataclass
class PlanOptions:
    name: str
    description: str = ""
    start_date: date | None = None
    session_time: str = "18:00"
    session_minutes: int = 60
    make_quests: bool = True
    make_events: bool = True
    make_habit: bool = True
    progression: bool = True
    load_increment_kg: float = 2.5


# ---------- Leitura ----------

def list_plans() -> list[WorkoutPlan]:
    return list(db.session.scalars(select(WorkoutPlan).order_by(WorkoutPlan.active.desc(), WorkoutPlan.name)))


def get_plan(plan_id: int) -> WorkoutPlan:
    plan = db.session.get(WorkoutPlan, plan_id)
    if plan is None:
        raise NotFoundError("Plano de treino não encontrado.")
    return plan


def plan_text(plan: WorkoutPlan) -> str:
    return parser.to_text(plan.name, [_parsed_day(day) for day in plan.days])


def sessions_count(plan_id: int | None = None) -> int:
    query = select(func.count(WorkoutSession.id))
    if plan_id is not None:
        query = query.where(WorkoutSession.plan_id == plan_id)
    return db.session.scalar(query) or 0


def week_progress(plan: WorkoutPlan, today: date | None = None) -> tuple[int, int]:
    """(treinos feitos nesta semana, treinos do plano por semana)."""
    monday = _monday(today or time.today())
    done = db.session.scalar(select(func.count(func.distinct(WorkoutSession.day_id))).where(
        WorkoutSession.plan_id == plan.id, WorkoutSession.completed_on >= monday,
        WorkoutSession.completed_on < monday + timedelta(days=7))) or 0
    return done, len(plan.days)


def recent_sessions(plan_id: int, limit: int = 10) -> list[tuple[date, str]]:
    rows = db.session.execute(
        select(WorkoutSession.completed_on, WorkoutDay.name)
        .join(WorkoutDay, WorkoutDay.id == WorkoutSession.day_id, isouter=True)
        .where(WorkoutSession.plan_id == plan_id)
        .order_by(WorkoutSession.completed_on.desc(), WorkoutSession.id.desc()).limit(limit))
    return [(day, name or "(dia removido)") for day, name in rows]


def progression_suggestions(plan: WorkoutPlan) -> list[progression.Suggestion]:
    suggestions = []
    for day in plan.days:
        for ex in day.exercises:
            values = progression.next_values(ex.reps, ex.load_kg, plan.load_increment_kg)
            if values is None:
                continue
            reps, load = values
            suggestions.append(progression.Suggestion(
                exercise_id=ex.id, name=f"{day.name}: {ex.name}",
                before=progression.describe(ex.sets, ex.reps, ex.load_kg),
                after=progression.describe(ex.sets, reps, load), load_kg=load, reps=reps))
    return suggestions


# ---------- Criação e edição ----------

def preview(text: str) -> parser.ParsedPlan:
    parsed = parser.parse(text)
    if not parsed.days:
        raise DomainError("Não encontrei nenhum treino no texto. Use o formato do exemplo: "
                          "um dia por linha (\"Segunda: Treino A\") e os exercícios abaixo (\"- Supino 4x10\").")
    weekdays = [day.weekday for day in parsed.days]
    if len(set(weekdays)) != len(weekdays):
        raise DomainError("Dois treinos no mesmo dia da semana. Junte os dois ou mude um deles de dia.")
    return parsed


def create_plan(text: str, options: PlanOptions, activate: bool = True) -> WorkoutPlan:
    parsed = preview(text)
    _validate(options)
    plan = WorkoutPlan()
    _apply_options(plan, options, parsed)
    db.session.add(plan)
    _replace_days(plan, parsed)
    db.session.commit()
    if activate:
        activate_plan(plan.id)
    return plan


def update_plan(plan_id: int, text: str, options: PlanOptions) -> WorkoutPlan:
    """Troca dias e exercícios. Se o plano estava ativo, refaz as automações com o conteúdo novo."""
    plan = get_plan(plan_id)
    parsed = preview(text)
    _validate(options)
    was_active = plan.active
    if was_active:
        deactivate_plan(plan_id, archive_habit=False)
    _apply_options(plan, options, parsed)
    _replace_days(plan, parsed)
    db.session.commit()
    if was_active:
        activate_plan(plan_id)
    return plan


def delete_plan(plan_id: int) -> None:
    plan = get_plan(plan_id)
    if plan.active:
        deactivate_plan(plan_id)
    db.session.delete(plan)
    db.session.commit()


# ---------- Automações ----------

def activate_plan(plan_id: int) -> list[str]:
    """Cria quests, eventos e hábito conforme as opções. Retorna o que foi feito (para a tela)."""
    plan = get_plan(plan_id)
    if plan.active:
        raise DomainError("Este plano já está ativo.")
    for other in db.session.scalars(select(WorkoutPlan).where(WorkoutPlan.active.is_(True), WorkoutPlan.id != plan.id)):
        clash = {d.weekday for d in other.days} & {d.weekday for d in plan.days}
        if clash:
            labels = ", ".join(parser.WEEKDAY_LABELS[d] for d in sorted(clash))
            raise DomainError(f"O plano \"{other.name}\" já está ativo em {labels}. Desative-o antes.")
    done: list[str] = []
    start = max(plan.start_date or time.today(), time.today())
    if plan.make_quests:
        attribute_ids = _training_attribute_ids()
        for day in plan.days:
            quest = quests.create_quest(QuestInput(
                title=f"Treino: {day.name}", description=_day_description(day), quest_type="daily",
                priority="medium", difficulty=3, due_date=_next_weekday(start, day.weekday),
                recurrence="weekly", attribute_ids=attribute_ids, estimated_minutes=plan.session_minutes,
            ), note=f"Quest criada pelo plano de treino \"{plan.name}\"")
            day.quest_series_id = quest.series_id or quest.id
        done.append(f"{len(plan.days)} quest(s) semanais")
    if plan.make_habit:
        weekdays = [d.weekday for d in plan.days]
        if plan.habit_id and _habit_exists(plan.habit_id):
            habit = habits.save_habit(f"Treinar ({plan.name})"[:120], "Marcado sozinho ao concluir um treino do plano.",
                                      HABIT_XP, [], plan.habit_id, weekdays=weekdays)
            habits.set_active(habit.id, True)
        else:
            habit = habits.save_habit(f"Treinar ({plan.name})"[:120], "Marcado sozinho ao concluir um treino do plano.",
                                      HABIT_XP, [], weekdays=weekdays)
        plan.habit_id = habit.id
        done.append("hábito de treino")
    plan.active = True
    db.session.commit()
    if plan.make_events:
        created = ensure_calendar(plan.id)
        done.append(f"{created} evento(s) no calendário")
    return done


def deactivate_plan(plan_id: int, archive_habit: bool = True) -> None:
    """Cancela as quests pendentes do plano, apaga os eventos futuros e arquiva o hábito.

    O histórico (treinos feitos, XP ganho) continua.
    """
    plan = get_plan(plan_id)
    for day in plan.days:
        if day.quest_series_id:
            active = quests.active_in_series(day.quest_series_id)
            if active:
                quests.cancel_quests([active.id])
            day.quest_series_id = None
    _delete_future_events(plan)
    if archive_habit and plan.habit_id and _habit_exists(plan.habit_id):
        habits.set_active(plan.habit_id, False)
    plan.active = False
    db.session.commit()


def ensure_calendar(plan_id: int, weeks: int = CALENDAR_WEEKS) -> int:
    """Garante eventos dos treinos nas próximas `weeks` semanas, sem duplicar. Retorna quantos criou."""
    plan = get_plan(plan_id)
    if not plan.active or not plan.make_events:
        return 0
    hour, minute = _parse_time(plan.session_time)
    today = time.today()
    start = max(plan.start_date or today, today)
    end = start + timedelta(weeks=weeks)
    mark = EVENT_MARK.format(plan_id=plan.id)
    existing = {(e.start_at, e.title) for e in calendar.events_between(datetime.combine(start, datetime.min.time()),
                                                                       datetime.combine(end, datetime.min.time()))
                if mark in (e.description or "")}
    created = 0
    for day in plan.days:
        cursor = _next_weekday(start, day.weekday)
        while cursor < end:
            start_at = datetime(cursor.year, cursor.month, cursor.day, hour, minute)
            title = f"Treino: {day.name}"
            if start_at >= time.now() and (start_at, title) not in existing:
                calendar.save_event(calendar.EventInput(
                    title=title, start_at=start_at, end_at=start_at + timedelta(minutes=plan.session_minutes),
                    kind="workout", description=f"{_day_description(day)}\n\n{mark}"))
                created += 1
            cursor += timedelta(weeks=1)
    return created


def record_workout(quest_series_id: int | None, quest_id: int, completed_on: date) -> list[tuple[str, str]]:
    """Chamado quando uma quest é concluída. Se for de um dia de treino, registra o treino."""
    if not quest_series_id:
        return []
    day = db.session.scalar(select(WorkoutDay).where(WorkoutDay.quest_series_id == quest_series_id))
    if day is None:
        return []
    plan = day.plan
    db.session.add(WorkoutSession(plan_id=plan.id, day_id=day.id, quest_id=quest_id, completed_on=completed_on))
    db.session.flush()
    messages: list[tuple[str, str]] = [(f"[SYSTEM] Treino registrado: {day.name}.", "success")]
    if plan.habit_id and _habit_exists(plan.habit_id):
        try:
            result = habits.check_in(plan.habit_id, completed_on)
            messages.extend(hunter.award_messages(result))
        except DomainError:
            pass  # já marcado hoje (dois treinos no mesmo dia) ou hábito arquivado
    messages.extend(hunter.title_unlock_messages(hunter.check_titles()))
    done, total = week_progress(plan, completed_on)
    monday = _monday(completed_on)
    if plan.progression and total and done >= total and plan.last_progression_week != monday:
        plan.pending_progression_week = monday
        messages.append(("[SYSTEM] Semana de treino completa! Há uma sugestão de progressão de carga no plano.",
                         "levelup"))
    if plan.active and plan.make_events:
        ensure_calendar(plan.id)
    return messages


def apply_progression(plan_id: int) -> int:
    """Aplica as sugestões aos exercícios e atualiza a descrição das quests. Retorna quantos mudaram."""
    plan = get_plan(plan_id)
    changes = progression_suggestions(plan)
    by_id = {s.exercise_id: s for s in changes}
    for day in plan.days:
        for ex in day.exercises:
            suggestion = by_id.get(ex.id)
            if suggestion:
                ex.reps, ex.load_kg = suggestion.reps, suggestion.load_kg
    plan.last_progression_week = plan.pending_progression_week or _monday(time.today())
    plan.pending_progression_week = None
    db.session.commit()
    _refresh_quest_descriptions(plan)
    return len(changes)


def dismiss_progression(plan_id: int) -> None:
    plan = get_plan(plan_id)
    plan.last_progression_week = plan.pending_progression_week
    plan.pending_progression_week = None
    db.session.commit()


# ---------- Internos ----------

def _validate(options: PlanOptions) -> None:
    if not 5 <= options.session_minutes <= 600:
        raise DomainError("Duração do treino entre 5 e 600 minutos.")
    if options.load_increment_kg < 0 or options.load_increment_kg > 50:
        raise DomainError("Aumento de carga entre 0 e 50 kg.")
    _parse_time(options.session_time)


def _apply_options(plan: WorkoutPlan, options: PlanOptions, parsed: parser.ParsedPlan) -> None:
    plan.name = (options.name or parsed.name or "Plano de treino").strip()[:120]
    plan.description = options.description.strip()
    plan.start_date = options.start_date
    plan.session_time = options.session_time
    plan.session_minutes = options.session_minutes
    plan.make_quests, plan.make_events = options.make_quests, options.make_events
    plan.make_habit, plan.progression = options.make_habit, options.progression
    plan.load_increment_kg = options.load_increment_kg


def _replace_days(plan: WorkoutPlan, parsed: parser.ParsedPlan) -> None:
    plan.days.clear()
    db.session.flush()
    for parsed_day in sorted(parsed.days, key=lambda d: d.weekday):
        day = WorkoutDay(weekday=parsed_day.weekday, name=parsed_day.name)
        for order, ex in enumerate(parsed_day.exercises):
            day.exercises.append(WorkoutExercise(name=ex.name, sets=ex.sets, reps=ex.reps, load_kg=ex.load_kg,
                                                 rest_seconds=ex.rest_seconds, notes=ex.notes, sort_order=order))
        plan.days.append(day)


def _parsed_day(day: WorkoutDay) -> parser.ParsedDay:
    return parser.ParsedDay(name=day.name, weekday=day.weekday, exercises=[
        parser.ParsedExercise(name=e.name, sets=e.sets, reps=e.reps, load_kg=e.load_kg,
                              rest_seconds=e.rest_seconds, notes=e.notes) for e in day.exercises])


def _day_description(day: WorkoutDay) -> str:
    lines = [f"• {ex.describe()}" for ex in _parsed_day(day).exercises]
    return "\n".join(lines)


def _refresh_quest_descriptions(plan: WorkoutPlan) -> None:
    for day in plan.days:
        if day.quest_series_id:
            active = quests.active_in_series(day.quest_series_id)
            if active:
                quests.update_description(active.id, _day_description(day))


def _delete_future_events(plan: WorkoutPlan) -> None:
    mark = EVENT_MARK.format(plan_id=plan.id)
    now = time.now()
    for event in calendar.events_between(now, now + timedelta(weeks=60)):
        if mark in (event.description or "") and event.start_at >= now:
            calendar.delete_event(event.id)


def _training_attribute_ids() -> list[int]:
    return [a.id for a in hunter.list_attributes() if a.key in ("strength", "vitality")]


def _habit_exists(habit_id: int) -> bool:
    try:
        habits.get_habit(habit_id)
        return True
    except NotFoundError:
        return False


def _next_weekday(start: date, weekday: int) -> date:
    return start + timedelta(days=(weekday - start.weekday()) % 7)


def _monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _parse_time(value: str) -> tuple[int, int]:
    try:
        hour, minute = (int(part) for part in (value or "").split(":"))
    except ValueError as exc:
        raise DomainError("Horário no formato HH:MM, ex.: 18:30.") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise DomainError("Horário no formato HH:MM, ex.: 18:30.")
    return hour, minute
