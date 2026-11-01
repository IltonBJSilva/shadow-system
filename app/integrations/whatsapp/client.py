"""WhatsApp Cloud API (Meta), oficial: https://developers.facebook.com/docs/whatsapp/cloud-api

Endpoints usados (Graph API, versão fixada em GRAPH_VERSION):
    GET  /{phone-number-id}?fields=display_phone_number,verified_name   confere token e número
    POST /{phone-number-id}/messages                                    envia mensagem

Regra do WhatsApp: mensagem de texto livre só é entregue se o destinatário mandou mensagem para o
número da empresa nas últimas 24 horas. Fora dessa janela, só templates aprovados (ex.: hello_world).
"""
import re

import httpx

GRAPH_URL = "https://graph.facebook.com"
GRAPH_VERSION = "v21.0"
_DIGITS = re.compile(r"\d{8,15}")


class WhatsAppError(Exception):
    """Erro da API do WhatsApp. A mensagem é mostrada ao usuário e nunca contém o token."""


def normalize_number(raw: str) -> str:
    """'+55 (11) 99999-9999' -> '5511999999999'. A API quer só dígitos, com DDI."""
    digits = re.sub(r"\D", "", raw or "")
    if not _DIGITS.fullmatch(digits):
        raise WhatsAppError("Número inválido. Use DDI + DDD + número, ex.: 5511999999999.")
    return digits


class WhatsAppClient:
    def __init__(self, token: str, phone_number_id: str, transport: httpx.BaseTransport | None = None):
        if not token or not phone_number_id:
            raise WhatsAppError("WhatsApp não configurado.")
        if not phone_number_id.isdigit():
            raise WhatsAppError("O Phone number ID tem só números (veja em WhatsApp > Configuração da API).")
        self.phone_number_id = phone_number_id
        self._http = httpx.Client(base_url=f"{GRAPH_URL}/{GRAPH_VERSION}", timeout=20.0, transport=transport,
                                  headers={"Authorization": f"Bearer {token}"})

    def phone_info(self) -> dict:
        return self._request("GET", f"/{self.phone_number_id}",
                             params={"fields": "display_phone_number,verified_name"})

    def send_text(self, to: str, body: str) -> str:
        if not body.strip():
            raise WhatsAppError("Mensagem vazia.")
        data = self._request("POST", f"/{self.phone_number_id}/messages", json={
            "messaging_product": "whatsapp", "to": normalize_number(to), "type": "text",
            "text": {"preview_url": False, "body": body[:4096]},
        })
        return _message_id(data)

    def send_template(self, to: str, name: str = "hello_world", language: str = "en_US") -> str:
        data = self._request("POST", f"/{self.phone_number_id}/messages", json={
            "messaging_product": "whatsapp", "to": normalize_number(to), "type": "template",
            "template": {"name": name, "language": {"code": language}},
        })
        return _message_id(data)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise WhatsAppError("Não foi possível falar com o WhatsApp. Confira a internet.") from exc
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code >= 400:
            error = data.get("error", {}) if isinstance(data, dict) else {}
            if response.status_code == 401 or error.get("code") == 190:
                raise WhatsAppError("O WhatsApp recusou o token (venceu ou é inválido). Gere outro.")
            raise WhatsAppError(f"WhatsApp: {error.get('message') or f'erro {response.status_code}'}")
        return data


def _message_id(data: dict) -> str:
    messages = data.get("messages") or [{}]
    return messages[0].get("id", "")
