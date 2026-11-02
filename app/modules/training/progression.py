"""Sugestão de progressão depois de uma semana de treino completa (funções puras).

Regras conservadoras, iguais para todo exercício:
- com carga: + `increment_kg` (padrão 2,5 kg);
- sem carga, repetições fixas ("12"): +1 repetição, até 30;
- faixa de repetições ("8-12"): +1 nas duas pontas, até 30;
- tempo ("45s", "20min"): +5 s ou +1 min;
- "max", "falha" e distâncias ficam como estão.
Nada é aplicado sozinho: a tela mostra a sugestão e você aplica ou ignora.
"""
import re
from dataclasses import dataclass

MAX_REPS = 30


@dataclass(frozen=True)
class Suggestion:
    exercise_id: int
    name: str
    before: str
    after: str
    load_kg: float | None
    reps: str


def next_values(reps: str, load_kg: float | None, increment_kg: float) -> tuple[str, float | None] | None:
    """(reps, carga) sugeridos, ou None se não há o que aumentar."""
    if load_kg is not None and increment_kg > 0:
        return reps, round(load_kg + increment_kg, 2)
    value = (reps or "").strip().lower()
    if re.fullmatch(r"\d+", value):
        n = int(value)
        return (str(n + 1), load_kg) if n < MAX_REPS else None
    match = re.fullmatch(r"(\d+)-(\d+)", value)
    if match:
        low, high = int(match.group(1)), int(match.group(2))
        if high >= MAX_REPS:
            return None
        return f"{low + 1}-{high + 1}", load_kg
    match = re.fullmatch(r"(\d+)(s|seg)", value)
    if match:
        return f"{int(match.group(1)) + 5}s", load_kg
    match = re.fullmatch(r"(\d+)min", value)
    if match:
        return f"{int(match.group(1)) + 1}min", load_kg
    return None


def describe(sets: int, reps: str, load_kg: float | None) -> str:
    text = f"{sets}x{reps}" if reps else f"{sets} série(s)"
    if load_kg is not None:
        text += f" · {load_kg:g} kg".replace(".", ",")
    return text
