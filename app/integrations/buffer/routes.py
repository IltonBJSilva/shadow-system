"""Telas do Buffer: visão geral, cadastro do token e novo post."""
import io
from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for

from app.core import time

from . import (BufferError, PostValidationError, StorageError, Upload, channels, delete_post,
               get_post, is_configured, posts, save_token, schedule, share_post_now, storage,
               storage_enabled, token_store, update_post)
from .posting import MODES, parse_image_urls

bp = Blueprint("buffer", __name__, url_prefix="/integrations/buffer")

TABS = {"scheduled": "Agendados", "draft": "Rascunhos", "sent": "Enviados", "error": "Com erro"}


@bp.errorhandler(BufferError)
@bp.errorhandler(PostValidationError)
@bp.errorhandler(StorageError)
def _handle(exc):
    flash(str(exc), "error")
    return redirect(request.referrer if (request.referrer or "").startswith(request.host_url)
                    else url_for("buffer.index"))


@bp.get("/")
def index():
    if not is_configured():
        return redirect(url_for("buffer.token"))
    tab = request.args.get("status", "scheduled")
    tab = tab if tab in TABS else "scheduled"
    error, items, chans = None, [], []
    try:
        chans = channels()
        items = posts([tab])
    except BufferError as exc:
        error = str(exc)
    return render_template("integrations/buffer/index.html", tabs=TABS, tab=tab, posts=items,
                           channels=chans, error=error, token=token_store.status())


@bp.route("/token", methods=["GET", "POST"])
def token():
    if request.method == "POST":
        raw_date = request.form.get("created_at") or time.today().isoformat()
        try:
            created_at = date.fromisoformat(raw_date)
        except ValueError:
            created_at = time.today()
        count = save_token(request.form.get("api_key", ""), created_at)
        flash(f"Token do Buffer salvo e conferido: {count} canal(is) encontrado(s).", "success")
        return redirect(url_for("buffer.index"))
    return render_template("integrations/buffer/token.html", token=token_store.status(),
                           tokens_url=token_store.TOKENS_URL, valid_days=token_store.VALID_DAYS)


@bp.post("/token/delete")
def delete_token():
    token_store.clear()
    flash("Token removido do Shadow System. Para invalidá-lo de vez, apague-o também no Buffer.", "info")
    return redirect(url_for("buffer.token"))


@bp.route("/new", methods=["GET", "POST"])
def new_post():
    if not is_configured():
        return redirect(url_for("buffer.token"))
    chans = [ch for ch in channels() if ch.usable]
    services = sorted({ch.service for ch in chans})
    if request.method == "POST":
        if request.form.get("confirm") != "yes":
            raise PostValidationError("Marque a confirmação: publicar ou agendar é uma ação pública.")
        mode = request.form.get("mode", "customScheduled")
        results = schedule(
            text=request.form.get("text", "").strip(),
            overrides={s: request.form.get(f"text_{s}", "").strip() for s in services
                       if request.form.get(f"text_{s}", "").strip()},
            channel_ids=request.form.getlist("channels"),
            mode=mode,
            due_local=_due_from_form() if mode == "customScheduled" else None,
            image_urls=parse_image_urls(request.form.get("image_urls", "")),
            uploads=[Upload(f.filename, f.read(), f.mimetype) for f in request.files.getlist("images")
                     if f and f.filename],
        )
        for result in results:
            flash(f"{result.channel} ({result.service}): {result.message}", "success" if result.ok else "error")
        return redirect(url_for("buffer.index"))
    host = request.host.lower()
    is_local = host.startswith(("localhost", "127.0.0.1"))
    return render_template("integrations/buffer/new.html", channels=chans, services=services, modes=MODES,
                           storage_enabled=True, supabase_enabled=storage.is_supabase_configured(),
                           is_local=is_local, today=time.today())


@bp.get("/uploads/<token>/<filename>")
def serve_upload(token: str, filename: str):
    """Serve uma imagem enviada do computador para post no Buffer."""
    asset = storage.get_upload(token)
    if asset is None:
        abort(404)
    response = send_file(
        io.BytesIO(asset.data),
        mimetype=asset.mimetype,
        conditional=True,
        max_age=30 * 24 * 3600,
    )
    response.cache_control.public = True
    response.headers["Accept-Ranges"] = "bytes"
    return response


@bp.post("/posts/<post_id>/delete")
def delete_post_route(post_id: str):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    delete_post(post_id)
    flash("Post excluído com sucesso do Buffer.", "success")
    return redirect(request.referrer if (request.referrer or "").startswith(request.host_url)
                    else url_for("buffer.index"))


@bp.post("/posts/<post_id>/share-now")
def share_now_route(post_id: str):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    share_post_now(post_id)
    flash("Publicação imediata solicitada ao Buffer.", "success")
    return redirect(url_for("buffer.index", status="sent"))


@bp.route("/posts/<post_id>/edit", methods=["GET", "POST"])
def edit_post_route(post_id: str):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    post = get_post(post_id)
    if request.method == "POST":
        text = request.form.get("text", "")
        due_date = request.form.get("due_date", "").strip()
        due_time = request.form.get("due_time", "").strip()
        due_local = None
        if due_date and due_time:
            try:
                due_local = datetime.fromisoformat(f"{due_date}T{due_time}")
            except ValueError as exc:
                raise PostValidationError("Informe uma data e hora válidas.") from exc
        update_post(post_id, text=text, due_local=due_local, service=post.service)
        flash("Post atualizado com sucesso no Buffer.", "success")
        return redirect(url_for("buffer.index"))
    return render_template("integrations/buffer/edit.html", post=post, today=time.today())


def _due_from_form() -> datetime:
    try:
        return datetime.fromisoformat(f"{request.form.get('due_date', '')}T{request.form.get('due_time', '')}")
    except ValueError as exc:
        raise PostValidationError("Informe a data e a hora do agendamento.") from exc
