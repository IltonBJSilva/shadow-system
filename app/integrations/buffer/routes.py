"""Telas do Buffer: visão geral, cadastro do token e novo post."""
import io
from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for

from app.core import time
from app.extensions import csrf

from . import (
    BufferError,
    PostValidationError,
    StorageError,
    Upload,
    channels,
    delete_post,
    delete_queue_post,
    dispatch_single_post,
    enqueue_post,
    get_post,
    get_queue_post,
    is_configured,
    list_queue_posts,
    posts,
    save_token,
    schedule,
    share_post_now,
    storage,
    storage_enabled,
    sync_queue,
    token_store,
    update_post,
    update_queue_post,
)
from .posting import MODES, parse_image_urls

bp = Blueprint("buffer", __name__, url_prefix="/integrations/buffer")

TABS = {
    "scheduled": "Agendados",
    "queue": "Fila do Sistema",
    "videos": "Vídeos",
    "draft": "Rascunhos",
    "sent": "Enviados",
    "error": "Com erro",
}


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
    video_sub = request.args.get("video_sub", "all")
    if video_sub not in ("all", "queue", "scheduled"):
        video_sub = "all"

    error, items, chans = None, [], []
    queue_posts = []
    video_queue_posts = []
    video_scheduled_posts = []
    queue_pending_count = len(list_queue_posts(status="pending"))
    video_total_count = len([p for p in list_queue_posts() if p.is_video])

    try:
        chans = channels()
        if tab == "queue":
            queue_posts = list_queue_posts()
        elif tab == "videos":
            video_queue_posts = [p for p in list_queue_posts() if p.is_video]
            try:
                buf_sched = posts(["scheduled"])
                video_scheduled_posts = [p for p in buf_sched if p.is_video]
            except Exception:
                video_scheduled_posts = []
            video_total_count = len(video_queue_posts) + len(video_scheduled_posts)
        else:
            items = posts([tab])
            if tab == "scheduled":
                video_total_count += len([p for p in items if p.is_video])
                # Se estiver nos agendados e houver posts na fila do sistema, despacha lote para canais com <= 5
                if queue_pending_count > 0:
                    try:
                        dispatched_map = sync_queue()
                        if dispatched_map:
                            total_disp = sum(dispatched_map.values())
                            summary_str = ", ".join(f"{ch} (+{c})" for ch, c in dispatched_map.items())
                            flash(f"Fila Inteligente: {total_disp} post(s) despachado(s) para o Buffer ({summary_str})!", "success")
                            queue_pending_count = len(list_queue_posts(status="pending"))
                            items = posts([tab])
                            video_total_count = len([p for p in list_queue_posts() if p.is_video]) + len([p for p in items if p.is_video])
                    except Exception:
                        pass
    except BufferError as exc:
        error = str(exc)
        if tab == "queue":
            queue_posts = list_queue_posts()
        elif tab == "videos":
            video_queue_posts = [p for p in list_queue_posts() if p.is_video]

    return render_template(
        "integrations/buffer/index.html",
        tabs=TABS,
        tab=tab,
        posts=items,
        queue_posts=queue_posts,
        queue_pending_count=queue_pending_count,
        video_sub=video_sub,
        video_queue_posts=video_queue_posts,
        video_scheduled_posts=video_scheduled_posts,
        video_total_count=video_total_count,
        channels=chans,
        error=error,
        token=token_store.status(),
    )


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
        destination = request.form.get("destination", "buffer")
        send_to_queue = (destination == "queue")
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
            send_to_queue=send_to_queue,
        )
        for result in results:
            flash(f"{result.channel} ({result.service}): {result.message}", "success" if result.ok else "error")
        return redirect(url_for("buffer.index", status="queue" if send_to_queue else "scheduled"))
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


# ---------- rotas da Fila do Sistema ----------

@bp.post("/queue/sync")
def sync_queue_route():
    if not is_configured():
        return redirect(url_for("buffer.token"))
    results = sync_queue()
    if results:
        total = sum(results.values())
        channels_str = ", ".join(f"{ch} (+{cnt})" for ch, cnt in results.items())
        flash(f"Lote despachado para o Buffer: {total} post(s) ({channels_str}).", "success")
    else:
        pending = len(list_queue_posts(status="pending"))
        if pending == 0:
            flash("A Fila do Sistema está vazia. Não há posts para despachar.", "info")
        else:
            flash(
                "Nenhum canal elegível para envio de lote no momento: os canais ainda possuem mais de 5 posts agendados no Buffer.",
                "info",
            )
    return redirect(url_for("buffer.index", status="queue"))


@bp.post("/queue/<int:post_id>/dispatch")
def dispatch_queue_post_route(post_id: int):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    post = dispatch_single_post(post_id)
    flash(f"Post #{post.id} ({post.service.capitalize()}) despachado com sucesso para o Buffer!", "success")
    return redirect(url_for("buffer.index", status="queue"))


@bp.post("/queue/<int:post_id>/share-now")
def share_now_queue_post_route(post_id: int):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    post = dispatch_single_post(post_id, mode="shareNow")
    flash(f"Post #{post.id} ({post.service.capitalize()}) publicado agora com sucesso via Buffer!", "success")
    return redirect(url_for("buffer.index", status="sent"))


@bp.post("/queue/<int:post_id>/delete")
def delete_queue_post_route(post_id: int):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    delete_queue_post(post_id)
    flash("Post removido da Fila do Sistema.", "info")
    return redirect(url_for("buffer.index", status="queue"))


@bp.route("/queue/<int:post_id>/edit", methods=["GET", "POST"])
def edit_queue_post_route(post_id: int):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    post = get_queue_post(post_id)
    if not post:
        abort(404)
    if request.method == "POST":
        text = request.form.get("text", "")
        due_date_raw = request.form.get("due_date", "").strip()
        due_time_raw = request.form.get("due_time", "").strip()
        target_d = None
        if due_date_raw:
            try:
                target_d = date.fromisoformat(due_date_raw)
            except ValueError as exc:
                raise PostValidationError("Informe uma data válida.") from exc
        update_queue_post(post_id, text=text, target_date=target_d, target_time=due_time_raw or "18:30")
        flash("Post da fila atualizado com sucesso.", "success")
        return redirect(url_for("buffer.index", status="queue"))
    return render_template("integrations/buffer/queue_edit.html", post=post, today=time.today())


def _due_from_form() -> datetime:
    try:
        return datetime.fromisoformat(f"{request.form.get('due_date', '')}T{request.form.get('due_time', '')}")
    except ValueError as exc:
        raise PostValidationError("Informe a data e a hora do agendamento.") from exc


# ---------- Sincronização Local -> Produção (Render) ----------

SYNC_KEY = "shadow-system-sync-2026-sec"


@bp.post("/api/sync-upload")
@csrf.exempt
def sync_upload():
    from app.extensions import db
    from app.core.models import BufferUpload

    if request.headers.get("X-Sync-Key") != SYNC_KEY and request.form.get("sync_key") != SYNC_KEY:
        abort(403)
    token = request.form.get("token")
    filename = request.form.get("filename")
    mimetype = request.form.get("mimetype", "video/mp4")
    f = request.files.get("file")
    if not token or not filename or not f:
        abort(400)
    data = f.read()
    existing = db.session.get(BufferUpload, token)
    if not existing:
        upload_row = BufferUpload(token=token, filename=filename, mimetype=mimetype, size=len(data), data=data)
        db.session.add(upload_row)
        db.session.commit()
    return {"status": "ok", "token": token, "size": len(data)}


@bp.post("/api/sync-queue")
@csrf.exempt
def sync_queue_api():
    from app.extensions import db
    from app.core.models import BufferQueuePost

    if request.headers.get("X-Sync-Key") != SYNC_KEY and request.form.get("sync_key") != SYNC_KEY:
        abort(403)
    data = request.get_json(silent=True) or {}
    posts = data.get("posts", [])
    added = 0
    for p in posts:
        target_d = date.fromisoformat(p["target_date"]) if p.get("target_date") else None
        exists = BufferQueuePost.query.filter_by(
            channel_id=p["channel_id"],
            target_date=target_d,
            target_time=p["target_time"],
        ).first()
        if not exists:
            row = BufferQueuePost(
                channel_id=p["channel_id"],
                channel_name=p["channel_name"],
                service=p["service"],
                text=p["text"],
                thumbnail=p["thumbnail"],
                target_date=target_d,
                target_time=p["target_time"],
                status=p.get("status", "pending"),
            )
            db.session.add(row)
            added += 1
    if added > 0:
        db.session.commit()
    return {"status": "ok", "added": added}

