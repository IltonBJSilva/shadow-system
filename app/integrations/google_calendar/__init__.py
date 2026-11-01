"""Integração com o Google Calendar (OAuth 2.0 + Calendar API v3).

Ponto de entrada para o resto do app: `get_client()`, `status()` e o módulo `sync`.
"""
from flask import current_app

from ..registry import IntegrationStatus
from . import oauth
from .client import GoogleCalendarClient, GoogleCalendarError, build_service
from .oauth import GoogleAuthError


def get_client() -> GoogleCalendarClient:
    """Cliente autenticado. Levanta GoogleAuthError se não houver conexão."""
    service = build_service(oauth.load_credentials())
    return GoogleCalendarClient(service, current_app.config.get("GOOGLE_CALENDAR_ID", "primary"))


def status() -> IntegrationStatus:
    base = dict(
        key="google_calendar",
        name="Google Calendar",
        description="Importa sua agenda para o calendário interno e envia eventos do Shadow System para o Google.",
        url="/integrations/google/",
    )
    if not oauth.is_configured():
        return IntegrationStatus(**base, state="not_configured",
                                 detail="Defina GOOGLE_CLIENT_SECRETS_FILE no .env.")
    if not oauth.is_connected():
        return IntegrationStatus(**base, state="configured", detail="Credenciais prontas. Falta conectar a conta.")
    return IntegrationStatus(**base, state="connected",
                             detail=f"Calendário: {current_app.config.get('GOOGLE_CALENDAR_ID', 'primary')}")


__all__ = ["GoogleAuthError", "GoogleCalendarClient", "GoogleCalendarError", "get_client", "status"]
