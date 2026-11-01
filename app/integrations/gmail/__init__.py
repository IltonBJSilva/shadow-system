"""Gmail (somente leitura): e-mails não lidos e transformar e-mail em quest.

Usa a mesma conta Google e o mesmo cliente OAuth do Google Calendar; só pede o escopo do Gmail
quando você clica em "Autorizar Gmail".
"""
from ..google_calendar import oauth
from ..google_calendar.oauth import GoogleAuthError
from ..registry import IntegrationStatus
from .client import EmailSummary, GmailClient, GmailError, build_service

# Testes trocam por um serviço falso.
_service_factory = None


def is_authorized() -> bool:
    return oauth.is_connected() and oauth.has_scope(oauth.GMAIL_SCOPE)


def get_client() -> GmailClient:
    if not is_authorized():
        raise GoogleAuthError("Gmail não autorizado. Clique em Autorizar Gmail.")
    factory = _service_factory or (lambda: build_service(oauth.load_credentials()))
    return GmailClient(factory())


def status() -> IntegrationStatus:
    base = dict(key="gmail", name="Gmail",
                description="E-mails não lidos no dashboard e e-mail virando quest. Somente leitura.",
                url="/integrations/gmail/")
    if not oauth.is_configured():
        return IntegrationStatus(**base, state="not_configured",
                                 detail="Usa o mesmo cliente OAuth do Google Calendar (GOOGLE_CLIENT_SECRETS_FILE).")
    if not is_authorized():
        return IntegrationStatus(**base, state="configured", detail="Falta autorizar o Gmail.")
    return IntegrationStatus(**base, state="connected", detail="Leitura autorizada.")


def unread_safe(limit: int = 5) -> tuple[int, list[EmailSummary], str | None]:
    """Para o dashboard: nunca quebra a página. Devolve (não lidos, e-mails, erro)."""
    if not is_authorized():
        return 0, [], None
    try:
        client = get_client()
        return client.unread_count(), client.unread(limit), None
    except (GmailError, GoogleAuthError) as exc:
        return 0, [], str(exc)


__all__ = ["EmailSummary", "GmailClient", "GmailError", "get_client", "is_authorized", "status", "unread_safe"]
