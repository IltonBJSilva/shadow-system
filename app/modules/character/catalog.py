"""Catálogo de equipamentos (em código: para adicionar um item, inclua-o em EQUIPMENT).

Cada item tem tipo (slot), raridade, rank mínimo para equipar, bônus de atributos de combate, uma
especialização (para o bônus de XP, opcional) e a condição que o desbloqueia: uma métrica real do
jogador chegando a um valor (ver stats.metrics). Nomes e itens são originais.
"""
from dataclasses import dataclass, field

SLOTS: dict[str, str] = {
    "weapon": "Arma", "armor": "Armadura", "helmet": "Capacete", "gloves": "Luvas",
    "boots": "Botas", "accessory": "Acessório", "ring": "Anel", "amulet": "Amuleto",
}
RARITIES: dict[str, tuple[str, str]] = {  # chave -> (rótulo, cor)
    "common": ("Comum", "#9ca3af"), "uncommon": ("Incomum", "#34d399"), "rare": ("Raro", "#38bdf8"),
    "epic": ("Épico", "#a855f7"), "legendary": ("Lendário", "#f59e0b"), "mythic": ("Mítico", "#ef4444"),
}
STATS: dict[str, tuple[str, str]] = {  # chave -> (nome, o que representa)
    "attack": ("Ataque", "Produtividade e execução: tempo dedicado e missões concluídas."),
    "defense": ("Defesa", "Consistência e resistência: hábitos mantidos e sequências."),
    "intelligence": ("Inteligência", "Aprendizado: tempo em Estudos, Faculdade, Carreira e Projetos."),
    "discipline": ("Disciplina", "Regularidade: missões recorrentes cumpridas e dias seguidos evoluindo."),
    "vitality": ("Vitalidade", "Corpo e saúde: tempo em missões de Corpo e treinos feitos."),
    "wisdom": ("Sabedoria", "Experiência acumulada: níveis alcançados e conquistas desbloqueadas."),
}
METRIC_LABELS: dict[str, str] = {
    "missions": "missões concluídas",
    "recurring": "missões recorrentes concluídas",
    "checkins": "dias de hábito marcados",
    "evolution_streak": "dias seguidos evoluindo (melhor sequência)",
    "study_hours": "horas em Estudos/Faculdade",
    "craft_hours": "horas em Projetos/Carreira",
    "body_hours": "horas em Corpo",
    "workouts": "treinos concluídos",
    "level": "nível",
    "achievements": "conquistas desbloqueadas",
}


@dataclass(frozen=True)
class Item:
    key: str
    name: str
    slot: str
    rarity: str
    min_rank: str
    description: str
    stats: dict[str, int]
    unlock: tuple[str, int]  # (métrica, valor)
    icon: str
    specialty: str | None = None   # bônus de XP nas missões desta especialização
    xp_bonus: int = 0
    extra_unlock: tuple[tuple[str, int], ...] = field(default=())

    @property
    def rarity_label(self) -> str:
        return RARITIES[self.rarity][0]

    @property
    def rarity_color(self) -> str:
        return RARITIES[self.rarity][1]

    @property
    def slot_label(self) -> str:
        return SLOTS[self.slot]

    @property
    def requirements(self) -> tuple[tuple[str, int], ...]:
        return (self.unlock,) + self.extra_unlock


ALL = ("attack", "defense", "intelligence", "discipline", "vitality", "wisdom")

EQUIPMENT: dict[str, Item] = {i.key: i for i in [
    Item("novice_dagger", "Adaga do Despertar", "weapon", "common", "E", "A primeira lâmina de quem decidiu começar.",
         {"attack": 1}, ("missions", 1), "🗡️"),
    Item("running_boots", "Botas do Corredor", "boots", "common", "E", "Leves, para quem não deixa o corpo parado.",
         {"vitality": 2}, ("body_hours", 3), "👟", specialty="body", xp_bonus=1),
    Item("scholar_hood", "Capuz do Estudioso", "helmet", "uncommon", "E", "Silencia distrações durante o estudo.",
         {"intelligence": 2}, ("study_hours", 5), "🎓"),
    Item("calm_amulet", "Amuleto da Calma", "amulet", "uncommon", "E", "Lembra que cada conquista foi uma escolha.",
         {"wisdom": 2}, ("achievements", 3), "📿"),
    Item("discipline_sword", "Espada da Disciplina", "weapon", "rare", "D", "Forjada em dezenas de missões cumpridas.",
         {"attack": 5}, ("missions", 25), "⚔️", specialty="discipline", xp_bonus=2),
    Item("artisan_gloves", "Luvas do Artesão", "gloves", "uncommon", "D", "Para quem constrói com as próprias mãos.",
         {"attack": 3}, ("craft_hours", 10), "🧤", specialty="projects", xp_bonus=2),
    Item("perseverance_boots", "Botas da Perseverança", "boots", "rare", "D", "Cada passo é um dia que não foi pulado.",
         {"discipline": 4}, ("evolution_streak", 14), "🥾"),
    Item("focus_ring", "Anel do Foco", "ring", "rare", "D", "Um ponto fixo no meio do caos.",
         {"intelligence": 3, "discipline": 2}, ("missions", 50), "💍"),
    Item("guardian_armor", "Armadura do Guardião", "armor", "rare", "C", "Resistência que vem da repetição diária.",
         {"defense": 8}, ("checkins", 30), "🛡️"),
    Item("iron_gauntlets", "Manoplas de Ferro", "gloves", "rare", "C", "Pesadas como as séries que você completou.",
         {"vitality": 4, "attack": 1}, ("body_hours", 20), "🥊", specialty="body", xp_bonus=2),
    Item("knowledge_grimoire", "Grimório do Conhecimento", "accessory", "epic", "C", "Cada página lida fica gravada aqui.",
         {"intelligence": 6}, ("study_hours", 30), "📘", specialty="studies", xp_bonus=3),
    Item("hunter_helm", "Elmo do Caçador", "helmet", "epic", "B", "Usado por quem cumpre a rotina sem falhar.",
         {"defense": 5, "discipline": 3}, ("recurring", 100), "⛑️"),
    Item("evolution_ring", "Anel da Evolução", "ring", "legendary", "B", "Prova de que você não é mais quem começou.",
         {stat: 3 for stat in ALL}, ("level", 40), "💠"),
    Item("monarch_amulet", "Amuleto do Monarca", "amulet", "mythic", "S", "Só responde a quem chegou ao topo.",
         {stat: 5 for stat in ALL}, ("level", 70), "👑", extra_unlock=(("missions", 300),)),
]}
