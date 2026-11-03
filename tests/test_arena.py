"""Arena: ranking entre contas, privacidade, perfil público e indicador de integridade."""
from datetime import date, datetime, timedelta

from app.core import accounts
from app.core.tenancy import as_user
from app.extensions import db as _db
from app.modules.arena import integrity, services as arena
from app.modules.quests import services as quests
from app.modules.quests.models import ActivitySession, Quest
from app.modules.quests.services import ActivityReport, QuestInput


def _tester(email="rival@example.com"):
    user, code = accounts.invite_tester(email, "Rival")
    accounts.accept_invite(code, "Rival", "12345678")
    return user


def _report(**overrides):
    days = [date(2026, 11, d) for d in range(1, 8)]
    base = dict(days=days, completions_by_day={d: 3 for d in days}, minutes_by_day={d: 180 for d in days},
                raw_minutes_by_day={d: 180 for d in days}, short_by_day={d: 0 for d in days},
                max_repeat_by_day={d: 1 for d in days}, bursts=0, edits_after_xp=0, avg_minutes=60, top_specialty="studies")
    base.update(overrides)
    return ActivityReport(**base)


def test_normal_week_is_trusted():
    result = integrity.evaluate(_report(), xp_week=1200)
    assert (result.score, result.level, result.reasons) == (100, "ok", [])


def test_one_24h_day_alone_is_not_an_accusation():
    days = [date(2026, 11, d) for d in range(1, 8)]
    minutes = {d: 180 for d in days} | {days[0]: 24 * 60}
    result = integrity.evaluate(_report(minutes_by_day=minutes, raw_minutes_by_day=minutes), xp_week=2000)
    assert result.level == "ok" and result.reasons


def test_many_signals_together_need_review():
    days = [date(2026, 11, d) for d in range(1, 8)]
    result = integrity.evaluate(_report(
        short_by_day={d: 40 for d in days}, bursts=25, max_repeat_by_day={d: 9 for d in days},
        edits_after_xp=6, raw_minutes_by_day={d: 600 for d in days}), xp_week=5000)
    assert result.level == "review" and len(result.reasons) >= 4


def test_leaderboard_lists_all_users_with_hours(app):
    quests.complete_quest(quests.create_quest(QuestInput(title="Estudar", estimated_minutes=90)).id)
    rival = _tester()
    with as_user(rival.id):
        quests.complete_quest(quests.create_quest(QuestInput(title="Treinar", estimated_minutes=60)).id)
    cards = arena.leaderboard("total_xp")
    assert [c.name for c in cards][:2] and len(cards) == 2
    me = next(c for c in cards if c.is_me)
    assert me.hours_today == 1.5 and me.missions_today == 1 and me.integrity.level == "ok"
    other = next(c for c in cards if not c.is_me)
    assert other.hours_today == 1.0


def test_unlisted_hunter_is_hidden_and_profile_blocked(app, client):
    rival = _tester()
    with as_user(rival.id):
        arena.set_privacy({k: k != "listed" for k in arena.PRIVACY_OPTIONS})
    assert all(c.user_id != rival.id for c in arena.leaderboard())
    assert client.get(f"/arena/{rival.id}").status_code == 404


def test_public_profile_respects_choices(app, client):
    rival = _tester()
    with as_user(rival.id):
        quests.create_quest(QuestInput(title="Ler 20 páginas", quest_type="daily", estimated_minutes=20))
        arena.set_privacy({**arena.DEFAULT_PRIVACY, "quests": False})
    page = client.get(f"/arena/{rival.id}").get_data(as_text=True)
    assert "Rival" in page and "Ler 20 páginas" not in page
    with as_user(rival.id):
        arena.set_privacy(arena.DEFAULT_PRIVACY)
    assert "Ler 20 páginas" in client.get(f"/arena/{rival.id}").get_data(as_text=True)


def test_arena_page_renders(app, client):
    _tester()
    page = client.get("/arena/").get_data(as_text=True)
    assert "Arena dos Hunters" in page and "Integridade" not in page or "Íntegro" in page


def test_activity_report_counts_bursts_and_edits(app):
    now = datetime.now()
    for i in range(5):
        quest = quests.create_quest(QuestInput(title=f"Rápida {i}", estimated_minutes=5))
        quests.complete_quest(quest.id)
    report = quests.activity_report(date.today(), date.today())
    assert report.bursts >= 4 and report.short_by_day[date.today()] == 5
    assert now  # o relógio usado é o do servidor (ActivitySession.ended_at)
    assert _db.session.query(ActivitySession).count() == 5
    assert _db.session.query(Quest).filter(Quest.status == "completed").count() == 5
    assert timedelta(minutes=5)
