"""Tabela das memórias (foto otimizada + miniatura ficam no banco, fora do repositório)."""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.core import time
from app.core.models import UserOwnedMixin
from app.extensions import db


class Memory(UserOwnedMixin, db.Model):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int | None] = mapped_column(ForeignKey("quests.id", ondelete="SET NULL"), nullable=True, index=True)
    quest_title: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)   # aparece se for pública
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)          # observação pessoal: sempre privada
    kind: Mapped[str] = mapped_column(String(20), default="other", nullable=False)
    specialty: Mapped[str] = mapped_column(String(20), default="other", nullable=False)
    achievement: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    rank_code: Mapped[str] = mapped_column(String(4), default="", nullable=False)  # rank no dia da memória
    visibility: Mapped[str] = mapped_column(String(10), default="private", nullable=False)  # private | public
    day: Mapped[date] = mapped_column(Date, default=time.today, nullable=False, index=True)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes da foto + miniatura
    image: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    thumb: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)
