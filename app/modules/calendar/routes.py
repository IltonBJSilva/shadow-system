from datetime import date

from flask import flash, redirect, render_template, request, url_for

from app.core import time
from app.modules.quests import services as quests

from . import bp, services
from .forms import EventForm

MONTH_NAMES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
               "Setembro", "Outubro", "Novembro", "Dezembro"]


@bp.get("/")
def index():
    year, month = _month_from_args()
    form = EventForm()
    if not form.start_date.data:
        form.start_date.data = time.today()
    previous = date(year - 1, 12, 1) if month == 1 else date(year, month - 1, 1)
    following = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return render_template(
        "calendar/index.html",
        weeks=services.month_grid(year, month),
        month_label=f"{MONTH_NAMES[month - 1]} {year}",
        previous=f"{previous:%Y-%m}",
        following=f"{following:%Y-%m}",
        upcoming=services.upcoming_events(days=14, limit=10),
        form=form,
        kinds=services.KINDS,
    )


@bp.post("/events")
def create():
    form = EventForm()
    if form.validate_on_submit():
        event, conflicts = services.save_event(form.to_input())
        flash(f"Evento criado: {event.title}", "success")
        _flash_conflicts(conflicts)
        return redirect(url_for("calendar.index", month=f"{event.start_at:%Y-%m}"))
    for field_name, errors in form.errors.items():
        flash(f"{getattr(form, field_name).label.text}: {'; '.join(errors)}", "error")
    return redirect(url_for("calendar.index"))


@bp.route("/events/<int:event_id>", methods=["GET", "POST"])
def edit(event_id: int):
    event = services.get_event(event_id)
    form = EventForm(obj=event)
    if request.method == "GET":
        form.fill_from(event)
    if form.validate_on_submit():
        event, conflicts = services.save_event(form.to_input(), event_id)
        flash("Evento atualizado.", "success")
        _flash_conflicts(conflicts)
        return redirect(url_for("calendar.index", month=f"{event.start_at:%Y-%m}"))
    return render_template(
        "calendar/form.html", form=form, event=event, quest_title=quests.quest_title(event.quest_id)
    )


@bp.post("/events/<int:event_id>/delete")
def delete(event_id: int):
    services.delete_event(event_id)
    flash("Evento removido do Shadow System.", "info")
    return redirect(url_for("calendar.index"))


def _month_from_args() -> tuple[int, int]:
    raw = request.args.get("month", "")
    try:
        year, month = (int(part) for part in raw.split("-"))
        if 1 <= month <= 12 and 1900 < year < 3000:
            return year, month
    except ValueError:
        pass
    today = time.today()
    return today.year, today.month


def _flash_conflicts(conflicts) -> None:
    if conflicts:
        names = ", ".join(f"{c.title} ({c.start_at:%d/%m %H:%M})" for c in conflicts[:3])
        flash(f"Conflito de horário com: {names}", "error")
