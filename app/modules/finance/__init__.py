"""Finanças pessoais: contas, cartões, lançamentos, recorrentes, orçamentos, metas, relatórios e
missões financeiras.

Privado por padrão e isolado: nenhum outro módulo lê estas tabelas (Arena e feed nunca mostram valores).
A única ligação com o jogo é o XP das missões financeiras (finance/missions.py), com limites.
Sem integração bancária: tudo é lançado pelo próprio usuário.
"""
from flask import Blueprint

bp = Blueprint("finance", __name__, url_prefix="/financas")

from . import models, routes  # noqa: E402,F401
