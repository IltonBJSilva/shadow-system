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


# ---------- Fila do Sistema (Batch + Forward Scheduling) ----------

def test_calculate_forward_dates():
    last_due = datetime(2026, 11, 20, 18, 30)
    dates = buffer.calculate_forward_dates(last_due, count=5, default_time="18:30")
    assert len(dates) == 5
    assert [d.date().isoformat() for d in dates] == [
        "2026-11-21", "2026-11-22", "2026-11-23", "2026-11-24", "2026-11-25"
    ]
    assert all(d.hour == 18 and d.minute == 30 for d in dates)


def test_calculate_forward_dates_no_last_due():
    dates = buffer.calculate_forward_dates(None, count=3, default_time="09:15")
    assert len(dates) == 3
    today = time.today()
    assert dates[0].date() == today + timedelta(days=1)
    assert dates[1].date() == today + timedelta(days=2)
    assert dates[2].date() == today + timedelta(days=3)
    assert all(d.hour == 9 and d.minute == 15 for d in dates)


def test_enqueue_post_and_list_queue(app, connected):
    post = buffer.enqueue_post(
        channel_id="ig1",
        channel_name="iltonbsilva",
        service="instagram",
        text="Legenda de teste da fila local",
        image_urls=["https://img.com/foto1.png"],
        target_date=date(2026, 11, 25),
        target_time="18:30",
    )
    assert post.id is not None
    assert post.status == "pending"
    assert post.thumbnail == "https://img.com/foto1.png"

    queued = buffer.list_queue_posts()
    assert len(queued) == 1
    assert queued[0].id == post.id
    assert queued[0].text == "Legenda de teste da fila local"
    assert queued[0].images == ["https://img.com/foto1.png"]


def test_dispatch_next_batch_success(app, connected):
    # FakeBuffer tem 1 post agendado para ig1 (id p2 no dia 2026-11-03T11:00:00Z)
    for i in range(3):
        buffer.enqueue_post(
            channel_id="ig1",
            channel_name="iltonbsilva",
            service="instagram",
            text=f"Post lote #{i}",
            image_urls=["https://img.com/1.png"],
        )

    dispatched = buffer.dispatch_next_batch("ig1", batch_size=5, trigger_threshold=5)
    assert len(dispatched) == 3
    assert all(p.status == "dispatched" for p in dispatched)
    assert all(p.buffer_post_id is not None for p in dispatched)

    # Confere se os posts chegaram ao FakeBuffer com modo customScheduled e dueAt no futuro
    created = [c for c in connected.created if c["channelId"] == "ig1"]
    assert len(created) == 3
    assert all(c["mode"] == "customScheduled" for c in created)
    assert all(c["dueAt"] is not None for c in created)


def test_dispatch_next_batch_waits_if_scheduled_count_above_threshold(app, connected, monkeypatch):
    # Simula 6 posts já agendados no Buffer para ig1 (acima do limiar 5)
    six_posts = [
        {"node": {"id": f"p_{i}", "text": f"Post {i}", "status": "scheduled",
                  "dueAt": "2026-11-10T18:00:00.000Z", "channelId": "ig1",
                  "channelService": "instagram", "error": None, "assets": []}}
        for i in range(6)
    ]
    orig_call = connected.__call__

    def mock_call(req):
        body = json.loads(req.content)
        if "posts(" in body.get("query", ""):
            return httpx.Response(200, json={"data": {"posts": {"edges": six_posts}}})
        return orig_call(req)

    monkeypatch.setattr(buffer, "_transport", httpx.MockTransport(mock_call))

    buffer.enqueue_post(
        channel_id="ig1",
        channel_name="iltonbsilva",
        service="instagram",
        text="Post que deve aguardar",
        image_urls=["https://img.com/1.png"],
    )

    dispatched = buffer.dispatch_next_batch("ig1", batch_size=5, trigger_threshold=5)
    assert len(dispatched) == 0
    pending = buffer.list_queue_posts(status="pending")
    assert len(pending) == 1
    assert pending[0].status == "pending"


def test_schedule_graceful_fallback_to_queue_on_limit_reached(app, connected, monkeypatch):
    # Quando o Buffer responde com limite atingido, schedule deve enfileirar automaticamente
    def limit_call(req):
        body = json.loads(req.content)
        query = body.get("query", "")
        if "createPost" in query:
            return httpx.Response(200, json={"data": {"createPost": {
                "message": "Scheduled posts limit reached. You have 10 scheduled posts out of 10 allowed."
            }}})
        return connected(req)

    monkeypatch.setattr(buffer, "_transport", httpx.MockTransport(limit_call))

    fut = _future()
    results = buffer.schedule(
        text="Post que estourou o limite",
        overrides={},
        channel_ids=["ig1"],
        mode="customScheduled",
        due_local=fut,
        image_urls=["https://img.com/1.png"],
        uploads=[],
    )
    assert len(results) == 1
    assert results[0].ok is True
    assert "Fila do Sistema" in results[0].message

    queue_posts = buffer.list_queue_posts(status="pending")
    assert len(queue_posts) == 1
    assert queue_posts[0].text == "Post que estourou o limite"


def test_queue_routes_crud_and_dispatch(client, connected):
    # 1. Enfileira um post
    p = buffer.enqueue_post(
        channel_id="ig1",
        channel_name="iltonbsilva",
        service="instagram",
        text="Post na fila para teste de rota",
        image_urls=["https://img.com/1.png"],
        target_date=date(2026, 11, 28),
        target_time="19:00",
    )

    # 2. GET index na aba queue
    res = client.get("/integrations/buffer/?status=queue")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Fila do Sistema" in html
    assert "Post na fila para teste de rota" in html
    assert "Pendente na Fila" in html

    # 3. GET edit queue post
    res_edit_get = client.get(f"/integrations/buffer/queue/{p.id}/edit")
    assert res_edit_get.status_code == 200
    assert "Editar post" in res_edit_get.get_data(as_text=True)

    # 4. POST edit queue post
    res_edit_post = client.post(f"/integrations/buffer/queue/{p.id}/edit", data={
        "text": "Post na fila com texto editado",
        "due_date": "2026-11-29",
        "due_time": "20:00",
    })
    assert res_edit_post.status_code == 302
    updated = buffer.get_queue_post(p.id)
    assert updated.text == "Post na fila com texto editado"
    assert updated.target_date == date(2026, 11, 29)
    assert updated.target_time == "20:00"

    # 5. POST dispatch single post
    res_dispatch = client.post(f"/integrations/buffer/queue/{p.id}/dispatch")
    assert res_dispatch.status_code == 302
    dispatched = buffer.get_queue_post(p.id)
    assert dispatched.status == "dispatched"
    assert dispatched.buffer_post_id is not None

    # 6. POST delete queue post
    res_delete = client.post(f"/integrations/buffer/queue/{p.id}/delete")
    assert res_delete.status_code == 302
    assert buffer.get_queue_post(p.id) is None


def test_sync_queue_route(client, connected):
    # Enfileira posts para testar rota de sync
    buffer.enqueue_post(
        channel_id="ig1",
        channel_name="iltonbsilva",
        service="instagram",
        text="Sync route post",
        image_urls=["https://img.com/1.png"],
    )
    res = client.post("/integrations/buffer/queue/sync")
    assert res.status_code == 302
    # Verifica que o post foi despachado
    queued = buffer.list_queue_posts()
    assert len(queued) == 1
    assert queued[0].status == "dispatched"


def test_video_asset_support():
    # Instagram com vídeo é formatado como Reel
    body_ig = posting.build_post_input(
        channel_id="ig1", service="instagram", text="Reel teste #ia #tech #PraTodosVerem Vídeo de IA",
        image_urls=["https://a/video.mp4"], mode="addToQueue",
    )
    assert body_ig["assets"] == [{"video": {"url": "https://a/video.mp4"}}]
    assert body_ig["metadata"]["instagram"] == {"type": "reel", "shouldShareToFeed": True}

    # TikTok com vídeo recebe metadados de título
    body_tt = posting.build_post_input(
        channel_id="tt1", service="tiktok", text="TikTok teste sobre IA",
        image_urls=["https://a/short.mp4"], mode="addToQueue",
    )
    assert body_tt["assets"] == [{"video": {"url": "https://a/short.mp4"}}]
    assert body_tt["metadata"]["tiktok"] == {"title": "TikTok teste sobre IA"}


def test_storage_accepts_mp4_video(app):
    url = buffer.storage.upload("video_teste.mp4", b"fake-video-bytes-123", "video/mp4")
    assert "video_teste.mp4" in url
    upload_row = buffer.storage.get_upload(url.split("/")[-2])
    assert upload_row is not None
    assert upload_row.mimetype == "video/mp4"


def test_share_now_queue_post_route(client, connected):
    p = buffer.enqueue_post(
        channel_id="ig1",
        channel_name="iltonbsilva",
        service="instagram",
        text="Post para teste share now",
        image_urls=["https://img.com/1.png"],
    )
    res = client.post(f"/integrations/buffer/queue/{p.id}/share-now")
    assert res.status_code == 302
    assert any(c.get("mode") == "shareNow" for c in connected.created)
    updated = buffer.get_queue_post(p.id)
    assert updated.status == "dispatched"


def test_videos_tab_queue_and_scheduled(client, connected):
    v_queue = buffer.enqueue_post(
        channel_id="ig1",
        channel_name="iltonbsilva",
        service="instagram",
        text="Reel exclusivo na fila",
        image_urls=["https://example.com/video1.mp4"],
    )
    img_queue = buffer.enqueue_post(
        channel_id="li1",
        channel_name="Ilton Batista",
        service="linkedin",
        text="Apenas imagem na fila",
        image_urls=["https://example.com/foto.png"],
    )

    res = client.get("/integrations/buffer/?status=videos")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Vídeos na Fila do Sistema" in html
    assert "Reel exclusivo na fila" in html
    assert "Apenas imagem na fila" not in html
    assert "Vídeos Agendados no Buffer" in html

    res_q = client.get("/integrations/buffer/?status=videos&video_sub=queue")
    assert res_q.status_code == 200
    html_q = res_q.data.decode("utf-8")
    assert "Vídeos na Fila do Sistema" in html_q
    assert "Vídeos Agendados no Buffer" not in html_q

    res_s = client.get("/integrations/buffer/?status=videos&video_sub=scheduled")
    assert res_s.status_code == 200
    html_s = res_s.data.decode("utf-8")
    assert "Vídeos Agendados no Buffer" in html_s
    assert "Vídeos na Fila do Sistema" not in html_s


def test_video_preview_renders_video_player_and_excludes_non_video_tiktok(client, connected):
    v_queue = buffer.enqueue_post(
        channel_id="li1",
        channel_name="Ilton Batista",
        service="linkedin",
        text="Vídeo LinkedIn na fila",
        image_urls=["https://example.com/aula-tokens.mp4"],
    )
    tt_image = buffer.enqueue_post(
        channel_id="tt1",
        channel_name="iltonbsilva",
        service="tiktok",
        text="Post TikTok apenas imagem",
        image_urls=["https://example.com/card.png"],
    )
    assert v_queue.is_video is True
    assert tt_image.is_video is False

    res = client.get("/integrations/buffer/?status=videos")
    assert res.status_code == 200
    assert "media-src 'self' blob: https:" in res.headers.get("Content-Security-Policy", "")
    html = res.get_data(as_text=True)
    assert "Vídeo LinkedIn na fila" in html
    assert "Post TikTok apenas imagem" not in html
    assert 'data-media-type="video"' in html
    assert '<video src="https://example.com/aula-tokens.mp4#t=0.5"' in html

    edit_html = client.get(f"/integrations/buffer/queue/{v_queue.id}/edit?tab=videos").get_data(as_text=True)
    assert '<video class="buffer-edit-video" src="https://example.com/aula-tokens.mp4"' in edit_html


def test_error_tab_shows_edit_share_now_and_buffer_link(client, connected):
    res = client.get("/integrations/buffer/?status=error")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "✏️ Editar" in html
    assert "⚡ Postar agora" in html
    assert "https://publish.buffer.com/channels/li1" in html
    assert "Abrir no Buffer" in html
    assert "falhou" in html


def test_queue_error_shows_message_and_clears_on_edit(client, connected, db):
    p = buffer.enqueue_post(
        channel_id="li1",
        channel_name="Ilton Batista",
        service="linkedin",
        text="Post com erro na fila",
        image_urls=["https://example.com/v.mp4"],
    )
    p.status = "error"
    p.error_message = "LinkedIn rejeitou formato"
    db.session.commit()

    html = client.get("/integrations/buffer/?status=queue").get_data(as_text=True)
    assert "LinkedIn rejeitou formato" in html
    assert "https://publish.buffer.com/channels/li1" in html

    res_post = client.post(f"/integrations/buffer/queue/{p.id}/edit?tab=videos", data={
        "text": "Texto corrigido",
        "due_date": "2026-12-01",
        "due_time": "08:00",
        "tab": "videos",
    })
    assert res_post.status_code == 302
    assert "status=videos" in res_post.headers["Location"]
    updated = buffer.get_queue_post(p.id)
    assert updated.status == "pending"
    assert updated.error_message is None


def test_channels_bar_shows_youtube_without_duplicating_and_when_connected(client, connected, monkeypatch):
    from app.integrations import youtube
    from app.integrations.buffer import routes as buf_routes
    from types import SimpleNamespace

    buf_routes._YT_CHANNEL_CACHE.clear()
    # 1. Quando CHANNELS já tem yt1, não duplica
    html = client.get("/integrations/buffer/").get_data(as_text=True)
    assert "▶ YouTube" in html

    # 2. Quando Buffer não retorna YouTube, mostra canal YouTube direto do Shadow System
    monkeypatch.setattr(buf_routes, "channels", lambda: [c for c in buffer.channels() if c.service != "youtube"])
    monkeypatch.setattr(youtube, "is_authorized", lambda: True)
    monkeypatch.setattr(youtube, "channel_info", lambda: SimpleNamespace(title="Cultura IB"))
    html2 = client.get("/integrations/buffer/").get_data(as_text=True)
    assert "▶ YouTube · Cultura IB" in html2
    assert "/integrations/youtube/" in html2


def test_detailed_filters_multi_service_origin_media_date_and_search(client, connected, db, monkeypatch):
    from app.integrations.buffer import routes as buf_routes
    from app.integrations import youtube
    from app.integrations.youtube.client import YouTubeVideo

    buf_routes._YT_VIDEOS_CACHE.clear()

    # Fila com TikTok (vídeo) + Instagram (vídeo com erro)
    buffer.enqueue_post(
        channel_id="tt1",
        service="tiktok",
        channel_name="ilton_tt",
        text="Post TikTok sobre tokens #ia",
        image_urls=["https://example.com/uploads/voce-nao-paga-a-ia-por-palavras.mp4"],
        target_date=date(2026, 12, 10),
        target_time="18:30",
    )
    err_q = buffer.enqueue_post(
        channel_id="ig1",
        service="instagram",
        channel_name="iltonbsilva",
        text="Post Instagram erro antigo",
        image_urls=["https://example.com/uploads/outro-video.mp4"],
        target_date=date(2026, 12, 20),
        target_time="18:30",
    )
    err_q.status = "error"
    err_q.error_message = "Falha de token"
    db.session.commit()

    # YouTube direto (1 agendado + 1 publicado)
    yt_videos = [
        YouTubeVideo(
            id="yt_vid_1",
            title="Você Não Paga a IA por Palavras 🤯 #Shorts",
            description="Explicando tokens na prática",
            thumbnail_url="https://i.ytimg.com/vi/yt_vid_1/hqdefault.jpg",
            published_at=datetime(2026, 11, 10, 12, 0),
            privacy_status="private",
            url="https://youtu.be/yt_vid_1",
            is_short=True,
            publish_at=datetime(2026, 12, 10, 18, 30),
        ),
        YouTubeVideo(
            id="yt_vid_2",
            title="Video Antigo Publicado",
            description="Outro conteudo",
            thumbnail_url="https://i.ytimg.com/vi/yt_vid_2/hqdefault.jpg",
            published_at=datetime(2026, 10, 1, 10, 0),
            privacy_status="public",
            url="https://youtu.be/yt_vid_2",
            is_short=False,
        ),
    ]
    monkeypatch.setattr(youtube, "is_authorized", lambda: True)
    monkeypatch.setattr(youtube, "recent_videos", lambda max_results=25: yt_videos)

    # 1. Somente TikTok
    html_tt = client.get("/integrations/buffer/?status=all&service=tiktok").get_data(as_text=True)
    assert "Post TikTok sobre tokens" in html_tt
    assert "Depois" not in html_tt
    assert "Você Não Paga a IA por Palavras" not in html_tt

    # 2. Multi-seleção Instagram + YouTube (sem TikTok nem LinkedIn)
    html_multi = client.get("/integrations/buffer/?status=all&service=instagram&service=youtube").get_data(as_text=True)
    assert "Depois" in html_multi
    assert "Você Não Paga a IA por Palavras" in html_multi
    assert "Post TikTok sobre tokens" not in html_multi
    assert "Antes" not in html_multi

    # 3. Origem = queue vs youtube
    html_q = client.get("/integrations/buffer/?status=all&source=queue").get_data(as_text=True)
    assert "Post TikTok sobre tokens" in html_q
    assert "Depois" not in html_q
    assert "Você Não Paga a IA por Palavras" not in html_q

    html_yt = client.get("/integrations/buffer/?status=all&source=youtube").get_data(as_text=True)
    assert "Você Não Paga a IA por Palavras" in html_yt
    assert "Post TikTok sobre tokens" not in html_yt

    # 4. Tipo de mídia (imagem vs vídeo)
    html_img = client.get("/integrations/buffer/?status=all&media_type=image").get_data(as_text=True)
    assert "Depois" in html_img
    assert "Post TikTok sobre tokens" not in html_img

    # 5. Status específico (error)
    html_err = client.get("/integrations/buffer/?status=all&post_status=error").get_data(as_text=True)
    assert "Post Instagram erro antigo" in html_err
    assert "Antes" in html_err  # FakeBuffer retorna p1 com error={'message': 'falhou'}
    assert "Depois" not in html_err

    # 6. Período de datas (date_from -> date_to)
    html_dates = client.get("/integrations/buffer/?status=all&date_from=2026-12-09&date_to=2026-12-11").get_data(as_text=True)
    assert "Post TikTok sobre tokens" in html_dates
    assert "Você Não Paga a IA por Palavras" in html_dates
    assert "Post Instagram erro antigo" not in html_dates
    assert "Depois" not in html_dates

    # 7. Busca livre sem acento e por nome de arquivo
    html_search = client.get("/integrations/buffer/?status=all&q=voce nao paga a ia").get_data(as_text=True)
    assert "Post TikTok sobre tokens" in html_search
    assert "Você Não Paga a IA por Palavras" in html_search
    assert "Post Instagram erro antigo" not in html_search


def test_grouped_view_unifies_same_post_across_networks_and_grid_view(client, connected, monkeypatch):
    from app.integrations.buffer import filters, routes as buf_routes
    from app.integrations import youtube
    from app.integrations.youtube.client import YouTubeVideo

    buf_routes._YT_VIDEOS_CACHE.clear()

    # Mesmo vídeo agendado para Instagram e LinkedIn na Fila do Sistema + no YouTube API
    buffer.enqueue_post(
        channel_id="ig1",
        service="instagram",
        channel_name="iltonbsilva",
        text="Legenda casual Reels sobre tokens",
        image_urls=["https://example.com/uploads/voce-nao-paga-a-ia-por-palavras.mp4"],
        target_date=date(2026, 12, 12),
        target_time="18:30",
    )
    buffer.enqueue_post(
        channel_id="li1",
        service="linkedin",
        channel_name="Ilton Silva",
        text="Artigo executivo LinkedIn sobre economia de tokens em LLMs",
        image_urls=["https://example.com/uploads/voce-nao-paga-a-ia-por-palavras.mp4"],
        target_date=date(2026, 12, 12),
        target_time="18:30",
    )
    monkeypatch.setattr(youtube, "is_authorized", lambda: True)
    monkeypatch.setattr(youtube, "recent_videos", lambda max_results=25: [
        YouTubeVideo(
            id="yt_same_1",
            title="Você Não Paga a IA por Palavras 🤯 #Shorts",
            description="Shorts sobre tokens",
            thumbnail_url="https://i.ytimg.com/vi/yt_same_1/hqdefault.jpg",
            published_at=datetime(2026, 11, 10, 12, 0),
            privacy_status="private",
            url="https://youtu.be/yt_same_1",
            is_short=True,
            publish_at=datetime(2026, 12, 12, 18, 30),
        ),
    ])

    # Verifica unidade pura group_posts
    q_items = [filters.from_queue_post(p) for p in buffer.list_queue_posts()]
    yt_items = [filters.from_youtube_video(v) for v in youtube.recent_videos()]
    groups = filters.group_posts(q_items + yt_items)
    assert len(groups) == 1
    assert set(groups[0].services) == {"instagram", "linkedin", "youtube"}
    assert len(groups[0].items) == 3

    # Verifica rota HTML view=grouped
    html_grouped = client.get("/integrations/buffer/?status=all&view=grouped&service=instagram&service=linkedin&service=youtube").get_data(as_text=True)
    assert "buffer-group-card" in html_grouped
    assert "Legenda casual Reels sobre tokens" in html_grouped
    assert "Artigo executivo LinkedIn" in html_grouped
    assert "Você Não Paga a IA por Palavras" in html_grouped
    assert "3 publicação(ões)" in html_grouped

    # Verifica rota HTML view=grid e ordenação
    html_grid = client.get("/integrations/buffer/?status=all&view=grid&sort=service").get_data(as_text=True)
    assert "buffer-cards-grid" in html_grid
    assert "buffer-grid-card" in html_grid


def test_youtube_client_recent_videos_populates_publish_at():
    from app.integrations.youtube.client import YouTubeClient

    class _Exec:
        def __init__(self, payload):
            self._payload = payload

        def execute(self):
            return self._payload

    class _PlaylistItems:
        def list(self, **kwargs):
            return _Exec({
                "items": [{
                    "snippet": {
                        "title": "Video Agendado",
                        "description": "Desc",
                        "publishedAt": "2026-11-10T12:00:00Z",
                        "resourceId": {"videoId": "vid_sched_1"},
                        "thumbnails": {"high": {"url": "https://img/thumb.jpg"}},
                    },
                    "status": {"privacyStatus": "private"},
                }]
            })

    class _Channels:
        def list(self, **kwargs):
            return _Exec({"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU_test"}}}]})

    class _Videos:
        def list(self, **kwargs):
            return _Exec({
                "items": [{
                    "id": "vid_sched_1",
                    "status": {
                        "privacyStatus": "private",
                        "publishAt": "2026-12-01T21:30:00Z",
                    },
                }]
            })

    class _Svc:
        def channels(self):
            return _Channels()

        def playlistItems(self):
            return _PlaylistItems()

        def videos(self):
            return _Videos()

    from datetime import timezone
    yt = YouTubeClient(_Svc())
    vids = yt.recent_videos(max_results=5)
    assert len(vids) == 1
    assert vids[0].is_scheduled is True
    assert vids[0].publish_at == datetime(2026, 12, 1, 21, 30, tzinfo=timezone.utc)





