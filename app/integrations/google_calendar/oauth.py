"""OAuth 2.0 com o Google, usando a biblioteca oficial google-auth-oauthlib.

Fluxo (Authorization Code):
1. /integrations/google/connect -> `authorization_url()` manda o usuário para o Google.
2. O Google volta em GOOGLE_REDIRECT_URI -> `exchange_code()` troca o código por tokens.
3. Os tokens (incluindo o refresh token) ficam em instance/google_token.json, fora do git.
4. `load_credentials()` lê o arquivo e renova o access token quando expira.

Docs: https://developers.google.com/identity/protocols/oauth2/web-server
"""
import json
import os
from pathlib import Path

from flask import current_app
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",   # ler/criar/editar/excluir eventos
    "https://www.googleapis.com/auth/calendar.readonly",  # listar calendários e consultar disponibilidade
]
# Pedido só quando você autoriza o Gmail (somente leitura: nada é enviado nem apagado).
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


class GoogleAuthError(Exception):
    """Problema de configuração ou autorização. A mensagem é mostrada ao usuário."""


def is_configured() -> bool:
    path = current_app.config.get("GOOGLE_CLIENT_SECRETS_FILE", "")
    return bool(path) and Path(path).is_file()


def _token_path() -> Path:
    return Path(current_app.config["GOOGLE_TOKEN_FILE"])


def is_connected() -> bool:
    return _token_path().is_file()


def granted_scopes() -> set[str]:
    """Escopos já autorizados, lidos do token salvo (sem chamar o Google)."""
    try:
        return set(json.loads(_token_path().read_text(encoding="utf-8")).get("scopes") or [])
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def has_scope(scope: str) -> bool:
    return scope in granted_scopes()


def _flow(state: str | None = None, code_verifier: str | None = None, scopes: list[str] | None = None) -> Flow:
    if not is_configured():
        raise GoogleAuthError(
            "Arquivo do cliente OAuth não encontrado. Defina GOOGLE_CLIENT_SECRETS_FILE no .env "
            "(veja docs/integrations.md)."
        )
    redirect_uri = current_app.config["GOOGLE_REDIRECT_URI"]
    if redirect_uri.startswith(("http://localhost", "http://127.0.0.1")):
        # O oauthlib exige HTTPS. Em localhost o Google aceita HTTP, então liberamos só nesse caso.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    # Com include_granted_scopes o Google devolve também escopos autorizados antes (ex.: Calendar ao
    # autorizar o Gmail). Isso é esperado, então o oauthlib não deve tratar como erro.
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    return Flow.from_client_secrets_file(
        current_app.config["GOOGLE_CLIENT_SECRETS_FILE"],
        scopes=scopes or SCOPES,
        redirect_uri=redirect_uri,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=code_verifier is None,
    )


def authorization_url(scopes: list[str] | None = None) -> tuple[str, str, str | None]:
    """Retorna (url, state, code_verifier). state e code_verifier vão para a sessão.

    scopes: padrão = Calendar. Para o Gmail: SCOPES + [GMAIL_SCOPE].
    """
    flow = _flow(scopes=scopes)
    url, state = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
    return url, state, flow.code_verifier


def exchange_code(authorization_response: str, state: str, code_verifier: str | None,
                  scopes: list[str] | None = None) -> None:
    flow = _flow(state=state, code_verifier=code_verifier, scopes=scopes)
    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as exc:  # oauthlib levanta vários tipos; a mensagem dele não tem segredos
        raise GoogleAuthError(f"O Google não autorizou: {type(exc).__name__}.") from exc
    _save(flow.credentials)


def load_credentials() -> Credentials:
    if not is_connected():
        raise GoogleAuthError("Google Calendar não conectado.")
    # Sem passar escopos: vale o que está no token (Calendar e, se autorizado, Gmail).
    creds = Credentials.from_authorized_user_file(str(_token_path()))
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            raise GoogleAuthError("A autorização do Google expirou ou foi revogada. Conecte de novo.") from exc
        _save(creds)
    return creds


def disconnect() -> None:
    """Apaga o token local. Para revogar no Google: https://myaccount.google.com/permissions"""
    _token_path().unlink(missing_ok=True)


def _save(creds: Credentials) -> None:
    path = _token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")
