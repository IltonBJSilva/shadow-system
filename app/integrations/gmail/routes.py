from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.core import time
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput

from ..google_calendar import oauth
from ..google_calendar.oauth import GoogleAuthError
from . import GmailError, get_client, is_authorized
from .client import PERIODS, PLACES, STATUSES, MailFilter

bp = Blueprint("gmail", __name__, url_prefix="/integrations/gmail")


@bp.errorhandler(GmailError)
@bp.errorhandler(GoogleAuthError)
def _handle(exc):
    flash(str(exc), "error")
    return redirect(url_for("integrations.index"))


@bp.get("/")
def index():
    emails, total, error = [], 0, None
    mail_filter = MailFilter.from_args(request.args)
    if is_authorized():
        try:
            client = get_client()
            emails, total = client.search(mail_filter, 25)
            if mail_filter.is_default:
                total = client.unread_count()  # número exato de não lidos (a estimativa da busca é aproximada)
        except (GmailError, GoogleAuthError) as exc:
            error = str(exc)
    return render_template("integrations/gmail.html", configured=oauth.is_configured(),
                           authorized=is_authorized(), emails=emails, total=total, error=error,
                           f=mail_filter, periods=PERIODS, statuses=STATUSES, places=PLACES)


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
    back = request.form.get("next", "")
    return redirect(back if back.startswith("/integrations/gmail/") else url_for("gmail.index"))
