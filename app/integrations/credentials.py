"""Credenciais cadastradas pela tela (Notion, WhatsApp...).

Ficam no banco (tabela stored_secrets, ver core/secret_store.py) com o nome "credentials:<integração>".
Valores secretos nunca voltam para a tela: use `mask()` para mostrar só o final.
"""
from pathlib import Path

from flask import current_app

from app.core import secret_store


def _key(name: str) -> str:
    return f"credentials:{name}"


def _legacy_file(name: str) -> Path:
    """Arquivo antigo (instance/credentials/<nome>.json), importado para o banco se existir."""
    return Path(current_app.config["CREDENTIALS_DIR"]) / f"{name}.json"


def load(name: str) -> dict:
    return secret_store.load(_key(name), _legacy_file(name))


def save(name: str, values: dict) -> None:
    secret_store.save(_key(name), values)


def update(name: str, **values) -> None:
    data = load(name)
    data.update(values)
    save(name, data)


def clear(name: str) -> None:
    secret_store.delete(_key(name), _legacy_file(name))


def mask(secret: str | None) -> str:
    return f"••••{secret[-4:]}" if secret and len(secret) > 8 else "••••"
