"""Arena dos Hunters: ranking entre as contas, indicador de integridade e perfis públicos.

Só lê dados pelas APIs públicas dos outros módulos (hunter, quests...). Respeita a privacidade que
cada jogador escolhe em Arena > Privacidade.
"""
from flask import Blueprint

bp = Blueprint("arena", __name__, url_prefix="/arena")

from . import routes  # noqa: E402,F401
