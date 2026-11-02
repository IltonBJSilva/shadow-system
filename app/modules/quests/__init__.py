"""Quest System: missões com tipos, prioridade, dificuldade, prazo, recorrência e recompensas.

Depende de: hunter.services (para conceder XP). API pública: `app.modules.quests.services`.
"""
from flask import Blueprint

bp = Blueprint("quests", __name__, url_prefix="/quests")

from . import cli, models, routes, services  # noqa: E402,F401
from app.modules.hunter import services as _hunter  # noqa: E402

_hunter.register_metric("quests_completed", services.completed_count)
