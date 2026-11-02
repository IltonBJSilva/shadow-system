"""Cliente da API pública do Notion (https://developers.notion.com/reference).

Endpoints usados (versão da API fixada em NOTION_VERSION):
    GET  /v1/users/me                  confere o token (bot da integração)
    POST /v1/search                    bancos de dados compartilhados com a integração
    POST /v1/databases/{id}/query      páginas de um banco de dados

A integração só enxerga o que você compartilhar com ela no Notion (menu ••• > Conexões).
"""
import re
from dataclasses import dataclass
from datetime import date

import httpx

from app.integrations.network import connection_message
API_URL = "https://api.notion.com/v1"
_ID = re.compile(r"[0-9a-fA-F-]{32,36}")
NOTION_VERSION = "2022-06-28"


class NotionError(Exception):
    """Erro da API do Notion. A mensagem é mostrada ao usuário e nunca contém o token."""


@dataclass(frozen=True)
class NotionDatabase:
    id: str
    title: str
    url: str


@dataclass(frozen=True)
class NotionPage:
    id: str
    title: str
    url: str
    due: date | None
    status: str | None


class NotionClient:
    def __init__(self, token: str, transport: httpx.BaseTransport | None = None):
        if not token:
            raise NotionError("Token do Notion não cadastrado.")
        self._http = httpx.Client(
            base_url=API_URL, timeout=20.0, transport=transport,
            headers={"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION,
                     "Content-Type": "application/json"},
        )

    def me(self) -> str:
        """Nome do bot da integração (confirma que o token funciona)."""
        data = self._request("GET", "/users/me")
        return data.get("name") or "Integração Notion"

    def databases(self) -> list[NotionDatabase]:
        data = self._request("POST", "/search", json={
            "filter": {"property": "object", "value": "database"}, "page_size": 50})
        return [NotionDatabase(item["id"], _plain(item.get("title")) or "(sem título)", item.get("url", ""))
                for item in data.get("results", [])]

    def pages(self, database_id: str, limit: int = 50) -> list[NotionPage]:
        if not _ID.fullmatch(database_id):
            raise NotionError("Id de banco de dados inválido.")
        data =self._request("POST", f"/databases/{database_id}/query", json={"page_size": limit})
        return [_page(item) for item in data.get("results", []) if item.get("object") == "page"]

    def _request(self, method: str, path: str, json: dict | None = None) -> dict:
        try:
            response = self._http.request(method, path, json=json)
        except httpx.HTTPError as exc:
            raise NotionError(connection_message("Notion", API_URL, exc)) from exc
        if response.status_code == 401:
            raise NotionError("O Notion recusou o token. Gere outro em notion.so/my-integrations.")
        if response.status_code == 404:
            raise NotionError("Não encontrado. Compartilhe a página/banco com a integração (••• > Conexões).")
        if response.status_code == 429:
            raise NotionError("Limite de uso do Notion. Tente de novo em instantes.")
        if response.status_code >= 400:
            try:
                message = response.json().get("message", "")
            except ValueError:
                message = ""
            raise NotionError(f"O Notion respondeu {response.status_code}. {message}".strip())
        return response.json()


def _plain(rich_text: list | None) -> str:
    return "".join(part.get("plain_text", "") for part in rich_text or [])


def _page(item: dict) -> NotionPage:
    title, due, status = "", None, None
    for prop in (item.get("properties") or {}).values():
        kind = prop.get("type")
        if kind == "title" and not title:
            title = _plain(prop.get("title"))
        elif kind == "date" and due is None and prop.get("date"):
            try:
                due = date.fromisoformat(prop["date"]["start"][:10])
            except (KeyError, TypeError, ValueError):
                due = None
        elif kind in ("status", "select") and status is None and prop.get(kind):
            status = prop[kind].get("name")
    return NotionPage(item["id"], title or "(sem título)", item.get("url", ""), due, status)
