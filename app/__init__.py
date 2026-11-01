"""Shadow System: Application Factory.

`create_app` monta a aplicação: lê a configuração, liga as extensões, registra o núcleo (core),
os módulos de domínio e as integrações. Nada roda na importação deste pacote.
"""
import logging
import os

from flask import Flask

from .config import CONFIGS, INSTANCE_DIR, ROOT_DIR, DevelopmentConfig


def create_app(config_name: str | None = None, overrides: dict | None = None) -> Flask:
    """Cria a aplicação.

    config_name: "development" (padrão), "production" ou "testing". Também lido de SHADOW_ENV.
    overrides: valores que substituem a configuração antes das extensões serem ligadas
    (usado nos testes, por exemplo para apontar outro banco).
    """
    name = config_name or os.getenv("SHADOW_ENV", "development")
    app = Flask(__name__, instance_path=str(INSTANCE_DIR))
    app.config.from_object(CONFIGS.get(name, DevelopmentConfig))
    app.config.update(overrides or {})
    INSTANCE_DIR.mkdir(exist_ok=True)

    _configure_logging(app)
    _init_extensions(app)
    _register_core(app)
    _register_modules(app)
    _register_integrations(app)
    return app


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("alembic.runtime.plugins").setLevel(logging.WARNING)


def _init_extensions(app: Flask) -> None:
    from .extensions import csrf, db, migrate

    db.init_app(app)
    # render_as_batch: o SQLite não altera colunas com ALTER TABLE; o modo batch recria a tabela.
    migrate.init_app(app, db, render_as_batch=True, directory=str(ROOT_DIR / "migrations"))
    csrf.init_app(app)


def _register_core(app: Flask) -> None:
    from .core import cli, errors, models, security, template_helpers  # noqa: F401 (models: tabelas)

    security.register(app)
    errors.register(app)
    template_helpers.register(app)
    cli.register(app)


def _register_modules(app: Flask) -> None:
    from .modules import register_modules

    register_modules(app)


def _register_integrations(app: Flask) -> None:
    from .integrations import register_integrations

    register_integrations(app)
