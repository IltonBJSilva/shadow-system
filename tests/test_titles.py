"""Títulos: desbloqueio por conquista, escolha do título exibido e títulos próprios."""
import pytest

from app.core.errors import DomainError
from app.modules.gamification import services as gamification
from app.modules.gamification.rules import Rules
from app.modules.habits import services as habits
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


@pytest.fixture(autouse=True)
def no_bonus(app):
    gamification.save_rules(Rules(bonuses_enabled=False, penalties_enabled=False))


def _title(name: str):
    return next(t for t in hunter.list_titles() if t.name == name)


def test_defaults_are_seeded_and_only_the_first_is_unlocked(app):
    titles = hunter.list_titles()
    assert [t.name for t in titles if t.unlocked] == ["Recém-desperto"]
    assert _title("Recém-desperto").is_active


def test_first_quest_unlocks_a_title_with_a_message(app):
    quest = quests.create_quest(QuestInput(title="Ler 10 páginas"))
    result = quests.complete_quest(quest.id)
    assert _title("Primeiro Passo").unlocked
    assert any("Título desbloqueado: Primeiro Passo" in text for text, _ in result.extra)


def test_progress_shows_current_and_threshold(app):
    for name in ("A", "B", "C"):
        quests.complete_quest(quests.create_quest(QuestInput(title=name)).id)
    ten = _title("Cumpridor de Missões")
    assert (ten.current, ten.threshold, ten.unlocked, ten.percent) == (3, 10, False, 30)


def test_habit_streak_metric(app):
    from datetime import timedelta

    from app.core import time

    habit = habits.save_habit("Ler", "", 10, [])
    for back in range(6, -1, -1):
        habits.check_in(habit.id, time.today() - timedelta(days=back))
    assert _title("Chama Constante").unlocked  # 7 dias seguidos


def test_choose_only_unlocked_titles(app):
    with pytest.raises(DomainError):
        hunter.choose_title(_title("Lenda Viva").id)
    custom = hunter.create_custom_title("Dev das Madrugadas", "Codando depois da meia-noite")
    assert hunter.choose_title(custom.id) == "Dev das Madrugadas"
    assert hunter.get_status().title == "Dev das Madrugadas"


def test_custom_titles_can_be_deleted_but_achievements_cannot(app):
    custom = hunter.create_custom_title("Temporário")
    hunter.choose_title(custom.id)
    hunter.delete_title(custom.id)
    assert hunter.get_status().title == "Recém-desperto"
    with pytest.raises(DomainError):
        hunter.delete_title(_title("Recém-desperto").id)
    with pytest.raises(DomainError):
        hunter.create_custom_title("recém-desperto")  # nome repetido, sem diferenciar maiúsculas


def test_old_free_text_title_is_kept_as_custom(app):
    from app.extensions import db

    hunter.get_hunter().title = "Shadow Developer"
    db.session.commit()
    title = _title("Shadow Developer")
    assert title.unlocked and title.is_custom and title.is_active


def test_pages_and_routes(client):
    html = client.get("/hunter/").get_data(as_text=True)
    assert "Título exibido" in html and "Títulos (1/" in html
    client.post("/hunter/titles", data={"name": "Mestre do Café"})
    page = client.get("/hunter/titles").get_data(as_text=True)
    assert "Mestre do Café" in page and "A conquistar" in page and "Lenda Viva" in page
    title_id = _title("Mestre do Café").id
    client.post("/hunter/titles/choose", data={"title_id": str(title_id), "next": "/hunter/"})
    assert hunter.get_status().title == "Mestre do Café"
