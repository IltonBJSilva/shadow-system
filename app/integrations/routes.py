"""Tela geral das integrações."""
from flask import Blueprint, render_template

from . import registry

bp = Blueprint("integrations", __name__, url_prefix="/integrations")


@bp.get("/")
def index():
    return render_template("integrations/index.html", statuses=registry.all_statuses())
