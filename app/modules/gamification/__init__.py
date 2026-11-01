"""Gamificação: bônus, punições e Penalty Quests.

Não é chamado diretamente pelos outros módulos: reage aos eventos de app/core/events.py
(quest.completed, quest.missed, habit.checked, habit.unchecked).
Depende de: hunter.services, quests.services.
"""
from flask import Blueprint

bp = Blueprint("gamification", __name__, url_prefix="/gamification")

from . import handlers, routes  # noqa: E402,F401  (handlers registra as assinaturas dos eventos)
