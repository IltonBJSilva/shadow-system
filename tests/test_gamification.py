from datetime import timedelta

from app.core import time
from app.modules.gamification import rules as r
from app.modules.gamification import services as gamification
from app.modules.gamification.rules import Rules
from app.modules.habits import services as habits
from app.modules.hunter import progression
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


def _only(**overrides) -> None:
    """Liga só as regras pedidas, zerando as outras, para medir cada uma isolada."""
    base = Rules(first_quest_bonus_xp=0, daily_combo_percent=0, daily_combo_min_xp=0, early_bonus_percent=0,
                 streak_tiers=[], penalty_xp_percent=0, penalty_quest_enabled=False)
    for key, value in overrides.items():
        setattr(base, key, value)
    gamification.save_rules(base)


# ---------- regras puras ----------

def test_percent_rounds_up():
    assert r.percent_of(15, 10) == 2 and r.percent_of(0, 50) == 0


def test_streak_tiers():
    tiers = [(7, 25), (30, 50)]
    assert r.streak_bonus_percent(6, tiers) == 0
    assert r.streak_bonus_percent(7, tiers) == 25
    assert r.streak_bonus_percent(45, tiers) == 50


def test_penalty_never_drops_a_level():
    assert r.penalty_amount(100, 10, xp_into_level=50) == 10
    assert r.penalty_amount(100, 10, xp_into_level=3) == 3
    assert r.penalty_amount(100, 10, xp_into_level=0) == 0


def test_rules_keep_defaults_for_missing_fields():
    rules = Rules.from_dict({"penalty_xp_percent": 30})
    assert rules.penalty_xp_percent == 30 and rules.first_quest_bonus_xp == 10


# ---------- bônus ----------

def test_first_quest_of_the_day_bonus_only_once(app):
    _only(first_quest_bonus_xp=10)
    a = quests.create_quest(QuestInput(title="A", xp_reward=50))
    b = quests.create_quest(QuestInput(title="B", xp_reward=50))
    result = quests.complete_quest(a.id)
    assert any("primeira quest" in m for m, _ in result.extra)
    quests.complete_quest(b.id)
    assert hunter.get_hunter().total_xp == 110


def test_early_completion_bonus(app):
    _only(early_bonus_percent=10)
    quest = quests.create_quest(QuestInput(title="Cedo", xp_reward=100, due_date=time.today() + timedelta(days=2)))
    quests.complete_quest(quest.id)
    assert hunter.get_hunter().total_xp == 110


def test_daily_combo_when_all_dailies_done(app):
    _only(daily_combo_percent=20, daily_combo_min_xp=5)
    today = time.today()
    a = quests.create_quest(QuestInput(title="Treino", quest_type="daily", recurrence="daily", due_date=today,
                                       xp_reward=50))
    b = quests.create_quest(QuestInput(title="Estudo", quest_type="daily", recurrence="daily", due_date=today,
                                       xp_reward=50))
    first = quests.complete_quest(a.id)
    assert not any("COMBO" in m for m, _ in first.extra)
    second = quests.complete_quest(b.id)
    assert any("COMBO" in m and c == "bonus" for m, c in second.extra)
    assert hunter.get_hunter().total_xp == 120  # 50 + 50 + 20% de 100


def test_habit_streak_bonus_and_refund(app):
    _only(streak_tiers=[(3, 50)])
    habit = habits.save_habit("Ler", "", 10, [])
    today = time.today()
    habits.check_in(habit.id, today - timedelta(days=2))
    habits.check_in(habit.id, today - timedelta(days=1))
    result = habits.check_in(habit.id)
    assert any("Sequência de 3 dias" in m for m, _ in result.extra)
    assert hunter.get_hunter().total_xp == 35
    habits.undo_check_in(habit.id)
    assert hunter.get_hunter().total_xp == 20


def test_bonuses_can_be_turned_off(app):
    gamification.save_rules(Rules(bonuses_enabled=False))
    quest = quests.create_quest(QuestInput(title="A", xp_reward=50))
    quests.complete_quest(quest.id)
    assert hunter.get_hunter().total_xp == 50


# ---------- punições ----------

def _give_xp(amount: int) -> None:
    hunter.award_xp(amount, source="manual", description="setup")


def test_missed_recurring_quest_costs_xp_and_spawns_penalty_quest(app):
    _only(penalty_xp_percent=20, penalty_quest_enabled=True)
    _give_xp(progression.total_xp_for_level(3) + 40)  # nível 3 com 40 XP no nível
    today = time.today()
    quests.create_quest(QuestInput(title="Treinar", recurrence="daily", due_date=today - timedelta(days=1),
                                   xp_reward=50))
    count, messages = quests.roll_over_with_messages(today)
    assert count == 1 and messages[0][1] == "penalty"
    assert hunter.get_status().progress.xp_into_level == 30  # -20% de 50
    penalty = next(q for q in quests.quests_for_today(today) if r.is_penalty_quest(q.title))
    assert penalty.quest_type == "emergency" and penalty.xp_reward == 10

    quests.complete_quest(penalty.id)  # redenção: devolve o XP perdido
    assert hunter.get_status().progress.xp_into_level == 40


def test_penalty_never_costs_a_level(app):
    _only(penalty_xp_percent=100)
    _give_xp(progression.total_xp_for_level(2) + 5)
    quests.create_quest(QuestInput(title="Grande", recurrence="daily", due_date=time.today() - timedelta(days=1),
                                   xp_reward=200))
    quests.roll_over_recurring()
    status = hunter.get_status()
    assert status.progress.level == 2 and status.progress.xp_into_level == 0


def test_missed_penalty_quest_is_not_punished_again(app):
    _only(penalty_xp_percent=50, penalty_quest_enabled=True)
    quests.create_quest(QuestInput(title=f"{r.PENALTY_PREFIX} Antiga", recurrence="daily",
                                   due_date=time.today() - timedelta(days=1), xp_reward=50))
    _, messages = quests.roll_over_with_messages()
    assert messages == []


def test_penalties_can_be_turned_off(app):
    gamification.save_rules(Rules(penalties_enabled=False))
    _give_xp(80)
    quests.create_quest(QuestInput(title="X", recurrence="daily", due_date=time.today() - timedelta(days=1)))
    quests.roll_over_recurring()
    assert hunter.get_hunter().total_xp == 80
    assert not any(r.is_penalty_quest(q.title) for q in quests.quests_for_today())


# ---------- telas ----------

def test_dashboard_shows_penalty_popup(client):
    _only(penalty_xp_percent=10, penalty_quest_enabled=True)
    quests.create_quest(QuestInput(title="Meditar", recurrence="daily", due_date=time.today() - timedelta(days=1)))
    html = client.get("/").get_data(as_text=True)
    assert 'data-category="penalty"' in html and "Penalty Zone" in html


def test_settings_page_saves_rules(client):
    client.post("/gamification/", data={
        "bonuses_enabled": "on", "first_quest_bonus_xp": "15", "early_bonus_percent": "5",
        "daily_combo_percent": "30", "daily_combo_min_xp": "10", "tier_days_0": "5", "tier_percent_0": "20",
        "penalty_xp_percent": "0",
    })
    rules = gamification.get_rules()
    assert rules.first_quest_bonus_xp == 15 and rules.streak_tiers == [(5, 20)]
    assert rules.penalties_enabled is False and rules.penalty_quest_enabled is False
    assert client.get("/gamification/").status_code == 200


def test_invalid_rule_value_is_rejected(client):
    client.post("/gamification/", data={"first_quest_bonus_xp": "muito", "penalty_xp_percent": "10"})
    assert gamification.get_rules().first_quest_bonus_xp == 10
