"""Feed dos Hunters: cada linha é uma atividade que o jogador permitiu compartilhar."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core import time
from app.core.models import UserOwnedMixin
from app.extensions import db


class ActivityPost(UserOwnedMixin, db.Model):
    __tablename__ = "activity_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # quest | level | rank | shadow | item | title | memory
    text: Mapped[str] = mapped_column(String(240), nullable=False)
    specialty: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reward: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    icon: Mapped[str] = mapped_column(String(8), default="◆", nullable=False)
    # Memória pública ligada ao post (só quando o jogador escolheu publicar a memória).
    memory_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False, index=True)
