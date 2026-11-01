"""Quest System: missões com tipos, prioridade, dificuldade, prazo, recorrência e recompensas.

Depende de: hunter.services (para conceder XP). API pública: `app.modules.quests.services`.
"""
from flask import Blueprint

bp = Blueprint("quests", __name__, url_prefix="/quests")

from . import cli, models, routes  # noqa: E402,F401
