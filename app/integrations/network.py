"""Mensagens de falha de rede compartilhadas pelos clientes das integrações.

No plano gratuito do PythonAnywhere toda chamada externa passa por um proxy que só deixa passar
domínios de uma lista liberada. Um domínio fora da lista volta como `httpx.ProxyError` (403 no
túnel), e "confira a internet" não ajuda: o usuário precisa saber que é o bloqueio do proxy.
"""
from urllib.parse import urlparse

import httpx

ALLOWLIST_URL = "https://www.pythonanywhere.com/whitelist/"


def connection_message(service: str, url: str, exc: Exception) -> str:
    host = urlparse(url).hostname or url
    if isinstance(exc, httpx.ProxyError) or ("403" in str(exc) and "proxy" in str(exc).lower()):
        return (f"O servidor bloqueou o acesso a {host}. No plano gratuito do PythonAnywhere só "
                f"sites liberados funcionam: peça a liberação de {host} no fórum do PythonAnywhere "
                f"(lista em {ALLOWLIST_URL}) ou use o plano pago.")
    if isinstance(exc, httpx.TimeoutException):
        return f"O {service} demorou demais para responder. Tente de novo."
    return f"Não foi possível falar com o {service} ({host}). Confira a internet."
