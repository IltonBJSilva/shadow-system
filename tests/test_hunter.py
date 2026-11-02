from datetime import timedelta

import pytest

from app.core import time
from app.core.errors import DomainError
from app.extensions import db
from app.modules.hunter import progression, services
from app.modules.hunter.models import Rank


# ---------- progressão (funções puras) ----------

def test_xp_curve_is_linear():
    assert progression.xp_to_next_level(1) == 100
    assert progression.xp_to_next_level(2) == 150
    assert progression.total_xp_for_level(1) == 0
    assert progression.total_xp_for_level(3) == 250


@pytest.mark.parametrize("total_xp,level,into", [(0, 1, 0), (99, 1, 99), (100, 2, 0), (260, 3, 10)])
def test_level_progress(total_xp, level, into):
    progress = progression.level_progress(total_xp)
    assert (progress.level, progress.xp_into_level) == (level, into)


def test_level_progress_matches_total_for_level():
    for level in range(1, 40):
        assert progression.level_progress(progression.total_xp_for_level(level)).level == level


def test_rank_for_level_picks_highest_reached():
    ranks = [Rank(code="E", min_level=1), Rank(code="D", min_level=10), Rank(code="C", min_level=20)]
    assert progression.rank_for_level(9, ranks).code == "E"
    assert progression.rank_for_level(10, ranks).code == "D"
    assert progression.rank_for_level(500, ranks).code == "C"


# ---------- serviços ----------

def test_get_hunter_seeds_defaults(app):
    status = services.get_status()
    assert status.progress.level == 1
    assert status.rank.code == "E"
    assert len(status.attributes) == 10  # 8 originais + Wisdom e Charisma


def test_award_xp_levels_up_and_records_history(app):
    strength = next(a for a in services.list_attributes() if a.key == "strength")
    result = services.award_xp(120, source="manual", description="Treino", attribute_ids=[strength.id],
                               attribute_points=3)
    db.session.commit()
    assert result.leveled_up and result.new_level == 2
    assert services.get_status().progress.xp_into_level == 20
    assert next(a for a in services.list_attributes() if a.key == "strength").points == 3
    event = services.recent_events()[0]
    assert event.amount == 120 and event.gains[0].points == 3


def test_award_xp_announces_new_rank(app):
    services.get_hunter()
    result = services.award_xp(progression.total_xp_for_level(10), source="manual", description="Boost")
    assert result.new_rank is not None and result.new_rank.code == "D"


def test_negative_award_never_goes_below_zero(app):
    services.award_xp(30, source="manual", description="ganho")
    result = services.award_xp(-100, source="manual", description="estorno")
    db.session.commit()
    assert result.amount == -30
    assert services.get_hunter().total_xp == 0


def test_xp_by_day_fills_missing_days(app):
    services.award_xp(40, source="manual", description="hoje")
    db.session.commit()
    series = services.xp_by_day(time.today(), days=7)
    assert len(series) == 7
    assert series[-1] == (time.today(), 40)
    assert series[0] == (time.today() - timedelta(days=6), 0)


def test_rank_rules(app):
    services.get_hunter()
    with pytest.raises(DomainError):
        services.save_rank("X", "Duplicado", 10, "#ffffff")  # nível 10 já é do rank D
    initial = next(r for r in services.list_ranks() if r.min_level == 1)
    with pytest.raises(DomainError):
        services.delete_rank(initial.id)
    custom = services.save_rank("Z", "Custom", 200, "#ffffff")
    services.delete_rank(custom.id)


# ---------- rotas ----------

def test_profile_page_renders(client):
    response = client.get("/hunter/")
    assert response.status_code == 200
    assert "STATUS" in response.get_data(as_text=True)


def test_update_profile(client):
    client.post("/hunter/", data={"name": "Ilton"})
    assert services.get_hunter().name == "Ilton"


def test_add_rank_via_form(client):
    services.get_hunter()
    client.post("/hunter/ranks", data={"code": "god", "name": "Deus", "min_level": 999, "color": "#ffffff"})
    assert any(r.code == "GOD" for r in services.list_ranks())


def test_avatar_must_be_public_https_link(client):
    client.post("/hunter/", data={"name": "Ilton", "title": "", "avatar_url": "https://exemplo.com/eu.png"})
    assert services.get_status().avatar_url == "https://exemplo.com/eu.png"
    assert "eu.png" in client.get("/hunter/").get_data(as_text=True)
    client.post("/hunter/", data={"name": "Ilton", "title": "", "avatar_url": r"C:\fotos\eu.png"})
    assert services.get_status().avatar_url == "https://exemplo.com/eu.png"


def test_flash_messages_carry_sound_category(client):
    from app.modules.quests import services as quests
    from app.modules.quests.services import QuestInput

    quest = quests.create_quest(QuestInput(title="Som", xp_reward=150))
    html = client.post(f"/quests/{quest.id}/complete", follow_redirects=True).get_data(as_text=True)
    assert 'data-category="levelup"' in html and "sounds.js" in html


def test_wisdom_and_charisma_are_added_to_old_databases(app):
    from sqlalchemy import delete

    from app.modules.hunter.models import Attribute

    services.get_hunter()
    db.session.execute(delete(Attribute).where(Attribute.key.in_(["wisdom", "charisma"])))
    db.session.commit()
    keys = [a.key for a in services.list_attributes()]
    assert "wisdom" in keys and "charisma" in keys and len(keys) == 10
