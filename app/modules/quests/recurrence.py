"""Cálculo da próxima data de uma quest recorrente (funções puras)."""
import calendar
from datetime import date, timedelta


def next_due(current: date, recurrence: str) -> date:
    """Próxima ocorrência depois de `current`."""
    if recurrence == "daily":
        return current + timedelta(days=1)
    if recurrence == "weekly":
        return current + timedelta(weeks=1)
    if recurrence == "monthly":
        return _add_month(current)
    raise ValueError(f"Recorrência desconhecida: {recurrence}")


def next_due_on_or_after(current: date, recurrence: str, today: date) -> date:
    """Avança a partir de `current` até a primeira ocorrência em `today` ou depois.

    Usado quando ocorrências passaram sem serem feitas: a nova quest aparece para hoje (ou para a
    próxima data da série), sem acumular uma pilha de quests atrasadas.
    """
    due = next_due(current, recurrence)
    while due < today:
        due = next_due(due, recurrence)
    return due


def _add_month(day: date) -> date:
    # 31/01 + 1 mês = 28/02 (ou 29): usa o último dia do mês quando o dia não existe.
    year, month = (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))
