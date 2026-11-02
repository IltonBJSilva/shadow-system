"""Hábitos diários com check-in, sequência (streak) e XP.

Depende de: hunter.services. API pública: `app.modules.habits.services`.
"""
from flask import Blueprint

bp = Blueprint("habits", __name__, url_prefix="/habits")

from . import models, routes, services  # noqa: E402,F401
from app.modules.hunter import services as _hunter  # noqa: E402

_hunter.register_metric("habit_best_streak", services.best_streak_ever)
