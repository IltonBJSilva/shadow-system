from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import credentials
from . import NAME, NotionError, get_client, import_pages, imported_ids, is_configured, save_token

bp = Blueprint("notion", __name__, url_prefix="/integrations/notion")


@bp.errorhandler(NotionError)
def _handle(exc):
    flash(str(exc), "error")
    return redirect(url_for("notion.index"))


@bp.get("/")
def index():
    databases, error = [], None
    if is_configured():
        try:
            databases = get_client().databases()
        except NotionError as exc:
            error = str(exc)
    data = credentials.load(NAME)
    return render_template("integrations/notion/index.html", configured=is_configured(), databases=databases,
                           error=error, bot=data.get("bot"), masked=credentials.mask(data.get("token")))


@bp.post("/token")
def token():
    bot = save_token(request.form.get("token", ""))
    flash(f"Notion conectado como {bot}.", "success")
    return redirect(url_for("notion.index"))


@bp.post("/token/delete")
def delete_token():
    credentials.clear(NAME)
    flash("Token do Notion removido. Para invalidá-lo, apague a integração em notion.so/my-integrations.", "info")
    return redirect(url_for("notion.index"))


@bp.get("/databases/<database_id>")
def database(database_id: str):
    pages = get_client().pages(database_id)
    return render_template("integrations/notion/database.html", database_id=database_id, pages=pages,
                           imported=imported_ids())


@bp.post("/databases/<database_id>/import")
def import_selected(database_id: str):
    chosen = set(request.form.getlist("pages"))
    pages = [p for p in get_client().pages(database_id) if p.id in chosen]
    created = import_pages(pages)
    untitled = sum(1 for p in pages if not p.title)
    flash(f"{created} quest(s) importada(s) do Notion.", "success")
    if untitled:
        flash(f"{untitled} página(s) sem título foram puladas. Dê um nome a elas no Notion e importe de novo.", "info")
    return redirect(url_for("notion.database", database_id=database_id))
