"""O Kausa real nunca é chamado: httpx.MockTransport responde no lugar dele."""
from datetime import datetime

import httpx
import pytest

from app import create_app
from app.extensions import db
from app.integrations import kausa_scheduler
from app.integrations.kausa_scheduler import KausaSchedulerClient, KausaSchedulerError

POSTS = {"posts": [
    {"id": "p2", "text": "Depois", "status": "scheduled", "dueAt": "2026-11-03T15:00:00.000Z",
     "channelId": "c1", "channelService": "instagram", "channelName": "kausa.tech", "error": None, "assets": []},
    {"id": "p1", "text": "Antes", "status": "scheduled", "dueAt": "2026-11-02T12:00:00Z",
     "channelId": "c1", "channelService": "instagram", "channelName": "kausa.tech",
     "error": {"message": "Imagem inválida"}, "assets": []},
]}
CHANNELS = {"channels": [{"id": "c1", "name": "kausa", "displayName": "kausa.tech", "service": "instagram",
                          "usable": True}]}


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/saude":
        return httpx.Response(200, json={"ok": True})
    if request.url.path == "/api/posts":
        assert request.url.params.get("status") == "scheduled"
        return httpx.Response(200, json=POSTS)
    if request.url.path == "/api/canais":
        return httpx.Response(200, json=CHANNELS)
    return httpx.Response(404)


def _client(handler=_handler) -> KausaSchedulerClient:
    return KausaSchedulerClient("http://kausa.test", transport=httpx.MockTransport(handler))


def test_posts_are_parsed_sorted_and_localized(app):
    posts = _client().posts()
    assert [p.id for p in posts] == ["p1", "p2"]
    assert posts[0].due_at == datetime(2026, 11, 2, 9, 0)  # 12:00 UTC = 09:00 em São Paulo
    assert posts[0].error == "Imagem inválida"
    assert posts[1].channel == "kausa.tech"


def test_channels_and_health(app):
    client = _client()
    assert client.health() is True
    assert client.channels()[0].name == "kausa.tech"


def test_login_enabled_on_kausa_gives_clear_error(app):
    client = _client(lambda request: httpx.Response(401, json={"error": "Entre com seu usuário e senha."}))
    with pytest.raises(KausaSchedulerError, match="login"):
        client.posts()


def test_offline_kausa(app):
    def offline(request):
        raise httpx.ConnectError("refused")

    client = _client(offline)
    assert client.health() is False
    with pytest.raises(KausaSchedulerError, match="rodando"):
        client.posts()


def test_missing_url_is_rejected():
    with pytest.raises(KausaSchedulerError):
        KausaSchedulerClient("")


def test_safe_helper_without_configuration(app):
    assert kausa_scheduler.scheduled_posts_safe() == ([], None)


def test_safe_helper_returns_error_instead_of_raising(monkeypatch):
    app = create_app("testing", {"KAUSA_SCHEDULER_URL": "http://kausa.test"})
    with app.app_context():
        monkeypatch.setattr(kausa_scheduler, "get_client", lambda: _client(lambda r: httpx.Response(500, json={})))
        posts, error = kausa_scheduler.scheduled_posts_safe()
        assert posts == [] and "500" in error


def test_integrations_pages_render(client):
    assert client.get("/integrations/").status_code == 200
    assert "KAUSA_SCHEDULER_URL" in client.get("/integrations/kausa").get_data(as_text=True)


def test_kausa_page_with_mocked_client(monkeypatch):
    app = create_app("testing", {"KAUSA_SCHEDULER_URL": "http://kausa.test"})
    with app.app_context():
        db.create_all()
        monkeypatch.setattr(kausa_scheduler, "get_client", _client)
        html = app.test_client().get("/integrations/kausa").get_data(as_text=True)
        assert "Antes" in html and "kausa.tech" in html
        db.drop_all()
