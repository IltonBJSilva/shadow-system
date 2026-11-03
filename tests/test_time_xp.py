"""XP por tempo: fórmula, repetição, limites diários, bônus com teto e tempo sem sobreposição."""
from datetime import date, datetime, timedelta

import pytest

from app.core.errors import DomainError
from app.extensions import db as _db
from app.modules.hunter import progression
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.quests import timeline
from app.modules.quests.models import ActivitySession
from app.modules.quests.services import QuestInput


def _quest(title="Estudar", minutes=30, difficulty=3, category_id=None, **kw):
    return quests.create_quest(QuestInput(title=title, estimated_minutes=minutes, difficulty=difficulty,
                                          category_id=category_id, **kw))


@pytest.mark.parametrize("minutes,expected", [(5, 5), (15, 15), (30, 30), (45, 45), (60, 60), (90, 90), (120, 120)])
def test_base_xp_follows_time(minutes, expected):
    assert progression.time_xp(minutes, difficulty=3).base == expected


def test_difficulty_and_category_adjust_moderately():
    assert progression.time_xp(60, difficulty=5).base == 78  # x1,3
    assert progression.time_xp(60, difficulty=1).base == 48  # x0,8
    assert progression.time_xp(60, 3, category_multiplier=5).base == 72  # categoria limitada a x1,2
    quote = progression.time_xp(45, difficulty=4, category_multiplier=1.1)
    assert sum(line.amount for line in quote.lines) == quote.base  # o "por quê" soma o total


def test_minutes_are_clamped():
    assert progression.time_xp(1).base == progression.MIN_MINUTES
    assert progression.time_xp(10_000).base == progression.MAX_MINUTES


def test_completion_records_immutable_breakdown_and_session(app):
    quest = _quest(minutes=45)
    result = quests.complete_quest(quest.id, actual_minutes=50)
    assert result.amount == 45
    event, lines = hunter.event_for("quest", quest.id)
    assert (event.base_amount, event.bonus_amount) == (45, 0)
    assert lines[0].label.startswith("Tempo estimado: 45 min")
    session = _db.session.query(ActivitySession).one()
    assert session.minutes == 50 and session.credited_minutes == 45
    assert (session.ended_at - session.started_at) == timedelta(minutes=50)


def test_editing_time_after_completion_is_blocked(app):
    quest = _quest(minutes=30)
    quests.complete_quest(quest.id)
    before = hunter.get_hunter().total_xp
    with pytest.raises(DomainError):
        quests.update_quest(quest.id, QuestInput(title="Estudar", estimated_minutes=120))
    quests.update_quest(quest.id, QuestInput(title="Estudar (renomeada)", estimated_minutes=30))
    assert hunter.get_hunter().total_xp == before  # nada retroativo


def test_repeating_same_task_has_diminishing_returns(app):
    gains = [quests.complete_quest(_quest(title="Flexão", minutes=10).id).amount for _ in range(6)]
    assert gains == [10, 10, 5, 2, 0, 0]


def test_daily_credited_minutes_are_capped(app):
    total = 0
    for i in range(3):
        total += quests.complete_quest(_quest(title=f"Bloco {i}", minutes=progression.MAX_MINUTES).id).amount
    assert total == progression.DAILY_MINUTES_CAP  # 3 x 8 h pedidas, 16 h creditadas
    extra = quests.complete_quest(_quest(title="Mais uma", minutes=30).id)
    assert extra.amount == 0


def test_bonus_providers_are_capped_per_mission_and_day(app):
    def generous(context):
        return [("Bônus de teste", 1000)] if context.specialty == "studies" else []

    hunter.register_bonus_provider(generous)
    try:
        category = quests.save_category("Estudos", "#22d3ee", [], specialty="studies")
        first = quests.complete_quest(_quest(title="A", minutes=60, category_id=category.id).id)
        assert first.amount == 60 + progression.BONUS_CAP_PER_MISSION
        other = quests.complete_quest(_quest(title="Sem bônus", minutes=60).id)
        assert other.amount == 60
        given = progression.BONUS_CAP_PER_MISSION
        for i in range(10):
            given += quests.complete_quest(_quest(title=f"E{i}", minutes=60, category_id=category.id).id).amount - 60
        assert given == progression.BONUS_CAP_PER_DAY
    finally:
        hunter._BONUS_PROVIDERS.remove(generous)


def test_overlapping_intervals_count_once_and_day_caps_at_24h():
    day = date(2026, 11, 3)
    at = lambda h, m=0: datetime.combine(day, datetime.min.time()) + timedelta(hours=h, minutes=m)  # noqa: E731
    intervals = [(at(9), at(10)), (at(9, 30), at(11)), (at(14), at(15))]
    assert timeline.raw_minutes_on(day, intervals) == 210
    assert timeline.minutes_on(day, intervals) == 180
    huge = [(at(0) - timedelta(hours=5), at(0) + timedelta(hours=30))]
    assert timeline.minutes_on(day, huge) == 24 * 60


def test_activity_minutes_merges_simultaneous_tasks(app):
    quests.complete_quest(_quest(title="X", minutes=60).id)
    quests.complete_quest(_quest(title="Y", minutes=60).id)  # terminou no mesmo instante: mesmo intervalo
    assert quests.activity_minutes(date.today()) in (60, 61)


def test_legacy_quest_without_minutes_keeps_fixed_xp(app):
    quest = quests.create_quest(QuestInput(title="Antiga", xp_reward=40))
    assert quests.complete_quest(quest.id).amount == 40


def test_actual_minutes_are_validated(app):
    with pytest.raises(DomainError):
        quests.complete_quest(_quest().id, actual_minutes=5000)
