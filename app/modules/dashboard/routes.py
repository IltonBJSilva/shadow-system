from flask import flash, redirect, render_template, request, url_for

from . import bp, services


@bp.get("/")
def index():
    return render_template("dashboard/index.html", **services.build())


@bp.route("/dashboard/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        services.save_widgets(request.form.getlist("widgets"))
        flash("Dashboard atualizado.", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("dashboard/settings.html", widgets=services.WIDGETS, enabled=services.enabled_widgets())
