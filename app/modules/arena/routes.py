"""Telas da Arena: ranking, perfil público e privacidade."""
from flask import flash, redirect, render_template, request, url_for

from . import bp, feed, services


@bp.get("/")
def index():
    sort = request.args.get("sort", "xp_week")
    sort = sort if sort in services.SORTS else "xp_week"
    return render_template("arena/index.html", cards=services.leaderboard(sort), sort=sort, sorts=services.SORTS,
                           privacy=services.privacy(), privacy_options=services.PRIVACY_OPTIONS)


@bp.get("/<int:user_id>")
def profile(user_id: int):
    return render_template("arena/profile.html", profile=services.public_profile(user_id))


@bp.get("/feed")
def feed_page():
    kind = request.args.get("tipo") or None
    return render_template("arena/feed.html", items=feed.recent(kind=kind), kind=kind, kinds=FEED_KINDS)


FEED_KINDS = {"quest": "Missões", "level": "Níveis", "rank": "Ranks", "title": "Conquistas", "shadow": "Sombras",
              "item": "Equipamentos", "memory": "Memórias"}


@bp.post("/privacidade")
def save_privacy():
    services.set_privacy({key: request.form.get(key) == "1" for key in services.PRIVACY_OPTIONS})
    flash("Privacidade da Arena salva.", "success")
    return redirect(url_for("arena.index"))
