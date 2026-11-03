"""Tabelas do módulo Hunter. Outros módulos não importam daqui: usam hunter.services."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import time
from app.core.models import TimestampMixin, UserOwnedMixin
from app.extensions import db


class Hunter(UserOwnedMixin, TimestampMixin, db.Model):
    """O perfil do jogador. Um por usuário (o filtro por user_id é automático, ver core/tenancy.py)."""

    __tablename__ = "hunters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    # Link público (https) de uma imagem para o avatar. Vazio = mostra só o rank.
    avatar_url: Mapped[str] = mapped_column(String(500), default="", server_default="", nullable=False)
    # Soma de todos os XpEvent. Guardada aqui para não somar o histórico a cada página.
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (CheckConstraint("total_xp >= 0", name="total_xp_non_negative"),)


class Rank(UserOwnedMixin, db.Model):
    """Rank configurável (E, D, C, ... SS e especiais), liberado ao atingir min_level."""

    __tablename__ = "ranks"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(4), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    min_level: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(String(9), default="#8b5cf6", nullable=False)

    __table_args__ = (
        CheckConstraint("min_level >= 1", name="min_level_positive"),
        UniqueConstraint("user_id", "code", name="uq_ranks_user_code"),
        UniqueConstraint("user_id", "min_level", name="uq_ranks_user_min_level"),
    )


class Attribute(UserOwnedMixin, db.Model):
    """Atributo pessoal (Strength, Focus...). É um indicador de evolução, não uma avaliação."""

    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_attributes_user_key"),)


class XpEvent(UserOwnedMixin, db.Model):
    """Histórico de evolução: cada ganho (ou estorno) de XP com sua origem."""

    __tablename__ = "xp_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False, index=True)

    gains: Mapped[list["AttributeGain"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class AttributeGain(UserOwnedMixin, db.Model):
    """Pontos de atributo concedidos por um XpEvent."""

    __tablename__ = "attribute_gains"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("xp_events.id", ondelete="CASCADE"), nullable=False)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)

    event: Mapped[XpEvent] = relationship(back_populates="gains")
    attribute: Mapped[Attribute] = relationship()


class Title(UserOwnedMixin, db.Model):
    """Título que o Hunter pode exibir. Desbloqueado quando a métrica `rule` chega em `threshold`.

    rule: "level", "total_xp" ou uma métrica registrada por outro módulo (ex.: "quests_completed").
    "custom" = criado pelo usuário, já nasce desbloqueado. `key` identifica os títulos padrão.
    """

    __tablename__ = "titles"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    rule: Mapped[str] = mapped_column(String(40), nullable=False)
    threshold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Conquista: ícone mostrado na lista e XP dado uma vez, no desbloqueio.
    icon: Mapped[str] = mapped_column(String(8), default="🏅", server_default="🏅", nullable=False)
    reward_xp: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    __table_args__ = (
        CheckConstraint("threshold >= 0", name="threshold_non_negative"),
        CheckConstraint("reward_xp >= 0", name="reward_xp_non_negative"),
        UniqueConstraint("user_id", "key", name="uq_titles_user_key"),
        UniqueConstraint("user_id", "name", name="uq_titles_user_name"),
    )
