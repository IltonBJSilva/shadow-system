"""Loja das Sombras: requisitos de rank e desafios, recrutamento único, bônus de XP com acúmulo controlado."""
from unittest import mock

import pytest

from app.core import accounts
from app.core.errors import DomainError
from app.core.tenancy import as_user
from app.extensions import db as _db
from app.modules.character import services as character
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput
from app.modules.shadows import catalog, services as shadows
from app.modules.shadows.models import PlayerShadow

READY = {"recurring": 500, "evolution_streak": 60, "body_hours": 100, "workouts": 50, "habit_streak": 60,
         "study_hours": 100, "missions": 999, "total_hours": 999, "level": 1, "checkins": 0, "craft_hours": 0,
         "achievements": 0}


def _metrics(**over):
    return mock.patch.object(character, "metrics", return_value={**READY, **over})


def _level_up(level):
    from app.modules.hunter import progression

    hunter.award_xp(progression.total_xp_for_level(level), source="test", description="teste")
    _db.session.commit()


def _done(minutes, specialty):
    category = next((c for c in quests.list_categories() if c.specialty == specialty), None) or \
        quests.save_category(f"Cat {specialty}", "#ffffff", [], specialty=specialty)
    quest = quests.create_quest(QuestInput(title=f"M {specialty} {minutes}", estimated_minutes=minutes, category_id=category.id))
    return quests.complete_quest(quest.id).amount


def test_rank_is_required_even_with_challenges_done(app):
    with _metrics():
        with pytest.raises(DomainError, match="Rank D"):
            shadows.recruit("igris")


def test_challenges_are_required(app):
    _level_up(10)
    with _metrics(recurring=3):
        with pytest.raises(DomainError, match="desafios"):
            shadows.recruit("igris")


def test_recruit_once_and_record_history(app):
    _level_up(10)
    with _metrics():
        shadows.recruit("igris")
        with pytest.raises(DomainError, match="já está"):
            shadows.recruit("igris")
    assert _db.session.query(PlayerShadow).count() == 1
    [(shadow, _, proof)] = shadows.history()
    assert shadow.key == "igris" and "recurring" in proof


def test_shadow_gives_xp_bonus_only_in_its_specialty(app):
    _level_up(10)
    with _metrics():
        shadows.recruit("iron")
    assert _done(60, "body") == 65
    assert _done(60, "studies") == 60


def test_same_specialty_shadows_stack_with_diminishing_factor(app):
    _level_up(20)
    with _metrics():
        shadows.recruit("iron")  # +5 Corpo
        shadows.recruit("tank")  # +4 Corpo -> metade (2)
    lines = shadows.xp_bonus_lines(hunter.BonusContext("body", 60, "custom", 60))
    assert [amount for _, amount in lines] == [5, 2]
    assert _done(60, "body") == 67


def test_bonus_respects_global_cap_on_short_missions(app):
    _level_up(20)
    with _metrics():
        shadows.recruit("iron")
    assert _done(5, "body") == 5 + 2  # teto de 50% do XP base (5 -> 2)


def test_shadows_add_combat_stats(app):
    _level_up(10)
    before = {s.key: s.bonus for s in character.sheet().stats}
    with _metrics():
        shadows.recruit("igris")
    after = {s.key: s.bonus for s in character.sheet().stats}
    assert after["discipline"] == before["discipline"] + 3


def test_shadows_are_per_user(app):
    _level_up(10)
    with _metrics():
        shadows.recruit("igris")
    user, code = accounts.invite_tester("s@example.com")
    accounts.accept_invite(code, "S", "12345678")
    with as_user(user.id):
        assert shadows.recruited() == []


def test_shop_page_and_recruit_route(app, client):
    _level_up(10)
    with _metrics():
        page = client.get("/sombras/").get_data(as_text=True)
        assert "Igris" in page and "ARISE" in page
        client.post("/sombras/igris/recrutar")
        client.post("/sombras/igris/recrutar")  # requisição repetida não duplica
    assert _db.session.query(PlayerShadow).count() == 1


def test_catalog_has_the_six_main_shadows():
    assert set(catalog.SHADOWS) == {"igris", "iron", "tank", "tusk", "beru", "bellion"}
    assert catalog.SHADOWS["bellion"].min_rank == "S"
