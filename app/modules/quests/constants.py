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

# Especializações das categorias: sombras e equipamentos dão bônus por especialização (não pelo nome,
# que é livre). "mastery" = maestria: grandes projetos e metas de longo prazo.
SPECIALTIES: dict[str, str] = {
    "body": "Corpo",
    "discipline": "Disciplina",
    "studies": "Estudos",
    "college": "Faculdade",
    "career": "Carreira",
    "projects": "Projetos",
    "spirituality": "Espiritualidade",
    "organization": "Organização pessoal",
    "finance": "Finanças",
    "hobbies": "Hobbies",
    "social": "Social",
    "mastery": "Maestria",
    "other": "Outras",
}

# Categorias sugeridas: (nome, cor, chaves dos atributos, especialização). "Criar sugeridas" em
# Quests > Categorias adiciona só as que faltam (pelo nome), sem mexer nas suas.
SUGGESTED_CATEGORIES: list[tuple[str, str, list[str], str]] = [
    ("Corpo", "#f97316", ["strength", "vitality", "discipline"], "body"),
    ("Disciplina", "#94a3b8", ["discipline", "focus"], "discipline"),
    ("Estudos", "#22d3ee", ["intelligence", "wisdom", "focus"], "studies"),
    ("Faculdade", "#38bdf8", ["intelligence", "wisdom", "focus"], "college"),
    ("Carreira", "#3b82f6", ["intelligence", "discipline", "charisma"], "career"),
    ("Projetos", "#60a5fa", ["intelligence", "creativity", "discipline"], "projects"),
    ("Espiritualidade", "#c4b5fd", ["spirituality", "wisdom"], "spirituality"),
    ("Organização pessoal", "#a1a1aa", ["discipline", "focus"], "organization"),
    ("Finanças", "#facc15", ["financial_intelligence", "discipline"], "finance"),
    ("Hobbies", "#a78bfa", ["creativity", "focus"], "hobbies"),
    ("Social", "#f472b6", ["charisma", "wisdom"], "social"),
    ("Outras", "#64748b", ["discipline"], "other"),
]

# Nomes antigos -> especialização (categorias criadas antes das especializações existirem).
LEGACY_SPECIALTY_BY_NAME: dict[str, str] = {
    "treino": "body", "saúde e bem-estar": "body", "saude e bem-estar": "body", "corpo": "body",
    "estudos": "studies", "faculdade": "college", "carreira": "career", "finanças": "finance",
    "financas": "finance", "música e arte": "hobbies", "hobbies": "hobbies", "organização pessoal": "organization",
    "espiritualidade": "spirituality", "projetos pessoais": "projects", "projetos": "projects",
    "conteúdo": "social", "social": "social", "disciplina": "discipline",
}

RECURRENCES: dict[str, str] = {"none": "Não repete", "daily": "Diária", "weekly": "Semanal", "monthly": "Mensal"}
