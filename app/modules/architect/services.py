"""API pública do Arquiteto: relatório, sugestões de missão, metas e conversa.

O relatório por regras roda sempre. A IA (Claude) é opcional e usa o mesmo retrato de dados.
Nenhuma sugestão vira quest sem você aceitar.
"""
from datetime import timedelta

from sqlalchemy import select

from app.core import time
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.hunter import progression
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput

from . import ai, analysis, context
from .models import ArchitectGoal, ArchitectMessage, ArchitectSuggestion

REPEAT_AFTER_DAYS = 14  # uma regra não sugere de novo a mesma coisa antes disso
MAX_PENDING_RULE_SUGGESTIONS = 8


# ---------- relatório ----------

def report(today=None) -> tuple[context.Snapshot, analysis.Report]:
    snapshot = context.build(today)
    result = analysis.analyze(snapshot)
    _store_drafts(result.drafts)
    return snapshot, result


def pending_suggestions() -> list[ArchitectSuggestion]:
    return list(db.session.scalars(select(ArchitectSuggestion).where(ArchitectSuggestion.status == "pending")
                                   .order_by(ArchitectSuggestion.source.desc(), ArchitectSuggestion.created_at.desc())))


def accept_suggestion(suggestion_id: int) -> int:
    """Cria a quest da sugestão. Retorna o id da quest."""
    suggestion = _suggestion(suggestion_id)
    if suggestion.status != "pending":
        raise DomainError("Esta sugestão já foi respondida.")
    category_id = next((c.id for c in quests.list_categories() if c.name.lower() == suggestion.category.lower()), None)
    description = suggestion.description
    if suggestion.reason:
        description = f"{description}\n\nPor que o Arquiteto sugeriu: {suggestion.reason}".strip()
    quest = quests.create_quest(QuestInput(
        title=suggestion.title,
        description=description,
        quest_type="daily" if suggestion.recurrence == "daily" else ("weekly" if suggestion.recurrence == "weekly" else "side"),
        category_id=category_id,
        priority=suggestion.priority,
        difficulty=suggestion.difficulty,
        due_date=time.today() + timedelta(days=suggestion.due_in_days),
        recurrence=suggestion.recurrence,
        estimated_minutes=progression.default_minutes(suggestion.difficulty),
    ), note="Quest sugerida pelo Arquiteto")
    suggestion.status, suggestion.quest_id = "accepted", quest.id
    db.session.commit()
    return quest.id


def dismiss_suggestion(suggestion_id: int) -> None:
    suggestion = _suggestion(suggestion_id)
    suggestion.status = "dismissed"
    db.session.commit()


# ---------- metas ----------

def list_goals(include_closed: bool = False) -> list[ArchitectGoal]:
    query = select(ArchitectGoal).order_by(ArchitectGoal.status, ArchitectGoal.deadline.is_(None), ArchitectGoal.deadline)
    if not include_closed:
        query = query.where(ArchitectGoal.status == "active")
    return list(db.session.scalars(query))


def save_goal(title: str, area: str = "", why: str = "", deadline=None, goal_id: int | None = None) -> ArchitectGoal:
    if not title.strip():
        raise DomainError("Dê um nome à meta.")
    goal = _goal(goal_id) if goal_id else ArchitectGoal()
    goal.title, goal.area, goal.why, goal.deadline = title.strip()[:160], area.strip()[:80], why.strip(), deadline
    db.session.add(goal)
    db.session.commit()
    return goal


def set_goal_status(goal_id: int, status: str) -> None:
    if status not in ("active", "done", "dropped"):
        raise DomainError("Situação inválida.")
    _goal(goal_id).status = status
    db.session.commit()


# ---------- IA ----------

def conversation(limit: int = 40) -> list[ArchitectMessage]:
    rows = list(db.session.scalars(select(ArchitectMessage).order_by(ArchitectMessage.id.desc()).limit(limit)))
    return list(reversed(rows))


def ask(question: str, client_factory=None) -> str:
    question = question.strip()
    if not question:
        raise DomainError("Escreva uma pergunta.")
    history = [(m.role, m.content) for m in conversation(ai.HISTORY_MESSAGES)]
    answer = ai.chat(history, question[:4000], context.build().as_prompt_data(), client_factory=client_factory)
    db.session.add(ArchitectMessage(role="user", content=question[:4000]))
    db.session.add(ArchitectMessage(role="assistant", content=answer))
    db.session.commit()
    return answer


def clear_conversation() -> None:
    for message in db.session.scalars(select(ArchitectMessage)):
        db.session.delete(message)
    db.session.commit()


def plan_with_ai(focus: str = "", client_factory=None) -> tuple[str, int]:
    """Pede ao Claude um plano de missões. Retorna (resumo, quantas sugestões novas)."""
    summary, missions = ai.plan(context.build().as_prompt_data(), focus, client_factory=client_factory)
    goal_ids = {g.id for g in list_goals()}
    created = 0
    for item in missions[:8]:
        title = str(item.get("title", "")).strip()[:160]
        if not title:
            continue
        goal_id = int(item.get("goal_id") or 0)
        db.session.add(ArchitectSuggestion(
            title=title, description=str(item.get("description", ""))[:2000], reason=str(item.get("reason", ""))[:1000],
            category=str(item.get("category", ""))[:80], difficulty=_clamp(item.get("difficulty"), 1, 5, 2),
            priority=item.get("priority") if item.get("priority") in ("low", "medium", "high", "critical") else "medium",
            recurrence=item.get("recurrence") if item.get("recurrence") in ("none", "daily", "weekly", "monthly") else "none",
            due_in_days=_clamp(item.get("due_in_days"), 0, 30, 1), source="ai", rule_key="ai",
            goal_id=goal_id if goal_id in goal_ids else None,
        ))
        created += 1
    db.session.commit()
    return summary, created


# ---------- internos ----------

def _store_drafts(drafts: list[analysis.Draft]) -> None:
    """Guarda as sugestões das regras sem repetir: mesma regra respondida há pouco não volta."""
    since = time.now() - timedelta(days=REPEAT_AFTER_DAYS)
    recent = set(db.session.scalars(select(ArchitectSuggestion.rule_key).where(
        (ArchitectSuggestion.status == "pending") | (ArchitectSuggestion.created_at >= since))))
    pending = db.session.scalar(select(db.func.count(ArchitectSuggestion.id)).where(
        ArchitectSuggestion.status == "pending", ArchitectSuggestion.source == "rules")) or 0
    added = False
    for draft in drafts:
        if draft.rule_key in recent or pending >= MAX_PENDING_RULE_SUGGESTIONS:
            continue
        db.session.add(ArchitectSuggestion(
            title=draft.title, description=draft.description, reason=draft.reason, category=draft.category,
            difficulty=draft.difficulty, priority=draft.priority, recurrence=draft.recurrence,
            due_in_days=draft.due_in_days, source="rules", rule_key=draft.rule_key, goal_id=draft.goal_id))
        recent.add(draft.rule_key)
        pending += 1
        added = True
    if added:
        db.session.commit()


def _clamp(value, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


def _suggestion(suggestion_id: int) -> ArchitectSuggestion:
    suggestion = db.session.get(ArchitectSuggestion, suggestion_id)
    if suggestion is None:
        raise NotFoundError("Sugestão não encontrada.")
    return suggestion


def _goal(goal_id: int) -> ArchitectGoal:
    goal = db.session.get(ArchitectGoal, goal_id)
    if goal is None:
        raise NotFoundError("Meta não encontrada.")
    return goal
