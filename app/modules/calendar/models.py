"""Eventos do calendário interno.

O calendário interno é a fonte de verdade do Shadow System. O Google Calendar é uma integração
opcional que importa e envia eventos para cá (ver app/integrations/google_calendar/).
"""
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TimestampMixin, UserOwnedMixin
from app.extensions import db


class CalendarEvent(UserOwnedMixin, TimestampMixin, db.Model):
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    location: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    kind: Mapped[str] = mapped_column(String(20), default="personal", nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quest_id: Mapped[int | None] = mapped_column(ForeignKey("quests.id", ondelete="SET NULL"), nullable=True)
    # Origem: "local" (criado aqui) ou "google" (importado).
    source: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    # Id do evento no Google. Único por usuário: é o que impede importar ou enviar o mesmo evento duas vezes.
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("end_at >= start_at", name="end_after_start"),
        UniqueConstraint("user_id", "google_event_id", name="uq_calendar_events_user_google_event"),
    )
