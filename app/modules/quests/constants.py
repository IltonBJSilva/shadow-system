"""Valores fixos do Quest System (chave gravada no banco -> rótulo da tela)."""

QUEST_TYPES: dict[str, str] = {
    "daily": "Daily Quest",
    "weekly": "Weekly Quest",
    "monthly": "Monthly Quest",
    "main": "Main Quest",
    "side": "Side Quest",
    "habit": "Habit Quest",
    "emergency": "Emergency Quest",
    "custom": "Custom Quest",
}

PRIORITIES: dict[str, str] = {"low": "Baixa", "medium": "Média", "high": "Alta", "critical": "Crítica"}
PRIORITY_ORDER: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# "missed" = ocorrência recorrente que passou do prazo. Não tira XP: só fica registrada.
STATUSES: dict[str, str] = {
    "pending": "Pendente",
    "in_progress": "Em andamento",
    "completed": "Concluída",
    "missed": "Não realizada",
    "cancelled": "Cancelada",
}
ACTIVE_STATUSES = ("pending", "in_progress")

# Categorias sugeridas: (nome, cor, chaves dos atributos). "Criar sugeridas" em Quests > Categorias
# adiciona só as que faltam (pelo nome), sem mexer nas suas.
SUGGESTED_CATEGORIES: list[tuple[str, str, list[str]]] = [
    ("Faculdade", "#38bdf8", ["intelligence", "wisdom", "focus"]),
    ("Carreira", "#3b82f6", ["intelligence", "discipline", "charisma"]),
    ("Estudos", "#22d3ee", ["intelligence", "wisdom", "focus"]),
    ("Treino", "#f97316", ["strength", "vitality", "discipline"]),
    ("Saúde e bem-estar", "#34d399", ["vitality", "discipline"]),
    ("Finanças", "#facc15", ["financial_intelligence", "discipline"]),
    ("Música e arte", "#e879f9", ["creativity", "charisma"]),
    ("Hobbies", "#a78bfa", ["creativity", "focus"]),
    ("Organização pessoal", "#94a3b8", ["discipline", "focus"]),
    ("Espiritualidade", "#c4b5fd", ["spirituality", "wisdom"]),
    ("Projetos pessoais", "#60a5fa", ["intelligence", "creativity", "discipline"]),
    ("Conteúdo", "#f472b6", ["creativity", "charisma"]),
]

RECURRENCES: dict[str, str] = {"none": "Não repete", "daily": "Diária", "weekly": "Semanal", "monthly": "Mensal"}
