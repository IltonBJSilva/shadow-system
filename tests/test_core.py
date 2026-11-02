from datetime import datetime, timezone

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.core import settings, time


def test_health_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


def test_security_headers_are_set(client):
    response = client.get("/health")
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_settings_roundtrip(app):
    assert settings.get_setting("missing", default=[1]) == [1]
    settings.set_setting("widgets", ["a", "b"])
    assert settings.get_setting("widgets") == ["a", "b"]
    settings.set_setting("widgets", ["c"])
    assert settings.get_setting("widgets") == ["c"]


def test_to_local_naive_converts_timezone(app):
    utc_noon = datetime(2026, 1, 10, 15, 0, tzinfo=timezone.utc)
    assert time.to_local_naive(utc_noon) == datetime(2026, 1, 10, 12, 0)  # São Paulo = UTC-3


def test_unknown_page_returns_404(client):
    assert client.get("/nao-existe").status_code == 404


def _auth_app():
    return create_app("testing", {
        "AUTH_ENABLED": True,
        "OWNER_USERNAME": "hunter",
        "OWNER_PASSWORD_HASH": generate_password_hash("arise"),
    })


def test_login_required_when_enabled():
    app = _auth_app()
    client = app.test_client()
    response = client.get("/some-page")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert client.get("/health").status_code == 200


def test_login_with_valid_and_invalid_password():
    app = _auth_app()
    client = app.test_client()
    bad = client.post("/login", data={"username": "hunter", "password": "wrong"})
    assert bad.status_code == 200
    with client.session_transaction() as session:
        assert "user" not in session

    good = client.post("/login?next=//evil.com", data={"username": "hunter", "password": "arise"})
    assert good.status_code == 302
    assert good.headers["Location"] == "/"  # não segue next externo
    with client.session_transaction() as session:
        assert session["user"] == "hunter"


def test_login_locks_after_repeated_failures():
    from app.core import security

    security._FAILURES.clear()
    client = _auth_app().test_client()
    for _ in range(5):
        client.post("/login", data={"username": "hunter", "password": "wrong"})
    locked = client.post("/login", data={"username": "hunter", "password": "arise"})
    assert locked.status_code == 429  # nem a senha certa entra durante o bloqueio
    security._FAILURES.clear()


def test_production_refuses_to_start_without_login():
    with pytest.raises(RuntimeError, match="AUTH_ENABLED"):
        create_app("production", {"SECRET_KEY": "x" * 32, "AUTH_ENABLED": False})


def test_production_behind_https_proxy():
    app = create_app("production", {
        "SECRET_KEY": "x" * 32, "AUTH_ENABLED": True, "OWNER_PASSWORD_HASH": generate_password_hash("arise"),
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    from flask import request

    app.add_url_rule("/_scheme", "scheme", lambda: request.url)
    from app.core import security
    security.PUBLIC_ENDPOINTS.add("scheme")
    try:
        response = app.test_client().get("/_scheme", headers={"X-Forwarded-Proto": "https"},
                                         base_url="http://hunter.pythonanywhere.com")
    finally:
        security.PUBLIC_ENDPOINTS.discard("scheme")
    # O callback do Google usa request.url: atrás do proxy ele precisa sair como https.
    assert response.get_data(as_text=True).startswith("https://hunter.pythonanywhere.com/")
    assert app.config["SESSION_COOKIE_SECURE"]
