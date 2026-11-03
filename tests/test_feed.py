"""Feed dos Hunters: eventos viram posts só com permissão, e desligar esconde os antigos."""
from app.core import accounts
from app.core.tenancy import as_user
from app.modules.arena import feed, services as arena
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


def _tester():
    user, code = accounts.invite_tester("feed@example.com", "Jin")
    accounts.accept_invite(code, "Jin", "12345678")
    return user


def _complete(title, quest_type="custom"):
    return quests.complete_quest(quests.create_quest(QuestInput(title=title, estimated_minutes=30, quest_type=quest_type)).id)


def test_completion_and_level_up_are_posted(app):
    from app.modules.hunter import services as hunter

    _complete("Ler capítulo")
    hunter.award_xp(500, source="test", description="subir")
    from app.extensions import db
    db.session.commit()
    texts = [item.text for item in feed.recent()]
    assert any("Ler capítulo" in t for t in texts)
    assert any("nível" in t for t in texts)
    first = next(i for i in feed.recent() if "Ler capítulo" in i.text)
    assert first.xp == 30 and first.name


def test_other_users_see_my_posts_but_not_after_i_hide_them(app):
    rival = _tester()
    with as_user(rival.id):
        _complete("Treino de pernas")
    assert any(i.name == "Jin" for i in feed.recent())
    with as_user(rival.id):
        arena.set_privacy({**arena.DEFAULT_PRIVACY, "feed": False})
    assert not any(i.name == "Jin" for i in feed.recent())


def test_nothing_is_posted_when_feed_is_off(app):
    arena.set_privacy({**arena.DEFAULT_PRIVACY, "feed": False})
    _complete("Secreta")
    arena.set_privacy(arena.DEFAULT_PRIVACY)
    assert not any("Secreta" in i.text for i in feed.recent())


def test_penalty_quests_stay_out_of_the_feed(app):
    _complete("[PENALTY] Recuperar", quest_type="emergency")
    assert not any("PENALTY" in i.text for i in feed.recent())


def test_feed_page_renders_and_filters(app, client):
    _complete("Estudar SQL")
    page = client.get("/arena/feed").get_data(as_text=True)
    assert "Estudar SQL" in page
    assert "Estudar SQL" not in client.get("/arena/feed?tipo=shadow").get_data(as_text=True)
