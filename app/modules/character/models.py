"""Inventário do jogador: itens do catálogo (character/catalog.py) que ele já conquistou."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core import time
from app.core.models import UserOwnedMixin
from app.extensions import db


class PlayerItem(UserOwnedMixin, db.Model):
    __tablename__ = "player_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_key: Mapped[str] = mapped_column(String(40), nullable=False)
    equipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(120), default="", nullable=False)  # como foi conquistado
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)

    # Um exemplar de cada item por jogador: nada de duplicar bônus.
    __table_args__ = (UniqueConstraint("user_id", "item_key", name="uq_player_items_user_item"),)
