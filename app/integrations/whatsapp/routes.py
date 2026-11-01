from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import credentials
from . import (NAME, WhatsAppError, daily_summary, is_configured, save, send_test_template, send_to_me,
               settings)

bp = Blueprint("whatsapp", __name__, url_prefix="/integrations/whatsapp")


@bp.errorhandler(WhatsAppError)
def _handle(exc):
    flash(str(exc), "error")
    return redirect(url_for("whatsapp.index"))


@bp.get("/")
def index():
    data = settings()
    return render_template("integrations/whatsapp.html", configured=is_configured(), data=data,
                           masked=credentials.mask(data.get("token")),
                           summary=daily_summary() if is_configured() else "")


@bp.post("/settings")
def save_settings():
    sender = save(request.form.get("token", ""), request.form.get("phone_number_id", ""),
                  request.form.get("my_number", ""))
    flash(f"WhatsApp conectado. Remetente: {sender}.", "success")
    return redirect(url_for("whatsapp.index"))


@bp.post("/settings/delete")
def delete_settings():
    credentials.clear(NAME)
    flash("Credenciais do WhatsApp removidas.", "info")
    return redirect(url_for("whatsapp.index"))


@bp.post("/test")
def test():
    send_test_template()
    flash("Template de teste (hello_world) enviado para o seu número.", "success")
    return redirect(url_for("whatsapp.index"))


@bp.post("/summary")
def summary():
    send_to_me(daily_summary())
    flash("Resumo do dia enviado para o seu WhatsApp.", "success")
    return redirect(url_for("whatsapp.index"))
