from flask import flash, redirect, render_template, request, url_for

from . import bp, services


@bp.get("/")
def index():
    data = services.build()
    # Punições aplicadas agora (quests recorrentes que venceram) aparecem como janela do sistema.
    for message, category in data.pop("system_messages"):
        flash(message, category)
    return render_template("dashboard/index.html", **data)


@bp.route("/dashboard/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        services.save_widgets(request.form.getlist("widgets"))
        flash("Dashboard atualizado.", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("dashboard/settings.html", widgets=services.WIDGETS, enabled=services.enabled_widgets())
