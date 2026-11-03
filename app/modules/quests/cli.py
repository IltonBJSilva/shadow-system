"""Comandos do Quest System (úteis para agendar no Agendador de Tarefas do Windows ou cron)."""
import click

from . import bp, services


@bp.cli.command("rollover")
def rollover():
    """Fecha ocorrências recorrentes vencidas e cria as de hoje."""
    from app.core import accounts
    from app.core.tenancy import as_user

    total = 0
    for user_id in accounts.all_user_ids():
        with as_user(user_id):
            total += services.roll_over_recurring()
    click.echo(f"{total} quest(s) recorrente(s) atualizada(s).")
