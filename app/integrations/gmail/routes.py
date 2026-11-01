from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.core import time
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput

from ..google_calendar import oauth
from ..google_calendar.oauth import GoogleAuthError
from . import GmailError, get_client, is_authorized

bp = Blueprint("gmail", __name__, url_prefix="/integrations/gmail")


@bp.errorhandler(GmailError)
@bp.errorhandler(GoogleAuthError)
def _handle(exc):
    flash(str(exc), "error")
    return redirect(url_for("integrations.index"))


@bp.get("/")
def index():
    emails, unread, error = [], 0, None
    if is_authorized():
        try:
            client = get_client()
            unread, emails = client.unread_count(), client.unread(15)
        except (GmailError, GoogleAuthError) as exc:
            error = str(exc)
    return render_template("integrations/gmail.html", configured=oauth.is_configured(),
                           authorized=is_authorized(), emails=emails, unread=unread, error=error)


@bp.post("/quest")
def to_quest():
    """Cria uma quest a partir de um e-mail (ex.: 'Responder: proposta do cliente')."""
    subject = (request.form.get("subject") or "").strip()[:120] or "e-mail"
    sender = (request.form.get("sender") or "").strip()[:80]
    link = request.form.get("url", "")
    quest = quests.create_quest(QuestInput(
        title=f"Responder: {subject}",
        quest_type="side",
        priority="medium",
        difficulty=2,
        due_date=time.today(),
        description=f"E-mail de {sender}.\n{link if link.startswith('https://mail.google.com/') else ''}".strip(),
    ), note="Quest criada a partir de um e-mail")
    flash(f"[Nova quest] {quest.title}", "success")
    return redirect(url_for("gmail.index"))
