"""Guarda o token da API do Buffer cadastrado pela tela.

Arquivo: instance/buffer_token.json (a pasta instance/ não vai para o git). O token nunca é mostrado
de volta na tela nem escrito em log: só os 4 últimos caracteres aparecem.
Se não houver token salvo pela tela, vale BUFFER_API_KEY do .env.

Tokens pessoais do Buffer vencem em 90 dias; a data de criação serve para avisar antes.
"""
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from flask import current_app

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


def _path() -> Path:
    return Path(current_app.config["BUFFER_TOKEN_FILE"])


def _load() -> dict:
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def api_key() -> str:
    return _load().get("api_key") or current_app.config.get("BUFFER_API_KEY", "")


def organization_id() -> str | None:
    return _load().get("organization_id")


def save(api_key_value: str, created_at: date, organization: str) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"api_key": api_key_value.strip(), "created_at": created_at.isoformat(), "organization_id": organization}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def remember_organization(organization: str) -> None:
    data = _load()
    if data:
        data["organization_id"] = organization
        _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear() -> None:
    _path().unlink(missing_ok=True)


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
