"""Arena dos Hunters: ranking entre as contas, perfis públicos e privacidade.

Só lê dados (nunca altera nada de outro usuário). Para cada conta, os números são calculados "como
aquele usuário" (tenancy.as_user), usando as APIs públicas dos outros módulos. Dados financeiros,
memórias privadas, tokens e e-mails nunca entram aqui.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable

from app.core import accounts, settings, time
from app.core.errors import NotFoundError
from app.core.tenancy import as_user, current_user_id
from app.modules.hunter import services as hunter
from app.modules.quests import constants as quest_constants
from app.modules.quests import services as quests

from . import integrity

PRIVACY_KEY = "arena.privacy"
# O que cada jogador mostra para os outros. Padrão: aparece no ranking com números e atributos;
# títulos das missões, histórico e feed também, e dá para desligar cada um.
PRIVACY_OPTIONS: dict[str, str] = {
    "listed": "Aparecer na Arena (ranking)",
    "attributes": "Mostrar atributos e status",
    "quests": "Mostrar minhas missões diárias e semanais (títulos)",
    "achievements": "Mostrar conquistas",
    "history": "Mostrar histórico recente de evolução",
    "loadout": "Mostrar equipamentos e sombras",
    "feed": "Publicar minhas atividades no feed dos Hunters",
}
DEFAULT_PRIVACY = {key: True for key in PRIVACY_OPTIONS}
SORTS = {"xp_week": "XP na semana", "total_xp": "XP total", "hours_week": "Horas na semana", "xp_today": "XP hoje"}

# Outros módulos acrescentam informações ao cartão (ex.: sombras recrutadas, equipamentos).
_CARD_EXTENSIONS: list[Callable[[], dict]] = []


def register_card_extension(provider: Callable[[], dict]) -> None:
    if provider not in _CARD_EXTENSIONS:
        _CARD_EXTENSIONS.append(provider)


def privacy() -> dict[str, bool]:
    saved = settings.get_setting(PRIVACY_KEY, {}) or {}
    return {key: bool(saved.get(key, default)) for key, default in DEFAULT_PRIVACY.items()}


def set_privacy(values: dict[str, bool]) -> None:
    settings.set_setting(PRIVACY_KEY, {key: bool(values.get(key)) for key in PRIVACY_OPTIONS})


@dataclass
class HunterCard:
    user_id: int
    name: str
    avatar_url: str
    rank_code: str
    rank_name: str
    rank_color: str
    level: int
    total_xp: int
    xp_today: int
    xp_week: int
    minutes_today: int
    minutes_week: int
    missions_total: int
    missions_today: int
    avg_minutes: float
    top_specialty: str
    integrity: integrity.Integrity
    is_me: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def hours_today(self) -> float:
        return round(self.minutes_today / 60, 1)

    @property
    def hours_week(self) -> float:
        return round(self.minutes_week / 60, 1)


def _card(user_id: int, today: date) -> HunterCard:
    status = hunter.get_status()
    week_start = today - timedelta(days=6)
    report = quests.activity_report(week_start, today)
    extra: dict = {}
    for provider in _CARD_EXTENSIONS:
        extra.update(provider())
    return HunterCard(
        user_id=user_id,
        name=status.name,
        avatar_url=extra.get("avatar_url") or status.avatar_url,
        rank_code=status.rank.code if status.rank else "?",
        rank_name=status.rank.name if status.rank else "",
        rank_color=status.rank.color if status.rank else "#8b5cf6",
        level=status.progress.level,
        total_xp=status.progress.total_xp,
        xp_today=hunter.xp_between(today, today),
        xp_week=hunter.xp_between(week_start, today),
        minutes_today=report.minutes_by_day.get(today, 0),
        minutes_week=report.minutes,
        missions_total=quests.completed_count(),
        missions_today=report.completions_by_day.get(today, 0),
        avg_minutes=report.avg_minutes,
        top_specialty=quest_constants.SPECIALTIES.get(report.top_specialty or "", "—"),
        integrity=integrity.evaluate(report, hunter.xp_from_source_between("quest", week_start, today)),
        extra=extra,
    )


def leaderboard(sort: str = "xp_week", today: date | None = None) -> list[HunterCard]:
    today = today or time.today()
    me = current_user_id()
    cards = []
    for user_id in accounts.all_user_ids():
        with as_user(user_id):
            if user_id != me and not privacy()["listed"]:
                continue
            card = _card(user_id, today)
        card.is_me = user_id == me
        cards.append(card)
    key = {"total_xp": lambda c: c.total_xp, "hours_week": lambda c: c.minutes_week,
           "xp_today": lambda c: c.xp_today}.get(sort, lambda c: c.xp_week)
    cards.sort(key=lambda c: (key(c), c.total_xp), reverse=True)
    return cards


@dataclass
class PublicProfile:
    card: HunterCard
    shows: dict[str, bool]
    attributes: list = field(default_factory=list)
    daily: list = field(default_factory=list)
    weekly: list = field(default_factory=list)
    achievements: list = field(default_factory=list)
    history: list = field(default_factory=list)
    week: list = field(default_factory=list)  # (dia, minutos, missões)


def public_profile(user_id: int, today: date | None = None) -> PublicProfile:
    """Perfil de outro Hunter, só com o que ele escolheu mostrar (o próprio jogador vê tudo)."""
    today = today or time.today()
    me = current_user_id()
    user = accounts.get_user(user_id)
    if user is None or not user.active:
        raise NotFoundError("Hunter não encontrado.")
    with as_user(user_id):
        shows = privacy() if user_id != me else dict(DEFAULT_PRIVACY)
        if not shows["listed"]:
            raise NotFoundError("Este Hunter não aparece na Arena.")
        card = _card(user_id, today)
        card.is_me = user_id == me
        profile = PublicProfile(card=card, shows=shows)
        report = quests.activity_report(today - timedelta(days=6), today)
        profile.week = [(d, report.minutes_by_day[d], report.completions_by_day[d]) for d in report.days]
        if shows["attributes"]:
            profile.attributes = hunter.get_status().attributes
        if shows["quests"]:
            profile.daily = quests.quests_for_period("daily")
            profile.weekly = quests.quests_for_period("weekly")
        if shows["achievements"]:
            profile.achievements = [t for t in hunter.list_titles() if t.unlocked]
        if shows["history"]:
            profile.history = [(e.created_at, e.amount, _public_description(e.description))
                               for e in hunter.recent_events(limit=12)]
    return profile


def _public_description(text: str) -> str:
    """Histórico público: sem detalhes que possam ser pessoais além do título da missão."""
    return text[:120]
