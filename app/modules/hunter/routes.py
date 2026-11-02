"""Telas do Hunter: status, edição do perfil, atributos e ranks."""
from flask import flash, redirect, render_template, request, url_for

from app.core.http import redirect_back

from . import bp, services
from .forms import AttributeForm, ProfileForm, RankForm, TitleForm


@bp.get("/")
def profile():
    # Confere conquistas ao abrir o perfil: pega metas atingidas antes dos títulos existirem.
    for message, category in services.title_unlock_messages(services.check_titles()):
        flash(message, category)
    services.db_commit()
    status = services.get_status()
    hunter = services.get_hunter()
    titles = services.list_titles()
    return render_template(
        "hunter/profile.html",
        status=status,
        profile_form=ProfileForm(obj=hunter),
        events=services.recent_events(limit=25),
        unlocked_titles=[t for t in titles if t.unlocked],
        history=services.attribute_history(),
        titles_total=len(titles),
    )


@bp.post("/")
def update_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        services.update_profile(form.name.data, avatar_url=form.avatar_url.data or "")
        flash("Perfil atualizado.", "success")
    else:
        flash("Confira os campos do perfil.", "error")
    return redirect(url_for("hunter.profile"))


@bp.route("/attributes/<int:attribute_id>", methods=["GET", "POST"])
def edit_attribute(attribute_id: int):
    attribute = next((a for a in services.list_attributes() if a.id == attribute_id), None)
    form = AttributeForm(obj=attribute)
    if form.validate_on_submit():
        services.update_attribute(attribute_id, form.name.data, form.description.data or "")
        flash("Atributo atualizado.", "success")
        return redirect(url_for("hunter.profile"))
    if attribute is None:
        return render_template("errors/404.html", message="Atributo não encontrado."), 404
    return render_template("hunter/attribute_form.html", form=form, attribute=attribute)


@bp.route("/ranks", methods=["GET", "POST"])
def ranks():
    form = RankForm()
    if form.validate_on_submit():
        services.save_rank(form.code.data, form.name.data, form.min_level.data, form.color.data)
        flash("Rank adicionado.", "success")
        return redirect(url_for("hunter.ranks"))
    return render_template("hunter/ranks.html", ranks=services.list_ranks(), form=form)


@bp.route("/ranks/<int:rank_id>", methods=["GET", "POST"])
def edit_rank(rank_id: int):
    rank = next((r for r in services.list_ranks() if r.id == rank_id), None)
    if rank is None:
        return render_template("errors/404.html", message="Rank não encontrado."), 404
    form = RankForm(obj=rank)
    if form.validate_on_submit():
        services.save_rank(form.code.data, form.name.data, form.min_level.data, form.color.data, rank_id)
        flash("Rank atualizado.", "success")
        return redirect(url_for("hunter.ranks"))
    return render_template("hunter/rank_form.html", form=form, rank=rank)


@bp.post("/ranks/<int:rank_id>/delete")
def delete_rank(rank_id: int):
    services.delete_rank(rank_id)
    flash("Rank removido.", "success")
    return redirect(url_for("hunter.ranks"))


# ---------- Títulos ----------

@bp.get("/titles")
def titles():
    return render_template("hunter/titles.html", titles=services.list_titles(), form=TitleForm(),
                           active=services.get_hunter().title)


@bp.post("/titles")
def create_title():
    form = TitleForm()
    if form.validate_on_submit():
        title = services.create_custom_title(form.name.data, form.description.data or "")
        flash(f"Título criado: {title.name}.", "success")
    else:
        flash("Dê um nome ao título (até 80 caracteres).", "error")
    return redirect(url_for("hunter.titles"))


@bp.post("/titles/choose")
def choose_title():
    title_id = request.form.get("title_id", "")
    if title_id.isdigit():
        flash(f"Título exibido: {services.choose_title(int(title_id))}.", "success")
    return redirect_back(url_for("hunter.titles"))


@bp.post("/titles/<int:title_id>/delete")
def delete_title(title_id: int):
    services.delete_title(title_id)
    flash("Título removido.", "info")
    return redirect(url_for("hunter.titles"))
