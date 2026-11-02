"""O Arquiteto: mentor do sistema. Lê os dados reais (context.py), tira conclusões por regras
(analysis.py) e, se você cadastrar uma chave da Anthropic, conversa e monta planos com o Claude (ai.py).

Depende de: hunter, quests, habits, gamification e training (só leitura, pela API pública), e de
quests para criar as missões que você aceitar. API pública: `app.modules.architect.services`.
"""
from flask import Blueprint

bp = Blueprint("architect", __name__, url_prefix="/architect")

from . import models, routes  # noqa: E402,F401
