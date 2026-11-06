"""Segurança: login (dono e usuários de teste), convites, cabeçalhos HTTP e comandos.

Com AUTH_ENABLED=false o app fica aberto (quem acessa é o dono) e deve rodar só em 127.0.0.1.
Antes de expor em rede, ligue o login (ver docs/security.md). Contas: core/accounts.py.
"""
import time
from functools import wraps

import click
from flask import (Blueprint, Flask, abort, current_app, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import generate_password_hash

from . import accounts
from . import time as clock
from .errors import DomainError
from .tenancy import OWNER_ID

bp = Blueprint("security", __name__)

# core.media confere o login por dentro: só a imagem da tela de acesso é pública.
# buffer.serve_upload é público para o Buffer baixar imagens de posts enviados do computador.
PUBLIC_ENDPOINTS = {"security.login", "security.invite", "static", "core.health", "core.media_file",
                    "core.manifest", "core.service_worker", "core.offline", "buffer.serve_upload"}

# Política de conteúdo: scripts e estilos só do próprio app. 'unsafe-inline' em estilos é necessário
# para larguras de barras de progresso definidas no template (style="width: 40%").
# Imagens HTTPS externas são permitidas para as miniaturas dos posts do Buffer.
# media-src 'self' blob:: músicas e efeitos do System são servidos pelo próprio app.
CSP = (
    "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; media-src 'self' blob:; worker-src 'self'; manifest-src 'self'; "
    "frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
)


def owner_required(view):
    """Páginas só do dono (usuários de teste, mídias do sistema)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_owner():
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def is_owner() -> bool:
    return g.get("user_id", OWNER_ID) == OWNER_ID


def register(app: Flask) -> None:
    app.register_blueprint(bp)

    @app.before_request
    def require_login():
        # Quem é o usuário desta requisição (filtro automático dos dados, ver core/tenancy.py).
        g.user_id = session.get("uid") or OWNER_ID
        if g.user_id != OWNER_ID and not _session_user_valid(g.user_id):
            session.clear()  # conta apagada ou bloqueada pelo dono
            g.user_id = OWNER_ID
            if app.config.get("AUTH_ENABLED") and request.endpoint not in PUBLIC_ENDPOINTS:
                return redirect(url_for("security.login"))
        if not app.config.get("AUTH_ENABLED") or request.endpoint in PUBLIC_ENDPOINTS:
            return None
        if session.get("uid") or session.get("user"):
            return None
        return redirect(url_for("security.login", next=request.path))

    @app.after_request
    def turbo_form_errors(response):
        # A navegação sem recarregar (Turbo, ver static/js/vendor) só mostra a resposta de um formulário
        # com erro se ela vier como 4xx. As rotas devolvem 200 ao reexibir o formulário: vira 422 aqui.
        if (request.method == "POST" and response.status_code == 200
                and request.headers.get("X-Turbo-Request-Id") and response.mimetype == "text/html"):
            response.status_code = 422
        return response

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("Content-Security-Policy", CSP)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.context_processor
    def inject_auth():
        uid = g.get("user_id", OWNER_ID)
        logged = bool(session.get("uid") or session.get("user"))
        account = accounts.get_user(uid) if uid != OWNER_ID else None
        return {
            "auth_enabled": app.config.get("AUTH_ENABLED"),
            "current_user": (account.label if account else session.get("user")) if logged else None,
            "is_owner": uid == OWNER_ID,
            "is_tester": uid != OWNER_ID,
        }

    @app.cli.group("security")
    def security_cli():
        """Comandos de segurança."""

    @security_cli.command("hash-password")
    @click.password_option("--password", prompt="Nova senha")
    def hash_password(password: str):
        """Gera o OWNER_PASSWORD_HASH para colocar no .env."""
        click.echo(generate_password_hash(password))

    @security_cli.command("lock-db")
    def lock_db():
        """Liga RLS em todas as tabelas do PostgreSQL (Supabase). Rode após `flask db upgrade`.

        O Supabase publica as tabelas do schema public na API REST dele. Com RLS ligado e nenhuma
        policy, essa API não lê nem grava nada; o app continua funcionando porque conecta como dono
        das tabelas. No SQLite não faz nada.
        """
        from app.extensions import db

        if db.engine.dialect.name != "postgresql":
            click.echo("Banco não é PostgreSQL: nada a fazer.")
            return
        with db.engine.begin() as conn:
            tables = conn.exec_driver_sql(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ).scalars().all()
            for table in tables:
                conn.exec_driver_sql(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY')
        click.echo(f"RLS ligado em {len(tables)} tabelas.")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if not current_app.config.get("AUTH_ENABLED"):
        return redirect("/")
    if request.method == "POST":
        client = request.remote_addr or "?"
        if _is_locked(client):
            flash("Muitas tentativas erradas. Espere alguns minutos e tente de novo.", "error")
            return render_template("security/login.html"), 429
        user = accounts.authenticate(request.form.get("username", ""), request.form.get("password", ""))
        if user is not None:
            _FAILURES.pop(client, None)
            _start_session(user)
            return redirect(_safe_next(request.args.get("next", "")))
        _FAILURES.setdefault(client, []).append(time.monotonic())
        flash("Usuário ou senha incorretos.", "error")
    return render_template("security/login.html")


@bp.route("/convite/<code>", methods=["GET", "POST"])
def invite(code: str):
    """Link de convite: a pessoa escolhe nome e senha e já entra. Sem Google, sem cadastro longo."""
    client = request.remote_addr or "?"
    if _is_locked(client):
        flash("Muitas tentativas. Espere alguns minutos e tente de novo.", "error")
        return render_template("security/invite.html", invited=None), 429
    invited = accounts.user_for_invite(code)
    if invited is None:
        _FAILURES.setdefault(client, []).append(time.monotonic())
        return render_template("security/invite.html", invited=None), 404
    if request.method == "POST":
        try:
            user = accounts.accept_invite(code, request.form.get("name", ""), request.form.get("password", ""))
        except DomainError as exc:
            flash(str(exc), "error")
            return render_template("security/invite.html", invited=invited)
        _start_session(user)
        flash("Acesso liberado. Bem-vindo ao System, Hunter.", "info")
        return redirect("/")
    return render_template("security/invite.html", invited=invited)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("security.login") if current_app.config.get("AUTH_ENABLED") else "/")


@bp.get("/usuarios-de-teste")
@owner_required
def testers():
    return render_template("security/testers.html", testers=accounts.list_testers(),
                           new_link=session.pop("new_invite_link", None), invite_days=accounts.INVITE_DAYS,
                           now=clock.now())


@bp.post("/usuarios-de-teste")
@owner_required
def invite_tester():
    try:
        user, code = accounts.invite_tester(request.form.get("email", ""), request.form.get("name", ""))
    except DomainError as exc:
        flash(str(exc), "error")
        return redirect(url_for("security.testers"))
    session["new_invite_link"] = {"email": user.email, "url": url_for("security.invite", code=code, _external=True)}
    flash(f"Convite criado para {user.email}. Copie o link e envie para a pessoa.", "success")
    return redirect(url_for("security.testers"))


@bp.post("/usuarios-de-teste/<int:user_id>/ativo")
@owner_required
def toggle_tester(user_id: int):
    user = accounts.set_tester_active(user_id, request.form.get("active") == "1")
    flash(f"{user.label}: acesso {'liberado' if user.active else 'bloqueado'}.", "info")
    return redirect(url_for("security.testers"))


@bp.post("/usuarios-de-teste/<int:user_id>/apagar")
@owner_required
def delete_tester(user_id: int):
    accounts.delete_tester(user_id)
    flash("Usuário de teste e todos os dados dele apagados.", "info")
    return redirect(url_for("security.testers"))


def _start_session(user) -> None:
    session.clear()
    session["uid"] = user.id
    session["user"] = user.username
    session.permanent = True


def _session_user_valid(user_id: int) -> bool:
    user = accounts.get_user(user_id)
    return bool(user and user.active and not user.is_owner)


# Tentativas erradas por IP (memória do processo). Simples, suficiente para poucos usuários.
_FAILURES: dict[str, list[float]] = {}


def _is_locked(client: str) -> bool:
    window = current_app.config.get("LOGIN_LOCK_MINUTES", 15) * 60
    recent = [t for t in _FAILURES.get(client, []) if time.monotonic() - t < window]
    _FAILURES[client] = recent
    return len(recent) >= current_app.config.get("LOGIN_MAX_FAILURES", 5)


def _safe_next(target: str) -> str:
    """Evita redirecionar para outro site depois do login (open redirect)."""
    return target if target.startswith("/") and not target.startswith("//") else "/"
