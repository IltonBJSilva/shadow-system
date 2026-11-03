"""Feed de atividades dos Hunters.

Os outros módulos publicam eventos (quest.completed, hunter.leveled_up, shadows.recruited...) e o feed
grava um post só se o jogador permitir ("Publicar minhas atividades no feed", em Arena > Privacidade).
Na leitura a permissão é conferida de novo: desligar esconde também os posts antigos. Fotos nunca são
publicadas sozinhas: só memórias que o jogador marcar como públicas.
"""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from app.core import accounts, events
from app.core.tenancy import as_user
from app.extensions import db
from app.modules.hunter import services as hunter
from app.modules.quests import constants as quest_constants

from . import services
from .models import ActivityPost

FEED_LIMIT = 60


def post(kind: str, text: str, *, icon: str = "◆", xp: int = 0, reward: str = "", specialty: str = "",
         memory_id: int | None = None) -> None:
    if not services.privacy()["feed"]:
        return
    db.session.add(ActivityPost(kind=kind, text=text[:240], icon=icon[:8], xp=max(0, xp), reward=reward[:120],
                                specialty=specialty, memory_id=memory_id))


@dataclass(frozen=True)
class FeedItem:
    user_id: int
    name: str
    avatar_url: str
    rank_code: str
    rank_color: str
    kind: str
    icon: str
    text: str
    specialty: str
    xp: int
    reward: str
    created_at: datetime
    memory_id: int | None


def recent(limit: int = FEED_LIMIT, kind: str | None = None) -> list[FeedItem]:
    query = select(ActivityPost).execution_options(all_users=True).order_by(ActivityPost.created_at.desc())
    if kind:
        query = query.where(ActivityPost.kind == kind)
    rows = db.session.scalars(query.limit(limit * 2)).all()
    authors: dict[int, tuple | None] = {}
    items = []
    for row in rows:
        if row.user_id not in authors:
            authors[row.user_id] = _author(row.user_id)
        author = authors[row.user_id]
        if author is None:
            continue
        name, avatar, code, color = author
        items.append(FeedItem(row.user_id, name, avatar, code, color, row.kind, row.icon, row.text,
                              quest_constants.SPECIALTIES.get(row.specialty, ""), row.xp, row.reward,
                              row.created_at, row.memory_id))
        if len(items) >= limit:
            break
    return items


def _author(user_id: int):
    user = accounts.get_user(user_id)
    if user is None or not user.active:
        return None
    with as_user(user_id):
        shows = services.privacy()
        if not (shows["listed"] and shows["feed"]):
            return None
        status = hunter.get_status()
        return (status.name, status.avatar_url, status.rank.code if status.rank else "?",
                status.rank.color if status.rank else "#8b5cf6")


# ---------- O que vira post ----------

@events.subscribe("quest.completed")
def _quest_completed(quest, **_):
    if quest.quest_type == "emergency":
        return None  # Penalty Quests ficam fora do feed
    xp = hunter.event_for("quest", quest.id)
    post("quest", f"concluiu a missão “{quest.title}”", icon="⚔", xp=xp[0].amount if xp else quest.xp_reward,
         specialty=quest.specialty)
    return None


@events.subscribe("hunter.leveled_up")
def _leveled_up(level, rank=None, **_):
    post("level", f"subiu para o nível {level}", icon="⬆")
    if rank is not None:
        post("rank", f"alcançou o {rank.name}", icon="♛", reward=f"Rank {rank.code}")
    return None


@events.subscribe("hunter.title_unlocked")
def _title(name, icon="🏅", reward_xp=0, **_):
    post("title", f"desbloqueou a conquista “{name}”", icon=icon, xp=reward_xp, reward=name)
    return None


@events.subscribe("shadows.recruited")
def _shadow(shadow, **_):
    post("shadow", f"recrutou a sombra {shadow.name}, {shadow.title}", icon=shadow.icon, reward=shadow.name,
         specialty=shadow.specialties[0])
    return None


@events.subscribe("character.item_acquired")
def _item(item, **_):
    post("item", f"conquistou {item.name} ({item.rarity_label})", icon=item.icon, reward=item.name,
         specialty=item.specialty or "")
    return None

