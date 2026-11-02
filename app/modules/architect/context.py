"""Retrato do jogador montado com os dados reais do sistema (nada inventado).

É a única entrada do Arquiteto: as regras (analysis.py) e a IA (ai.py) leem este mesmo retrato.
Só usa a API pública dos outros módulos.
"""
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

from app.core import time
from app.modules.gamification import services as gamification
from app.modules.gamification.rules import FAILURE_REASONS
from app.modules.habits import services as habits
from app.modules.hunter import services as hunter
from app.modules.quests import constants as quest_constants
from app.modules.quests import services as quests
from app.modules.training import services as training

from .models import ArchitectGoal


@dataclass
class Snapshot:
    today: date
    name: str
    level: int
    rank: str
    xp_into_level: int
    xp_for_next: int
    evolution_streak: int
    attributes: dict[str, int]                 # pontos atuais
    attributes_gained_4w: dict[str, int]       # pontos ganhos nas últimas 4 semanas
    attribute_categories: dict[str, list[str]]  # atributo -> categorias que o desenvolvem
    quest_stats: dict[str, int]
    active_quests: list[dict] = field(default_factory=list)
    category_performance: list[dict] = field(default_factory=list)
    failures_60d: dict[str, int] = field(default_factory=dict)
    habits: list[dict] = field(default_factory=list)
    training: list[dict] = field(default_factory=list)
    goals: list[dict] = field(default_factory=list)
    xp_week: int = 0
    xp_last_week: int = 0

    def as_prompt_data(self) -> dict:
        """Versão para a IA: datas viram texto, nada de nomes internos."""
        data = asdict(self)
        data["today"] = self.today.isoformat()
        return data


def build(today: date | None = None) -> Snapshot:
    today = today or time.today()
    status = hunter.get_status()
    _, trends = hunter.attribute_history(weeks=4, today=today)
    monday = today - timedelta(days=today.weekday())

    category_attrs: dict[str, list[str]] = {}
    names_by_id = {a.id: a.name for a in status.attributes}
    for category in quests.list_categories():
        for attribute_id in quests.category_attribute_ids(category.id):
            category_attrs.setdefault(names_by_id.get(attribute_id, "?"), []).append(category.name)

    active = []
    for q in quests.list_quests("active")[:40]:
        active.append({
            "id": q.id, "title": q.title, "type": quest_constants.QUEST_TYPES.get(q.quest_type, q.quest_type),
            "category": q.category.name if q.category else "", "priority": q.priority, "difficulty": q.difficulty,
            "due": q.due_date.isoformat() if q.due_date else None,
            "overdue": bool(q.due_date and q.due_date < today), "recurrence": q.recurrence, "xp": q.xp_reward,
        })

    labels = {key: label for key, (label, _) in FAILURE_REASONS.items()} | {"unknown": "Sem motivo registrado"}
    return Snapshot(
        today=today,
        name=status.name,
        level=status.progress.level,
        rank=status.rank.name if status.rank else "",
        xp_into_level=status.progress.xp_into_level,
        xp_for_next=status.progress.xp_for_next,
        evolution_streak=hunter.evolution_streak(today),
        attributes={a.name: a.points for a in status.attributes},
        attributes_gained_4w={t.name: t.gained for t in trends},
        attribute_categories=category_attrs,
        quest_stats=quests.stats(),
        active_quests=active,
        category_performance=[
            {"category": p.name, "completed": p.completed, "missed": p.missed, "avg_difficulty": p.avg_difficulty,
             "rate": round(p.rate, 2) if p.rate is not None else None}
            for p in quests.category_performance(30, today)
        ],
        failures_60d={labels.get(k, k): v for k, v in gamification.failure_stats(60).items()},
        habits=[{"name": h.name, "streak": h.current_streak, "best": h.best_streak, "done_today": h.done_today,
                 "expected_today": h.expected_today, "schedule": h.schedule} for h in habits.list_habits(today=today)],
        training=[{"plan": p.name, "done_this_week": training.week_progress(p, today)[0],
                   "per_week": training.week_progress(p, today)[1]}
                  for p in training.list_plans() if p.active],
        goals=[{"id": g.id, "title": g.title, "area": g.area, "why": g.why,
                "deadline": g.deadline.isoformat() if g.deadline else None}
               for g in _active_goals()],
        xp_week=hunter.xp_between(monday, today),
        xp_last_week=hunter.xp_between(monday - timedelta(days=7), today - timedelta(days=7)),
    )


def _active_goals() -> list[ArchitectGoal]:
    from sqlalchemy import select

    from app.extensions import db

    return list(db.session.scalars(select(ArchitectGoal).where(ArchitectGoal.status == "active")
                                   .order_by(ArchitectGoal.deadline.is_(None), ArchitectGoal.deadline)))
