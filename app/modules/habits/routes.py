from datetime import date

from flask import flash, redirect, render_template, request, url_for

from app.core.errors import DomainError
from app.core.http import redirect_back
from app.modules.hunter import services as hunter

from . import bp, services
from .forms import HabitForm


@bp.get("/")
def index():
    return render_template(
        "habits/index.html",
        habits=services.list_habits(active=True),
        archived=services.list_habits(active=False),
        form=HabitForm(),
    )


@bp.post("/")
def create():
    form = HabitForm()
    if form.validate_on_submit():
        services.save_habit(form.name.data, form.description.data or "", form.xp_per_check.data,
                            list(form.attribute_ids.data or []), weekdays=list(form.weekdays.data or []))
        flash("Hábito criado.", "success")
    else:
        flash("Confira os campos do hábito.", "error")
    return redirect(url_for("habits.index"))


@bp.route("/<int:habit_id>/edit", methods=["GET", "POST"])
def edit(habit_id: int):
    habit = services.get_habit(habit_id)
    form = HabitForm(obj=habit)
    if request.method == "GET":
        form.attribute_ids.data = services.attribute_ids_for(habit)
        form.weekdays.data = sorted(services.weekdays_for(habit))
    if form.validate_on_submit():
        services.save_habit(form.name.data, form.description.data or "", form.xp_per_check.data,
                            list(form.attribute_ids.data or []), habit_id,
                            weekdays=list(form.weekdays.data or []))
        flash("Hábito atualizado.", "success")
        return redirect(url_for("habits.index"))
    return render_template("habits/form.html", form=form, habit=habit)


@bp.post("/<int:habit_id>/check")
def check(habit_id: int):
    result = services.check_in(habit_id, _day_from_form())
    for message, category in hunter.award_messages(result):
        flash(message, category)
    return redirect_back(url_for("habits.index"))


@bp.post("/<int:habit_id>/uncheck")
def uncheck(habit_id: int):
    services.undo_check_in(habit_id, _day_from_form())
    flash("Dia desmarcado e XP estornado.", "info")
    return redirect_back(url_for("habits.index"))


@bp.post("/<int:habit_id>/archive")
def archive(habit_id: int):
    services.set_active(habit_id, False)
    flash("Hábito arquivado. O histórico foi mantido.", "info")
    return redirect(url_for("habits.index"))


@bp.post("/<int:habit_id>/restore")
def restore(habit_id: int):
    services.set_active(habit_id, True)
    flash("Hábito reativado.", "success")
    return redirect(url_for("habits.index"))


@bp.post("/<int:habit_id>/delete")
def delete(habit_id: int):
    services.delete_habit(habit_id)
    flash("Hábito removido.", "info")
    return redirect(url_for("habits.index"))


def _day_from_form() -> date | None:
    raw = request.form.get("day")
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise DomainError("Data inválida.") from exc
