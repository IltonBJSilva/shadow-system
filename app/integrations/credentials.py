"""Credenciais cadastradas pela tela (Notion, WhatsApp...).

Cada integração tem um arquivo em instance/credentials/<nome>.json (fora do git). Valores secretos
nunca voltam para a tela: use `mask()` para mostrar só o final.
"""
import json
from pathlib import Path

from flask import current_app


def _path(name: str) -> Path:
    return Path(current_app.config["CREDENTIALS_DIR"]) / f"{name}.json"


def load(name: str) -> dict:
    try:
        return json.loads(_path(name).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(name: str, values: dict) -> None:
    path = _path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(values, indent=2, ensure_ascii=False), encoding="utf-8")


def update(name: str, **values) -> None:
    data = load(name)
    data.update(values)
    save(name, data)


def clear(name: str) -> None:
    _path(name).unlink(missing_ok=True)


def mask(secret: str | None) -> str:
    return f"••••{secret[-4:]}" if secret and len(secret) > 8 else "••••"
