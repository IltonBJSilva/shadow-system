"""Regras de negócio do Quest System e API pública para outros módulos.

Funções de leitura para outros módulos (dashboard, calendário) retornam `QuestView`,
não o modelo, para que eles não dependam das tabelas de Quests.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import delete, func, insert, or_, select

from app.core import events, time
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.hunter import progression
from app.modules.hunter import services as hunter

from . import constants, recurrence
from .models import Quest, QuestCategory, QuestLog, category_attributes, quest_attributes


# ---------- Tipos ----------

@dataclass
class QuestInput:
    """Dados de criação/edição vindos do formulário (ou de outro módulo, ex.: IA no futuro)."""

    title: str
    description: str = ""
    quest_type: str = "custom"
    category_id: int | None = None
    priority: str = "medium"
    difficulty: int = 3
    xp_reward: int | None = None  # None = XP padrão da dificuldade
    due_date: date | None = None
    recurrence: str = "none"
    completion_criteria: str = ""
    reward: str = ""
    attribute_ids: list[int] = field(default_factory=list)  # vazio = atributos da categoria


@dataclass(frozen=True)
class QuestView:
    id: int
    title: str
    quest_type: str
    type_label: str
    priority: str
    status: str
    difficulty: int
    xp_reward: int
    due_date: date | None
    category_name: str | None
    category_color: str | None
    is_overdue: bool
    series_id: int | None = None  # ocorrências de uma recorrente compartilham o id da primeira


# ---------- Leitura ----------

def get_quest(quest_id: int) -> Quest:
    quest = db.session.get(Quest, quest_id)
    if quest is None:
        raise NotFoundError("Quest não encontrada.")
    return quest


def list_quests(view: str = "active", quest_type: str | None = None, category_id: int | None = None) -> list[Quest]:
    """view: 'active' (pendentes e em andamento), 'completed', 'closed' (não realizadas/canceladas), 'all'."""
    query = select(Quest)
    if view == "active":
        query = query.where(Quest.status.in_(constants.ACTIVE_STATUSES))
    elif view == "completed":
        query = query.where(Quest.status == "completed")
    elif view == "closed":
        query = query.where(Quest.status.in_(("missed", "cancelled")))
    if quest_type:
        query = query.where(Quest.quest_type == quest_type)
    if category_id:
        query = query.where(Quest.category_id == category_id)
    quests = list(db.session.scalars(query))
    if view == "completed":
        return sorted(quests, key=lambda q: q.completed_at or q.updated_at, reverse=True)
    return sorted(quests, key=_urgency_key)


def quests_for_today(today: date | None = None) -> list[QuestView]:
    """Ativas com prazo até hoje (inclui atrasadas) e Daily Quests sem prazo."""
    today = today or time.today()
    rows = db.session.scalars(
        select(Quest).where(
            Quest.status.in_(constants.ACTIVE_STATUSES),
            or_(Quest.due_date <= today, (Quest.due_date.is_(None)) & (Quest.quest_type == "daily")),
        )
    )
    return [_view(q, today) for q in sorted(rows, key=_urgency_key)]


def priority_quests(limit: int = 5) -> list[QuestView]:
    today = time.today()
    rows = db.session.scalars(
        select(Quest).where(
            Quest.status.in_(constants.ACTIVE_STATUSES),
            or_(Quest.priority.in_(("high", "critical")), Quest.quest_type.in_(("main", "emergency"))),
        )
    )
    return [_view(q, today) for q in sorted(rows, key=_urgency_key)[:limit]]


def quests_due_between(start: date, end: date) -> list[QuestView]:
    """Quests com prazo no intervalo (inclusive). Usado pelo calendário."""
    today = time.today()
    rows = db.session.scalars(
        select(Quest).where(Quest.due_date >= start, Quest.due_date <= end, Quest.status != "cancelled")
    )
    return [_view(q, today) for q in rows]


def quest_choices() -> list[tuple[int, str]]:
    """Quests ativas (id, título) para vincular em outros módulos, ex.: eventos do calendário."""
    rows = db.session.scalars(
        select(Quest).where(Quest.status.in_(constants.ACTIVE_STATUSES)).order_by(Quest.title)
    )
    return [(q.id, q.title) for q in rows]


def quest_title(quest_id: int | None) -> str | None:
    quest = db.session.get(Quest, quest_id) if quest_id else None
    return quest.title if quest else None


def active_in_series(series_id: int) -> Quest | None:
    """A ocorrência ativa (pendente ou em andamento) de uma quest recorrente."""
    return db.session.scalar(select(Quest).where(Quest.series_id == series_id,
                                                 Quest.status.in_(constants.ACTIVE_STATUSES)).order_by(Quest.id.desc()))


def update_description(quest_id: int, description: str) -> None:
    """Troca só a descrição (ex.: treino com carga nova). A próxima ocorrência herda o texto."""
    get_quest(quest_id).description = description.strip()
    db.session.commit()


def completed_between(start: date, end: date) -> int:
    """Quests concluídas entre start e end, inclusive."""
    return db.session.scalar(select(func.count(Quest.id)).where(
        Quest.status == "completed",
        Quest.completed_at >= datetime.combine(start, datetime.min.time()),
        Quest.completed_at < datetime.combine(end + timedelta(days=1), datetime.min.time()))) or 0


@dataclass(frozen=True)
class CategoryPerformance:
    name: str
    completed: int
    missed: int
    avg_difficulty: float

    @property
    def rate(self) -> float | None:
        """Taxa de conclusão (0 a 1). None = sem dados suficientes."""
        total = self.completed + self.missed
        return self.completed / total if total else None


def category_performance(days: int = 30, today: date | None = None) -> list[CategoryPerformance]:
    """Concluídas x não realizadas por categoria nos últimos `days` dias (pelo prazo ou conclusão)."""
    today = today or time.today()
    since = today - timedelta(days=days)
    rows = db.session.scalars(select(Quest).where(
        Quest.status.in_(("completed", "missed")),
        ((Quest.completed_at >= datetime.combine(since, datetime.min.time())) | (Quest.due_date >= since)),
    ))
    stats: dict[str, list] = {}
    for quest in rows:
        name = quest.category.name if quest.category else "Sem categoria"
        entry = stats.setdefault(name, [0, 0, []])
        entry[0 if quest.status == "completed" else 1] += 1
        entry[2].append(quest.difficulty)
    return sorted((CategoryPerformance(name, c, m, round(sum(d) / len(d), 1)) for name, (c, m, d) in stats.items()),
                  key=lambda p: (-(p.completed + p.missed), p.name))


def completed_count(quest_type: str | None = None) -> int:
    """Quantas quests estão concluídas, de um tipo ou de todos (métrica das conquistas)."""
    query = select(func.count(Quest.id)).where(Quest.status == "completed")
    if quest_type:
        query = query.where(Quest.quest_type == quest_type)
    return db.session.scalar(query) or 0


def stats() -> dict[str, int]:
    counts = dict(db.session.execute(select(Quest.status, func.count(Quest.id)).group_by(Quest.status)).all())
    today = time.today()
    overdue = db.session.scalar(
        select(func.count(Quest.id)).where(Quest.status.in_(constants.ACTIVE_STATUSES), Quest.due_date < today)
    )
    return {
        "completed": counts.get("completed", 0),
        "active": counts.get("pending", 0) + counts.get("in_progress", 0),
        "overdue": overdue or 0,
    }


def attribute_ids_for(quest: Quest) -> list[int]:
    return list(db.session.scalars(select(quest_attributes.c.attribute_id).where(quest_attributes.c.quest_id == quest.id)))


def attribute_names_for(quest: Quest) -> list[str]:
    ids = set(attribute_ids_for(quest))
    return [a.name for a in hunter.list_attributes() if a.id in ids]


# ---------- Escrita ----------

def create_quest(data: QuestInput, *, series_id: int | None = None, note: str = "Quest criada") -> Quest:
    _validate(data)
    quest = Quest()
    _apply(quest, data)
    quest.series_id = series_id
    db.session.add(quest)
    db.session.flush()  # gera o id
    if data.recurrence != "none" and series_id is None:
        quest.series_id = quest.id
    _set_attributes(quest, data.attribute_ids or category_attribute_ids(data.category_id))
    _log(quest, "created", note)
    db.session.commit()
    return quest


def update_quest(quest_id: int, data: QuestInput) -> Quest:
    _validate(data)
    quest = get_quest(quest_id)
    _apply(quest, data)
    if quest.recurrence != "none" and quest.series_id is None:
        quest.series_id = quest.id
    _set_attributes(quest, data.attribute_ids or category_attribute_ids(data.category_id))
    _log(quest, "edited", "Quest editada")
    db.session.commit()
    return quest


def start_quest(quest_id: int) -> Quest:
    quest = get_quest(quest_id)
    if quest.status != "pending":
        raise DomainError("Só quests pendentes podem ser iniciadas.")
    quest.status = "in_progress"
    _log(quest, "started", "Quest iniciada")
    db.session.commit()
    return quest


def complete_quest(quest_id: int) -> hunter.AwardResult:
    """Conclui a quest, concede XP/atributos e cria a próxima ocorrência se for recorrente."""
    quest = get_quest(quest_id)
    if quest.status not in constants.ACTIVE_STATUSES:
        raise DomainError("Esta quest não está ativa; não pode ser concluída de novo.")
    quest.status = "completed"
    quest.completed_at = time.now()
    _log(quest, "completed", f"Concluída: +{quest.xp_reward} XP")
    result = hunter.award_xp(
        quest.xp_reward,
        source="quest",
        source_id=quest.id,
        description=f"Quest concluída: {quest.title}",
        attribute_ids=attribute_ids_for(quest),
        attribute_points=progression.attribute_points_for_difficulty(quest.difficulty),
    )
    if quest.recurrence != "none":
        # Concluir uma ocorrência atrasada hoje conta como a de hoje: a próxima vem depois de hoje.
        base = max(quest.due_date or time.today(), time.today())
        _spawn_next(quest, recurrence.next_due(base, quest.recurrence))
    db.session.flush()
    # Outros módulos (ex.: gamificação) reagem aqui, na mesma transação.
    result.extra.extend(events.publish("quest.completed", quest=_view(quest, time.today()),
                                       completed_at=quest.completed_at))
    db.session.commit()
    return result


def cancel_quest(quest_id: int) -> Quest:
    quest = get_quest(quest_id)
    if quest.status not in constants.ACTIVE_STATUSES:
        raise DomainError("Só quests ativas podem ser canceladas.")
    quest.status = "cancelled"
    _log(quest, "cancelled", "Quest cancelada")
    db.session.commit()
    return quest


def delete_quest(quest_id: int) -> None:
    """Remove a quest e seu log. O XP já ganho continua no histórico do Hunter."""
    db.session.delete(get_quest(quest_id))
    db.session.commit()


def delete_quests(quest_ids: list[int]) -> int:
    """Remove várias quests de uma vez. O XP já ganho continua no histórico. Retorna quantas saíram."""
    rows = db.session.scalars(select(Quest).where(Quest.id.in_(quest_ids))).all() if quest_ids else []
    for quest in rows:
        db.session.delete(quest)
    db.session.commit()
    return len(rows)


def cancel_quests(quest_ids: list[int]) -> int:
    """Cancela as quests ativas da lista (as já fechadas são ignoradas). Sem perda de XP."""
    rows = db.session.scalars(
        select(Quest).where(Quest.id.in_(quest_ids), Quest.status.in_(constants.ACTIVE_STATUSES))
    ).all() if quest_ids else []
    for quest in rows:
        quest.status = "cancelled"
        _log(quest, "cancelled", "Quest cancelada (em massa)")
    db.session.commit()
    return len(rows)


def roll_over_recurring(today: date | None = None) -> int:
    """Fecha ocorrências recorrentes vencidas e cria a próxima. Retorna quantas foram roladas."""
    return roll_over_with_messages(today)[0]


def roll_over_with_messages(today: date | None = None) -> tuple[int, list[tuple[str, str]]]:
    """Igual a roll_over_recurring, mas devolve também as mensagens (ex.: punições aplicadas).

    Uma Daily Quest de ontem não feita vira "Não realizada" e a de hoje aparece. A quest em si não tira
    XP; quem decide punições é a gamificação, que recebe o evento "quest.missed".
    É idempotente: rodar duas vezes no mesmo dia não duplica nada.
    """
    today = today or time.today()
    messages: list[tuple[str, str]] = []
    overdue = list(db.session.scalars(
        select(Quest).where(
            Quest.recurrence != "none",
            Quest.status.in_(constants.ACTIVE_STATUSES),
            Quest.due_date < today,
        )
    ))
    for quest in overdue:
        quest.status = "missed"
        _log(quest, "missed", "Prazo passou: a próxima ocorrência foi criada.")
        _spawn_next(quest, recurrence.next_due_on_or_after(quest.due_date, quest.recurrence, today))
        db.session.flush()
        messages.extend(events.publish("quest.missed", quest=_view(quest, today), today=today))
    if overdue:
        db.session.commit()
    return len(overdue), messages


def completed_on(day: date) -> list[QuestView]:
    """Quests concluídas no dia (usado para o bônus de combo diário)."""
    start = datetime.combine(day, datetime.min.time())
    rows = db.session.scalars(
        select(Quest).where(Quest.status == "completed", Quest.completed_at >= start,
                            Quest.completed_at < start + timedelta(days=1))
    )
    return [_view(q, day) for q in rows]


# ---------- Categorias ----------

def list_categories() -> list[QuestCategory]:
    return list(db.session.scalars(select(QuestCategory).order_by(QuestCategory.name)))


def create_suggested_categories() -> list[str]:
    """Cria as categorias sugeridas que ainda não existem (pelo nome). Retorna os nomes criados."""
    existing = {name.lower() for name in db.session.scalars(select(QuestCategory.name))}
    ids_by_key = {a.key: a.id for a in hunter.list_attributes()}
    created = []
    for name, color, keys in constants.SUGGESTED_CATEGORIES:
        if name.lower() in existing:
            continue
        save_category(name, color, [ids_by_key[k] for k in keys if k in ids_by_key])
        created.append(name)
    return created


def category_choices() -> list[tuple[int, str]]:
    return [(c.id, c.name) for c in list_categories()]


def category_attribute_ids(category_id: int | None) -> list[int]:
    if not category_id:
        return []
    return list(db.session.scalars(
        select(category_attributes.c.attribute_id).where(category_attributes.c.category_id == category_id)
    ))


def save_category(name: str, color: str, attribute_ids: list[int], category_id: int | None = None) -> QuestCategory:
    name = name.strip()
    clash = db.session.scalar(
        select(QuestCategory).where(func.lower(QuestCategory.name) == name.lower(),
                                    QuestCategory.id != (category_id or 0))
    )
    if clash:
        raise DomainError(f"A categoria {clash.name} já existe.")
    category = db.session.get(QuestCategory, category_id) if category_id else QuestCategory()
    if category is None:
        raise NotFoundError("Categoria não encontrada.")
    category.name, category.color = name, color
    db.session.add(category)
    db.session.flush()
    db.session.execute(delete(category_attributes).where(category_attributes.c.category_id == category.id))
    if attribute_ids:
        db.session.execute(insert(category_attributes),
                           [{"category_id": category.id, "attribute_id": a} for a in set(attribute_ids)])
    db.session.commit()
    return category


def delete_category(category_id: int) -> None:
    category = db.session.get(QuestCategory, category_id)
    if category is None:
        raise NotFoundError("Categoria não encontrada.")
    db.session.delete(category)  # quests da categoria ficam sem categoria (ON DELETE SET NULL)
    db.session.commit()


# ---------- Internos ----------

def _validate(data: QuestInput) -> None:
    if not data.title.strip():
        raise DomainError("A quest precisa de um título.")
    if data.quest_type not in constants.QUEST_TYPES:
        raise DomainError("Tipo de quest inválido.")
    if data.priority not in constants.PRIORITIES:
        raise DomainError("Prioridade inválida.")
    if data.recurrence not in constants.RECURRENCES:
        raise DomainError("Recorrência inválida.")
    if not 1 <= data.difficulty <= 5:
        raise DomainError("Dificuldade deve ser de 1 a 5.")
    if data.xp_reward is not None and data.xp_reward < 0:
        raise DomainError("XP não pode ser negativo.")
    if data.recurrence != "none" and data.due_date is None:
        # Sem data não há como saber quando a próxima ocorrência vence.
        data.due_date = time.today()


def _apply(quest: Quest, data: QuestInput) -> None:
    quest.title = data.title.strip()
    quest.description = data.description.strip()
    quest.quest_type = data.quest_type
    quest.category_id = data.category_id or None
    quest.priority = data.priority
    quest.difficulty = data.difficulty
    quest.xp_reward = data.xp_reward if data.xp_reward is not None else progression.xp_for_difficulty(data.difficulty, data.priority)
    quest.due_date = data.due_date
    quest.recurrence = data.recurrence
    quest.completion_criteria = data.completion_criteria.strip()
    quest.reward = data.reward.strip()


def _set_attributes(quest: Quest, attribute_ids: list[int]) -> None:
    db.session.execute(delete(quest_attributes).where(quest_attributes.c.quest_id == quest.id))
    if attribute_ids:
        db.session.execute(insert(quest_attributes),
                           [{"quest_id": quest.id, "attribute_id": a} for a in set(attribute_ids)])


def _spawn_next(quest: Quest, due: date) -> Quest:
    data = QuestInput(
        title=quest.title, description=quest.description, quest_type=quest.quest_type,
        category_id=quest.category_id, priority=quest.priority, difficulty=quest.difficulty,
        xp_reward=quest.xp_reward, due_date=due, recurrence=quest.recurrence,
        completion_criteria=quest.completion_criteria, reward=quest.reward,
        attribute_ids=attribute_ids_for(quest),
    )
    next_quest = Quest()
    _apply(next_quest, data)
    next_quest.series_id = quest.series_id or quest.id
    db.session.add(next_quest)
    db.session.flush()
    _set_attributes(next_quest, data.attribute_ids)
    _log(next_quest, "created", "Nova ocorrência da quest recorrente")
    return next_quest


def _log(quest: Quest, action: str, note: str) -> None:
    quest.logs.append(QuestLog(action=action, note=note[:200]))


def _urgency_key(quest: Quest) -> tuple:
    """Ordena: com prazo antes de sem prazo, prazo mais próximo, depois prioridade."""
    return (quest.due_date is None, quest.due_date or date.max, constants.PRIORITY_ORDER.get(quest.priority, 9), quest.id)


def _view(quest: Quest, today: date) -> QuestView:
    return QuestView(
        id=quest.id,
        title=quest.title,
        quest_type=quest.quest_type,
        type_label=constants.QUEST_TYPES.get(quest.quest_type, quest.quest_type),
        priority=quest.priority,
        status=quest.status,
        difficulty=quest.difficulty,
        xp_reward=quest.xp_reward,
        due_date=quest.due_date,
        category_name=quest.category.name if quest.category else None,
        category_color=quest.category.color if quest.category else None,
        is_overdue=bool(quest.due_date and quest.due_date < today and quest.status in constants.ACTIVE_STATUSES),
        series_id=quest.series_id,
    )
