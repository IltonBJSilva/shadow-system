"""Tabelas do Quest System.

As ligações com atributos usam apenas o id (FK para attributes.id). O módulo Quests não importa
os modelos do Hunter: nomes de atributos vêm de hunter.services.
"""
from datetime import date, datetime

from sqlalchemy import (CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Integer, String, Table,
                        Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import time
from app.core.models import TimestampMixin, UserOwnedMixin
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


class QuestCategory(UserOwnedMixin, db.Model):
    """Categoria (Treino, Estudos, Finanças...). Define os atributos padrão das quests dela."""

    __tablename__ = "quest_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    color: Mapped[str] = mapped_column(String(9), default="#8b5cf6", nullable=False)
    # Especialização (corpo, estudos, disciplina...): é o que sombras e equipamentos usam para dar bônus.
    specialty: Mapped[str] = mapped_column(String(20), default="other", server_default="other", nullable=False)
    # Ajuste do XP das missões desta categoria (0,8 a 1,2). Ver hunter/progression.py.
    xp_multiplier: Mapped[float] = mapped_column(Float, default=1.0, server_default="1", nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_quest_categories_user_name"),)


class Quest(UserOwnedMixin, TimestampMixin, db.Model):
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
    # XP por tempo: minutos estimados (definidos antes de concluir). Vazio = missão antiga (XP fixo).
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)  # informado ao concluir
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # hora do servidor
    # O que foi dado na conclusão (cópia do XpEvent, imutável): base, bônus.
    xp_base: Mapped[int | None] = mapped_column(Integer, nullable=True)
    xp_bonus: Mapped[int | None] = mapped_column(Integer, nullable=True)

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


class QuestLog(UserOwnedMixin, db.Model):
    """Histórico da quest: criada, iniciada, concluída, não realizada, cancelada, editada."""

    __tablename__ = "quest_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)

    quest: Mapped[Quest] = relationship(back_populates="logs")


class ActivitySession(UserOwnedMixin, db.Model):
    """Intervalo de tempo dedicado a uma missão concluída (hora do servidor).

    É a base das "horas de atividade" do ranking: intervalos que se sobrepõem contam uma vez só e um
    dia nunca passa de 24 h (ver quests.timeline). Cada linha nasce na conclusão e não é editada.
    """

    __tablename__ = "activity_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int | None] = mapped_column(ForeignKey("quests.id", ondelete="SET NULL"), nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)  # tempo dedicado (real ou estimado)
    credited_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # minutos que renderam XP base
    specialty: Mapped[str] = mapped_column(String(20), default="other", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)

    __table_args__ = (CheckConstraint("ended_at >= started_at", name="session_end_after_start"),)
