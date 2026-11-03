"""Telas do Quest System. As regras ficam em services.py; aqui só entrada e saída."""
from flask import flash, redirect, render_template, request, url_for

from app.core.http import redirect_back
from app.modules.hunter import services as hunter

from . import bp, constants, services
from .forms import CategoryForm, QuestForm

VIEWS = {"active": "Ativas", "completed": "Concluídas", "closed": "Não realizadas / canceladas", "all": "Todas"}


@bp.get("/")
def index():
    _, messages = services.roll_over_with_messages()
    for message, category in messages:
        flash(message, category)
    view = request.args.get("view", "active")
    view = view if view in VIEWS else "active"
    quest_type = request.args.get("type") or None
    quests = services.list_quests(view, quest_type if quest_type in constants.QUEST_TYPES else None)
    return render_template(
        "quests/index.html",
        quests=quests,
        form=QuestForm(),
        views=VIEWS,
        current_view=view,
        current_type=quest_type,
        stats=services.stats(),
        constants=constants,
    )


@bp.post("/")
def create():
    form = QuestForm()
    if form.validate_on_submit():
        quest = services.create_quest(form.to_input())
        flash(f"[Nova quest] {quest.title}", "success")
    else:
        _flash_errors(form)
    return redirect(url_for("quests.index"))


@bp.get("/<int:quest_id>")
def detail(quest_id: int):
    quest = services.get_quest(quest_id)
    return render_template(
        "quests/detail.html",
        quest=quest,
        attribute_names=services.attribute_names_for(quest),
        constants=constants,
        quote=services.quote_quest(quest),
        award=hunter.event_for("quest", quest.id),
        memories=_memories_for(quest.id),
    )


@bp.route("/<int:quest_id>/edit", methods=["GET", "POST"])
def edit(quest_id: int):
    quest = services.get_quest(quest_id)
    form = QuestForm(obj=quest)
    if request.method == "GET":
        form.category_id.data = quest.category_id or 0
        form.attribute_ids.data = services.attribute_ids_for(quest)
    if form.validate_on_submit():
        services.update_quest(quest_id, form.to_input())
        flash("Quest atualizada.", "success")
        return redirect(url_for("quests.detail", quest_id=quest_id))
    return render_template("quests/form.html", form=form, quest=quest)


@bp.post("/<int:quest_id>/start")
def start(quest_id: int):
    services.start_quest(quest_id)
    return redirect_back(url_for("quests.index"))


@bp.post("/<int:quest_id>/complete")
def complete(quest_id: int):
    raw = (request.form.get("actual_minutes") or "").strip()
    result = services.complete_quest(quest_id, int(raw) if raw.isdigit() else None)
    for message, category in hunter.award_messages(result):
        flash(message, category)
    return redirect_back(url_for("quests.index"))


@bp.post("/<int:quest_id>/cancel")
def cancel(quest_id: int):
    services.cancel_quest(quest_id)
    flash("Quest cancelada. Sem perda de XP.", "info")
    return redirect_back(url_for("quests.index"))


@bp.post("/<int:quest_id>/delete")
def delete(quest_id: int):
    services.delete_quest(quest_id)
    flash("Quest removida.", "info")
    return redirect(url_for("quests.index"))


@bp.post("/bulk")
def bulk():
    """Ações em várias quests marcadas na lista: excluir ou cancelar."""
    ids = [int(value) for value in request.form.getlist("ids") if value.isdigit()]
    action = request.form.get("action")
    if not ids:
        flash("Marque pelo menos uma quest.", "info")
    elif action == "delete":
        flash(f"{services.delete_quests(ids)} quest(s) removida(s).", "info")
    elif action == "cancel":
        flash(f"{services.cancel_quests(ids)} quest(s) cancelada(s). Sem perda de XP.", "info")
    else:
        flash("Ação desconhecida.", "error")
    return redirect_back(url_for("quests.index"))


@bp.route("/categories", methods=["GET", "POST"])
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        services.save_category(form.name.data, form.color.data, list(form.attribute_ids.data or []),
                               specialty=form.specialty.data, xp_multiplier=float(form.xp_multiplier.data or 1))
        flash("Categoria criada.", "success")
        return redirect(url_for("quests.categories"))
    attribute_names = {a.id: a.name for a in hunter.list_attributes()}
    items = [(c, [attribute_names.get(i, "?") for i in services.category_attribute_ids(c.id)])
             for c in services.list_categories()]
    return render_template("quests/categories.html", form=form, items=items)


@bp.post("/categories/suggested")
def suggested_categories():
    created = services.create_suggested_categories()
    flash(f"{len(created)} categoria(s) criada(s): {', '.join(created)}." if created
          else "Todas as categorias sugeridas já existem.", "success" if created else "info")
    return redirect(url_for("quests.categories"))


@bp.route("/categories/<int:category_id>", methods=["GET", "POST"])
def edit_category(category_id: int):
    category = next((c for c in services.list_categories() if c.id == category_id), None)
    if category is None:
        return render_template("errors/404.html", message="Categoria não encontrada."), 404
    form = CategoryForm(obj=category)
    if request.method == "GET":
        form.attribute_ids.data = services.category_attribute_ids(category_id)
    if form.validate_on_submit():
        services.save_category(form.name.data, form.color.data, list(form.attribute_ids.data or []), category_id,
                               specialty=form.specialty.data, xp_multiplier=float(form.xp_multiplier.data or 1))
        flash("Categoria atualizada.", "success")
        return redirect(url_for("quests.categories"))
    return render_template("quests/category_form.html", form=form, category=category)


@bp.post("/categories/<int:category_id>/delete")
def delete_category(category_id: int):
    services.delete_category(category_id)
    flash("Categoria removida. As quests dela ficaram sem categoria.", "info")
    return redirect(url_for("quests.categories"))


def _flash_errors(form) -> None:
    for field_name, errors in form.errors.items():
        label = getattr(form, field_name).label.text if hasattr(form, field_name) else field_name
        flash(f"{label}: {'; '.join(errors)}", "error")


def _memories_for(quest_id: int) -> list:
    """Memórias ligadas à missão (a tela de Quests mostra as miniaturas)."""
    from app.modules.memories import services as memories

    return memories.for_quest(quest_id)
