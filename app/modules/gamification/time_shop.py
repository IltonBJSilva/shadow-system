"""Loja do Tempo: moedas ganhas com missões viram proteção contra a Zona de Falha.

- Moedas: 1 a cada 10 XP base de missão concluída (mínimo 1), até 50 por dia. Penalty Quests não rendem.
- Escudo do Tempo: absorve a próxima punição (sem perda de XP e sem Penalty Quest). Até 3 guardados.
- Ampulheta: adia em 1 dia o prazo de uma missão ativa que vence hoje ou amanhã.
Cada moeda ganha ou gasta vira uma linha no extrato (auditável); o saldo é a soma do extrato.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import func, select

from app.core import settings, time
from app.core.errors import DomainError
from app.extensions import db
from app.modules.quests import services as quests

from .models import CoinTransaction

COINS_PER_XP = 10
DAILY_COIN_CAP = 50
SHIELDS_KEY = "gamification.shields"
MAX_SHIELDS = 3


@dataclass(frozen=True)
class ShopItem:
    key: str
    name: str
    price: int
    icon: str
    description: str


ITEMS: dict[str, ShopItem] = {i.key: i for i in [
    ShopItem("shield", "Escudo do Tempo", 50, "🛡️",
             "Absorve a próxima punição da Zona de Falha: sem perda de XP e sem Penalty Quest."),
    ShopItem("hourglass", "Ampulheta", 30, "⏳", "Adia em 1 dia o prazo de uma missão que vence hoje ou amanhã."),
]}


def balance() -> int:
    return int(db.session.scalar(select(func.coalesce(func.sum(CoinTransaction.amount), 0))) or 0)


def earned_today(today: date | None = None) -> int:
    start = datetime.combine(today or time.today(), datetime.min.time())
    return int(db.session.scalar(select(func.coalesce(func.sum(CoinTransaction.amount), 0)).where(
        CoinTransaction.amount > 0, CoinTransaction.created_at >= start,
        CoinTransaction.created_at < start + timedelta(days=1))) or 0)


def earn_for_quest(quest_id: int, base_xp: int) -> int:
    """Moedas pela missão concluída (uma vez por missão, com teto diário). Sem commit."""
    if base_xp <= 0:
        return 0
    already = db.session.scalar(select(CoinTransaction.id).where(CoinTransaction.source == "quest",
                                                                 CoinTransaction.source_id == quest_id))
    if already:
        return 0
    coins = min(max(1, base_xp // COINS_PER_XP), max(0, DAILY_COIN_CAP - earned_today()))
    if coins:
        db.session.add(CoinTransaction(amount=coins, reason="Missão concluída", source="quest", source_id=quest_id))
    return coins


def shields() -> int:
    return int(settings.get_setting(SHIELDS_KEY, 0) or 0)


def buy(item_key: str, quest_id: int | None = None) -> str:
    item = ITEMS.get(item_key)
    if item is None:
        raise DomainError("Item desconhecido.")
    if balance() < item.price:
        raise DomainError(f"Moedas insuficientes: {item.name} custa {item.price}.")
    if item.key == "shield":
        if shields() >= MAX_SHIELDS:
            raise DomainError(f"Você já guarda {MAX_SHIELDS} escudos.")
        settings.set_setting(SHIELDS_KEY, shields() + 1)
        message = "Escudo do Tempo guardado. Ele absorve a próxima punição."
    else:
        if not quest_id:
            raise DomainError("Escolha a missão para adiar.")
        quest = quests.postpone_quest(quest_id, days=1, max_days_ahead=1)
        message = f"Ampulheta usada: “{quest.title}” agora vence em {quest.due_date:%d/%m}."
        quest_id = quest.id
    db.session.add(CoinTransaction(amount=-item.price, reason=item.name, source=item.key, source_id=quest_id))
    db.session.commit()
    return message


def use_shield() -> bool:
    """Consome um escudo, se houver (chamado quando uma punição ia ser aplicada). Sem commit próprio."""
    count = shields()
    if count <= 0:
        return False
    settings.set_setting(SHIELDS_KEY, count - 1)
    return True


def statement(limit: int = 20) -> list[CoinTransaction]:
    return list(db.session.scalars(select(CoinTransaction).order_by(CoinTransaction.created_at.desc(),
                                                                  CoinTransaction.id.desc()).limit(limit)))


def postponable() -> list:
    """Missões ativas que vencem hoje ou amanhã (as que a Ampulheta pode adiar)."""
    today = time.today()
    return [q for q in quests.quests_due_between(today, today + timedelta(days=1))
            if q.status in ("pending", "in_progress") and q.quest_type != "emergency"]
