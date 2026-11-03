"""Guarda o token da API do Buffer cadastrado pela tela.

Fica no banco (tabela stored_secrets, nome "buffer_token"). O token nunca é mostrado
de volta na tela nem escrito em log: só os 4 últimos caracteres aparecem.
Se não houver token salvo pela tela, vale BUFFER_API_KEY do .env (só para o dono).

Tokens pessoais do Buffer vencem em 90 dias; a data de criação serve para avisar antes.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from flask import current_app

from app.core import secret_store

VALID_DAYS = 90
REMINDER_DAYS = 15
TOKENS_URL = "https://publish.buffer.com/settings/api"


@dataclass(frozen=True)
class TokenStatus:
    configured: bool
    source: str | None  # "tela" ou ".env"
    masked: str
    created_at: date | None
    expires_at: date | None
    days_left: int | None

    @property
    def level(self) -> str:
        if not self.configured:
            return "missing"
        if self.days_left is None:
            return "unknown"
        if self.days_left < 0:
            return "expired"
        return "warning" if self.days_left <= REMINDER_DAYS else "ok"


KEY = "buffer_token"


def _legacy_file() -> Path:
    """Arquivo antigo (instance/buffer_token.json), importado para o banco se existir."""
    return Path(current_app.config["BUFFER_TOKEN_FILE"])


def _load() -> dict:
    return secret_store.load(KEY, _legacy_file())


def api_key() -> str:
    return _load().get("api_key") or _env_key()


def _env_key() -> str:
    """BUFFER_API_KEY do .env é do dono: usuários de teste só usam o token que cadastrarem."""
    from app.core.tenancy import OWNER_ID, current_user_id

    return current_app.config.get("BUFFER_API_KEY", "") if current_user_id() == OWNER_ID else ""


def organization_id() -> str | None:
    return _load().get("organization_id")


def save(api_key_value: str, created_at: date, organization: str) -> None:
    payload = {"api_key": api_key_value.strip(), "created_at": created_at.isoformat(), "organization_id": organization}
    secret_store.save(KEY, payload)


def remember_organization(organization: str) -> None:
    data = _load()
    if data:
        data["organization_id"] = organization
        secret_store.save(KEY, data)


def clear() -> None:
    secret_store.delete(KEY, _legacy_file())


def status(today: date | None = None) -> TokenStatus:
    data = _load()
    key = api_key()
    if not key:
        return TokenStatus(False, None, "", None, None, None)
    source = "tela" if data.get("api_key") else ".env"
    created = None
    raw_created = data.get("created_at") if source == "tela" else current_app.config.get("BUFFER_KEY_CREATED_AT")
    try:
        created = date.fromisoformat(raw_created) if raw_created else None
    except ValueError:
        created = None
    expires = created + timedelta(days=VALID_DAYS) if created else None
    today = today or date.today()
    return TokenStatus(
        configured=True,
        source=source,
        masked=f"••••{key[-4:]}" if len(key) > 4 else "••••",
        created_at=created,
        expires_at=expires,
        days_left=(expires - today).days if expires else None,
    )
