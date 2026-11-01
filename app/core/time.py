"""Relógio da aplicação.

Decisão: datas e horas são gravadas *sem fuso* (naive), já no horário local configurado em
TIMEZONE. É um sistema pessoal de uma pessoa só, em um fuso; isso deixa consultas e telas simples.
Integrações que recebem horários com fuso (ex.: Google Calendar) convertem com `to_local_naive`.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import current_app, has_app_context

DEFAULT_TZ = "America/Sao_Paulo"


def local_tz() -> ZoneInfo:
    name = current_app.config.get("TIMEZONE", DEFAULT_TZ) if has_app_context() else DEFAULT_TZ
    return ZoneInfo(name)


def now() -> datetime:
    """Agora, no horário local, sem fuso."""
    return datetime.now(local_tz()).replace(tzinfo=None, microsecond=0)


def today() -> date:
    return now().date()


def to_local_naive(value: datetime) -> datetime:
    """Converte um datetime com fuso para o horário local sem fuso. Naive passa direto."""
    if value.tzinfo is None:
        return value
    return value.astimezone(local_tz()).replace(tzinfo=None)


def to_aware(value: datetime) -> datetime:
    """Anexa o fuso local a um datetime naive (para enviar a APIs externas)."""
    return value if value.tzinfo else value.replace(tzinfo=local_tz())


def week_start(day: date) -> date:
    """Segunda-feira da semana de `day`."""
    return day - timedelta(days=day.weekday())
