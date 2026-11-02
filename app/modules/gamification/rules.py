"""Regras de bônus e punições (funções puras) e seus valores padrão.

Tudo é configurável na tela /gamification/. Princípios:
- Bônus recompensam constância: primeira quest do dia, combo das Daily Quests, adiantar prazo,
  sequência longa de hábitos.
- Punições existem, mas são justas: só para quests recorrentes não feitas, tiram uma parte pequena
  do XP, **nunca fazem perder nível** e sempre geram uma Penalty Quest que devolve o XP se for cumprida.
"""
import math
from dataclasses import asdict, dataclass, field, fields

PENALTY_PREFIX = "[PENALTY]"

# Motivos de falha: (rótulo, o que o System sugere). A escolha é sua, depois que a falha acontece.
FAILURE_REASONS: dict[str, tuple[str, str]] = {
    "procrastination": ("Procrastinação", "Divida a missão em uma parte de 15 minutos e comece por ela amanhã cedo."),
    "planning": ("Falta de planejamento", "Reveja o prazo e a recorrência: talvez o dia ou o horário não caibam na rotina."),
    "unexpected": ("Imprevisto", "Acontece. A punição foi desfeita; siga na próxima ocorrência."),
    "real_limit": ("Limitação real", "Saúde, cansaço ou falta de recurso contam. A punição foi desfeita; ajuste a meta ao seu momento."),
}


@dataclass
class Rules:
    bonuses_enabled: bool = True
    first_quest_bonus_xp: int = 10
    daily_combo_percent: int = 20      # % do XP das Daily Quests do dia, ao concluir todas
    daily_combo_min_xp: int = 20
    early_bonus_percent: int = 10      # % do XP ao concluir antes do dia do prazo
    # (dias de sequência, % extra de XP no check do hábito)
    streak_tiers: list[tuple[int, int]] = field(default_factory=lambda: [(7, 25), (30, 50), (100, 100)])

    penalties_enabled: bool = True
    penalty_xp_percent: int = 10       # % do XP da quest recorrente não feita
    penalty_quest_enabled: bool = True  # cria Penalty Quest para recuperar o XP
    # Motivos que devolvem o XP da punição e cancelam a Penalty Quest ao serem escolhidos.
    refund_reasons: list[str] = field(default_factory=lambda: ["unexpected", "real_limit"])

    @classmethod
    def from_dict(cls, data: dict | None) -> "Rules":
        """Junta o que foi salvo com os padrões (campos novos ganham o valor padrão)."""
        rules = cls()
        for f in fields(cls):
            if data and f.name in data:
                value = data[f.name]
                if f.name == "streak_tiers":
                    value = [(int(d), int(p)) for d, p in value]
                setattr(rules, f.name, value)
        return rules

    def to_dict(self) -> dict:
        return asdict(self)


def percent_of(amount: int, percent: int) -> int:
    """Arredonda para cima, para que 10% de 15 XP ainda dê 2, não 1."""
    return math.ceil(amount * percent / 100) if amount > 0 and percent > 0 else 0


def streak_bonus_percent(streak: int, tiers: list[tuple[int, int]]) -> int:
    reached = [percent for days, percent in tiers if streak >= days]
    return max(reached) if reached else 0


def penalty_amount(quest_xp: int, percent: int, xp_into_level: int) -> int:
    """XP perdido por uma quest recorrente não feita. Limitado ao XP do nível atual: nunca cai de nível."""
    return min(percent_of(quest_xp, percent), max(0, xp_into_level))


def is_penalty_quest(title: str) -> bool:
    return title.startswith(PENALTY_PREFIX)
