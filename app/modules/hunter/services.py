"""API pública do módulo Hunter.

Outros módulos concedem XP chamando `award_xp` e leem o status com `get_status`.
Eles nunca alteram as tabelas do Hunter diretamente.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Callable

from sqlalchemy import func, select

from app.core.errors import DomainError, NotFoundError
from app.extensions import db

from . import defaults, progression
from app.core import time

from .models import Attribute, AttributeGain, Hunter, Rank, Title, XpEvent


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
    avatar_url: str
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
    # Mensagens extras de quem reagiu ao ganho (ex.: bônus da gamificação).
    extra: list[tuple[str, str]] = field(default_factory=list)

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
    _seed_missing_attributes()
    _seed_titles()
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
        avatar_url=hunter.avatar_url,
        progress=progress,
        rank=_rank_view(current),
        next_rank=_rank_view(min(upcoming, key=lambda r: r.min_level)) if upcoming else None,
        attributes=list_attributes(),
    )


def list_attributes() -> list[AttributeView]:
    get_hunter()  # garante os atributos padrão na primeira execução
    if db.session.scalar(select(func.count(Attribute.id))) < len(defaults.DEFAULT_ATTRIBUTES):
        _seed_missing_attributes()  # banco antigo: ganha os atributos novos (Wisdom, Charisma)
        db.session.commit()
    rows = db.session.scalars(select(Attribute).order_by(Attribute.sort_order, Attribute.id))
    return [AttributeView(a.id, a.key, a.name, a.description, a.points) for a in rows]


def attribute_choices() -> list[tuple[int, str]]:
    """Opções (id, nome) para formulários de outros módulos."""
    return [(a.id, a.name) for a in list_attributes()]


def list_ranks() -> list[Rank]:
    get_hunter()
    return _ranks()


def recent_events(limit: int = 10, sources: list[str] | None = None) -> list[XpEvent]:
    query = select(XpEvent)
    if sources:
        query = query.where(XpEvent.source.in_(sources))
    return list(db.session.scalars(query.order_by(XpEvent.created_at.desc(), XpEvent.id.desc()).limit(limit)))


def count_events_on(day: date, source: str) -> int:
    """Quantos eventos de XP positivos daquela origem aconteceram no dia (ex.: quests concluídas hoje)."""
    start = datetime.combine(day, datetime.min.time())
    return db.session.scalar(
        select(func.count(XpEvent.id)).where(
            XpEvent.source == source, XpEvent.amount > 0,
            XpEvent.created_at >= start, XpEvent.created_at < start + timedelta(days=1),
        )
    ) or 0


def revert_events(source: str, source_id: int, description: str) -> int:
    """Estorna a soma do XP já dado por (source, source_id). Retorna o XP estornado.

    Usado para desfazer bônus quando a ação que os gerou é desfeita (ex.: desmarcar um hábito).
    """
    total = db.session.scalar(
        select(func.coalesce(func.sum(XpEvent.amount), 0)).where(XpEvent.source == source, XpEvent.source_id == source_id)
    ) or 0
    if total > 0:
        award_xp(-total, source=source, source_id=source_id, description=description)
    return total


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
    if applied > 0:
        result.extra.extend(title_unlock_messages(check_titles()))
    if new_level > old_level:
        ranks = _ranks()
        before = progression.rank_for_level(old_level, ranks)
        after = progression.rank_for_level(new_level, ranks)
        if after is not None and after is not before:
            result.new_rank = _rank_view(after)
    return result


def update_profile(name: str, title: str | None = None, avatar_url: str = "") -> None:
    """Nome e avatar. O título exibido é escolhido entre os desbloqueados (`choose_title`);
    `title`, se vier, precisa ser um título já desbloqueado."""
    avatar_url = avatar_url.strip()
    if avatar_url and not avatar_url.startswith("https://"):
        raise DomainError("O avatar precisa ser um link público começando com https://")
    hunter = get_hunter()
    hunter.name = name.strip() or hunter.name
    if title is not None and title.strip() != hunter.title:
        _seed_titles()
        unlocked = {t.name for t in db.session.scalars(select(Title).where(Title.unlocked_at.is_not(None)))}
        if title.strip() not in unlocked:
            raise DomainError("Escolha um título já desbloqueado.")
        hunter.title = title.strip()
    hunter.avatar_url = avatar_url
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
        return list(result.extra)
    messages = [(f"+{result.amount} XP"
                 + (f" · {', '.join(result.attribute_names)} aumentou" if result.attribute_names else ""),
                 "success")]
    if result.leveled_up:
        messages.append((f"LEVEL UP! Você alcançou o nível {result.new_level}.", "levelup"))
    if result.new_rank:
        messages.append((f"Novo rank desbloqueado: {result.new_rank.name}.", "levelup"))
    return messages + result.extra


# ---------- Internos ----------

def _ranks() -> list[Rank]:
    return list(db.session.scalars(select(Rank).order_by(Rank.min_level)))


def _rank_view(rank: Rank | None) -> RankView | None:
    return RankView(rank.code, rank.name, rank.color, rank.min_level) if rank else None


def _attributes_by_ids(ids: list[int]) -> list[Attribute]:
    if not ids:
        return []
    return list(db.session.scalars(select(Attribute).where(Attribute.id.in_(ids))))


# ---------- Títulos ----------

@dataclass(frozen=True)
class TitleView:
    id: int
    name: str
    description: str
    rule: str
    rule_label: str
    threshold: int
    current: int
    unlocked_at: datetime | None
    is_custom: bool
    is_active: bool

    @property
    def unlocked(self) -> bool:
        return self.unlocked_at is not None

    @property
    def percent(self) -> int:
        if self.unlocked or not self.threshold:
            return 100
        return min(99, int(self.current * 100 / self.threshold))


# Métricas vindas de outros módulos (ex.: quests registra "quests_completed"). O Hunter não importa
# esses módulos: eles se registram aqui ao serem importados, e o Hunter só chama a função.
_metrics: dict[str, Callable[[], int]] = {}


def register_metric(rule: str, provider: Callable[[], int]) -> None:
    _metrics[rule] = provider


def _metric_values() -> dict[str, int]:
    hunter = get_hunter()
    values = {"level": progression.level_progress(hunter.total_xp).level, "total_xp": hunter.total_xp}
    for rule, provider in _metrics.items():
        values[rule] = int(provider() or 0)
    return values


def check_titles() -> list[str]:
    """Desbloqueia os títulos cuja meta foi atingida e retorna os nomes recém-desbloqueados.

    Não faz commit (roda dentro de award_xp); quem chama salva junto.
    """
    _seed_titles()
    values = _metric_values()
    unlocked: list[str] = []
    for title in db.session.scalars(select(Title).where(Title.unlocked_at.is_(None))).all():
        if title.rule == "custom" or values.get(title.rule, -1) >= title.threshold:
            title.unlocked_at = time.now()
            unlocked.append(title.name)
    return unlocked


def title_unlock_messages(names: list[str]) -> list[tuple[str, str]]:
    return [(f"Título desbloqueado: {name}. Escolha-o no seu perfil.", "achievement") for name in names]


def list_titles() -> list[TitleView]:
    _seed_titles()
    values = _metric_values()
    active = get_hunter().title
    rows = db.session.scalars(select(Title).order_by(Title.sort_order, Title.id)).all()
    rows.sort(key=lambda t: t.unlocked_at is None)  # desbloqueados primeiro, na ordem padrão
    return [
        TitleView(id=t.id, name=t.name, description=t.description, rule=t.rule,
                  rule_label=defaults.RULE_LABELS.get(t.rule, t.rule), threshold=t.threshold,
                  current=values.get(t.rule, 0), unlocked_at=t.unlocked_at, is_custom=t.rule == "custom",
                  is_active=t.name == active)
        for t in rows
    ]


def choose_title(title_id: int) -> str:
    title = db.session.get(Title, title_id)
    if title is None:
        raise NotFoundError("Título não encontrado.")
    if title.unlocked_at is None:
        raise DomainError("Esse título ainda está bloqueado.")
    get_hunter().title = title.name
    db.session.commit()
    return title.name


def create_custom_title(name: str, description: str = "") -> Title:
    name = name.strip()[:80]
    if not name:
        raise DomainError("Dê um nome ao título.")
    _seed_titles()
    if db.session.scalar(select(Title).where(func.lower(Title.name) == name.lower())):
        raise DomainError("Já existe um título com esse nome.")
    order = (db.session.scalar(select(func.max(Title.sort_order))) or 0) + 1
    title = Title(name=name, description=description.strip()[:500], rule="custom", threshold=0,
                  unlocked_at=time.now(), sort_order=order)
    db.session.add(title)
    db.session.commit()
    return title


def delete_title(title_id: int) -> None:
    """Só títulos criados por você podem ser apagados. Se era o exibido, volta ao inicial."""
    title = db.session.get(Title, title_id)
    if title is None:
        raise NotFoundError("Título não encontrado.")
    if title.rule != "custom":
        raise DomainError("Títulos de conquista não podem ser apagados.")
    hunter = get_hunter()
    if hunter.title == title.name:
        hunter.title = defaults.DEFAULT_HUNTER_TITLE
    db.session.delete(title)
    db.session.commit()


def _seed_missing_attributes() -> None:
    """Cria os atributos padrão que faltarem pela chave (bancos antigos ganham Wisdom e Charisma).

    Atributos renomeados por você continuam com o seu nome: a comparação é pela chave.
    """
    existing = set(db.session.scalars(select(Attribute.key)))
    for order, (key, name, description) in enumerate(defaults.DEFAULT_ATTRIBUTES):
        if key not in existing:
            db.session.add(Attribute(key=key, name=name, description=description, sort_order=order))


def _seed_titles() -> None:
    """Cria os títulos padrão que faltarem (também em bancos antigos). Não faz commit."""
    existing_keys = set(db.session.scalars(select(Title.key).where(Title.key.is_not(None))))
    existing_names = {n.lower() for n in db.session.scalars(select(Title.name))}
    added = False
    for order, (key, name, description, rule, threshold) in enumerate(defaults.DEFAULT_TITLES):
        if key in existing_keys or name.lower() in existing_names:
            continue  # já existe (ou você criou um título com o mesmo nome: fica o seu)
        db.session.add(Title(key=key, name=name, description=description, rule=rule, threshold=threshold,
                             sort_order=order, unlocked_at=time.now() if key == "start" else None))
        existing_names.add(name.lower())
        added = True
    # Título escrito à mão na versão antiga (campo livre): vira um título seu, para não sumir.
    hunter = db.session.scalar(select(Hunter).order_by(Hunter.id))
    if hunter and hunter.title.strip() and hunter.title.strip().lower() not in existing_names:
        db.session.add(Title(name=hunter.title.strip()[:80], description="Seu título anterior.", rule="custom",
                             threshold=0, unlocked_at=time.now(), sort_order=len(defaults.DEFAULT_TITLES)))
        added = True
    if added:
        db.session.flush()


def db_commit() -> None:
    """Salva desbloqueios feitos por check_titles() fora de award_xp (ex.: ao abrir o perfil)."""
    db.session.commit()
