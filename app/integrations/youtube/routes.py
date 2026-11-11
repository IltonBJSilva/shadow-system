"""Telas e rotas da integração com o YouTube."""
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.core import time

from ..google_calendar import oauth
from ..google_calendar.oauth import GoogleAuthError
from . import (
    ChannelInfo,
    YouTubeError,
    channel_info,
    get_client,
    is_authorized,
    recent_videos,
    status,
    upload_video,
)

bp = Blueprint("youtube", __name__, url_prefix="/integrations/youtube")


@bp.errorhandler(YouTubeError)
@bp.errorhandler(GoogleAuthError)
def _handle(exc):
    flash(str(exc), "error")
    return redirect(url_for("youtube.index"))


@bp.get("/")
def index():
    info = status()
    ch_info = None
    videos = []
    error = None
    authorized = is_authorized()

    if authorized:
        try:
            client = get_client()
            ch_info = client.channel_info()
            try:
                videos = client.recent_videos(max_results=12)
            except Exception:
                videos = []
        except (YouTubeError, GoogleAuthError) as exc:
            error = str(exc)
        except Exception as exc:
            error = f"Erro na comunicação com o YouTube: {exc}"

    return render_template(
        "integrations/youtube.html",
        status_info=info,
        authorized=authorized,
        configured=oauth.is_configured(),
        channel=ch_info,
        videos=videos,
        error=error,
    )


@bp.get("/connect")
def connect():
    """Redireciona para o fluxo OAuth do Google pedindo permissão do YouTube."""
    return redirect(url_for("google_calendar.connect", youtube=1))


@bp.post("/upload")
def upload():
    """Recebe upload de vídeo ou caminho local e envia para o YouTube."""
    if not is_authorized():
        flash("YouTube não conectado. Autorize primeiro a conexão.", "error")
        return redirect(url_for("youtube.index"))

    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Informe o título do vídeo.", "error")
        return redirect(url_for("youtube.index"))

    description = (request.form.get("description") or "").strip()
    tags_raw = request.form.get("tags") or ""
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    is_short = request.form.get("is_short", "1") == "1"
    privacy_status = request.form.get("privacy_status") or "public"

    # Agendamento
    publish_at_utc = None
    mode = request.form.get("mode") or "now"
    if mode == "schedule":
        sched_date = request.form.get("schedule_date")
        sched_time = request.form.get("schedule_time") or "12:00"
        if sched_date:
            try:
                local_dt = datetime.strptime(f"{sched_date} {sched_time}", "%Y-%m-%d %H:%M")
                publish_at_utc = time.to_aware(local_dt).astimezone(timezone.utc)
            except ValueError:
                flash("Formato de data ou hora inválido para agendamento.", "error")
                return redirect(url_for("youtube.index"))

    # Arquivo: pode vir por upload de formulário ou caminho local
    video_file = request.files.get("video_file")
    local_path = (request.form.get("file_path") or "").strip()

    media_source = None
    if video_file and video_file.filename:
        media_source = video_file.stream
    elif local_path:
        p = Path(local_path)
        if not p.is_file():
            flash(f"Arquivo local não encontrado: {local_path}", "error")
            return redirect(url_for("youtube.index"))
        media_source = p
    else:
        flash("Selecione um arquivo de vídeo (.mp4) ou informe o caminho local.", "error")
        return redirect(url_for("youtube.index"))

    try:
        vid = upload_video(
            media_source=media_source,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
            publish_at_utc=publish_at_utc,
            is_short=is_short,
        )
        if publish_at_utc:
            flash(f"Vídeo agendado com sucesso no YouTube para {sched_date} às {sched_time}! ({vid.url})", "success")
        else:
            flash(f"Vídeo publicado com sucesso no YouTube! ({vid.url})", "success")
    except (YouTubeError, GoogleAuthError) as exc:
        flash(f"Erro ao enviar vídeo para o YouTube: {exc}", "error")

    return redirect(url_for("youtube.index"))
