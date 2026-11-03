"""Leitura e escrita das configurações do usuário (tabela app_settings)."""
import json
from typing import Any

from app.extensions import db

from .models import AppSetting
from .tenancy import current_user_id


def get_setting(key: str, default: Any = None) -> Any:
    row = _row(key)
    if row is None:
        return default
    try:
        return json.loads(row.value)
    except json.JSONDecodeError:
        return default


def set_setting(key: str, value: Any) -> None:
    payload = json.dumps(value, ensure_ascii=False)
    row = _row(key)
    if row is None:
        db.session.add(AppSetting(key=key, value=payload))
    else:
        row.value = payload
    db.session.commit()


def _row(key: str) -> AppSetting | None:
    return db.session.get(AppSetting, (current_user_id(), key))
