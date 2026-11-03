"""Loja do Tempo: moedas por missão (com teto), escudo contra punição e ampulheta para adiar prazo."""
from datetime import timedelta

import pytest

from app.core import time
from app.core.errors import DomainError
from app.extensions import db as _db
from app.modules.gamification import time_shop
from app.modules.gamification.models import CoinTransaction, QuestFailure
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


def _complete(title, minutes=60):
    return quests.complete_quest(quests.create_quest(QuestInput(title=title, estimated_minutes=minutes)).id)


def _give(coins):
    _db.session.add(CoinTransaction(amount=coins, reason="teste", source="test"))
    _db.session.commit()


def test_missions_earn_coins_with_daily_cap(app):
    _complete("Estudar", 60)
    assert time_shop.balance() == 6
    for i in range(10):
        _complete(f"Bloco {i}", 120)
    assert time_shop.earned_today() == time_shop.DAILY_COIN_CAP


def test_shield_absorbs_next_penalty(app):
    _give(60)
    time_shop.buy("shield")
    assert time_shop.balance() == 10 and time_shop.shields() == 1
    yesterday = time.today() - timedelta(days=1)
    quests.create_quest(QuestInput(title="Treino diário", quest_type="daily", recurrence="daily",
                                   due_date=yesterday, estimated_minutes=60))
    hunter.award_xp(500, source="test", description="saldo")
    _db.session.commit()
    before = hunter.get_hunter().total_xp
    count, messages = quests.roll_over_with_messages()
    assert any("Escudo do Tempo" in m for m, _ in messages)
    assert hunter.get_hunter().total_xp == before and time_shop.shields() == 0
    assert _db.session.query(QuestFailure).one().penalty_xp == 0


def test_cannot_buy_without_coins_or_beyond_limit(app):
    with pytest.raises(DomainError):
        time_shop.buy("shield")
    _give(500)
    for _ in range(time_shop.MAX_SHIELDS):
        time_shop.buy("shield")
    with pytest.raises(DomainError):
        time_shop.buy("shield")


def test_hourglass_postpones_quest_due_soon(app):
    _give(30)
    quest = quests.create_quest(QuestInput(title="Entrega", due_date=time.today(), estimated_minutes=30))
    far = quests.create_quest(QuestInput(title="Depois", due_date=time.today() + timedelta(days=5), estimated_minutes=30))
    with pytest.raises(DomainError):
        time_shop.buy("hourglass", far.id)
    time_shop.buy("hourglass", quest.id)
    assert quests.get_quest(quest.id).due_date == time.today() + timedelta(days=1)
    assert time_shop.balance() == 0


def test_shop_page(app, client):
    _complete("Ler")
    page = client.get("/gamification/loja").get_data(as_text=True)
    assert "Escudo do Tempo" in page and "Missão concluída" in page
