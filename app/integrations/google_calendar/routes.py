"""Telas da integração com o Google Calendar."""
from datetime import timedelta

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for

from app.core import time
from app.modules.calendar import services as calendar

from . import get_client, oauth, status, sync
from .client import GoogleCalendarError
from .oauth import GoogleAuthError

bp = Blueprint("google_calendar", __name__, url_prefix="/integrations/google")


@bp.errorhandler(GoogleAuthError)
@bp.errorhandler(GoogleCalendarError)
def _handle(exc):
    flash(str(exc), "error")
    return redirect(url_for("google_calendar.index"))


@bp.get("/")
def index():
    info = status()
    calendars, busy = [], []
    if info.state == "connected":
        try:
            client = get_client()
            calendars = client.calendars()
            now = time.now()
            busy = client.busy_periods(now, now + timedelta(days=1))
        except (GoogleAuthError, GoogleCalendarError) as exc:
            flash(str(exc), "error")
    return render_template(
        "integrations/google.html",
        info=info,
        calendars=calendars,
        busy=busy,
        pending=len(calendar.local_events_to_push()),
        redirect_uri=current_app.config["GOOGLE_REDIRECT_URI"],
        calendar_id=current_app.config.get("GOOGLE_CALENDAR_ID", "primary"),
    )


@bp.get("/connect")
def connect():
    """?gmail=1 pede também acesso de leitura ao Gmail (além do Calendar)."""
    scopes = oauth.SCOPES + ([oauth.GMAIL_SCOPE] if request.args.get("gmail") or oauth.has_scope(oauth.GMAIL_SCOPE) else [])
    url, state, code_verifier = oauth.authorization_url(scopes)
    session["google_oauth_state"] = state
    session["google_code_verifier"] = code_verifier
    session["google_scopes"] = scopes
    session["google_return_to"] = "/integrations/gmail/" if request.args.get("gmail") else "/integrations/google/"
    return redirect(url)


@bp.get("/callback")
def callback():
    state = session.pop("google_oauth_state", None)
    code_verifier = session.pop("google_code_verifier", None)
    scopes = session.pop("google_scopes", None)
    return_to = session.pop("google_return_to", "/integrations/google/")
    if not state or request.args.get("state") != state:
        abort(400)  # protege contra CSRF no retorno do OAuth
    if request.args.get("error"):
        flash("Conexão com o Google cancelada.", "info")
        return redirect(url_for("google_calendar.index"))
    oauth.exchange_code(request.url, state, code_verifier, scopes)
    flash("Conta Google conectada.", "success")
    return redirect(return_to if return_to.startswith("/integrations/") else url_for("google_calendar.index"))


@bp.post("/disconnect")
def disconnect():
    oauth.disconnect()
    flash("Token local removido. Para revogar o acesso no Google: myaccount.google.com/permissions", "info")
    return redirect(url_for("google_calendar.index"))


@bp.post("/sync")
def sync_now():
    client = get_client()
    imported = sync.import_events(client)
    pushed = sync.push_pending(client)
    flash(
        f"Sincronizado: {imported.created} novo(s), {imported.updated} atualizado(s), "
        f"{imported.removed} removido(s), {pushed.pushed} enviado(s) ao Google.",
        "success",
    )
    return redirect(url_for("google_calendar.index"))


@bp.post("/events/<int:event_id>/push")
def push_one(event_id: int):
    event = calendar.get_event(event_id)
    if event.source != "local":
        flash("Este evento veio do Google; edite-o lá.", "info")
    else:
        sync.push_event(get_client(), event)
        flash("Evento enviado ao Google Calendar.", "success")
    return redirect(url_for("calendar.edit", event_id=event_id))
