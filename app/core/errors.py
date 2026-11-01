"""Exceções de domínio e páginas de erro.

Serviços levantam `DomainError` (ou subclasses) quando uma regra de negócio é violada.
As rotas não precisam capturar: o handler global mostra a mensagem e volta para a página anterior.
"""
import logging

from flask import Flask, flash, redirect, render_template, request

log = logging.getLogger(__name__)


class DomainError(Exception):
    """Regra de negócio violada. A mensagem é mostrada ao usuário, então escreva-a para ele."""


class NotFoundError(DomainError):
    """Registro pedido não existe."""


def register(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def handle_domain_error(exc: DomainError):
        if isinstance(exc, NotFoundError):
            return render_template("errors/404.html", message=str(exc)), 404
        flash(str(exc), "error")
        return redirect(_safe_referrer())

    @app.errorhandler(404)
    def not_found(_exc):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(exc):
        # Só o tipo do erro vai para o log; o stack trace completo aparece no modo debug.
        log.error("Erro interno: %s", type(exc).__name__)
        return render_template("errors/500.html"), 500


def _safe_referrer() -> str:
    """Volta para a página anterior apenas se ela for deste mesmo site."""
    ref = request.referrer or ""
    if ref.startswith(request.host_url):
        return ref
    return "/"
