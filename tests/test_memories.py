"""Memórias: upload otimizado sem metadados, ligação com missão, privacidade, filtros e exclusão."""
import io

import pytest
from PIL import Image

from app.core import accounts
from app.core.errors import DomainError
from app.core.tenancy import as_user
from app.modules.arena import feed
from app.modules.memories import services as memories
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


def _photo(size=(2400, 1800), with_gps=True) -> bytes:
    image = Image.new("RGB", size, (30, 60, 200))
    out = io.BytesIO()
    exif = Image.Exif()
    if with_gps:
        exif[0x8825] = {1: "S", 2: (23.0, 33.0, 0.0)}  # GPSInfo
        exif[0x0110] = "Celular Teste"                   # Model
    image.save(out, "JPEG", exif=exif)
    return out.getvalue()


def _tester():
    user, code = accounts.invite_tester("mem@example.com", "Mem")
    accounts.accept_invite(code, "Mem", "12345678")
    return user


def test_upload_is_resized_and_metadata_stripped(app):
    memory = memories.create(memories.MemoryInput(title="Primeiro treino", kind="workout"), _photo())
    assert max(memory.width, memory.height) == memories.IMAGE_SIDE
    stored = Image.open(io.BytesIO(memory.image))
    assert stored.format == "WEBP" and not stored.getexif()
    assert len(memory.thumb) < len(memory.image)


def test_invalid_file_is_rejected(app):
    with pytest.raises(DomainError):
        memories.create(memories.MemoryInput(title="x"), b"isso nao e imagem")
    with pytest.raises(DomainError):
        memories.create(memories.MemoryInput(title=""), _photo())


def test_memory_linked_to_quest_takes_category(app):
    category = quests.save_category("Corpo", "#f97316", [], specialty="body")
    quest = quests.create_quest(QuestInput(title="Correr 5 km", estimated_minutes=40, category_id=category.id))
    quests.complete_quest(quest.id)
    memory = memories.create(memories.MemoryInput(title="5 km!", quest_id=quest.id), _photo((800, 600)))
    assert memory.specialty == "body" and memory.quest_title == "Correr 5 km" and memory.rank_code == "E"
    assert memories.for_quest(quest.id) == [memory]


def test_private_by_default_and_hidden_from_others(app, client):
    memory = memories.create(memories.MemoryInput(title="Privada"), _photo((600, 400)))
    other = _tester()
    with client.session_transaction() as session:
        session["uid"] = other.id
    assert client.get(f"/memorias/publica/{memory.id}").status_code == 404
    assert client.get(f"/memorias/{memory.id}/foto").status_code == 404
    with as_user(other.id):
        with pytest.raises(Exception):
            memories.get(memory.id)


def test_public_memory_is_visible_and_can_go_to_feed(app, client):
    memory = memories.create(memories.MemoryInput(title="Projeto entregue", description="App no ar", public=True,
                                                  share_in_feed=True, note="segredo"), _photo((600, 400)))
    assert any(item.memory_id == memory.id for item in feed.recent())
    other = _tester()
    with client.session_transaction() as session:
        session["uid"] = other.id
    page = client.get(f"/memorias/publica/{memory.id}").get_data(as_text=True)
    assert "Projeto entregue" in page and "segredo" not in page  # observação pessoal nunca aparece
    assert client.get(f"/memorias/{memory.id}/foto").status_code == 200


def test_private_memory_never_goes_to_feed(app):
    memories.create(memories.MemoryInput(title="Só minha", share_in_feed=True), _photo((300, 300)))
    assert not any(item.kind == "memory" for item in feed.recent())


def test_filters_and_search(app):
    memories.create(memories.MemoryInput(title="Livro de SQL", kind="book"), _photo((300, 300)))
    memories.create(memories.MemoryInput(title="Supino", kind="workout"), _photo((300, 300)))
    assert [m.title for m in memories.gallery(kind="book")] == ["Livro de SQL"]
    assert [m.title for m in memories.gallery(search="supi")] == ["Supino"]
    assert memories.gallery(visibility="public") == []


def test_delete_removes_photo_and_feed_post(app):
    memory = memories.create(memories.MemoryInput(title="Apagar", public=True, share_in_feed=True), _photo((300, 300)))
    memories.delete(memory.id)
    assert memories.gallery() == [] and not any(i.memory_id == memory.id for i in feed.recent())


def test_upload_route_and_gallery_page(app, client):
    response = client.post("/memorias/nova", data={"title": "Via tela", "kind": "goal",
                                                   "photo": (io.BytesIO(_photo((500, 500))), "foto.jpg")},
                           content_type="multipart/form-data")
    assert response.status_code == 302
    assert "Via tela" in client.get("/memorias/").get_data(as_text=True)
