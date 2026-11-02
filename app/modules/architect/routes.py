"""Telas do Arquiteto: relatório, sugestões, metas, conversa e configuração da IA."""
from flask import flash, redirect, render_template, request, url_for

from app.modules.quests import services as quests

from . import ai, bp, services
from .ai import ArchitectAIError
from .forms import AskForm, GoalForm, KeyForm, PlanForm


@bp.errorhandler(ArchitectAIError)
def _ai_error(exc):
    flash(str(exc), "error")
    return redirect(url_for("architect.index"))


@bp.get("/")
def index():
    snapshot, report = services.report()
    goal_form = GoalForm()
    goal_form.area.choices = [("", "—")] + [(c.name, c.name) for c in quests.list_categories()]
    return render_template(
        "architect/index.html", snapshot=snapshot, report=report, suggestions=services.pending_suggestions(),
        goals=services.list_goals(), goal_form=goal_form, ask_form=AskForm(), plan_form=PlanForm(),
        ai_ready=ai.is_configured(), ai_model=ai.MODELS.get(ai.model(), ai.model()),
        messages=services.conversation(12),
    )


@bp.post("/suggestions/<int:suggestion_id>/accept")
def accept(suggestion_id: int):
    services.accept_suggestion(suggestion_id)
    flash("Missão criada a partir da sugestão do Arquiteto. Ela já está em Quests.", "success")
    return redirect(url_for("architect.index"))


@bp.post("/suggestions/<int:suggestion_id>/dismiss")
def dismiss(suggestion_id: int):
    services.dismiss_suggestion(suggestion_id)
    flash("Sugestão descartada. A mesma regra não sugere de novo por 14 dias.", "info")
    return redirect(url_for("architect.index"))


@bp.post("/goals")
def create_goal():
    form = GoalForm()
    form.area.choices = [("", "—")] + [(c.name, c.name) for c in quests.list_categories()]
    if form.validate_on_submit():
        services.save_goal(form.title.data, form.area.data or "", form.why.data or "", form.deadline.data)
        flash("Meta registrada. O Arquiteto vai sugerir o próximo passo.", "success")
    else:
        flash("Dê um nome à meta (até 160 caracteres).", "error")
    return redirect(url_for("architect.index"))


@bp.post("/goals/<int:goal_id>/status")
def goal_status(goal_id: int):
    status = request.form.get("status", "")
    services.set_goal_status(goal_id, status)
    flash("Meta concluída. Bom trabalho." if status == "done" else "Meta arquivada.", "success" if status == "done" else "info")
    return redirect(url_for("architect.index"))


@bp.post("/ask")
def ask():
    form = AskForm()
    if form.validate_on_submit():
        services.ask(form.question.data)
    else:
        flash("Escreva uma pergunta (até 4000 caracteres).", "error")
    return redirect(url_for("architect.index") + "#conversa")


@bp.post("/plan")
def plan():
    form = PlanForm()
    summary, created = services.plan_with_ai(form.focus.data or "")
    flash(f"Plano do Arquiteto: {summary} ({created} missão(ões) sugerida(s) abaixo)." if summary
          else f"{created} missão(ões) sugerida(s).", "success")
    return redirect(url_for("architect.index") + "#sugestoes")


@bp.post("/conversation/clear")
def clear_conversation():
    services.clear_conversation()
    flash("Conversa apagada.", "info")
    return redirect(url_for("architect.index"))


@bp.route("/settings", methods=["GET", "POST"])
def settings():
    form = KeyForm()
    if request.method == "POST" and request.form.get("action") == "model":
        ai.set_model(request.form.get("model", ""))
        flash("Modelo do Arquiteto atualizado.", "success")
        return redirect(url_for("architect.settings"))
    if form.validate_on_submit():
        ai.save_key(form.api_key.data, form.model.data)
        flash("Chave conferida e salva. O Arquiteto já pode conversar e montar planos.", "success")
        return redirect(url_for("architect.index"))
    form.model.data = ai.model()
    return render_template("architect/settings.html", form=form, configured=ai.is_configured(),
                           masked=ai.masked_key(), current_model=ai.model(), models=ai.MODELS)


@bp.post("/settings/delete")
def delete_key():
    ai.clear_key()
    flash("Chave da Anthropic removida. Para invalidá-la, apague-a em console.anthropic.com.", "info")
    return redirect(url_for("architect.settings"))
