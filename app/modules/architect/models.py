"""Tabelas do Arquiteto: suas metas, as sugestões de missão e a conversa (memória do chat)."""
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core import time
from app.core.models import TimestampMixin, UserOwnedMixin
from app.extensions import db


class ArchitectGoal(UserOwnedMixin, TimestampMixin, db.Model):
    """Uma meta sua ("Passar em Cálculo II", "Correr 5 km"). O Arquiteto sugere missões para ela."""

    __tablename__ = "architect_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    area: Mapped[str] = mapped_column(String(80), default="", nullable=False)  # nome de uma categoria de quest
    why: Mapped[str] = mapped_column(Text, default="", nullable=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active | done | dropped

    __table_args__ = (CheckConstraint("status IN ('active', 'done', 'dropped')", name="goal_status"),)


class ArchitectSuggestion(UserOwnedMixin, db.Model):
    """Missão sugerida. Só vira quest quando você aceita."""

    __tablename__ = "architect_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)  # por que o Arquiteto sugeriu
    category: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    recurrence: Mapped[str] = mapped_column(String(10), default="none", nullable=False)
    due_in_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    source: Mapped[str] = mapped_column(String(10), default="rules", nullable=False)  # rules | ai
    rule_key: Mapped[str] = mapped_column(String(80), default="", nullable=False, index=True)  # evita repetir
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("architect_goals.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="pending", nullable=False, index=True)
    quest_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)

    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="suggestion_difficulty"),
        CheckConstraint("status IN ('pending', 'accepted', 'dismissed')", name="suggestion_status"),
    )


class ArchitectMessage(UserOwnedMixin, db.Model):
    """Uma fala da conversa com o Arquiteto (só existe com a IA configurada)."""

    __tablename__ = "architect_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False, index=True)

    __table_args__ = (CheckConstraint("role IN ('user', 'assistant')", name="message_role"),)
