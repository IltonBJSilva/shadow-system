"""Registro de falhas (Zona de Falha): cada quest recorrente não feita vira uma linha aqui.

O motivo é escolhido por você depois (procrastinação, planejamento, imprevisto, limitação real).
Conforme as regras, alguns motivos devolvem o XP da punição e cancelam a Penalty Quest.
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core import time
from app.core.models import UserOwnedMixin
from app.extensions import db


class QuestFailure(UserOwnedMixin, db.Model):
    __tablename__ = "quest_failures"

    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int | None] = mapped_column(ForeignKey("quests.id", ondelete="SET NULL"), nullable=True)
    quest_title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    penalty_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    penalty_quest_id: Mapped[int | None] = mapped_column(ForeignKey("quests.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False, index=True)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CoinTransaction(UserOwnedMixin, db.Model):
    """Extrato de moedas da Loja do Tempo: + ganhas em missões, - gastas na loja. Saldo = soma."""

    __tablename__ = "coin_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False, index=True)
