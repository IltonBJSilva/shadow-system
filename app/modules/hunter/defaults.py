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
]
