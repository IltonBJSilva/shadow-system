"""Garante que as migrations criam o mesmo schema que os modelos descrevem."""
from flask_migrate import upgrade
from sqlalchemy import inspect

from app import create_app
from app.extensions import db


def test_migrations_create_every_model_table(tmp_path):
    database = tmp_path / "migrated.db"
    app = create_app("testing", {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}"})
    with app.app_context():
        upgrade()
        migrated = set(inspect(db.engine).get_table_names())
        db.engine.dispose()  # libera o arquivo no Windows
    assert database.exists()
    missing = set(db.metadata.tables) - migrated
    assert not missing, f"Tabelas sem migration: {missing}. Rode `flask db migrate`."
