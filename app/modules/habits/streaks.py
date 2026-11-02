"""Cálculo de sequências (streaks) a partir dos dias feitos. Funções puras.

`weekdays` = dias da semana em que o hábito é esperado (0 = segunda ... 6 = domingo). Vazio ou None
= todos os dias. Um dia fora da agenda (ex.: domingo de descanso) não quebra a sequência; se o hábito
for feito nesse dia mesmo assim, conta.
"""
from datetime import date, timedelta
from typing import Iterable

WEEKDAY_NAMES = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def parse_weekdays(value: str | None) -> set[int]:
    """"0,2,4" -> {0, 2, 4}. Ignora o que não for dia válido."""
    return {int(p) for p in (value or "").split(",") if p.strip().isdigit() and 0 <= int(p) <= 6}


def format_weekdays(days: Iterable[int]) -> str:
    return ",".join(str(d) for d in sorted(set(days)) if 0 <= d <= 6)


def describe_weekdays(days: set[int]) -> str:
    if not days or len(days) == 7:
        return "Todos os dias"
    return ", ".join(WEEKDAY_NAMES[d] for d in sorted(days))


def _expected(day: date, weekdays: set[int] | None) -> bool:
    return not weekdays or day.weekday() in weekdays


def current_streak(days_done: Iterable[date], today: date, weekdays: set[int] | None = None) -> int:
    """Sequência até hoje.

    Se hoje ainda não foi feito, conta até ontem: a sequência só "quebra" depois que o dia acaba.
    """
    done = set(days_done)
    if not done:
        return 0
    earliest = min(done)
    cursor = today if today in done else today - timedelta(days=1)
    streak = 0
    while cursor >= earliest:
        if cursor in done:
            streak += 1
        elif _expected(cursor, weekdays):
            break
        cursor -= timedelta(days=1)
    return streak


def best_streak(days_done: Iterable[date], weekdays: set[int] | None = None) -> int:
    done = set(days_done)
    if not done:
        return 0
    best = run = 0
    cursor, last = min(done), max(done)
    while cursor <= last:
        if cursor in done:
            run += 1
            best = max(best, run)
        elif _expected(cursor, weekdays):
            run = 0
        cursor += timedelta(days=1)
    return best
