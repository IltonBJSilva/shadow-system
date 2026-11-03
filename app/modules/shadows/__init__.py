"""Loja das Sombras: sombras recrutadas ao superar desafios reais.

Cada sombra representa uma habilidade conquistada, exige um rank mínimo e desafios medidos com dados
reais (character.services.metrics), dá bônus de atributo (ficha do Personagem) e bônus de XP nas
missões da sua especialização, com acúmulo controlado e os limites gerais de bônus.
"""
from flask import Blueprint

bp = Blueprint("shadows", __name__, url_prefix="/sombras")

from . import handlers, models, routes  # noqa: E402,F401
