"""O Buffer real nunca é chamado: FakeBuffer responde no lugar dele via httpx.MockTransport."""
import json
from datetime import date, datetime, timedelta

import httpx
import pytest

from app.core import time
from app.integrations import buffer
from app.integrations.buffer import posting, token_store
from app.integrations.buffer.posting import PostValidationError

TOKEN = "tok_" + "x" * 40

CHANNELS = [
    {"id": "li1", "name": "ilton", "displayName": "Ilton Silva", "service": "linkedin", "avatar": None,
     "isQueuePaused": False, "isDisconnected": False},
    {"id": "ig1", "name": "iltonbsilva", "displayName": None, "service": "instagram", "avatar": None,
     "isQueuePaused": False, "isDisconnected": False},
    {"id": "yt1", "name": "canal", "displayName": None, "service": "youtube", "avatar": None,
     "isQueuePaused": False, "isDisconnected": False},
]


class FakeBuffer:
    def __init__(self, reject_token=False):
        self.created: list[dict] = []
        self.edited: list[dict] = []
        self.deleted: list[str] = []
        self.reject_token = reject_token
        self.calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        assert request.headers["Authorization"].startswith("Bearer ")
        if self.reject_token:
            return httpx.Response(401)
        body = json.loads(request.content)
        query = body["query"]
        if "organizations" in query:
            return httpx.Response(200, json={"data": {"account": {"organizations": [{"id": "org1", "name": "Eu"}]}}})
        if "channels(" in query:
            return httpx.Response(200, json={"data": {"channels": CHANNELS}})
        if "post(" in query:
            post_id = body["variables"]["id"]
            return httpx.Response(200, json={"data": {"post": {
                "id": post_id, "text": "Post único", "status": "scheduled",
                "dueAt": "2026-11-03T11:00:00.000Z", "channelId": "ig1",
                "channelService": "instagram", "error": None,
                "assets": [{"source": "https://img/1.png", "thumbnail": "https://img/1.png"}],
            }}})
        if "posts(" in query:
            return httpx.Response(200, json={"data": {"posts": {"edges": [
                {"node": {"id": "p2", "text": "Depois", "status": "scheduled", "dueAt": "2026-11-03T11:00:00.000Z",
                          "channelId": "ig1", "channelService": "instagram", "error": None,
                          "assets": [{"thumbnail": "https://img/1.png"}]}},
                {"node": {"id": "p1", "text": "Antes", "status": "scheduled", "dueAt": "2026-11-02T09:00:00.000Z",
                          "channelId": "li1", "channelService": "linkedin", "error": {"message": "falhou"},
                          "assets": []}},
            ]}}})
        if "createPost" in query:
            post_input = body["variables"]["input"]
            self.created.append(post_input)
            if post_input["channelId"] == "li1" and "FALHA" in post_input["text"]:
                return httpx.Response(200, json={"data": {"createPost": {"message": "Limite da fila atingido"}}})
            return httpx.Response(200, json={"data": {"createPost": {"post": {
                "id": f"new{len(self.created)}", "status": "scheduled", "dueAt": post_input.get("dueAt")}}}})
        if "editPost" in query:
            post_input = body["variables"]["input"]
            self.edited.append(post_input)
            return httpx.Response(200, json={"data": {"editPost": {"post": {
                "id": post_input["id"], "status": "sent" if post_input.get("mode") == "shareNow" else "scheduled",
                "dueAt": post_input.get("dueAt"), "text": post_input.get("text", "")
            }}}})
        if "deletePost" in query:
            post_id = body["variables"]["input"]["id"]
            self.deleted.append(post_id)
            return httpx.Response(200, json={"data": {"deletePost": {"id": post_id}}})
        return httpx.Response(400)


@pytest.fixture
def fake(monkeypatch):
    fake = FakeBuffer()
    monkeypatch.setattr(buffer, "_transport", httpx.MockTransport(fake))
    return fake


@pytest.fixture
def connected(app, fake):
    buffer.save_token(TOKEN, time.today())
    return fake


# ---------- regras puras ----------

def test_instagram_keeps_at_most_five_hashtags_and_accessibility_tag():
    text = "Post #a #b #c #d #e #f #g #PraTodosVerem"
    out = posting.limit_instagram_hashtags(text)
    assert out.count("#") == 5 and "#PraTodosVerem" in out and "#a" in out and "#f" not in out


def test_instagram_requires_image():
    with pytest.raises(PostValidationError):
        posting.build_post_input(channel_id="ig1", service="instagram", text="oi", image_urls=[], mode="addToQueue")


def test_instagram_metadata_and_carousel():
    body = posting.build_post_input(channel_id="ig1", service="instagram", text="oi",
                                    image_urls=["https://a/1.png", "https://a/2.png"], mode="addToQueue")
    assert body["metadata"] == {"instagram": {"type": "post", "shouldShareToFeed": True}}
    assert len(body["assets"]) == 2 and "dueAt" not in body


def test_linkedin_text_limit():
    with pytest.raises(PostValidationError):
        posting.build_post_input(channel_id="li1", service="linkedin", text="x" * 3001, image_urls=[],
                                 mode="addToQueue")


def test_due_at_is_converted_to_utc_and_must_be_future():
    now = datetime(2026, 11, 1, 12, 0)
    assert posting.due_at_utc(datetime(2026, 11, 2, 6, 0), now=now) == "2026-11-02T09:00:00.000Z"
    with pytest.raises(PostValidationError):
        posting.due_at_utc(datetime(2026, 11, 1, 11, 0), now=now)


def test_image_urls_must_be_links():
    assert posting.parse_image_urls("https://a/1.png\n\n https://a/2.png ") == ["https://a/1.png", "https://a/2.png"]
    with pytest.raises(PostValidationError):
        posting.parse_image_urls("C:\\imagens\\foto.png")


# ---------- token ----------

def test_token_is_validated_before_saving(app, fake):
    assert buffer.save_token(TOKEN, date(2026, 11, 1)) == 3
    status = token_store.status(today=date(2026, 11, 1))
    assert status.configured and status.source == "tela"
    assert status.masked == "••••xxxx" and TOKEN not in status.masked
    assert status.expires_at == date(2027, 1, 30) and status.level == "ok"


def test_rejected_token_is_not_saved(app, monkeypatch):
    monkeypatch.setattr(buffer, "_transport", httpx.MockTransport(FakeBuffer(reject_token=True)))
    with pytest.raises(buffer.BufferError, match="recusou"):
        buffer.save_token(TOKEN, date(2026, 11, 1))
    assert not token_store.status().configured


def test_short_token_is_rejected_without_calling_buffer(app, fake):
    with pytest.raises(buffer.BufferError):
        buffer.save_token("curto", date(2026, 11, 1))
    assert fake.calls == 0


def test_token_expiry_levels(app, fake):
    buffer.save_token(TOKEN, date(2026, 8, 1))
    assert token_store.status(today=date(2026, 10, 25)).level == "warning"
    assert token_store.status(today=date(2026, 11, 1)).level == "expired"


def test_token_page_never_shows_the_token(client, connected):
    html = client.get("/integrations/buffer/token").get_data(as_text=True)
    assert TOKEN not in html and "••••xxxx" in html


def test_token_form_saves(client, fake):
    response = client.post("/integrations/buffer/token", data={"api_key": TOKEN, "created_at": "2026-11-01"})
    assert response.status_code == 302
    assert token_store.api_key() == TOKEN


def test_delete_token(client, connected):
    client.post("/integrations/buffer/token/delete")
    assert not buffer.is_configured()


# ---------- leitura ----------

def test_posts_have_channel_names_and_local_time(app, connected):
    posts = buffer.posts(["scheduled"])
    assert [p.id for p in posts] == ["p1", "p2"]
    assert posts[0].channel_name == "Ilton Silva" and posts[0].due_at == datetime(2026, 11, 2, 6, 0)
    assert posts[0].error == "falhou" and posts[1].thumbnail == "https://img/1.png"


def test_youtube_is_not_usable_for_image_posts(app, connected):
    usable = {ch.service: ch.usable for ch in buffer.channels()}
    assert usable == {"linkedin": True, "instagram": True, "youtube": False}


def test_dashboard_widget_without_token(client):
    assert "Cadastrar o token" in client.get("/").get_data(as_text=True)


def test_dashboard_widget_with_token(client, connected):
    assert "Antes" in client.get("/").get_data(as_text=True)


# ---------- agendamento ----------

def _future():
    return time.now() + timedelta(days=2)


def test_schedule_uses_text_per_network(app, connected):
    results = buffer.schedule(
        text="padrão", overrides={"instagram": "texto do insta #a"}, channel_ids=["li1", "ig1"],
        mode="customScheduled", due_local=_future(), image_urls=["https://a/1.png"], uploads=[],
    )
    assert all(r.ok for r in results)
    by_channel = {c["channelId"]: c for c in connected.created}
    assert by_channel["li1"]["text"] == "padrão"
    assert by_channel["ig1"]["text"] == "texto do insta #a"
    assert by_channel["ig1"]["dueAt"].endswith(".000Z")


def test_one_channel_failing_does_not_block_others(app, connected):
    results = buffer.schedule(text="FALHA", overrides={}, channel_ids=["li1", "ig1"], mode="addToQueue",
                              due_local=None, image_urls=["https://a/1.png"], uploads=[])
    assert [(r.service, r.ok) for r in results] == [("linkedin", False), ("instagram", True)]
    assert "Limite" in results[0].message


def test_validation_happens_before_any_post_is_created(app, connected):
    with pytest.raises(PostValidationError):
        buffer.schedule(text="sem imagem", overrides={}, channel_ids=["li1", "ig1"], mode="addToQueue",
                        due_local=None, image_urls=[], uploads=[])
    assert connected.created == []


def test_unusable_channel_is_rejected(app, connected):
    with pytest.raises(PostValidationError):
        buffer.schedule(text="x", overrides={}, channel_ids=["yt1"], mode="addToQueue", due_local=None,
                        image_urls=["https://a/1.png"], uploads=[])


def test_uploads_with_builtin_storage_succeed(app, connected):
    results = buffer.schedule(
        text="x", overrides={}, channel_ids=["li1"], mode="addToQueue", due_local=None,
        image_urls=[], uploads=[buffer.Upload("a.png", b"123", "image/png")]
    )
    assert len(connected.created) == 1
    post = connected.created[0]
    assert len(post["assets"]) == 1
    img_url = post["assets"][0]["image"]["url"]
    assert "/integrations/buffer/uploads/" in img_url
    assert img_url.endswith("/a.png")


def test_serve_upload_publicly(client):
    from app.integrations.buffer import storage
    url = storage.upload("foto.png", b"testbytes", "image/png")
    path = url if url.startswith("/") else "/" + url.split("/", 3)[-1]
    res = client.get(path)
    assert res.status_code == 200
    assert res.data == b"testbytes"
    assert "image/png" in res.content_type


def test_uploads_invalid_format_or_size(app, connected):
    with pytest.raises(buffer.StorageError, match="formato não aceito"):
        buffer.schedule(text="x", overrides={}, channel_ids=["li1"], mode="addToQueue", due_local=None,
                        image_urls=[], uploads=[buffer.Upload("a.exe", b"123", "application/x-msdownload")])
    with pytest.raises(buffer.StorageError, match="maior que 20 MB"):
        buffer.schedule(text="x", overrides={}, channel_ids=["li1"], mode="addToQueue", due_local=None,
                        image_urls=[], uploads=[buffer.Upload("a.png", b"1" * (21 * 1024 * 1024), "image/png")])


def test_new_post_form_requires_confirmation(client, connected):
    data = {"channels": ["li1"], "text": "Olá", "mode": "addToQueue", "image_urls": ""}
    client.post("/integrations/buffer/new", data=data)
    assert connected.created == []
    client.post("/integrations/buffer/new", data={**data, "confirm": "yes"})
    assert len(connected.created) == 1


def test_pages_render(client, connected):
    for url in ("/integrations/buffer/", "/integrations/buffer/?status=sent", "/integrations/buffer/new",
                "/integrations/"):
        assert client.get(url).status_code == 200, url


def test_buffer_page_redirects_to_token_when_missing(client):
    assert client.get("/integrations/buffer/").headers["Location"].endswith("/integrations/buffer/token")


def test_blocked_by_pythonanywhere_proxy_explains_allowlist():
    def handler(request):
        raise httpx.ProxyError("403 Forbidden", request=request)

    client = buffer.client.BufferClient("x" * 40, transport=httpx.MockTransport(handler))
    with pytest.raises(buffer.client.BufferError, match="api.buffer.com.*PythonAnywhere"):
        client.organization_id()


def test_offline_keeps_generic_message():
    def handler(request):
        raise httpx.ConnectError("sem rede", request=request)

    client = buffer.client.BufferClient("x" * 40, transport=httpx.MockTransport(handler))
    with pytest.raises(buffer.client.BufferError, match="Confira a internet"):
        client.organization_id()


# ---------- ações em posts (editar, excluir, postar agora) ----------

def test_get_single_post(app, connected):
    post = buffer.get_post("p2")
    assert post.id == "p2"
    assert post.channel_name == "iltonbsilva"
    assert post.service == "instagram"
    assert post.thumbnail == "https://img/1.png"


def test_delete_post_client(app, connected):
    deleted_id = buffer.delete_post("p2")
    assert deleted_id == "p2"
    assert connected.deleted == ["p2"]


def test_share_post_now(app, connected):
    res = buffer.share_post_now("p2")
    assert res["status"] == "sent"
    assert connected.edited[-1]["id"] == "p2"
    assert connected.edited[-1]["mode"] == "shareNow"
    assert connected.edited[-1]["text"] == "Post único"
    assert connected.edited[-1]["metadata"] == {"instagram": {"type": "post", "shouldShareToFeed": True}}


def test_update_post(app, connected):
    fut = _future()
    res = buffer.update_post("p2", text="Texto alterado #tag1 #tag2", due_local=fut, service="instagram")
    assert res["id"] == "p2"
    assert connected.edited[-1]["id"] == "p2"
    assert connected.edited[-1]["text"] == "Texto alterado #tag1 #tag2"
    assert connected.edited[-1]["dueAt"].endswith(".000Z")


def test_delete_post_route(client, connected):
    res = client.post("/integrations/buffer/posts/p2/delete")
    assert res.status_code == 302
    assert "p2" in connected.deleted


def test_share_now_route(client, connected):
    res = client.post("/integrations/buffer/posts/p2/share-now")
    assert res.status_code == 302
    assert any(e.get("mode") == "shareNow" for e in connected.edited)


def test_edit_post_route_get_and_post(client, connected):
    # GET renders edit page
    res_get = client.get("/integrations/buffer/posts/p2/edit")
    assert res_get.status_code == 200
    html = res_get.get_data(as_text=True)
    assert "Editar post" in html
    assert "Instagram" in html
    assert "Post único" in html

    # POST updates post
    fut = _future()
    res_post = client.post("/integrations/buffer/posts/p2/edit", data={
        "text": "Texto editado via form",
        "due_date": fut.strftime("%Y-%m-%d"),
        "due_time": fut.strftime("%H:%M"),
    })
    assert res_post.status_code == 302
    assert connected.edited[-1]["text"] == "Texto editado via form"


def test_index_displays_network_tags_and_action_buttons(client, connected):
    html = client.get("/integrations/buffer/").get_data(as_text=True)
    assert "tag-instagram" in html
    assert "tag-linkedin" in html
    assert "Instagram" in html
    assert "Postar agora" in html
    assert "Editar" in html
    assert "Excluir" in html
