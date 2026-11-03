"""Mídias do System (áudio e imagens no banco) e página de Configurações."""
import io

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.core import accounts, media
from app.core.errors import DomainError
from app.extensions import db as _db

MP3 = b"ID3" + b"\x00" * 2048


def test_save_validates_type_and_size(app):
    with pytest.raises(DomainError):
        media.save("music", "trilha.txt", b"abc", "text/plain")
    with pytest.raises(DomainError):
        media.save("nao-existe", "a.mp3", MP3, "audio/mpeg")
    with pytest.raises(DomainError):
        media.save("boot", "grande.webp", b"x" * (media.MAX_BYTES["image"] + 1), "image/webp")
    asset = media.save("music", "trilha.mp3", MP3, "audio/mp3")
    assert asset.mimetype == "audio/mpeg" and asset.size == len(MP3)
    assert media.versions() == {"music": asset.etag[:10]}


def test_media_is_served_with_range_and_cache(app, client):
    media.save("entrance", "entrada.mp3", MP3, "audio/mpeg")
    full = client.get("/media/entrance")
    assert full.status_code == 200 and full.data == MP3
    assert "max-age" in full.headers["Cache-Control"]
    part = client.get("/media/entrance", headers={"Range": "bytes=0-9"})
    assert part.status_code == 206 and part.data == MP3[:10]
    assert client.get("/media/music").status_code == 404


def test_upload_page_is_owner_only(app, client):
    response = client.post("/configuracoes/midia/music", data={"file": (io.BytesIO(MP3), "trilha.mp3")},
                           content_type="multipart/form-data")
    assert response.status_code == 302
    assert media.get("music") is not None

    user, code = accounts.invite_tester("t@example.com")
    accounts.accept_invite(code, "T", "12345678")
    with client.session_transaction() as session:
        session["uid"] = user.id
    assert client.post("/configuracoes/midia/music/apagar").status_code == 403
    page = client.get("/configuracoes").get_data(as_text=True)
    assert "Mídias do System" not in page and "data-audio-pref" in page
    assert client.get("/media/music").status_code == 200  # testers também ouvem a música


def test_only_login_art_is_public_when_auth_is_on():
    app = create_app("testing", {"AUTH_ENABLED": True, "OWNER_PASSWORD_HASH": generate_password_hash("x")})
    with app.app_context():
        _db.create_all()
        accounts.ensure_owner()
        media.save("login", "login.webp", b"RIFF0000WEBP", "image/webp")
        media.save("music", "m.mp3", MP3, "audio/mpeg")
        client = app.test_client()
        assert client.get("/media/login").status_code == 200
        assert client.get("/media/music").status_code == 403
        _db.session.remove()
        _db.drop_all()


def test_layout_exposes_media_versions_and_experience(app, client):
    media.save("music", "m.mp3", MP3, "audio/mpeg")
    page = client.get("/").get_data(as_text=True)
    assert 'data-experience="main"' in page
    assert 'name="shadow-media"' in page and "music" in page
    assert "turbo-8.0.12.min.js" in page
    assert 'data-audio-toggle="music"' in page


def test_preferences_saves_boot_mode(app, client):
    client.post("/configuracoes", data={"boot_mode": "off"})
    from app.core import experience

    assert experience.boot_mode() == "off"
