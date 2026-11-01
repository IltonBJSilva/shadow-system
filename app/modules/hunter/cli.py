"""Comando `flask seed`: cria os dados iniciais (hunter, ranks e atributos)."""
import click

from . import bp, services


@bp.cli.command("seed")
def seed():
    """Cria hunter, ranks e atributos padrão (não altera o que já existe)."""
    services.seed_defaults()
    click.echo("Dados iniciais conferidos.")
