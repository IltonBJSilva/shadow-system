"""Modelos e mixins compartilhados por todos os módulos."""
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db

from . import time


class TimestampMixin:
    """Adiciona created_at/updated_at (horário local, ver core/time.py)."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=time.now, onupdate=time.now, nullable=False
    )


class AppSetting(db.Model):
    """Configurações do usuário guardadas no banco (ex.: widgets do dashboard).

    O valor é JSON em texto para aceitar listas e dicionários sem criar uma tabela por opção.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
