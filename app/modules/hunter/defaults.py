"""Valores iniciais criados na primeira execução. Depois disso, tudo é editável pela interface."""

DEFAULT_HUNTER_NAME = "Hunter"
DEFAULT_HUNTER_TITLE = "Recém-desperto"

# (code, name, min_level, color)
DEFAULT_RANKS: list[tuple[str, str, int, str]] = [
    ("E", "E-Rank Hunter", 1, "#9ca3af"),
    ("D", "D-Rank Hunter", 10, "#34d399"),
    ("C", "C-Rank Hunter", 20, "#38bdf8"),
    ("B", "B-Rank Hunter", 35, "#818cf8"),
    ("A", "A-Rank Hunter", 50, "#a855f7"),
    ("S", "S-Rank Hunter", 70, "#f59e0b"),
    ("SS", "SS-Rank Hunter", 90, "#ef4444"),
    ("NL", "National Level", 120, "#f472b6"),
    ("MON", "Shadow Monarch", 150, "#c084fc"),
]

# (key, name, description)
DEFAULT_ATTRIBUTES: list[tuple[str, str, str]] = [
    ("strength", "Strength", "Treinos de força, academia, esforço físico."),
    ("vitality", "Vitality", "Cardio, sono, alimentação, cuidado com a saúde."),
    ("intelligence", "Intelligence", "Estudos, faculdade, leitura técnica, aprendizado."),
    ("discipline", "Discipline", "Constância: hábitos mantidos e compromissos cumpridos."),
    ("focus", "Focus", "Trabalho profundo, sessões sem distração, projetos concluídos."),
    ("creativity", "Creativity", "Música, escrita, game dev, criação de conteúdo."),
    ("financial_intelligence", "Financial Intelligence", "Organização financeira, orçamento, investimentos."),
    ("spirituality", "Spirituality", "Atividades espirituais, reflexão, gratidão."),
    ("wisdom", "Wisdom", "Sabedoria: aplicar o que aprendeu, revisar, refletir, ensinar."),
    ("charisma", "Charisma", "Carisma: comunicação, música e palco, conteúdo, networking, relações."),
]

# Conquistas padrão: (key, nome do título, descrição, regra, limite, ícone, XP de recompensa).
# Cada conquista desbloqueia um título com o mesmo nome. Nomes originais, não do anime.
# Regras "quests_completed", "main_quests_completed", "habit_best_streak" e "workouts_completed" vêm de
# outros módulos (registradas com hunter.services.register_metric).
DEFAULT_TITLES: list[tuple[str, str, str, str, int, str, int]] = [
    ("start", "Recém-desperto", "O começo de tudo.", "level", 1, "🌑", 0),
    ("first_quest", "Primeiro Passo", "Concluiu a primeira missão.", "quests_completed", 1, "👣", 10),
    ("level_2", "Despertar", "Subiu de nível pela primeira vez.", "level", 2, "⬆️", 15),
    ("week_7", "Semana Consistente", "7 dias seguidos evoluindo (com XP).", "evolution_days", 7, "📆", 50),
    ("quests_10", "Cumpridor de Missões", "10 missões concluídas.", "quests_completed", 10, "⚔️", 25),
    ("main_1", "Projeto Finalizado", "Concluiu a primeira Main Quest.", "main_quests_completed", 1, "🏁", 50),
    ("streak_7", "Chama Constante", "7 dias seguidos num hábito.", "habit_best_streak", 7, "🔥", 30),
    ("workout_1", "Primeiro Treino", "Concluiu o primeiro treino.", "workouts_completed", 1, "🏋️", 15),
    ("level_10", "Ascendente", "Chegou ao nível 10 (Rank D).", "level", 10, "🛡️", 100),
    ("days_30", "30 Dias de Evolução", "30 dias seguidos com XP.", "evolution_days", 30, "🌗", 150),
    ("streak_30", "Inquebrável", "30 dias seguidos num hábito.", "habit_best_streak", 30, "💎", 100),
    ("workout_20", "Corpo em Forja", "20 treinos concluídos.", "workouts_completed", 20, "⚒️", 60),
    ("quests_50", "Veterano das Missões", "50 missões concluídas.", "quests_completed", 50, "🎖️", 80),
    ("quests_100", "Centurião", "100 missões concluídas.", "quests_completed", 100, "💯", 150),
    ("level_25", "Caçador Experiente", "Chegou ao nível 25.", "level", 25, "🗡️", 200),
    ("quests_200", "Incansável", "200 missões concluídas.", "quests_completed", 200, "♾️", 250),
    ("workout_100", "Corpo de Aço", "100 treinos concluídos.", "workouts_completed", 100, "🦾", 250),
    ("streak_100", "Disciplina de Ferro", "100 dias seguidos num hábito.", "habit_best_streak", 100, "🧱", 300),
    ("xp_10000", "Colecionador de XP", "10.000 XP no total.", "total_xp", 10000, "💠", 0),
    ("level_50", "Elite", "Chegou ao nível 50.", "level", 50, "👑", 500),
    ("level_100", "Lenda Viva", "Chegou ao nível 100.", "level", 100, "🌌", 1000),
]

# Como cada regra aparece na tela ("7 / 30 dias seguidos").
RULE_LABELS: dict[str, str] = {
    "level": "nível",
    "total_xp": "XP no total",
    "quests_completed": "quests concluídas",
    "habit_best_streak": "dias seguidos (melhor sequência)",
    "workouts_completed": "treinos concluídos",
    "main_quests_completed": "Main Quests concluídas",
    "evolution_days": "dias seguidos evoluindo (com XP)",
    "custom": "criado por você",
}
