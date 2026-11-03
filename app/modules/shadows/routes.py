"""Tela da Loja das Sombras."""
from flask import flash, redirect, render_template, url_for

from app.modules.character import catalog as items

from . import bp, catalog, services


@bp.get("/")
def index():
    return render_template("shadows/index.html", states=services.shop(), history=services.history(),
                           labels=catalog.METRIC_LABELS, stack=catalog.STACK_FACTOR,
                           stat_names={key: name for key, (name, _) in items.STATS.items()})


@bp.post("/<shadow_key>/recrutar")
def recruit(shadow_key: str):
    shadow = services.recruit(shadow_key)
    flash(f"ARISE. {shadow.name}, {shadow.title}, agora segue você. +{shadow.xp_bonus} XP em missões de {shadow.specialty_label}.",
          "achievement")
    return redirect(url_for("shadows.index"))
