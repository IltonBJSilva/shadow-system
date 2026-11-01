"""Cálculo de sequências (streaks) a partir dos dias feitos. Funções puras."""
from datetime import date, timedelta
from typing import Iterable


def current_streak(days_done: Iterable[date], today: date) -> int:
    """Dias seguidos até hoje.

    Se hoje ainda não foi feito, conta até ontem: a sequência só "quebra" depois que o dia acaba.
    """
    done = set(days_done)
    cursor = today if today in done else today - timedelta(days=1)
    streak = 0
    while cursor in done:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def best_streak(days_done: Iterable[date]) -> int:
    ordered = sorted(set(days_done))
    best = run = 0
    previous: date | None = None
    for day in ordered:
        run = run + 1 if previous and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    return best
