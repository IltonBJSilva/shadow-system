"""Rotas do núcleo: saúde, Configurações (áudio e mídias do System) e arquivos de mídia."""
import io
import logging

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request,
                   send_file, send_from_directory, session, url_for)
from sqlalchemy import text

from app.extensions import db

from . import experience, media
from .errors import DomainError
from .security import is_owner, owner_required

bp = Blueprint("core", __name__)
log = logging.getLogger(__name__)


@bp.get("/health")
def health():
    """Checagem de vida para monitoramento e keep-alive. Pública mesmo com login ligado.

    Faz um SELECT 1 no banco: assim o ping que mantém o Render acordado também mantém o projeto do
    Supabase ativo (o plano gratuito pausa após 7 dias sem uso). Não expõe nenhum dado.
    """
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 (qualquer falha do banco vira 503, detalhe só no log)
        log.exception("health: banco indisponível")
        db.session.rollback()
        return {"ok": False, "database": False}, 503
    return {"ok": True, "database": True}


@bp.route("/configuracoes", methods=["GET", "POST"])
def preferences():
    """Configurações: áudio (no navegador de cada um), inicialização e, para o dono, as mídias."""
    if request.method == "POST":
        experience.set_boot_mode(request.form.get("boot_mode", ""))
        flash("Inicialização salva.", "success")
        return redirect(url_for("core.preferences"))
    return render_template(
        "core/preferences.html",
        boot_modes=experience.BOOT_MODES,
        current_boot=experience.boot_mode(),
        media_slots=media.listing() if is_owner() else [],
        max_mb={kind: size // (1024 * 1024) for kind, size in media.MAX_BYTES.items()},
    )


@bp.post("/configuracoes/midia/<slot>")
@owner_required
def upload_media(slot: str):
    file = request.files.get("file")
    try:
        if not file or not file.filename:
            raise DomainError("Escolha um arquivo.")
        limit = max(media.MAX_BYTES.values())
        media.save(slot, file.filename, file.read(limit + 1), file.mimetype)
        flash(f"{media.SLOTS[slot].label}: arquivo salvo.", "success")
    except DomainError as exc:
        flash(str(exc), "error")
    return redirect(url_for("core.preferences") + "#midias")


@bp.post("/configuracoes/midia/<slot>/apagar")
@owner_required
def delete_media(slot: str):
    media.delete(slot)
    flash("Mídia removida. O System volta a usar o som/visual padrão nesse momento.", "info")
    return redirect(url_for("core.preferences") + "#midias")


@bp.get("/media/<slot>")
def media_file(slot: str):
    """Serve uma mídia do System com cache e suporte a Range (necessário para áudio no iPhone)."""
    logged = session.get("uid") or session.get("user")
    if current_app.config.get("AUTH_ENABLED") and not logged and slot not in media.PUBLIC_SLOTS:
        abort(403)
    asset = media.get(slot)
    if asset is None:
        abort(404)
    response = send_file(io.BytesIO(asset.data), mimetype=asset.mimetype, conditional=True,
                         etag=asset.etag, max_age=7 * 24 * 3600, last_modified=asset.updated_at)
    response.cache_control.public = slot in media.PUBLIC_SLOTS
    response.cache_control.private = slot not in media.PUBLIC_SLOTS
    response.headers["Accept-Ranges"] = "bytes"
    return response


# ---------- App instalável (PWA), ajuda e novidades ----------

@bp.get("/manifest.webmanifest")
def manifest():
    response = jsonify({
        "name": "Shadow System",
        "short_name": "Shadow",
        "description": "Sistema pessoal de evolução inspirado em Solo Leveling.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#040714",
        "theme_color": "#040714",
        "lang": "pt-BR",
        "icons": [
            {"src": url_for("static", filename="img/icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": url_for("static", filename="img/icon-512.png"), "sizes": "512x512", "type": "image/png"},
            {"src": url_for("static", filename="img/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    })
    response.mimetype = "application/manifest+json"
    return response


@bp.get("/sw.js")
def service_worker():
    """O service worker precisa ser servido da raiz para controlar o site inteiro."""
    response = send_from_directory(current_app.static_folder, "js/sw.js", mimetype="text/javascript", max_age=0)
    response.headers["Cache-Control"] = "no-cache"
    return response


@bp.get("/offline")
def offline():
    return render_template("core/offline.html")


@bp.get("/como-usar")
def guide():
    return render_template("core/guide.html")


@bp.get("/novidades")
def changelog():
    from .changelog import RELEASES

    return render_template("core/changelog.html", releases=RELEASES)
