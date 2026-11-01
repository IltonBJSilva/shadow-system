"""Comandos do Quest System (úteis para agendar no Agendador de Tarefas do Windows ou cron)."""
import click

from . import bp, services


@bp.cli.command("rollover")
def rollover():
    """Fecha ocorrências recorrentes vencidas e cria as de hoje."""
    count = services.roll_over_recurring()
    click.echo(f"{count} quest(s) recorrente(s) atualizada(s).")
