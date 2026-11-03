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


# Importância (prioridade da quest) ajusta o XP padrão em até ±20/40%: o esforço (dificuldade) continua
# sendo o que mais pesa, para que uma tarefa trivial marcada como "crítica" não renda XP absurdo.
PRIORITY_MULTIPLIER: dict[str, float] = {"low": 0.8, "medium": 1.0, "high": 1.2, "critical": 1.4}


def xp_for_difficulty(difficulty: int, priority: str = "medium") -> int:
    """XP padrão de uma quest: dificuldade (esforço) x importância, arredondado para múltiplo de 5."""
    base = DIFFICULTY_XP.get(difficulty, DIFFICULTY_XP[3])
    value = base * PRIORITY_MULTIPLIER.get(priority, 1.0)
    return max(5, int(round(value / 5)) * 5)


def attribute_points_for_difficulty(difficulty: int) -> int:
    """Pontos de atributo ganhos por atividade: igual à dificuldade (1 a 5)."""
    return max(1, min(5, difficulty))


def rank_for_level(level: int, ranks: Sequence[RankLike]) -> RankLike | None:
    """Maior rank cujo nível mínimo já foi alcançado."""
    reached = [rank for rank in ranks if rank.min_level <= level]
    return max(reached, key=lambda rank: rank.min_level) if reached else None


# ---------- XP por tempo (regra atual das missões) ----------
# "O tempo é o que temos de mais valioso." O XP base de uma missão vem do tempo estimado (1 XP por
# minuto), com ajustes moderados de dificuldade e da categoria. Bônus (sombras, equipamentos, eventos)
# entram por cima, com limites. Tudo é calculado no servidor (quests.services.complete_quest).
XP_PER_MINUTE = 1.0
MIN_MINUTES = 5
MAX_MINUTES = 8 * 60  # uma missão maior que 8 h deve ser quebrada em partes
# Tempo sugerido quando a missão não informa (ex.: criada por outro módulo).
MINUTES_BY_DIFFICULTY: dict[int, int] = {1: 10, 2: 20, 3: 30, 4: 60, 5: 90}
DIFFICULTY_TIME_MULTIPLIER: dict[int, float] = {1: 0.8, 2: 0.9, 3: 1.0, 4: 1.15, 5: 1.3}
CATEGORY_MULTIPLIER_RANGE = (0.8, 1.2)
# Repetir a mesma missão no mesmo dia rende cada vez menos: 1ª e 2ª inteiras, 3ª metade, 4ª um quarto,
# da 5ª em diante nada (evita farm de XP com a mesma tarefa).
REPEAT_FACTORS: tuple[float, ...] = (1.0, 1.0, 0.5, 0.25)
# Minutos creditados por dia (soma do tempo das missões concluídas). Acima disso, XP base 0.
DAILY_MINUTES_CAP = 16 * 60
# Bônus por missão: no máximo 50% do XP base e nunca mais que 30 XP; por dia, no máximo 150 XP de bônus.
BONUS_CAP_RATIO = 0.5
BONUS_CAP_PER_MISSION = 30
BONUS_CAP_PER_DAY = 150


@dataclass(frozen=True)
class XpLine:
    label: str
    amount: int
    kind: str = "base"  # base | bonus | limit


@dataclass(frozen=True)
class XpQuote:
    base: int
    bonus: int
    lines: tuple[XpLine, ...]

    @property
    def total(self) -> int:
        return self.base + self.bonus


def clamp_minutes(minutes: int | None) -> int:
    return max(MIN_MINUTES, min(MAX_MINUTES, int(minutes or 0)))


def default_minutes(difficulty: int) -> int:
    return MINUTES_BY_DIFFICULTY.get(difficulty, MINUTES_BY_DIFFICULTY[3])


def clamp_category_multiplier(value: float | None) -> float:
    low, high = CATEGORY_MULTIPLIER_RANGE
    return round(max(low, min(high, float(value if value is not None else 1.0))), 2)


def time_xp(minutes: int, difficulty: int = 3, category_multiplier: float = 1.0) -> XpQuote:
    """XP base previsto de uma missão (sem repetição nem bônus): o que aparece antes de concluir."""
    minutes = clamp_minutes(minutes)
    raw = minutes * XP_PER_MINUTE
    lines = [XpLine(f"Tempo estimado: {minutes} min", int(round(raw)))]
    factor = DIFFICULTY_TIME_MULTIPLIER.get(difficulty, 1.0)
    value = raw * factor
    if factor != 1.0:
        lines.append(XpLine(f"Dificuldade {DIFFICULTY_LABELS.get(difficulty, difficulty)} ×{factor:g}",
                            int(round(value - raw))))
    category_multiplier = clamp_category_multiplier(category_multiplier)
    if category_multiplier != 1.0:
        before = value
        value *= category_multiplier
        lines.append(XpLine(f"Categoria ×{category_multiplier:g}", int(round(value - before))))
    base = max(1, int(round(value)))
    return XpQuote(base, 0, _fix_rounding(tuple(lines), base))


def repeat_factor(previous_today: int) -> float:
    """Fator para a (previous_today + 1)-ésima conclusão da mesma missão no dia."""
    return REPEAT_FACTORS[previous_today] if previous_today < len(REPEAT_FACTORS) else 0.0


def cap_bonus(base: int, requested: int, bonus_today: int) -> int:
    """Bônus que pode ser dado nesta missão, respeitando os limites por missão e por dia."""
    per_mission = min(BONUS_CAP_PER_MISSION, int(base * BONUS_CAP_RATIO))
    left_today = max(0, BONUS_CAP_PER_DAY - bonus_today)
    return max(0, min(requested, per_mission, left_today))


def _fix_rounding(lines: tuple[XpLine, ...], total: int) -> tuple[XpLine, ...]:
    """Ajusta a primeira linha para que a soma das linhas bata com o total arredondado."""
    diff = total - sum(line.amount for line in lines)
    if not diff or not lines:
        return lines
    first = lines[0]
    return (XpLine(first.label, first.amount + diff, first.kind),) + lines[1:]
