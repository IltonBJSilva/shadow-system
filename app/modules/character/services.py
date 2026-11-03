"""Personagem: atributos de combate, inventário e equipamentos.

Atributos de combate (Ataque, Defesa, Inteligência, Disciplina, Vitalidade, Sabedoria) não são
decorativos: o valor base vem de dados reais (tempo dedicado, missões, hábitos, treinos, níveis e
conquistas, ver `base_stats`), e equipamentos e sombras somam bônus por cima. Tudo calculado aqui,
no servidor. Os equipamentos são conquistados sozinhos quando a métrica do item é atingida.
"""
from dataclasses import dataclass
from typing import Callable

from sqlalchemy import select

from app.core import events
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.habits import services as habits
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.training import services as training

from . import catalog
from .models import PlayerItem

STUDY = ("studies", "college")
CRAFT = ("projects", "career")
# Uma especialização de item cobre também as vizinhas (ex.: Estudos vale para Faculdade).
SPECIALTY_GROUPS = {"studies": STUDY, "projects": CRAFT, "body": ("body",), "discipline": ("discipline", "organization")}
# Ranks padrão (código -> nível mínimo), usados se o jogador apagou ou renomeou um rank do catálogo.
DEFAULT_RANK_LEVELS = {"E": 1, "D": 10, "C": 20, "B": 35, "A": 50, "S": 70, "SS": 90}

# Outros módulos (sombras) somam bônus de atributo: provider() -> [(rótulo, {stat: pontos})].
_STAT_PROVIDERS: list[Callable[[], list[tuple[str, dict[str, int]]]]] = []


def register_stat_provider(provider: Callable[[], list[tuple[str, dict[str, int]]]]) -> None:
    if provider not in _STAT_PROVIDERS:
        _STAT_PROVIDERS.append(provider)


# ---------- Métricas reais ----------

def metrics() -> dict[str, int]:
    minutes = quests.credited_minutes_by_specialty()
    status = hunter.get_status()
    return {
        "missions": quests.completed_count(),
        "recurring": quests.recurring_completed_count(),
        "checkins": habits.checkins_count(),
        "habit_streak": habits.best_streak_ever(),
        "evolution_streak": hunter.best_evolution_streak(),
        "study_hours": sum(minutes.get(s, 0) for s in STUDY) // 60,
        "craft_hours": sum(minutes.get(s, 0) for s in CRAFT) // 60,
        "body_hours": minutes.get("body", 0) // 60,
        "total_hours": sum(minutes.values()) // 60,
        "workouts": training.sessions_count(),
        "level": status.progress.level,
        "achievements": sum(1 for t in hunter.list_titles() if t.unlocked),
    }


def base_stats(m: dict[str, int]) -> dict[str, int]:
    """Regra de cada atributo de combate (pura, fácil de testar e de ajustar)."""
    return {
        "attack": m["total_hours"] + m["missions"] // 10,            # 1 por hora dedicada + 1 a cada 10 missões
        "defense": m["checkins"] // 5 + m["habit_streak"] // 7,      # 1 a cada 5 hábitos + 1 por semana de sequência
        "intelligence": m["study_hours"] + m["craft_hours"] // 2,    # 1 por hora de estudo + 1 a cada 2 h de projeto/carreira
        "discipline": m["recurring"] // 5 + m["evolution_streak"] // 7,  # recorrentes cumpridas + semanas seguidas
        "vitality": m["body_hours"] + m["workouts"] // 3,            # 1 por hora de Corpo + 1 a cada 3 treinos
        "wisdom": (m["level"] - 1) + m["achievements"],              # níveis alcançados + conquistas
    }


@dataclass(frozen=True)
class StatLine:
    key: str
    name: str
    meaning: str
    base: int
    bonus: int

    @property
    def total(self) -> int:
        return self.base + self.bonus


@dataclass(frozen=True)
class OwnedItem:
    item: catalog.Item
    equipped: bool
    can_equip: bool
    acquired_at: object
    source: str


@dataclass
class Sheet:
    stats: list[StatLine]
    bonus_sources: list[tuple[str, dict[str, int]]]
    equipped: dict[str, OwnedItem]          # slot -> item
    owned: list[OwnedItem]
    locked: list[tuple[catalog.Item, list[tuple[str, int, int]]]]  # item, [(métrica, atual, meta)]
    metrics: dict[str, int]
    rank_code: str


def sheet() -> Sheet:
    """Ficha completa do personagem (sincroniza o inventário antes)."""
    sync_inventory()
    m = metrics()
    rank = _rank_code()
    owned = _owned()
    bonus_sources = [(f"{o.item.icon} {o.item.name}", o.item.stats) for o in owned if o.equipped]
    for provider in _STAT_PROVIDERS:
        bonus_sources.extend(provider())
    bonus = {key: 0 for key in catalog.STATS}
    for _, values in bonus_sources:
        for key, points in values.items():
            bonus[key] = bonus.get(key, 0) + points
    base = base_stats(m)
    owned_keys = {o.item.key for o in owned}
    locked = [(item, [(metric, m.get(metric, 0), goal) for metric, goal in item.requirements])
              for item in catalog.EQUIPMENT.values() if item.key not in owned_keys]
    return Sheet(
        stats=[StatLine(k, name, meaning, base[k], bonus.get(k, 0)) for k, (name, meaning) in catalog.STATS.items()],
        bonus_sources=bonus_sources,
        equipped={o.item.slot: o for o in owned if o.equipped},
        owned=owned,
        locked=locked,
        metrics=m,
        rank_code=rank,
    )


def total_stats() -> dict[str, int]:
    return {line.key: line.total for line in sheet().stats}


# ---------- Inventário ----------

def sync_inventory() -> list[str]:
    """Entrega os itens cujas metas já foram atingidas. Devolve os nomes novos. Idempotente."""
    m = metrics()
    owned = set(db.session.scalars(select(PlayerItem.item_key)))
    new = []
    for item in catalog.EQUIPMENT.values():
        if item.key in owned:
            continue
        if all(m.get(metric, 0) >= goal for metric, goal in item.requirements):
            metric, goal = item.unlock
            db.session.add(PlayerItem(item_key=item.key, source=f"{goal} {catalog.METRIC_LABELS.get(metric, metric)}"))
            new.append(item)
    if new:
        db.session.flush()
        for item in new:
            events.publish("character.item_acquired", item=item)
    return [item.name for item in new]


def equip(item_key: str) -> catalog.Item:
    row = _row(item_key)
    item = catalog.EQUIPMENT[item_key]
    if not _rank_allows(item.min_rank):
        raise DomainError(f"{item.name} exige Rank {item.min_rank}. Continue evoluindo.")
    for other in db.session.scalars(select(PlayerItem).where(PlayerItem.equipped.is_(True))):
        if catalog.EQUIPMENT.get(other.item_key) and catalog.EQUIPMENT[other.item_key].slot == item.slot:
            other.equipped = False  # um item por slot
    row.equipped = True
    db.session.commit()
    return item


def unequip(item_key: str) -> None:
    _row(item_key).equipped = False
    db.session.commit()


def equipped_items() -> list[catalog.Item]:
    keys = db.session.scalars(select(PlayerItem.item_key).where(PlayerItem.equipped.is_(True)))
    return [catalog.EQUIPMENT[k] for k in keys if k in catalog.EQUIPMENT]


def xp_bonus_lines(context: hunter.BonusContext) -> list[tuple[str, int]]:
    """Bônus de XP dos itens equipados na especialização da missão (cada item conta uma vez)."""
    lines = []
    for item in equipped_items():
        if item.xp_bonus and item.specialty and context.specialty in SPECIALTY_GROUPS.get(item.specialty, (item.specialty,)):
            lines.append((f"Equipamento: {item.name}", item.xp_bonus))
    return lines


def _owned() -> list[OwnedItem]:
    rows = db.session.scalars(select(PlayerItem).order_by(PlayerItem.acquired_at))
    result = []
    for row in rows:
        item = catalog.EQUIPMENT.get(row.item_key)
        if item:
            result.append(OwnedItem(item, row.equipped, _rank_allows(item.min_rank), row.acquired_at, row.source))
    return result


def _row(item_key: str) -> PlayerItem:
    row = db.session.scalar(select(PlayerItem).where(PlayerItem.item_key == item_key))
    if row is None or item_key not in catalog.EQUIPMENT:
        raise NotFoundError("Você ainda não tem esse item.")
    return row


def _rank_code() -> str:
    status = hunter.get_status()
    return status.rank.code if status.rank else "E"


def rank_level(code: str) -> int:
    ranks = {r.code: r.min_level for r in hunter.list_ranks()}
    return ranks.get(code, DEFAULT_RANK_LEVELS.get(code, 999))


def _rank_allows(code: str) -> bool:
    return hunter.get_status().progress.level >= rank_level(code)


def db_commit() -> None:
    db.session.commit()
