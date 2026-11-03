"""Catálogo das sombras. Para adicionar uma, inclua um Shadow(...) em SHADOWS.

Desafios usam as métricas reais do Personagem (character.services.metrics): horas por área, missões,
recorrentes cumpridas, sequências, treinos e nível. Valores pensados para uma progressão equilibrada:
as primeiras sombras chegam em algumas semanas de constância; Bellion é para o topo.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Shadow:
    key: str
    name: str
    title: str
    rarity: str               # mesma escala dos equipamentos (character/catalog.RARITIES)
    min_rank: str
    specialties: tuple[str, ...]  # especializações das missões que recebem o bônus de XP
    specialty_label: str
    xp_bonus: int
    stats: dict[str, int]
    challenges: tuple[tuple[str, int], ...]  # (métrica, meta)
    lore: str
    icon: str


SHADOWS: dict[str, Shadow] = {s.key: s for s in [
    Shadow("igris", "Igris", "Cavaleiro da Disciplina", "rare", "D", ("discipline", "organization"), "Disciplina",
           3, {"discipline": 3, "defense": 1},
           (("recurring", 20), ("evolution_streak", 7)),
           "Honra e constância: não abandona a rotina, nem quando ninguém está olhando.", "⚔️"),
    Shadow("iron", "Iron", "Guardião de Ferro", "rare", "D", ("body",), "Corpo",
           5, {"vitality": 3, "defense": 1},
           (("body_hours", 10), ("workouts", 8)),
           "Resistência física e mental, forjada em cada treino que você não pulou.", "🛡️"),
    Shadow("tank", "Tank", "Força Inabalável", "epic", "C", ("body",), "Corpo e resistência",
           4, {"defense": 4, "vitality": 2},
           (("body_hours", 30), ("habit_streak", 14)),
           "Força e perseverança: aguenta o peso que faria qualquer um desistir.", "🐻"),
    Shadow("tusk", "Tusk", "Sábio das Runas", "epic", "C", ("studies", "college"), "Estudos",
           5, {"intelligence": 4, "wisdom": 1},
           (("study_hours", 25), ("missions", 60)),
           "Inteligência e conhecimento: cada hora de estudo vira poder.", "📜"),
    Shadow("beru", "Beru", "Rei das Formigas", "legendary", "B", ("discipline", "projects", "career"), "Disciplina e produtividade",
           6, {"attack": 3, "discipline": 3},
           (("evolution_streak", 30), ("recurring", 100), ("total_hours", 120)),
           "Evolução rápida e dedicação extrema: produtividade sem descanso para o progresso.", "🐜"),
    Shadow("bellion", "Bellion", "Marechal das Sombras", "mythic", "S", ("mastery",), "Maestria",
           10, {s: 5 for s in ("attack", "defense", "intelligence", "discipline", "vitality", "wisdom")},
           (("level", 70), ("missions", 400), ("total_hours", 300)),
           "Maestria, liderança e excelência: o mais forte dos que te seguem.", "👑"),
]}

METRIC_LABELS: dict[str, str] = {
    "recurring": "missões recorrentes cumpridas",
    "evolution_streak": "dias seguidos evoluindo (melhor sequência)",
    "body_hours": "horas em missões de Corpo",
    "workouts": "treinos concluídos",
    "habit_streak": "dias seguidos no melhor hábito",
    "study_hours": "horas em Estudos/Faculdade",
    "missions": "missões concluídas",
    "total_hours": "horas dedicadas no total",
    "level": "nível",
}
# Várias sombras na mesma especialização: a mais forte vale inteira, cada outra vale metade.
STACK_FACTOR = 0.5
