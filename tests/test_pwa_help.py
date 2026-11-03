"""App instalável (PWA), páginas de ajuda/novidades e matriz de prioridades."""
from datetime import timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from app.core import accounts, time
from app.extensions import db as _db
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


def test_manifest_and_service_worker(client):
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200 and manifest.mimetype == "application/manifest+json"
    assert manifest.json["display"] == "standalone" and len(manifest.json["icons"]) == 3
    sw = client.get("/sw.js")
    assert sw.status_code == 200 and "javascript" in sw.mimetype and b"caches" in sw.data
    assert client.get("/static/img/icon-192.png").status_code == 200


def test_pwa_files_are_public_even_with_login():
    app = create_app("testing", {"AUTH_ENABLED": True, "OWNER_PASSWORD_HASH": generate_password_hash("x")})
    with app.app_context():
        _db.create_all()
        accounts.ensure_owner()
        client = app.test_client()
        for path in ("/manifest.webmanifest", "/sw.js", "/offline"):
            assert client.get(path).status_code == 200, path
        assert client.get("/como-usar").status_code == 302  # ajuda é para quem já entrou
        _db.session.remove()
        _db.drop_all()


def test_help_and_changelog_pages(client):
    assert "Instalar no celular" in client.get("/como-usar").get_data(as_text=True)
    assert "A grande evolução" in client.get("/novidades").get_data(as_text=True)
    page = client.get("/").get_data(as_text=True)
    assert 'rel="manifest"' in page and "Como usar" in page


def test_priority_matrix_quadrants(app):
    today = time.today()
    quests.create_quest(QuestInput(title="Prova amanhã", priority="critical", due_date=today + timedelta(days=1), estimated_minutes=60))
    quests.create_quest(QuestInput(title="Projeto do ano", quest_type="main", estimated_minutes=120))
    quests.create_quest(QuestInput(title="Responder e-mail", priority="low", due_date=today, estimated_minutes=10))
    quests.create_quest(QuestInput(title="Organizar gaveta", priority="low", estimated_minutes=15))
    matrix = quests.priority_matrix(today)
    assert [q.title for q in matrix["do"]] == ["Prova amanhã"]
    assert [q.title for q in matrix["plan"]] == ["Projeto do ano"]
    assert [q.title for q in matrix["delegate"]] == ["Responder e-mail"]
    assert [q.title for q in matrix["drop"]] == ["Organizar gaveta"]


def test_matrix_page_and_voice_button(app, client):
    assert client.get("/quests/matriz").status_code == 200
    # O botão de voz só aparece com a IA do Arquiteto ligada; o JS o mostra se o navegador tiver reconhecimento de fala.
    source = open("app/templates/architect/index.html", encoding="utf-8").read()
    assert 'data-voice-for="question"' in source
