"""Extensões Flask criadas sem app e ligadas em `create_app` (padrão Application Factory).

Importe daqui em qualquer módulo: `from app.extensions import db`.
"""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import MetaData

# Nomes fixos para constraints deixam as migrations do Alembic previsíveis (e funcionam no SQLite).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENTION))
migrate = Migrate()
csrf = CSRFProtect()
