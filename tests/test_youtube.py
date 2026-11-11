"""Testes da integração direta com o YouTube (YouTube Data API v3)."""
import io
from datetime import datetime, timezone
from pathlib import Path
import pytest

from app.integrations import youtube
from app.integrations.google_calendar import oauth
from app.integrations.youtube import YouTubeError, YouTubeVideo, ChannelInfo


class _Req:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeYouTubeService:
    def __init__(self):
        self.uploaded = []

    def channels(self):
        fake = self

        class Channels:
            def list(self, part, mine):
                return _Req({
                    "items": [{
                        "id": "UC_TEST_123",
                        "snippet": {
                            "title": "Ilton Tech",
                            "description": "Canal oficial de Tecnologia e IA",
                            "customUrl": "@iltontech",
                            "thumbnails": {"default": {"url": "https://img/avatar.jpg"}},
                        },
                        "statistics": {
                            "videoCount": "42",
                            "subscriberCount": "1250",
                        },
                        "contentDetails": {
                            "relatedPlaylists": {"uploads": "UU_TEST_123"}
                        },
                    }]
                })
        return Channels()

    def playlistItems(self):
        class PlaylistItems:
            def list(self, part, playlistId, maxResults):
                return _Req({
                    "items": [{
                        "snippet": {
                            "resourceId": {"videoId": "vid_abc123"},
                            "title": "O que é Token em IA? #Shorts",
                            "description": "Explicando tokens em 60s.",
                            "publishedAt": "2026-11-09T18:30:00Z",
                            "thumbnails": {"default": {"url": "https://img/thumb.jpg"}},
                        },
                        "status": {"privacyStatus": "public"},
                    }]
                })
        return PlaylistItems()

    def videos(self):
        fake = self

        class Videos:
            def insert(self, part, body, media_body):
                fake.uploaded.append({"body": body, "media": media_body})
                vid_id = f"vid_new_{len(fake.uploaded)}"
                return _Req({
                    "id": vid_id,
                    "snippet": {
                        "title": body["snippet"]["title"],
                        "description": body["snippet"]["description"],
                        "thumbnails": {"medium": {"url": f"https://img/{vid_id}.jpg"}},
                    },
                    "status": body["status"],
                })
        return Videos()


@pytest.fixture
def fake_youtube(monkeypatch):
    fake = FakeYouTubeService()
    monkeypatch.setattr(youtube, "_service_factory", lambda: fake)
    # Simula autenticado com o escopo do YouTube
    monkeypatch.setattr(oauth, "is_connected", lambda: True)
    monkeypatch.setattr(oauth, "is_configured", lambda: True)
    monkeypatch.setattr(oauth, "has_scope", lambda s: s in (oauth.YOUTUBE_UPLOAD_SCOPE, oauth.YOUTUBE_READONLY_SCOPE))
    return fake


def test_youtube_status(monkeypatch):
    monkeypatch.setattr(oauth, "is_configured", lambda: False)
    assert youtube.status().state == "not_configured"

    monkeypatch.setattr(oauth, "is_configured", lambda: True)
    monkeypatch.setattr(oauth, "is_connected", lambda: False)
    assert youtube.status().state == "configured"

    monkeypatch.setattr(oauth, "is_connected", lambda: True)
    monkeypatch.setattr(oauth, "has_scope", lambda s: True)
    assert youtube.status().state == "connected"


def test_channel_info_and_recent_videos(fake_youtube):
    ch = youtube.channel_info()
    assert ch is not None
    assert ch.title == "Ilton Tech"
    assert ch.video_count == 42
    assert ch.subscriber_count == 1250

    vids = youtube.recent_videos()
    assert len(vids) == 1
    assert vids[0].id == "vid_abc123"
    assert vids[0].is_short is True
    assert vids[0].url == "https://youtu.be/vid_abc123"


def test_upload_video_now(fake_youtube):
    data = b"fake video bytes content"
    vid = youtube.upload_video(
        media_source=data,
        title="Aprendendo Inteligencia Artificial",
        description="Video explicativo",
        tags=["ia", "python"],
        is_short=True,
    )
    assert vid.id == "vid_new_1"
    assert "#Shorts" in vid.title
    assert len(fake_youtube.uploaded) == 1
    item = fake_youtube.uploaded[0]
    assert item["body"]["status"]["privacyStatus"] == "public"
    assert "Shorts" in item["body"]["snippet"]["tags"]


def test_upload_video_scheduled(fake_youtube):
    data = b"video data"
    future_utc = datetime(2026, 11, 20, 21, 30, tzinfo=timezone.utc)
    vid = youtube.upload_video(
        media_source=data,
        title="Tokens e embeddings",
        description="Aula rapida",
        publish_at_utc=future_utc,
        is_short=False,
    )
    assert vid.id == "vid_new_1"
    item = fake_youtube.uploaded[0]
    assert item["body"]["status"]["privacyStatus"] == "private"
    assert item["body"]["status"]["publishAt"] == "2026-11-20T21:30:00.000Z"


def test_youtube_routes(client, fake_youtube, tmp_path):
    # GET index
    res = client.get("/integrations/youtube/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Ilton Tech" in html
    assert "vid_abc123" in html

    # GET connect
    res_conn = client.get("/integrations/youtube/connect")
    assert res_conn.status_code == 302
    assert "youtube=1" in res_conn.headers["Location"]

    # POST upload com arquivo
    res_up = client.post("/integrations/youtube/upload", data={
        "title": "Shorts de Teste",
        "description": "Descricao do teste",
        "tags": "ia, shorts",
        "mode": "now",
        "is_short": "1",
        "video_file": (io.BytesIO(b"dummy video"), "test.mp4"),
    }, content_type="multipart/form-data")
    assert res_up.status_code == 302
    assert len(fake_youtube.uploaded) == 1

    # POST upload com caminho local
    test_file = tmp_path / "render.mp4"
    test_file.write_bytes(b"render video bytes")
    res_path = client.post("/integrations/youtube/upload", data={
        "title": "Shorts via caminho local",
        "file_path": str(test_file),
        "mode": "schedule",
        "schedule_date": "2026-11-25",
        "schedule_time": "19:00",
        "is_short": "1",
    })
    assert res_path.status_code == 302
    assert len(fake_youtube.uploaded) == 2
    assert fake_youtube.uploaded[1]["body"]["status"]["privacyStatus"] == "private"


def test_youtube_edge_cases_render(client, fake_youtube, monkeypatch):
    from app.integrations.youtube import routes as yt_routes
    # 1. Not authorized: should show connect prompt and upload form
    monkeypatch.setattr(yt_routes, "is_authorized", lambda: False)
    res = client.get("/integrations/youtube/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Conectar Canal do YouTube" in html
    assert "Enviar ou Agendar" in html

    # 2. Authorized but channel is None (no channel created yet)
    monkeypatch.setattr(yt_routes, "is_authorized", lambda: True)
    class FakeNoChannelClient:
        def channel_info(self):
            return None
        def recent_videos(self, max_results=12):
            return []
    monkeypatch.setattr(yt_routes, "get_client", lambda: FakeNoChannelClient())
    res2 = client.get("/integrations/youtube/")
    assert res2.status_code == 200
    html2 = res2.data.decode("utf-8")
    assert "Sem Canal Detectado" in html2
    assert "Enviar ou Agendar" in html2

    # 3. Communication error with YouTube API
    class FakeErrorClient:
        def channel_info(self):
            raise YouTubeError("YouTube Data API v3 has not been used in project")
    monkeypatch.setattr(yt_routes, "get_client", lambda: FakeErrorClient())
    res3 = client.get("/integrations/youtube/")
    assert res3.status_code == 200
    html3 = res3.data.decode("utf-8")
    assert "Erro no YouTube" in html3
    assert "YouTube Data API v3 has not been used" in html3


def test_nav_items_contains_youtube(client):
    res = client.get("/integrations/youtube/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "YouTube" in html
    assert "/integrations/youtube/" in html


