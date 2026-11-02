"""Telas de treinos: lista, criar (rotina pronta, texto ou documento), plano, editar e progressão."""
from flask import flash, redirect, render_template, request, url_for

from app.core.errors import DomainError

from . import bp, documents, library, parser, services
from .forms import PlanForm, UploadForm

EXAMPLE = """Plano: Meu treino
Segunda: Treino A - Peito e tríceps
- Supino reto 4x8-12 40kg descanso 90s
- Tríceps na polia 3x12 (pegada neutra)
Quarta: Treino B - Costas e bíceps
- Puxada frontal 4x10 35kg
- Rosca direta 3x12
Sexta: Treino C - Pernas
- Agachamento 4x8 60kg descanso 2min
- Prancha 3x45s
"""


@bp.get("/")
def index():
    plans = services.list_plans()
    weeks = {p.id: services.week_progress(p) for p in plans}
    return render_template("training/index.html", plans=plans, weeks=weeks, weekdays=parser.WEEKDAY_LABELS,
                           sessions={p.id: services.sessions_count(p.id) for p in plans})


@bp.route("/new", methods=["GET", "POST"])
def new():
    form = PlanForm()
    template = library.get_template(request.args.get("template", ""))
    if request.method == "GET":
        if template:
            form.text.data = template.text
            form.name.data = parser.parse(template.text).name
    parsed, error = None, None
    if request.method == "POST":
        if form.validate_on_submit():
            if request.form.get("action") == "create":
                try:
                    plan = services.create_plan(form.text.data, _options(form))
                except DomainError as exc:
                    error = str(exc)
                else:
                    flash(f"Plano \"{plan.name}\" criado e ativado.", "success")
                    return redirect(url_for("training.detail", plan_id=plan.id))
            parsed, error = _preview(form.text.data, error)
        else:
            error = "Confira os campos destacados."
    elif form.text.data:
        parsed, error = _preview(form.text.data, None)
    return render_template("training/new.html", form=form, upload=UploadForm(), parsed=parsed, error=error,
                           templates=library.TEMPLATES, example=EXAMPLE, weekdays=parser.WEEKDAY_LABELS)


@bp.post("/upload")
def upload():
    file = request.files.get("document")
    form = PlanForm(formdata=None)
    parsed, error = None, None
    if not file or not file.filename:
        error = "Escolha um arquivo."
    else:
        try:
            form.text.data = documents.extract_text(file.filename, file.read(documents.MAX_BYTES + 1))
        except documents.DocumentError as exc:
            error = str(exc)
        else:
            parsed, error = _preview(form.text.data, None)
            form.name.data = (parsed.name if parsed and parsed.name else file.filename.rsplit(".", 1)[0])[:120]
    return render_template("training/new.html", form=form, upload=UploadForm(), parsed=parsed, error=error,
                           templates=library.TEMPLATES, example=EXAMPLE, weekdays=parser.WEEKDAY_LABELS,
                           from_document=True)


@bp.get("/<int:plan_id>")
def detail(plan_id: int):
    plan = services.get_plan(plan_id)
    return render_template(
        "training/detail.html", plan=plan, weekdays=parser.WEEKDAY_LABELS,
        week=services.week_progress(plan), sessions=services.sessions_count(plan.id),
        recent=services.recent_sessions(plan.id),
        suggestions=services.progression_suggestions(plan) if plan.pending_progression_week else [],
    )


@bp.route("/<int:plan_id>/edit", methods=["GET", "POST"])
def edit(plan_id: int):
    plan = services.get_plan(plan_id)
    form = PlanForm(obj=plan)
    if request.method == "GET":
        form.text.data = services.plan_text(plan)
    parsed, error = None, None
    if request.method == "POST":
        if form.validate_on_submit():
            if request.form.get("action") == "save":
                try:
                    services.update_plan(plan_id, form.text.data, _options(form))
                except DomainError as exc:
                    error = str(exc)
                else:
                    flash("Plano atualizado." + (" Quests e calendário refeitos." if plan.active else ""), "success")
                    return redirect(url_for("training.detail", plan_id=plan_id))
            parsed, error = _preview(form.text.data, error)
        else:
            error = "Confira os campos destacados."
    else:
        parsed, error = _preview(form.text.data, None)
    return render_template("training/edit.html", form=form, plan=plan, parsed=parsed, error=error,
                           weekdays=parser.WEEKDAY_LABELS)


@bp.post("/<int:plan_id>/activate")
def activate(plan_id: int):
    done = services.activate_plan(plan_id)
    flash("Plano ativado: " + ", ".join(done) + "." if done else "Plano ativado.", "success")
    return redirect(url_for("training.detail", plan_id=plan_id))


@bp.post("/<int:plan_id>/deactivate")
def deactivate(plan_id: int):
    services.deactivate_plan(plan_id)
    flash("Plano pausado: quests pendentes canceladas e eventos futuros removidos. O histórico continua.", "info")
    return redirect(url_for("training.detail", plan_id=plan_id))


@bp.post("/<int:plan_id>/delete")
def delete(plan_id: int):
    services.delete_plan(plan_id)
    flash("Plano removido. O XP já ganho continua no histórico.", "info")
    return redirect(url_for("training.index"))


@bp.post("/<int:plan_id>/progression/apply")
def apply_progression(plan_id: int):
    changed = services.apply_progression(plan_id)
    flash(f"Progressão aplicada em {changed} exercício(s). As próximas quests já mostram os valores novos.", "success")
    return redirect(url_for("training.detail", plan_id=plan_id))


@bp.post("/<int:plan_id>/progression/dismiss")
def dismiss_progression(plan_id: int):
    services.dismiss_progression(plan_id)
    flash("Sugestão ignorada. Os valores continuam os mesmos.", "info")
    return redirect(url_for("training.detail", plan_id=plan_id))


def _preview(text: str, error: str | None):
    try:
        return services.preview(text), error
    except DomainError as exc:
        return None, error or str(exc)


def _options(form: PlanForm) -> services.PlanOptions:
    increment = form.load_increment_kg.data
    return services.PlanOptions(
        name=form.name.data or "", description=form.description.data or "", start_date=form.start_date.data,
        session_time=form.session_time.data.zfill(5), session_minutes=form.session_minutes.data,
        make_quests=form.make_quests.data, make_events=form.make_events.data, make_habit=form.make_habit.data,
        progression=form.progression.data,
        load_increment_kg=float(increment) if increment is not None else 2.5,
    )
