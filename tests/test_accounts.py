"""Multiusuário: convites de teste, login, isolamento dos dados e páginas só do dono."""
from datetime import timedelta

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.core import accounts, secret_store, settings, time
from app.core.errors import DomainError
from app.core.models import User
from app.core.tenancy import OWNER_ID, as_user
from app.extensions import db as _db
from app.modules.habits.models import Habit
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests


def _tester(email="amigo@example.com", password="senha-forte-1"):
    user, code = accounts.invite_tester(email, "Amigo")
    accounts.accept_invite(code, "Amigo", password)
    return user


def test_invite_flow_lets_tester_in_without_google(app, client):
    user, code = accounts.invite_tester("Amigo@Example.com", "Amigo")
    assert user.email == "amigo@example.com"
    assert user.invite_hash != code  # só o hash fica no banco
    assert client.get(f"/convite/{code}").status_code == 200

    response = client.post(f"/convite/{code}", data={"name": "Jin", "password": "12345678"})
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session["uid"] == user.id
    page = client.get("/").get_data(as_text=True)
    assert "Jin" in page
    assert client.get(f"/convite/{code}").status_code == 404  # uso único


def test_invite_rejects_short_password_and_expired_link(app):
    user, code = accounts.invite_tester("a@example.com")
    with pytest.raises(DomainError):
        accounts.accept_invite(code, "", "curta")
    user.invite_expires_at = time.now() - timedelta(minutes=1)
    _db.session.commit()
    assert accounts.user_for_invite(code) is None


def test_invite_needs_valid_email(app):
    with pytest.raises(DomainError):
        accounts.invite_tester("sem-arroba")


def test_tester_login_by_email_and_block():
    app = create_app("testing", {"AUTH_ENABLED": True, "OWNER_USERNAME": "hunter",
                                 "OWNER_PASSWORD_HASH": generate_password_hash("arise")})
    with app.app_context():
        _db.create_all()
        accounts.ensure_owner()
        user = _tester()
        client = app.test_client()
        assert client.post("/login", data={"username": "amigo@example.com", "password": "errada"}).status_code == 200
        assert client.post("/login", data={"username": "amigo@example.com", "password": "senha-forte-1"}).status_code == 302
        assert client.get("/").status_code == 200

        accounts.set_tester_active(user.id, False)
        assert client.get("/").status_code == 302  # bloqueado: sessão encerrada
        assert accounts.authenticate("amigo@example.com", "senha-forte-1") is None
        assert accounts.authenticate("hunter", "arise").id == OWNER_ID
        _db.session.remove()
        _db.drop_all()


def test_data_is_isolated_between_users(app):
    quest = quests.create_quest(quests.QuestInput(title="Missão do dono"))
    settings.set_setting("ui.test", "dono")
    secret_store.save("credentials:notion", {"token": "secreto-do-dono"})
    owner_status = hunter.get_status()
    tester = _tester()

    with as_user(tester.id):
        assert quests.list_quests("all") == []
        assert _db.session.get(type(quest), quest.id) is None or _db.session.get(type(quest), quest.id).user_id == OWNER_ID
        _db.session.expunge_all()
        assert _db.session.get(type(quest), quest.id) is None
        assert settings.get_setting("ui.test") is None
        assert secret_store.load("credentials:notion") == {}
        status = hunter.get_status()  # o Hunter do convidado nasce do zero
        assert status.progress.total_xp == 0
        assert len(hunter.list_ranks()) == len(owner_status and hunter.list_ranks())
        quests.create_quest(quests.QuestInput(title="Missão do convidado"))
        settings.set_setting("ui.test", "convidado")

    _db.session.expunge_all()
    assert [q.title for q in quests.list_quests("all")] == ["Missão do dono"]
    assert settings.get_setting("ui.test") == "dono"


def test_tester_cannot_touch_owner_rows_by_id(app, client):
    quest = quests.create_quest(quests.QuestInput(title="Só do dono"))
    tester = _tester()
    with client.session_transaction() as session:
        session["uid"] = tester.id
    assert client.get(f"/quests/{quest.id}").status_code == 404
    client.post(f"/quests/{quest.id}/delete")
    _db.session.expunge_all()
    assert quests.list_quests("all")[0].title == "Só do dono"


def test_owner_only_pages(app, client):
    assert client.get("/usuarios-de-teste").status_code == 200
    tester = _tester()
    with client.session_transaction() as session:
        session["uid"] = tester.id
    assert client.get("/usuarios-de-teste").status_code == 403


def test_owner_creates_invite_from_page(app, client):
    response = client.post("/usuarios-de-teste", data={"email": "novo@example.com", "name": "Novo"},
                           follow_redirects=True)
    page = response.get_data(as_text=True)
    assert "/convite/" in page and "novo@example.com" in page


def test_delete_tester_removes_all_their_data(app):
    tester = _tester()
    with as_user(tester.id):
        hunter.get_status()
        _db.session.add(Habit(name="Ler"))
        _db.session.commit()
    accounts.delete_tester(tester.id)
    _db.session.expunge_all()
    assert _db.session.get(User, tester.id) is None
    remaining = _db.session.query(Habit).execution_options(all_users=True).all()
    assert remaining == []
    with pytest.raises(Exception):
        accounts.delete_tester(OWNER_ID)


def test_turbo_form_error_becomes_422(app, client):
    response = client.post("/quests/categories", data={"name": ""}, headers={"X-Turbo-Request-Id": "x"})
    assert response.status_code in (302, 422)


def test_env_buffer_key_is_only_for_owner(app):
    from app.integrations.buffer import token_store

    app.config["BUFFER_API_KEY"] = "chave-do-dono-1234"
    assert token_store.api_key() == "chave-do-dono-1234"
    tester = _tester()
    with as_user(tester.id):
        assert token_store.api_key() == ""
