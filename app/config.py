"""Configuração da aplicação, lida das variáveis de ambiente (.env).

Cada classe é um ambiente. `create_app` escolhe uma delas; os testes usam `TestingConfig`.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = ROOT_DIR / "instance"

# Carregado aqui, antes das classes, porque elas leem os.getenv na definição.
load_dotenv(ROOT_DIR / ".env")


def _bool(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "sim", "on")


def _project_path(value: str) -> str:
    """Caminhos relativos no .env são relativos à raiz do projeto, não à pasta de onde se roda."""
    if not value:
        return ""
    path = Path(value)
    return str(path if path.is_absolute() else ROOT_DIR / path)


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{INSTANCE_DIR / 'shadow.db'}"
    # Alguns provedores ainda entregam "postgres://", que o SQLAlchemy 2 não aceita.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = None  # o token vale enquanto a sessão durar

    AUTH_ENABLED = _bool(os.getenv("AUTH_ENABLED"))
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "hunter")
    OWNER_PASSWORD_HASH = os.getenv("OWNER_PASSWORD_HASH", "")

    GOOGLE_CLIENT_SECRETS_FILE = _project_path(os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "").strip())
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:5050/integrations/google/callback"
    )
    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    GOOGLE_TOKEN_FILE = str(INSTANCE_DIR / "google_token.json")

    KAUSA_SCHEDULER_URL = os.getenv("KAUSA_SCHEDULER_URL", "").strip().rstrip("/")

    BACKUP_DIR = str(INSTANCE_DIR / "backups")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    AUTH_ENABLED = False
    GOOGLE_CLIENT_SECRETS_FILE = ""
    KAUSA_SCHEDULER_URL = ""


CONFIGS = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
