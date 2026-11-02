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


class StoredSecret(db.Model):
    """Tokens das integrações (Google, Buffer, Notion, WhatsApp) cadastrados pela tela.

    Ficam no banco, não em arquivo, porque em hospedagens como o Render o disco é apagado a cada
    deploy ou reinício. O valor é JSON em texto. Nunca é mostrado de volta na tela.
    """

    __tablename__ = "stored_secrets"

    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, onupdate=time.now, nullable=False)
