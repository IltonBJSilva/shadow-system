"""Tabelas do Quest System.

As ligações com atributos usam apenas o id (FK para attributes.id). O módulo Quests não importa
os modelos do Hunter: nomes de atributos vêm de hunter.services.
"""
from datetime import date, datetime

from sqlalchemy import (CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, String, Table,
                        Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import time
from app.core.models import TimestampMixin
from app.extensions import db

quest_attributes = Table(
    "quest_attributes",
    db.metadata,
    Column("quest_id", ForeignKey("quests.id", ondelete="CASCADE"), primary_key=True),
    Column("attribute_id", ForeignKey("attributes.id", ondelete="CASCADE"), primary_key=True),
)

category_attributes = Table(
    "quest_category_attributes",
    db.metadata,
    Column("category_id", ForeignKey("quest_categories.id", ondelete="CASCADE"), primary_key=True),
    Column("attribute_id", ForeignKey("attributes.id", ondelete="CASCADE"), primary_key=True),
)


class QuestCategory(db.Model):
    """Categoria (Treino, Estudos, Finanças...). Define os atributos padrão das quests dela."""

    __tablename__ = "quest_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(9), default="#8b5cf6", nullable=False)


class Quest(TimestampMixin, db.Model):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    quest_type: Mapped[str] = mapped_column(String(20), default="custom", nullable=False, index=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("quest_categories.id", ondelete="SET NULL"), nullable=True
    )
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    completion_criteria: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reward: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    recurrence: Mapped[str] = mapped_column(String(10), default="none", nullable=False)
    # Todas as ocorrências de uma quest recorrente compartilham o series_id (id da primeira).
    series_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    category: Mapped[QuestCategory | None] = relationship()
    logs: Mapped[list["QuestLog"]] = relationship(
        back_populates="quest", cascade="all, delete-orphan", order_by="QuestLog.created_at.desc()"
    )

    # Mesmos nomes de QuestView, para que os templates aceitem os dois.
    @property
    def category_name(self) -> str | None:
        return self.category.name if self.category else None

    @property
    def category_color(self) -> str | None:
        return self.category.color if self.category else None

    @property
    def type_label(self) -> str:
        from .constants import QUEST_TYPES

        return QUEST_TYPES.get(self.quest_type, self.quest_type)

    @property
    def is_overdue(self) -> bool:
        from .constants import ACTIVE_STATUSES

        return bool(self.due_date and self.due_date < time.today() and self.status in ACTIVE_STATUSES)

    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="difficulty_range"),
        CheckConstraint("xp_reward >= 0", name="xp_reward_non_negative"),
    )


class QuestLog(db.Model):
    """Histórico da quest: criada, iniciada, concluída, não realizada, cancelada, editada."""

    __tablename__ = "quest_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)

    quest: Mapped[Quest] = relationship(back_populates="logs")
