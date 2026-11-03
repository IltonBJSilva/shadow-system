"""Personagem (inspirado nos menus de RPG): atributos de combate, inventário e equipamentos.

Depende de: hunter, quests, habits, training (só APIs públicas). Registra um provedor de bônus de XP
(itens equipados) e reage a "quest.completed" para entregar itens conquistados.
"""
from flask import Blueprint

bp = Blueprint("character", __name__, url_prefix="/personagem")

from . import handlers, models, routes  # noqa: E402,F401
