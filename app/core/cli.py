"""Comandos de manutenção: `flask backup create` e `flask backup list`."""
import shutil
from pathlib import Path

import click
from flask import Flask, current_app

from . import time


def register(app: Flask) -> None:
    @app.cli.group("backup")
    def backup_cli():
        """Backup do banco de dados."""

    @backup_cli.command("create")
    def create_backup():
        """Copia o banco SQLite para instance/backups/ com data e hora no nome."""
        destination = create_sqlite_backup()
        click.echo(f"Backup criado: {destination}")

    @backup_cli.command("list")
    def list_backups():
        """Lista os backups existentes."""
        folder = Path(current_app.config["BACKUP_DIR"])
        files = sorted(folder.glob("*.db")) if folder.exists() else []
        for file in files:
            click.echo(file.name)
        if not files:
            click.echo("Nenhum backup ainda.")


def create_sqlite_backup() -> Path:
    """Copia o arquivo do SQLite. Para PostgreSQL use pg_dump (ver docs/security.md)."""
    uri: str = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:///") or uri.endswith(":memory:"):
        raise click.ClickException("Backup automático só para SQLite. No PostgreSQL use pg_dump.")
    source = Path(uri.removeprefix("sqlite:///"))
    if not source.exists():
        raise click.ClickException(f"Banco não encontrado em {source}. Rode `flask db upgrade`.")
    folder = Path(current_app.config["BACKUP_DIR"])
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / f"shadow-{time.now():%Y%m%d-%H%M%S}.db"
    shutil.copy2(source, destination)
    return destination
