"""API pública do módulo Hunter.

Outros módulos concedem XP chamando `award_xp` e leem o status com `get_status`.
Eles nunca alteram as tabelas do Hunter diretamente.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import func, select

from app.core.errors import DomainError, NotFoundError
from app.extensions import db

from . import defaults, progression
from .models import Attribute, AttributeGain, Hunter, Rank, XpEvent


# ---------- Tipos retornados para outros módulos ----------

@dataclass(frozen=True)
class AttributeView:
    id: int
    key: str
    name: str
    description: str
    points: int


@dataclass(frozen=True)
class RankView:
    code: str
    name: str
    color: str
    min_level: int


@dataclass(frozen=True)
class HunterStatus:
    name: str
    title: str
    progress: progression.LevelProgress
    rank: RankView | None
    next_rank: RankView | None
    attributes: list[AttributeView]

    @property
    def max_attribute_points(self) -> int:
        """Referência para as barras de atributo (relativas ao maior atributo)."""
        return max([a.points for a in self.attributes] + [10])


@dataclass
class AwardResult:
    amount: int
    old_level: int
    new_level: int
    new_rank: RankView | None = None
    attribute_names: list[str] = field(default_factory=list)

    @property
    def leveled_up(self) -> bool:
        return self.new_level > self.old_level


# ---------- Inicialização ----------

def seed_defaults() -> None:
    """Cria hunter, ranks e atributos padrão se ainda não existirem. Pode rodar várias vezes."""
    if db.session.scalar(select(func.count(Hunter.id))) == 0:
        db.session.add(Hunter(name=defaults.DEFAULT_HUNTER_NAME, title=defaults.DEFAULT_HUNTER_TITLE))
    if db.session.scalar(select(func.count(Rank.id))) == 0:
        for code, name, min_level, color in defaults.DEFAULT_RANKS:
            db.session.add(Rank(code=code, name=name, min_level=min_level, color=color))
    if db.session.scalar(select(func.count(Attribute.id))) == 0:
        for order, (key, name, description) in enumerate(defaults.DEFAULT_ATTRIBUTES):
            db.session.add(Attribute(key=key, name=name, description=description, sort_order=order))
    db.session.commit()


def get_hunter() -> Hunter:
    hunter = db.session.scalar(select(Hunter).order_by(Hunter.id))
    if hunter is None:
        seed_defaults()
        hunter = db.session.scalar(select(Hunter).order_by(Hunter.id))
    return hunter


# ---------- Leitura ----------

def get_status() -> HunterStatus:
    hunter = get_hunter()
    progress = progression.level_progress(hunter.total_xp)
    ranks = _ranks()
    current = progression.rank_for_level(progress.level, ranks)
    upcoming = [r for r in ranks if r.min_level > progress.level]
    return HunterStatus(
        name=hunter.name,
        title=hunter.title,
        progress=progress,
        rank=_rank_view(current),
        next_rank=_rank_view(min(upcoming, key=lambda r: r.min_level)) if upcoming else None,
        attributes=list_attributes(),
    )


def list_attributes() -> list[AttributeView]:
    get_hunter()  # garante os atributos padrão na primeira execução
    rows = db.session.scalars(select(Attribute).order_by(Attribute.sort_order, Attribute.id))
    return [AttributeView(a.id, a.key, a.name, a.description, a.points) for a in rows]


def attribute_choices() -> list[tuple[int, str]]:
    """Opções (id, nome) para formulários de outros módulos."""
    return [(a.id, a.name) for a in list_attributes()]


def list_ranks() -> list[Rank]:
    get_hunter()
    return _ranks()


def recent_events(limit: int = 10) -> list[XpEvent]:
    return list(db.session.scalars(select(XpEvent).order_by(XpEvent.created_at.desc(), XpEvent.id.desc()).limit(limit)))


def xp_by_day(end: date, days: int = 7) -> list[tuple[date, int]]:
    """XP ganho por dia nos últimos `days` dias até `end` (inclusive). Dias sem XP aparecem com 0."""
    start = end - timedelta(days=days - 1)
    rows = db.session.execute(
        select(func.date(XpEvent.created_at), func.sum(XpEvent.amount))
        .where(XpEvent.created_at >= datetime.combine(start, datetime.min.time()))
        .group_by(func.date(XpEvent.created_at))
    ).all()
    totals = {str(day): int(total or 0) for day, total in rows}
    return [(start + timedelta(days=i), max(0, totals.get(str(start + timedelta(days=i)), 0)))
            for i in range(days)]


# ---------- Escrita ----------

def award_xp(amount: int, *, source: str, description: str, source_id: int | None = None,
             attribute_ids: list[int] | None = None, attribute_points: int = 1) -> AwardResult:
    """Concede (ou estorna, se amount < 0) XP e pontos de atributo, registrando no histórico.

    Não faz commit: quem chama decide, para que a quest/hábito e o XP sejam salvos juntos.
    """
    hunter = get_hunter()
    old_level = progression.level_progress(hunter.total_xp).level
    # XP nunca fica negativo: um estorno maior que o saldo zera, não pune além disso.
    applied = max(amount, -hunter.total_xp)
    hunter.total_xp += applied

    event = XpEvent(amount=applied, source=source, source_id=source_id, description=description[:200])
    db.session.add(event)

    names: list[str] = []
    for attribute in _attributes_by_ids(attribute_ids or []):
        points = attribute_points if amount >= 0 else -min(attribute_points, attribute.points)
        attribute.points += points
        event.gains.append(AttributeGain(attribute=attribute, points=points))
        names.append(attribute.name)

    new_level = progression.level_progress(hunter.total_xp).level
    result = AwardResult(amount=applied, old_level=old_level, new_level=new_level, attribute_names=names)
    if new_level > old_level:
        ranks = _ranks()
        before = progression.rank_for_level(old_level, ranks)
        after = progression.rank_for_level(new_level, ranks)
        if after is not None and after is not before:
            result.new_rank = _rank_view(after)
    return result


def update_profile(name: str, title: str) -> None:
    hunter = get_hunter()
    hunter.name = name.strip() or hunter.name
    hunter.title = title.strip()
    db.session.commit()


def update_attribute(attribute_id: int, name: str, description: str) -> None:
    attribute = db.session.get(Attribute, attribute_id)
    if attribute is None:
        raise NotFoundError("Atributo não encontrado.")
    attribute.name = name.strip() or attribute.name
    attribute.description = description.strip()
    db.session.commit()


def save_rank(code: str, name: str, min_level: int, color: str, rank_id: int | None = None) -> Rank:
    code = code.strip().upper()
    clash = db.session.scalar(
        select(Rank).where((Rank.code == code) | (Rank.min_level == min_level), Rank.id != (rank_id or 0))
    )
    if clash:
        raise DomainError(f"Já existe o rank {clash.code} com esse código ou nível mínimo.")
    rank = db.session.get(Rank, rank_id) if rank_id else Rank()
    if rank is None:
        raise NotFoundError("Rank não encontrado.")
    rank.code, rank.name, rank.min_level, rank.color = code, name.strip(), min_level, color
    db.session.add(rank)
    db.session.commit()
    return rank


def delete_rank(rank_id: int) -> None:
    rank = db.session.get(Rank, rank_id)
    if rank is None:
        raise NotFoundError("Rank não encontrado.")
    if rank.min_level == 1:
        raise DomainError("O rank inicial (nível 1) não pode ser removido; edite-o se quiser.")
    db.session.delete(rank)
    db.session.commit()


def award_messages(result: AwardResult) -> list[tuple[str, str]]:
    """Mensagens (texto, categoria do flash) para mostrar depois de um ganho de XP."""
    if result.amount <= 0:
        return []
    messages = [(f"+{result.amount} XP"
                 + (f" · {', '.join(result.attribute_names)} aumentou" if result.attribute_names else ""),
                 "success")]
    if result.leveled_up:
        messages.append((f"LEVEL UP! Você alcançou o nível {result.new_level}.", "levelup"))
    if result.new_rank:
        messages.append((f"Novo rank desbloqueado: {result.new_rank.name}.", "levelup"))
    return messages


# ---------- Internos ----------

def _ranks() -> list[Rank]:
    return list(db.session.scalars(select(Rank).order_by(Rank.min_level)))


def _rank_view(rank: Rank | None) -> RankView | None:
    return RankView(rank.code, rank.name, rank.color, rank.min_level) if rank else None


def _attributes_by_ids(ids: list[int]) -> list[Attribute]:
    if not ids:
        return []
    return list(db.session.scalars(select(Attribute).where(Attribute.id.in_(ids))))
