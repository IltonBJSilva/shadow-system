"""Regras de hábitos e API pública do módulo."""
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import delete, insert, select

from app.core import time
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.hunter import services as hunter

from . import streaks
from .models import Habit, HabitLog, habit_attributes

HISTORY_DAYS = 7
MAX_BACKFILL_DAYS = 7  # dá para marcar um dia esquecido da última semana, não do passado distante


@dataclass(frozen=True)
class HabitView:
    id: int
    name: str
    description: str
    xp_per_check: int
    done_today: bool
    current_streak: int
    best_streak: int
    last_days: list[tuple[date, bool]]  # (dia, feito) dos últimos HISTORY_DAYS dias


# ---------- Leitura ----------

def get_habit(habit_id: int) -> Habit:
    habit = db.session.get(Habit, habit_id)
    if habit is None:
        raise NotFoundError("Hábito não encontrado.")
    return habit


def list_habits(active: bool = True, today: date | None = None) -> list[HabitView]:
    today = today or time.today()
    habits = db.session.scalars(select(Habit).where(Habit.active == active).order_by(Habit.name))
    return [_view(h, today) for h in habits]


def best_current_streak(today: date | None = None) -> int:
    """Maior sequência atual entre os hábitos ativos (mostrado no dashboard)."""
    return max((h.current_streak for h in list_habits(today=today)), default=0)


def attribute_ids_for(habit: Habit) -> list[int]:
    return list(db.session.scalars(
        select(habit_attributes.c.attribute_id).where(habit_attributes.c.habit_id == habit.id)
    ))


# ---------- Escrita ----------

def save_habit(name: str, description: str, xp_per_check: int, attribute_ids: list[int],
               habit_id: int | None = None) -> Habit:
    if not name.strip():
        raise DomainError("O hábito precisa de um nome.")
    if xp_per_check < 0:
        raise DomainError("XP não pode ser negativo.")
    habit = get_habit(habit_id) if habit_id else Habit()
    habit.name, habit.description, habit.xp_per_check = name.strip(), description.strip(), xp_per_check
    db.session.add(habit)
    db.session.flush()
    db.session.execute(delete(habit_attributes).where(habit_attributes.c.habit_id == habit.id))
    if attribute_ids:
        db.session.execute(insert(habit_attributes),
                           [{"habit_id": habit.id, "attribute_id": a} for a in set(attribute_ids)])
    db.session.commit()
    return habit


def set_active(habit_id: int, active: bool) -> None:
    get_habit(habit_id).active = active
    db.session.commit()


def delete_habit(habit_id: int) -> None:
    db.session.delete(get_habit(habit_id))
    db.session.commit()


def check_in(habit_id: int, day: date | None = None) -> hunter.AwardResult:
    """Marca o hábito como feito no dia e concede XP (+1 ponto em cada atributo ligado)."""
    today = time.today()
    day = day or today
    if day > today:
        raise DomainError("Não dá para marcar um dia que ainda não chegou.")
    if (today - day).days > MAX_BACKFILL_DAYS:
        raise DomainError(f"Só é possível marcar até {MAX_BACKFILL_DAYS} dias atrás.")
    habit = get_habit(habit_id)
    if not habit.active:
        raise DomainError("Hábito arquivado. Reative para marcar.")
    if _log_for(habit_id, day):
        raise DomainError("Este dia já está marcado.")
    db.session.add(HabitLog(habit_id=habit_id, day=day, xp_awarded=habit.xp_per_check))
    result = hunter.award_xp(
        habit.xp_per_check,
        source="habit",
        source_id=habit.id,
        description=f"Hábito: {habit.name}" + ("" if day == today else f" ({day:%d/%m})"),
        attribute_ids=attribute_ids_for(habit),
        attribute_points=1,
    )
    db.session.commit()
    return result


def undo_check_in(habit_id: int, day: date | None = None) -> None:
    """Desmarca o dia e estorna exatamente o XP que foi dado."""
    day = day or time.today()
    habit = get_habit(habit_id)
    log = _log_for(habit_id, day)
    if log is None:
        raise DomainError("Este dia não estava marcado.")
    hunter.award_xp(
        -log.xp_awarded,
        source="habit",
        source_id=habit.id,
        description=f"Hábito desmarcado: {habit.name}",
        attribute_ids=attribute_ids_for(habit),
        attribute_points=1,
    )
    db.session.delete(log)
    db.session.commit()


# ---------- Internos ----------

def _log_for(habit_id: int, day: date) -> HabitLog | None:
    return db.session.scalar(select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.day == day))


def _view(habit: Habit, today: date) -> HabitView:
    days_done = {log.day for log in habit.logs}
    window = [today - timedelta(days=offset) for offset in range(HISTORY_DAYS - 1, -1, -1)]
    return HabitView(
        id=habit.id,
        name=habit.name,
        description=habit.description,
        xp_per_check=habit.xp_per_check,
        done_today=today in days_done,
        current_streak=streaks.current_streak(days_done, today),
        best_streak=streaks.best_streak(days_done),
        last_days=[(day, day in days_done) for day in window],
    )
