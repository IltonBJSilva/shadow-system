"""Segurança: login opcional do dono, cabeçalhos HTTP e comando para gerar hash de senha.

O Shadow System tem um único usuário (você). Com AUTH_ENABLED=false o app fica aberto e deve
rodar só em 127.0.0.1. Antes de expor em rede, ligue o login (ver docs/security.md).
"""
import hmac

import click
from flask import (Blueprint, Flask, current_app, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("security", __name__)

PUBLIC_ENDPOINTS = {"security.login", "static", "core.health"}

# Política de conteúdo: só recursos do próprio app. 'unsafe-inline' em estilos é necessário
# para larguras de barras de progresso definidas no template (style="width: 40%").
CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
)


def check_credentials(username: str, password: str) -> bool:
    cfg = current_app.config
    password_hash = cfg.get("OWNER_PASSWORD_HASH", "")
    if not password_hash:
        return False
    same_user = hmac.compare_digest(username.encode(), cfg.get("OWNER_USERNAME", "").encode())
    return same_user and check_password_hash(password_hash, password)


def register(app: Flask) -> None:
    app.register_blueprint(bp)

    @app.before_request
    def require_login():
        if not app.config.get("AUTH_ENABLED") or request.endpoint in PUBLIC_ENDPOINTS:
            return None
        if session.get("user"):
            return None
        return redirect(url_for("security.login", next=request.path))

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("Content-Security-Policy", CSP)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.context_processor
    def inject_auth():
        return {"auth_enabled": app.config.get("AUTH_ENABLED"), "current_user": session.get("user")}

    @app.cli.group("security")
    def security_cli():
        """Comandos de segurança."""

    @security_cli.command("hash-password")
    @click.password_option("--password", prompt="Nova senha")
    def hash_password(password: str):
        """Gera o OWNER_PASSWORD_HASH para colocar no .env."""
        click.echo(generate_password_hash(password))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if not current_app.config.get("AUTH_ENABLED"):
        return redirect("/")
    if request.method == "POST":
        username = request.form.get("username", "")
        if check_credentials(username, request.form.get("password", "")):
            session.clear()
            session["user"] = username
            return redirect(_safe_next(request.args.get("next", "")))
        flash("Usuário ou senha incorretos.", "error")
    return render_template("security/login.html")


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("security.login"))


def _safe_next(target: str) -> str:
    """Evita redirecionar para outro site depois do login (open redirect)."""
    return target if target.startswith("/") and not target.startswith("//") else "/"
