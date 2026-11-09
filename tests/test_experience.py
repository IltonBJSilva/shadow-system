"""Inicialização do System: aparece conforme a preferência e nunca na tela de login."""
from werkzeug.security import generate_password_hash

from app import create_app
from app.core import experience
from app.extensions import db


def test_boot_overlay_is_rendered_by_default(client):
    html = client.get("/").get_data(as_text=True)
    assert "data-boot" in html and 'data-boot-mode="session"' in html
    assert experience.MANIFESTO in html and "SISTEMA ATIVADO." in html


def test_boot_can_be_turned_off_in_settings(client):
    client.post("/dashboard/settings", data={"widgets": ["status"], "boot_mode": "off"})
    assert experience.boot_mode() == "off"
    assert "data-boot" not in client.get("/").get_data(as_text=True)
    client.post("/dashboard/settings", data={"widgets": ["status"], "boot_mode": "x"})
    assert experience.boot_mode() == "session"  # valor estranho volta ao padrão


def test_settings_page_lists_boot_modes(client):
    html = client.get("/dashboard/settings").get_data(as_text=True)
    assert "Inicialização do System" in html and 'value="dashboard"' in html


def test_no_boot_on_login_page():
    app = create_app("testing", {"AUTH_ENABLED": True, "OWNER_PASSWORD_HASH": generate_password_hash("x")})
    with app.app_context():
        db.create_all()
    assert "data-boot" not in app.test_client().get("/login").get_data(as_text=True)


def test_sidebar_hidden_on_login_page():
    app = create_app("testing", {"AUTH_ENABLED": True, "OWNER_PASSWORD_HASH": generate_password_hash("x")})
    with app.app_context():
        db.create_all()
    client = app.test_client()
    html = client.get("/login").get_data(as_text=True)
    assert 'class="sidebar"' not in html
    assert 'data-toggle-sidebar' not in html
