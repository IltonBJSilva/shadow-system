"""Telas das integrações."""
from flask import Blueprint, current_app, render_template

from . import kausa_scheduler, registry

bp = Blueprint("integrations", __name__, url_prefix="/integrations")


@bp.get("/")
def index():
    return render_template("integrations/index.html", statuses=registry.all_statuses())


@bp.get("/kausa")
def kausa():
    posts, channels, error = [], [], None
    if kausa_scheduler.is_configured():
        try:
            client = kausa_scheduler.get_client()
            channels = client.channels()
            posts = client.posts("scheduled")
        except kausa_scheduler.KausaSchedulerError as exc:
            error = str(exc)
    return render_template(
        "integrations/kausa.html",
        configured=kausa_scheduler.is_configured(),
        kausa_url=current_app.config.get("KAUSA_SCHEDULER_URL"),
        posts=posts,
        channels=channels,
        error=error,
    )
