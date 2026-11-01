"""Regras de progressão: XP, níveis e ranks.

Funções puras (sem banco), fáceis de testar e de ajustar. Se quiser outra curva de evolução,
mude só este arquivo.

Curva de nível: para sair do nível N você precisa de 100 + 50 * (N - 1) XP.
    Nível 1 -> 2: 100 XP | 2 -> 3: 150 XP | 10 -> 11: 550 XP
A curva é linear de propósito: cresce, mas nunca fica impossível.
"""
from dataclasses import dataclass
from typing import Protocol, Sequence

XP_BASE = 100
XP_STEP = 50

# XP sugerido por dificuldade (1 = trivial ... 5 = extrema). Quests podem sobrescrever.
DIFFICULTY_XP: dict[int, int] = {1: 10, 2: 25, 3: 50, 4: 100, 5: 200}
DIFFICULTY_LABELS: dict[int, str] = {1: "Trivial", 2: "Fácil", 3: "Normal", 4: "Difícil", 5: "Extrema"}


@dataclass(frozen=True)
class LevelProgress:
    level: int
    total_xp: int
    xp_into_level: int
    xp_for_next: int

    @property
    def percent(self) -> float:
        return 100 * self.xp_into_level / self.xp_for_next


class RankLike(Protocol):
    min_level: int


def xp_to_next_level(level: int) -> int:
    """XP necessário para passar do nível `level` para o próximo."""
    if level < 1:
        raise ValueError("Nível mínimo é 1.")
    return XP_BASE + XP_STEP * (level - 1)


def total_xp_for_level(level: int) -> int:
    """XP acumulado necessário para *chegar* ao nível `level`."""
    steps = level - 1
    return XP_BASE * steps + XP_STEP * steps * (steps - 1) // 2


def level_progress(total_xp: int) -> LevelProgress:
    total_xp = max(0, total_xp)
    level = 1
    remaining = total_xp
    while remaining >= xp_to_next_level(level):
        remaining -= xp_to_next_level(level)
        level += 1
    return LevelProgress(level, total_xp, remaining, xp_to_next_level(level))


def xp_for_difficulty(difficulty: int) -> int:
    return DIFFICULTY_XP.get(difficulty, DIFFICULTY_XP[3])


def attribute_points_for_difficulty(difficulty: int) -> int:
    """Pontos de atributo ganhos por atividade: igual à dificuldade (1 a 5)."""
    return max(1, min(5, difficulty))


def rank_for_level(level: int, ranks: Sequence[RankLike]) -> RankLike | None:
    """Maior rank cujo nível mínimo já foi alcançado."""
    reached = [rank for rank in ranks if rank.min_level <= level]
    return max(reached, key=lambda rank: rank.min_level) if reached else None
