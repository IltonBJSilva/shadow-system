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

RECURRENCES: dict[str, str] = {"none": "Não repete", "daily": "Diária", "weekly": "Semanal", "monthly": "Mensal"}
