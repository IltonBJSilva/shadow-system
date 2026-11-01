"""Calendário interno: eventos, visão mensal, quests com prazo e detecção de conflitos.

Depende de: quests.services (quests com prazo aparecem no calendário).
API pública: `app.modules.calendar.services`.
"""
from flask import Blueprint

bp = Blueprint("calendar", __name__, url_prefix="/calendar")

from . import models, routes  # noqa: E402,F401
