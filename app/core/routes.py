"""Rotas técnicas do núcleo."""
import logging

from flask import Blueprint
from sqlalchemy import text

from app.extensions import db

bp = Blueprint("core", __name__)
log = logging.getLogger(__name__)


@bp.get("/health")
def health():
    """Checagem de vida para monitoramento e keep-alive. Pública mesmo com login ligado.

    Faz um SELECT 1 no banco: assim o ping que mantém o Render acordado também mantém o projeto do
    Supabase ativo (o plano gratuito pausa após 7 dias sem uso). Não expõe nenhum dado.
    """
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 (qualquer falha do banco vira 503, detalhe só no log)
        log.exception("health: banco indisponível")
        db.session.rollback()
        return {"ok": False, "database": False}, 503
    return {"ok": True, "database": True}
