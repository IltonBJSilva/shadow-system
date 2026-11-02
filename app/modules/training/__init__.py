"""Treinos: rotinas prontas ou importadas de texto/documento, viradas em quests, calendário,
hábito e progressão de carga.

Depende de: quests, habits, calendar e hunter (pelas APIs públicas). API pública:
`app.modules.training.services`. Reage ao evento "quest.completed" (handlers.py).
"""
from flask import Blueprint

bp = Blueprint("training", __name__, url_prefix="/training")

from . import handlers, models, routes, services  # noqa: E402,F401
from app.modules.hunter import services as _hunter  # noqa: E402

_hunter.register_metric("workouts_completed", services.sessions_count)
