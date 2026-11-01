"""Hábitos diários com check-in, sequência (streak) e XP.

Depende de: hunter.services. API pública: `app.modules.habits.services`.
"""
from flask import Blueprint

bp = Blueprint("habits", __name__, url_prefix="/habits")

from . import models, routes  # noqa: E402,F401
