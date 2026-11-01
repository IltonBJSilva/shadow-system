"""Rotas técnicas do núcleo."""
from flask import Blueprint

bp = Blueprint("core", __name__)


@bp.get("/health")
def health():
    """Checagem de vida para monitoramento. Pública mesmo com login ligado."""
    return {"ok": True}
