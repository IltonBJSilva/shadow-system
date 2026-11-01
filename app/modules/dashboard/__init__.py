"""Dashboard principal: janela de status e widgets configuráveis.

Só lê a API pública de hunter, quests, habits, calendar e da integração com o Buffer.
"""
from flask import Blueprint

bp = Blueprint("dashboard", __name__)

from . import routes  # noqa: E402,F401
