"""Guarda os tokens das integrações no banco (tabela stored_secrets).

Antes eles ficavam em arquivos JSON dentro de instance/. Se um arquivo antigo ainda existir e o banco
não tiver o valor, ele é importado na primeira leitura e o arquivo é apagado, então quem já tinha
tokens salvos localmente não precisa cadastrar de novo.
"""
import json
from pathlib import Path

from app.extensions import db

from .models import StoredSecret


def load(name: str, legacy_file: str | Path | None = None) -> dict:
    row = db.session.get(StoredSecret, name)
    if row is not None:
        try:
            return json.loads(row.value)
        except json.JSONDecodeError:
            return {}
    return (_import_legacy(name, legacy_file) if legacy_file else None) or {}


def exists(name: str, legacy_file: str | Path | None = None) -> bool:
    if db.session.get(StoredSecret, name) is not None:
        return True
    return bool(legacy_file) and _import_legacy(name, legacy_file) is not None


def save(name: str, values: dict) -> None:
    payload = json.dumps(values, ensure_ascii=False)
    row = db.session.get(StoredSecret, name)
    if row is None:
        db.session.add(StoredSecret(name=name, value=payload))
    else:
        row.value = payload
    db.session.commit()


def delete(name: str, legacy_file: str | Path | None = None) -> None:
    row = db.session.get(StoredSecret, name)
    if row is not None:
        db.session.delete(row)
        db.session.commit()
    if legacy_file:
        Path(legacy_file).unlink(missing_ok=True)


def _import_legacy(name: str, legacy_file: str | Path) -> dict | None:
    """Importa o arquivo antigo para o banco. None quando não há arquivo válido."""
    path = Path(legacy_file)
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(values, dict):
        return None
    save(name, values)
    path.unlink(missing_ok=True)
    return values
