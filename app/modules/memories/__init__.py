"""Memórias: diário visual da evolução (fotos das atividades, ligadas ou não a uma missão).

Privadas por padrão. Uma memória pública pode ser vista pelos outros Hunters e, se o jogador quiser,
vira um post no feed. Fotos passam por core/images.py (sem metadados, WebP reduzido).
"""
from flask import Blueprint

bp = Blueprint("memories", __name__, url_prefix="/memorias")

from . import models, routes  # noqa: E402,F401
