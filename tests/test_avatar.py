"""Avatar gerado da foto: estilos, foto original privada, remoção e evolução visual por rank."""
import io

import pytest
from PIL import Image

from app.core import accounts
from app.core.errors import DomainError
from app.core.tenancy import as_user
from app.modules.hunter import avatar, services as hunter


def _photo() -> bytes:
    image = Image.new("RGB", (1200, 900), (200, 150, 120))
    out = io.BytesIO()
    image.save(out, "JPEG")
    return out.getvalue()


def test_each_style_generates_a_portrait():
    image = Image.open(io.BytesIO(_photo())).convert("RGB")
    gen = avatar.provider()
    for style in gen.styles:
        result = Image.open(io.BytesIO(gen.generate(image, style)))
        assert result.size == avatar.SIZE and result.format == "WEBP"


def test_upload_sets_status_avatar_and_restyle(app):
    row = hunter.upload_avatar(_photo(), "shadow")
    assert hunter.get_status().avatar_url.startswith("/hunter/avatar/1.webp?v=1")
    hunter.restyle_avatar("monarch")
    assert hunter.get_avatar().style == "monarch" and hunter.get_avatar().version == row.version
    with pytest.raises(DomainError):
        hunter.upload_avatar(_photo(), "estilo-que-nao-existe")


def test_original_photo_can_be_deleted_and_is_owner_only(app, client):
    hunter.upload_avatar(_photo(), "hologram")
    assert client.get("/hunter/avatar/foto-original").status_code == 200
    user, code = accounts.invite_tester("av@example.com", "Av")
    accounts.accept_invite(code, "Av", "12345678")
    with client.session_transaction() as session:
        session["uid"] = user.id
    assert client.get("/hunter/avatar/1.webp").status_code == 200       # avatar estilizado: visível na Arena
    assert client.get("/hunter/avatar/foto-original").status_code == 404  # a foto do dono, nunca
    with client.session_transaction() as session:
        session.pop("uid")
    hunter.delete_avatar_photo()
    assert hunter.get_avatar().photo is None and hunter.get_status().avatar_url
    with pytest.raises(DomainError):
        hunter.restyle_avatar("shadow")


def test_remove_goes_back_to_default(app):
    hunter.upload_avatar(_photo(), "classic")
    hunter.remove_avatar()
    assert hunter.get_status().avatar_url == ""


def test_profile_shows_rank_frame(app, client):
    hunter.upload_avatar(_photo(), "shadow")
    page = client.get("/hunter/").get_data(as_text=True)
    assert "avatar-rank-e" in page and "Gerar avatar" not in page and "Trocar foto" in page


def test_avatar_is_per_user(app):
    hunter.upload_avatar(_photo(), "shadow")
    user, code = accounts.invite_tester("av2@example.com")
    accounts.accept_invite(code, "B", "12345678")
    with as_user(user.id):
        assert hunter.get_avatar() is None and hunter.get_status().avatar_url == ""
