"""Contabilização de tempo: une intervalos sobrepostos e limita cada dia a 24 h.

Funções puras (sem banco). As horas de atividade do ranking e o indicador de integridade usam isto, a
partir das ActivitySession gravadas pelo servidor na conclusão de cada missão.
"""
from datetime import date, datetime, time, timedelta
from typing import Iterable

Interval = tuple[datetime, datetime]


def merge(intervals: Iterable[Interval]) -> list[Interval]:
    """Une intervalos que se sobrepõem ou encostam. [(9h,10h),(9h30,11h)] -> [(9h,11h)]."""
    ordered = sorted((s, e) for s, e in intervals if e > s)
    merged: list[Interval] = []
    for start, end in ordered:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def clip(intervals: Iterable[Interval], start: datetime, end: datetime) -> list[Interval]:
    return [(max(s, start), min(e, end)) for s, e in intervals if e > start and s < end]


def minutes_on(day: date, intervals: Iterable[Interval]) -> int:
    """Minutos de atividade no dia, sem contar sobreposições duas vezes. Nunca passa de 24 h."""
    start = datetime.combine(day, time.min)
    total = sum((e - s).total_seconds() for s, e in merge(clip(intervals, start, start + timedelta(days=1))))
    return min(24 * 60, int(round(total / 60)))


def raw_minutes_on(day: date, intervals: Iterable[Interval]) -> int:
    """Soma simples (com sobreposições), para comparar com minutes_on e achar registros duplicados."""
    start = datetime.combine(day, time.min)
    return int(round(sum((e - s).total_seconds() for s, e in clip(intervals, start, start + timedelta(days=1))) / 60))
