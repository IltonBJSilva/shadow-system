"""Tabelas do módulo de treinos. Outros módulos não importam daqui: usam training.services.

Um plano tem dias (um por dia da semana) e cada dia tem exercícios. Ao ativar, cada dia vira uma
quest semanal recorrente (`quest_series_id` liga o dia à série de quests), eventos no calendário e,
se pedido, um hábito "Treinar" com os mesmos dias. Cada treino concluído vira uma WorkoutSession.
"""
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import time
from app.core.models import TimestampMixin, UserOwnedMixin
from app.extensions import db


class WorkoutPlan(UserOwnedMixin, TimestampMixin, db.Model):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    session_time: Mapped[str] = mapped_column(String(5), default="18:00", nullable=False)  # "HH:MM"
    session_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    # Automações escolhidas ao criar (ver services.activate_plan).
    make_quests: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    make_events: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    make_habit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    progression: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    load_increment_kg: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    habit_id: Mapped[int | None] = mapped_column(ForeignKey("habits.id", ondelete="SET NULL"), nullable=True)
    # Semana (segunda-feira) cuja sugestão de progressão está esperando você aplicar ou ignorar.
    pending_progression_week: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_progression_week: Mapped[date | None] = mapped_column(Date, nullable=True)

    days: Mapped[list["WorkoutDay"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="WorkoutDay.weekday")

    __table_args__ = (
        CheckConstraint("session_minutes BETWEEN 5 AND 600", name="session_minutes_range"),
        CheckConstraint("load_increment_kg >= 0", name="load_increment_non_negative"),
    )


class WorkoutDay(UserOwnedMixin, db.Model):
    __tablename__ = "workout_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 = segunda ... 6 = domingo
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    quest_series_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    plan: Mapped[WorkoutPlan] = relationship(back_populates="days")
    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="day", cascade="all, delete-orphan", order_by="WorkoutExercise.sort_order")

    __table_args__ = (CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),)


class WorkoutExercise(UserOwnedMixin, db.Model):
    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sets: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    reps: Mapped[str] = mapped_column(String(20), default="", nullable=False)  # "8-12", "45s", "20min", "max"
    load_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    day: Mapped[WorkoutDay] = relationship(back_populates="exercises")

    __table_args__ = (CheckConstraint("sets BETWEEN 1 AND 20", name="sets_range"),)


class WorkoutSession(UserOwnedMixin, db.Model):
    """Um treino feito (a quest do dia foi concluída)."""

    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    day_id: Mapped[int | None] = mapped_column(ForeignKey("workout_days.id", ondelete="SET NULL"), nullable=True)
    quest_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)
