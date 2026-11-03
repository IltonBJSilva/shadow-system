"""Tabelas de hábitos. Cada dia feito vira uma linha em habit_logs; `weekdays` diz quais dias contam."""
from datetime import date, datetime

from sqlalchemy import (Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, String,
                        Table, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import time
from app.core.models import TimestampMixin, UserOwnedMixin
from app.extensions import db

habit_attributes = Table(
    "habit_attributes",
    db.metadata,
    Column("habit_id", ForeignKey("habits.id", ondelete="CASCADE"), primary_key=True),
    Column("attribute_id", ForeignKey("attributes.id", ondelete="CASCADE"), primary_key=True),
)


class Habit(UserOwnedMixin, TimestampMixin, db.Model):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    xp_per_check: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Dias esperados ("0,2,4" = seg, qua, sex). Vazio = todos os dias. Ver streaks.py.
    weekdays: Mapped[str] = mapped_column(String(20), default="", server_default="", nullable=False)

    logs: Mapped[list["HabitLog"]] = relationship(back_populates="habit", cascade="all, delete-orphan")

    __table_args__ = (CheckConstraint("xp_per_check >= 0", name="xp_non_negative"),)


class HabitLog(UserOwnedMixin, db.Model):
    """Um dia em que o hábito foi feito. xp_awarded guarda o XP dado, para estornar o valor certo."""

    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    xp_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)

    habit: Mapped[Habit] = relationship(back_populates="logs")

    # Um check por hábito por dia: impede XP duplicado mesmo com clique duplo.
    __table_args__ = (UniqueConstraint("habit_id", "day", name="uq_habit_logs_habit_day"),)
