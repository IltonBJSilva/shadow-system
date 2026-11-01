"""Fixtures compartilhadas.

Cada teste recebe um app novo com SQLite em memória e as tabelas criadas por `db.create_all()`
(rápido). A migration real é testada separadamente em test_migrations.py.
Arquivos de token (Google, Buffer) vão para uma pasta temporária do teste, nunca para instance/.
"""
import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture
def app(tmp_path):
    app = create_app("testing", {
        "GOOGLE_TOKEN_FILE": str(tmp_path / "google_token.json"),
        "BUFFER_TOKEN_FILE": str(tmp_path / "buffer_token.json"),
        "CREDENTIALS_DIR": str(tmp_path / "credentials"),
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db
