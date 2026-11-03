"""Personagem: atributos de combate com regra real, inventário, equipar e bônus de equipamentos."""
import pytest

from app.core import accounts
from app.core.errors import DomainError, NotFoundError
from app.core.tenancy import as_user
from app.modules.character import catalog, services as character
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


def _done(title="Missão", minutes=60, category_id=None):
    return quests.complete_quest(quests.create_quest(QuestInput(title=title, estimated_minutes=minutes,
                                                                category_id=category_id)).id)


def test_base_stats_rules():
    m = dict(total_hours=12, missions=25, checkins=17, habit_streak=14, study_hours=7, craft_hours=5,
             recurring=11, evolution_streak=8, body_hours=4, workouts=7, level=6, achievements=3)
    assert character.base_stats(m) == {"attack": 14, "defense": 5, "intelligence": 9, "discipline": 3,
                                       "vitality": 6, "wisdom": 8}


def test_stats_grow_with_real_activity(app):
    studies = quests.save_category("Estudos", "#22d3ee", [], specialty="studies")
    before = {s.key: s.total for s in character.sheet().stats}
    for i in range(3):
        _done(f"Estudo {i}", 60, studies.id)
    after = {s.key: s.total for s in character.sheet().stats}
    assert after["intelligence"] == before["intelligence"] + 3
    assert after["attack"] >= before["attack"] + 3


def test_first_mission_delivers_starter_item_once(app):
    result = _done()
    assert any("Adaga do Despertar" in message for message, _ in result.extra)
    assert character.sync_inventory() == []  # idempotente: sem item duplicado
    assert [o.item.key for o in character.sheet().owned] == ["novice_dagger"]


def test_equip_applies_bonus_and_one_item_per_slot(app):
    _done()
    character.equip("novice_dagger")
    attack = next(s for s in character.sheet().stats if s.key == "attack")
    assert attack.bonus == 1
    character.unequip("novice_dagger")
    assert next(s for s in character.sheet().stats if s.key == "attack").bonus == 0


def test_cannot_equip_item_not_owned_or_above_rank(app):
    with pytest.raises(NotFoundError):
        character.equip("monarch_amulet")
    from app.extensions import db
    from app.modules.character.models import PlayerItem

    db.session.add(PlayerItem(item_key="evolution_ring", source="teste"))
    db.session.commit()
    with pytest.raises(DomainError):
        character.equip("evolution_ring")  # exige Rank B (nível 35)


def test_equipped_item_gives_capped_xp_bonus_in_its_specialty(app):
    from app.extensions import db
    from app.modules.character.models import PlayerItem

    db.session.add(PlayerItem(item_key="knowledge_grimoire", source="teste"))
    db.session.commit()
    hunter.award_xp(20_000, source="test", description="subir para rank C")
    character.equip("knowledge_grimoire")
    studies = quests.save_category("Faculdade", "#38bdf8", [], specialty="college")
    other = quests.save_category("Hobbies", "#a78bfa", [], specialty="hobbies")
    assert _done("Aula", 60, studies.id).amount == 63  # +3 do Grimório (Estudos cobre Faculdade)
    assert _done("Violão", 60, other.id).amount == 60


def test_inventory_is_per_user(app):
    _done()
    user, code = accounts.invite_tester("p@example.com")
    accounts.accept_invite(code, "P", "12345678")
    with as_user(user.id):
        assert character.sheet().owned == []


def test_catalog_is_consistent():
    for item in catalog.EQUIPMENT.values():
        assert item.slot in catalog.SLOTS and item.rarity in catalog.RARITIES
        assert set(item.stats) <= set(catalog.STATS)
        assert all(metric in catalog.METRIC_LABELS for metric, _ in item.requirements)


def test_character_page_renders(app, client):
    _done()
    page = client.get("/personagem/").get_data(as_text=True)
    assert "Ataque" in page and "Adaga do Despertar" in page and "Itens bloqueados" in page
