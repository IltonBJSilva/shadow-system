from flask import flash, redirect, render_template, request, url_for

from app.core import experience

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
        experience.set_boot_mode(request.form.get("boot_mode", experience.DEFAULT_BOOT_MODE))
        flash("Dashboard atualizado.", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("dashboard/settings.html", widgets=services.WIDGETS, enabled=services.enabled_widgets(),
                           boot_modes=experience.BOOT_MODES, current_boot=experience.boot_mode())
