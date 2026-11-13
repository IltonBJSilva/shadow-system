"""Telas do Buffer: visão geral, cadastro do token e novo post."""
import io
import time as pytime
from datetime import date, datetime, timedelta

from flask import Blueprint, abort, flash, g, redirect, render_template, request, send_file, url_for

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
from . import filters
from .posting import MODES, parse_image_urls

bp = Blueprint("buffer", __name__, url_prefix="/integrations/buffer")

TABS = {
    "all": "Todos",
    "scheduled": "Agendados",
    "queue": "Fila do Sistema",
    "videos": "Vídeos",
    "draft": "Rascunhos",
    "sent": "Enviados",
    "error": "Com erro",
}

_YT_CHANNEL_CACHE: dict[int, tuple[float, str]] = {}
_YT_VIDEOS_CACHE: dict[int, tuple[float, list]] = {}
_YT_CACHE_TTL_SECONDS = 300


def _youtube_channel_summary(buffer_channels: list) -> dict | None:
    """Retorna informações do canal YouTube conectado diretamente ao System, se não vier do Buffer."""
    if any(ch.service == "youtube" for ch in buffer_channels):
        return None
    try:
        from app.integrations import youtube

        if not youtube.is_authorized():
            return {
                "connected": False,
                "name": "desconectado",
                "url": url_for("youtube.index"),
            }
        uid = getattr(g, "user_id", 1) or 1
        now_ts = pytime.monotonic()
        cached = _YT_CHANNEL_CACHE.get(uid)
        if cached and (now_ts - cached[0]) < 600:
            title = cached[1]
        else:
            title = "Conectado"
            try:
                info = youtube.channel_info()
                if info and info.title:
                    title = info.title
            except Exception:
                pass
            _YT_CHANNEL_CACHE[uid] = (now_ts, title)
        return {
            "connected": True,
            "name": title,
            "url": url_for("youtube.index"),
        }
    except Exception:
        return None


def _youtube_post_items(yt_summary: dict | None, force_refresh: bool = False) -> list[filters.PostItem]:
    """Busca vídeos/Shorts do YouTube (com cache em memória) convertidos em PostItem."""
    if yt_summary is not None and not yt_summary.get("connected"):
        return []
    try:
        from app.integrations import youtube

        if not youtube.is_authorized():
            return []
        uid = getattr(g, "user_id", 1) or 1
        now_ts = pytime.monotonic()
        cached = None if force_refresh else _YT_VIDEOS_CACHE.get(uid)
        if cached and (now_ts - cached[0]) < _YT_CACHE_TTL_SECONDS:
            vids = cached[1]
        else:
            vids = youtube.recent_videos(max_results=25)
            _YT_VIDEOS_CACHE[uid] = (now_ts, vids)
        ch_name = (yt_summary or {}).get("name") or "YouTube"
        return [filters.from_youtube_video(v, channel_name=ch_name) for v in vids]
    except Exception:
        return []


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
    if video_sub not in ("all", "queue", "scheduled", "youtube"):
        video_sub = "all"

    params = filters.parse_filter_params(request.args)
    force_refresh = request.args.get("refresh") == "1"

    error, chans = None, []
    all_queue_posts = list_queue_posts()
    queue_pending_count = sum(1 for p in all_queue_posts if p.status == "pending")
    video_total_count = sum(1 for p in all_queue_posts if p.is_video)

    buf_items = []
    raw_items: list[filters.PostItem] = []

    try:
        chans = channels()
        yt_summary = _youtube_channel_summary(chans)

        if tab == "queue":
            raw_items = [filters.from_queue_post(p) for p in all_queue_posts]
        elif tab == "videos":
            q_videos = [filters.from_queue_post(p) for p in all_queue_posts if p.is_video]
            try:
                buf_sched = posts(["scheduled"], channels_list=chans)
                buf_videos = [filters.from_buffer_post(p, "scheduled") for p in buf_sched if p.is_video]
            except Exception:
                buf_videos = []
            yt_videos = _youtube_post_items(yt_summary, force_refresh=force_refresh)
            raw_items = q_videos + buf_videos + yt_videos
            video_total_count = len(raw_items)
        elif tab == "all":
            try:
                buf_all = posts(["scheduled", "draft", "error", "sent"], channels_list=chans, first=100)
                buf_items = [filters.from_buffer_post(p) for p in buf_all]
            except BufferError as exc:
                error = str(exc)
            buf_ids = {p.id for p in buf_items}
            q_items = [
                filters.from_queue_post(p)
                for p in all_queue_posts
                if not (p.status == "dispatched" and p.buffer_post_id in buf_ids)
            ]
            yt_videos = _youtube_post_items(yt_summary, force_refresh=force_refresh)
            raw_items = q_items + buf_items + yt_videos
            video_total_count += sum(1 for i in buf_items + yt_videos if i.is_video and i.status == "scheduled")
        else:
            raw_buf = posts([tab], channels_list=chans)
            if tab == "scheduled":
                video_total_count += sum(1 for p in raw_buf if p.is_video)
                if queue_pending_count > 0:
                    try:
                        dispatched_map = sync_queue(channels_list=chans, scheduled_posts=raw_buf)
                        if dispatched_map:
                            total_disp = sum(dispatched_map.values())
                            summary_str = ", ".join(f"{ch} (+{c})" for ch, c in dispatched_map.items())
                            flash(f"Fila Inteligente: {total_disp} post(s) despachado(s) para o Buffer ({summary_str})!", "success")
                            all_queue_posts = list_queue_posts()
                            queue_pending_count = sum(1 for p in all_queue_posts if p.status == "pending")
                            raw_buf = posts([tab], channels_list=chans)
                            video_total_count = sum(1 for p in all_queue_posts if p.is_video) + sum(1 for p in raw_buf if p.is_video)
                    except Exception:
                        pass
                buf_items = [filters.from_buffer_post(p, "scheduled") for p in raw_buf]
                yt_videos = [v for v in _youtube_post_items(yt_summary, force_refresh=force_refresh) if v.status == "scheduled"]
                raw_items = buf_items + yt_videos
            elif tab == "sent":
                buf_items = [filters.from_buffer_post(p, "sent") for p in raw_buf]
                yt_videos = [v for v in _youtube_post_items(yt_summary, force_refresh=force_refresh) if v.status == "sent"]
                raw_items = buf_items + yt_videos
            elif tab == "error":
                buf_items = [filters.from_buffer_post(p, "error") for p in raw_buf]
                q_errors = [
                    filters.from_queue_post(p)
                    for p in all_queue_posts
                    if p.status == "error" or p.error_message
                ]
                raw_items = buf_items + q_errors
            else:
                raw_items = [filters.from_buffer_post(p, tab) for p in raw_buf]
    except BufferError as exc:
        error = str(exc)
        yt_summary = _youtube_channel_summary(chans)
        if tab in ("queue", "all"):
            raw_items = [filters.from_queue_post(p) for p in all_queue_posts]
        elif tab == "videos":
            raw_items = [filters.from_queue_post(p) for p in all_queue_posts if p.is_video]
        elif tab == "error":
            raw_items = [
                filters.from_queue_post(p)
                for p in all_queue_posts
                if p.status == "error" or p.error_message
            ]
        if tab in ("all", "videos"):
            raw_items = raw_items + _youtube_post_items(yt_summary, force_refresh=force_refresh)

    filtered_items = filters.sort_items(filters.apply_filters(raw_items, params), params.sort)
    grouped_posts = filters.group_posts(filtered_items) if params.view == "grouped" else []
    service_counts = filters.count_by_service(filtered_items)
    total_service_counts = filters.count_by_service(raw_items)

    # Lista ordenada de redes disponíveis para o painel de filtros
    preferred_order = ["instagram", "linkedin", "tiktok", "youtube", "facebook", "twitter", "threads"]
    seen_services = set(ch.service for ch in chans) | set(total_service_counts.keys())
    if yt_summary is not None:
        seen_services.add("youtube")
    available_services = sorted(
        seen_services,
        key=lambda s: (preferred_order.index(s) if s in preferred_order else 99, s),
    )

    video_queue_posts = [i for i in filtered_items if i.origin == "queue"] if tab == "videos" else []
    video_scheduled_posts = [i for i in filtered_items if i.origin == "buffer"] if tab == "videos" else []
    video_youtube_posts = [i for i in filtered_items if i.origin == "youtube"] if tab == "videos" else []

    return render_template(
        "integrations/buffer/index.html",
        tabs=TABS,
        tab=tab,
        items=filtered_items,
        raw_total=len(raw_items),
        grouped_posts=grouped_posts,
        filter_params=params,
        available_services=available_services,
        service_counts=service_counts,
        total_service_counts=total_service_counts,
        queue_pending_count=queue_pending_count,
        video_sub=video_sub,
        video_queue_posts=video_queue_posts,
        video_scheduled_posts=video_scheduled_posts,
        video_youtube_posts=video_youtube_posts,
        video_total_count=video_total_count,
        channels=chans,
        youtube_channel=yt_summary,
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
    back_tab = request.args.get("tab") or request.form.get("tab") or "scheduled"
    if back_tab not in TABS:
        back_tab = "scheduled"
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
        return redirect(url_for("buffer.index", status=back_tab))
    now_local = time.now()
    suggested_due = post.due_at if (post.due_at and post.due_at > now_local) else (now_local + timedelta(days=1))
    buffer_url = f"https://publish.buffer.com/channels/{post.channel_id}" if post.channel_id else "https://publish.buffer.com/"
    return render_template(
        "integrations/buffer/edit.html",
        post=post,
        today=time.today(),
        suggested_due=suggested_due,
        back_tab=back_tab,
        buffer_url=buffer_url,
    )


# ---------- rotas da Fila do Sistema ----------

@bp.post("/queue/sync")
def sync_queue_route():
    if not is_configured():
        return redirect(url_for("buffer.token"))
    back_tab = request.form.get("tab") if request.form.get("tab") in TABS else "queue"
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
    return redirect(url_for("buffer.index", status=back_tab))


@bp.post("/queue/<int:post_id>/dispatch")
def dispatch_queue_post_route(post_id: int):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    back_tab = request.form.get("tab") if request.form.get("tab") in TABS else "queue"
    post = dispatch_single_post(post_id)
    flash(f"Post #{post.id} ({post.service.capitalize()}) despachado com sucesso para o Buffer!", "success")
    return redirect(url_for("buffer.index", status=back_tab))


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
    back_tab = request.form.get("tab") if request.form.get("tab") in TABS else "queue"
    delete_queue_post(post_id)
    flash("Post removido da Fila do Sistema.", "info")
    return redirect(url_for("buffer.index", status=back_tab))


@bp.route("/queue/<int:post_id>/edit", methods=["GET", "POST"])
def edit_queue_post_route(post_id: int):
    if not is_configured():
        return redirect(url_for("buffer.token"))
    back_tab = request.args.get("tab") or request.form.get("tab") or "queue"
    if back_tab not in TABS:
        back_tab = "queue"
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
        update_queue_post(post_id, text=text, target_date=target_d, target_time=due_time_raw or "18:30", clear_error=True)
        flash("Post da fila atualizado com sucesso.", "success")
        return redirect(url_for("buffer.index", status=back_tab))
    buffer_url = f"https://publish.buffer.com/channels/{post.channel_id}" if post.channel_id else "https://publish.buffer.com/"
    return render_template(
        "integrations/buffer/queue_edit.html",
        post=post,
        today=time.today(),
        back_tab=back_tab,
        buffer_url=buffer_url,
    )


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
                target_date=target_d,
                target_time=p["target_time"],
                status=p.get("status", "pending"),
            )
            if p.get("thumbnail"):
                row.images = [p["thumbnail"]]
            db.session.add(row)
            added += 1
    if added > 0:
        db.session.commit()
    return {"status": "ok", "added": added}

