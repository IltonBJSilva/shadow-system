"""Modelos e mixins compartilhados por todos os módulos."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.extensions import db

from . import tenancy, time


class TimestampMixin:
    """Adiciona created_at/updated_at (horário local, ver core/time.py)."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=time.now, onupdate=time.now, nullable=False
    )


class User(db.Model):
    """Uma conta. O dono (id 1, role "owner") entra com OWNER_USERNAME/OWNER_PASSWORD_HASH do .env;
    usuários de teste (role "tester") são convidados pelo dono e definem a própria senha no convite.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(80), default="", server_default="", nullable=False)
    role: Mapped[str] = mapped_column(String(10), default="tester", server_default="tester", nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Convite: só o hash (sha256) do código fica no banco. Some quando a pessoa define a senha.
    invite_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    invite_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def is_owner(self) -> bool:
        return self.role == "owner"

    @property
    def label(self) -> str:
        return self.display_name or self.username


class UserOwnedMixin:
    """Coluna `user_id` de quem é a linha. Ver core/tenancy.py: o filtro por usuário é automático."""

    @declared_attr
    def user_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(
            ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
            default=tenancy.current_user_id,
        )


tenancy.install(UserOwnedMixin)


def _owner_pk_column():
    """user_id como parte da chave primária (tabelas chave-valor: app_settings, stored_secrets)."""
    return mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True,
                         default=tenancy.current_user_id)


class AppSetting(UserOwnedMixin, db.Model):
    """Configurações do usuário guardadas no banco (ex.: widgets do dashboard).

    O valor é JSON em texto para aceitar listas e dicionários sem criar uma tabela por opção.
    """

    __tablename__ = "app_settings"

    user_id: Mapped[int] = _owner_pk_column()
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class StoredSecret(UserOwnedMixin, db.Model):
    """Tokens das integrações (Google, Buffer, Notion, WhatsApp) cadastrados pela tela.

    Ficam no banco, não em arquivo, porque em hospedagens como o Render o disco é apagado a cada
    deploy ou reinício. O valor é JSON em texto. Nunca é mostrado de volta na tela.
    """

    __tablename__ = "stored_secrets"

    user_id: Mapped[int] = _owner_pk_column()
    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, onupdate=time.now, nullable=False)


class MediaAsset(db.Model):
    """Áudios e imagens do System (música, voz de entrada, fundos), enviados pelo dono pela tela.

    Ficam no banco e não no repositório: o repositório é público e esses arquivos podem ter direitos
    autorais (trilha e cenas do anime). São do sistema inteiro, não de um usuário (sem user_id).
    """

    __tablename__ = "media_assets"

    slot: Mapped[str] = mapped_column(String(30), primary_key=True)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    mimetype: Mapped[str] = mapped_column(String(60), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    etag: Mapped[str] = mapped_column(String(40), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, onupdate=time.now, nullable=False)
