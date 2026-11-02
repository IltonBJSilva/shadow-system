"""Tokens no banco (stored_secrets) e importação dos arquivos antigos de instance/."""
import json
from datetime import date

from app import config
from app.core import secret_store
from app.integrations import credentials
from app.integrations.buffer import token_store


def test_save_load_delete(app):
    secret_store.save("x", {"token": "abc"})
    assert secret_store.exists("x") and secret_store.load("x") == {"token": "abc"}
    secret_store.save("x", {"token": "def"})
    assert secret_store.load("x") == {"token": "def"}
    secret_store.delete("x")
    assert not secret_store.exists("x") and secret_store.load("x") == {}


def test_legacy_file_is_imported_once_and_removed(app, tmp_path):
    legacy = tmp_path / "old.json"
    legacy.write_text(json.dumps({"api_key": "k" * 40}))
    assert secret_store.load("buffer_token", legacy) == {"api_key": "k" * 40}
    assert not legacy.exists()
    assert secret_store.load("buffer_token") == {"api_key": "k" * 40}


def test_integration_stores_use_database(app):
    credentials.save("notion", {"token": "secret_1234567890"})
    assert credentials.load("notion")["token"] == "secret_1234567890"
    token_store.save("t" * 40, date(2026, 11, 1), "org1")
    assert token_store.api_key() == "t" * 40 and token_store.organization_id() == "org1"
    token_store.clear()
    assert token_store.api_key() == ""


def test_postgres_urls_use_psycopg_driver(monkeypatch):
    for raw in ("postgres://u:p@h:5432/db", "postgresql://u:p@h:5432/db"):
        monkeypatch.setenv("DATABASE_URL", raw)
        assert config._database_url() == "postgresql+psycopg://u:p@h:5432/db"
    assert config._engine_options("postgresql+psycopg://x")["pool_pre_ping"] is True
    assert config._engine_options("sqlite:///x.db") == {}
