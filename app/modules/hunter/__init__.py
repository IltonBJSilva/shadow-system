"""Módulo Hunter: perfil, nível, rank, atributos e histórico de XP.

API pública para outros módulos: `app.modules.hunter.services` (award_xp, get_status...).
"""
from flask import Blueprint

bp = Blueprint("hunter", __name__, url_prefix="/hunter")

from . import cli, models, routes  # noqa: E402,F401  (registra rotas, comandos e tabelas)
