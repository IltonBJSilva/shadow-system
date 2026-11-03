"""Sombras recrutadas pelo jogador (o catálogo fica em shadows/catalog.py)."""
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core import time
from app.core.models import UserOwnedMixin
from app.extensions import db


class PlayerShadow(UserOwnedMixin, db.Model):
    __tablename__ = "player_shadows"

    id: Mapped[int] = mapped_column(primary_key=True)
    shadow_key: Mapped[str] = mapped_column(String(40), nullable=False)
    recruited_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)
    # Retrato dos desafios no momento do recrutamento (auditoria), ex.: "recurring 22/20 · evolution_streak 9/7".
    proof: Mapped[str] = mapped_column(String(300), default="", nullable=False)

    # Cada sombra uma vez só por jogador: recrutar de novo não duplica bônus.
    __table_args__ = (UniqueConstraint("user_id", "shadow_key", name="uq_player_shadows_user_shadow"),)
