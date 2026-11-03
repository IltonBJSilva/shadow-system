"""Telas das Memórias: galeria, nova memória, visualização, privacidade e as imagens."""
import io

from flask import abort, flash, redirect, render_template, request, send_file, url_for

from app.core.errors import DomainError
from app.core.tenancy import current_user_id
from app.modules.quests import constants as quest_constants
from app.modules.quests import services as quests

from . import bp, services


@bp.get("/")
def index():
    filters = {key: request.args.get(key, "") for key in ("search", "kind", "specialty", "rank", "month", "visibility")}
    return render_template(
        "memories/index.html", memories=services.gallery(**filters), filters=filters, kinds=services.KINDS,
        specialties=quest_constants.SPECIALTIES, ranks=services.ranks_used(),
        used_mb=round(services.used_bytes() / (1024 * 1024), 1), max_mb=services.MAX_PER_USER_BYTES // (1024 * 1024),
    )


@bp.route("/nova", methods=["GET", "POST"])
def new():
    quest_id = request.values.get("quest_id", type=int)
    quest = quests.get_quest(quest_id) if quest_id else None
    if request.method == "POST":
        photo = request.files.get("photo")
        try:
            memory = services.create(services.MemoryInput(
                title=request.form.get("title", ""), description=request.form.get("description", ""),
                note=request.form.get("note", ""), kind=request.form.get("kind", "other"),
                quest_id=quest.id if quest else None, achievement=request.form.get("achievement", ""),
                public=request.form.get("public") == "1", share_in_feed=request.form.get("share") == "1",
            ), photo.read(services.images.MAX_UPLOAD_BYTES + 1) if photo else b"")
        except DomainError as exc:
            flash(str(exc), "error")
            return render_template("memories/new.html", quest=quest, kinds=services.KINDS, form=request.form), 400
        flash("Memória registrada no seu álbum de evolução.", "success")
        return redirect(url_for("memories.view", memory_id=memory.id))
    return render_template("memories/new.html", quest=quest, kinds=services.KINDS, form={})


@bp.get("/<int:memory_id>")
def view(memory_id: int):
    return render_template("memories/view.html", memory=services.get(memory_id), kinds=services.KINDS,
                           specialties=quest_constants.SPECIALTIES, own=True)


@bp.get("/publica/<int:memory_id>")
def public_view(memory_id: int):
    memory = services.public(memory_id)
    return render_template("memories/view.html", memory=memory, kinds=services.KINDS,
                           specialties=quest_constants.SPECIALTIES, own=memory.user_id == current_user_id())


@bp.post("/<int:memory_id>/visibilidade")
def visibility(memory_id: int):
    memory = services.set_visibility(memory_id, request.form.get("public") == "1")
    flash("Memória pública: outros Hunters podem ver." if memory.visibility == "public" else "Memória privada.", "info")
    return redirect(url_for("memories.view", memory_id=memory_id))


@bp.post("/<int:memory_id>/apagar")
def delete(memory_id: int):
    services.delete(memory_id)
    flash("Memória e foto apagadas.", "info")
    return redirect(url_for("memories.index"))


@bp.get("/<int:memory_id>/foto")
def photo(memory_id: int):
    return _image(memory_id, "image")


@bp.get("/<int:memory_id>/miniatura")
def thumb(memory_id: int):
    return _image(memory_id, "thumb")


def _image(memory_id: int, field: str):
    try:
        memory = services.public(memory_id)
    except DomainError:
        abort(404)
    response = send_file(io.BytesIO(getattr(memory, field)), mimetype="image/webp", max_age=24 * 3600,
                         etag=f"m{memory.id}-{field}-{memory.size}")
    response.cache_control.private = True  # nunca em cache compartilhado
    return response
