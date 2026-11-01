"""Cliente HTTP do Kausa Social Scheduler (projeto separado, em E:\\Repositorio\\kausa-social-scheduler).

Usa somente rotas que existem no Kausa (conferido no código dele em 01/11/2026, app/routes.py):

    GET /saude                       -> {"ok": true}
    GET /api/canais                  -> {"channels": [{id, name, displayName, service, usable, ...}]}
    GET /api/posts?status=scheduled  -> {"posts": [{id, text, status, dueAt, channelId,
                                                     channelService, channelName, error, assets}]}

Criar posts (POST /api/posts) exige upload multipart de imagens; isso continua sendo feito pelo
painel do Kausa. Este cliente é só leitura por enquanto.
"""
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.core import time


class KausaSchedulerError(Exception):
    """Falha ao falar com o Kausa. A mensagem é mostrada ao usuário."""


@dataclass(frozen=True)
class ScheduledPost:
    id: str
    text: str
    status: str
    due_at: datetime | None  # horário local
    channel: str
    service: str
    error: str | None


@dataclass(frozen=True)
class Channel:
    id: str
    name: str
    service: str
    usable: bool


class KausaSchedulerClient:
    def __init__(self, base_url: str, timeout: float = 5.0, transport: httpx.BaseTransport | None = None):
        if not base_url:
            raise KausaSchedulerError("KAUSA_SCHEDULER_URL não configurada.")
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout, transport=transport)

    def health(self) -> bool:
        try:
            return self._get("/saude").get("ok") is True
        except KausaSchedulerError:
            return False

    def channels(self) -> list[Channel]:
        data = self._get("/api/canais")
        return [
            Channel(
                id=str(ch.get("id", "")),
                name=ch.get("displayName") or ch.get("name") or ch.get("service", ""),
                service=ch.get("service", ""),
                usable=bool(ch.get("usable")),
            )
            for ch in data.get("channels", [])
        ]

    def posts(self, status: str | None = "scheduled") -> list[ScheduledPost]:
        params = {"status": status} if status else None
        data = self._get("/api/posts", params=params)
        posts = [_parse_post(p) for p in data.get("posts", [])]
        return sorted(posts, key=lambda p: p.due_at or datetime.max)

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            response = self._http.get(path, params=params)
        except httpx.HTTPError as exc:
            raise KausaSchedulerError(
                "Não foi possível falar com o Kausa Social Scheduler. Ele está rodando? (.\\run.ps1 no projeto dele)"
            ) from exc
        if response.status_code == 401:
            raise KausaSchedulerError(
                "O Kausa está com login ligado e a API dele não aceita acesso de outro app ainda. "
                "Veja docs/integrations.md (Kausa: limitações)."
            )
        if response.status_code >= 400:
            message = _error_message(response)
            raise KausaSchedulerError(f"Kausa respondeu {response.status_code}: {message}")
        try:
            return response.json()
        except ValueError as exc:
            raise KausaSchedulerError("Resposta inesperada do Kausa (não é JSON).") from exc


def _parse_post(raw: dict) -> ScheduledPost:
    due_at = None
    if raw.get("dueAt"):
        try:
            due_at = time.to_local_naive(datetime.fromisoformat(raw["dueAt"].replace("Z", "+00:00")))
        except ValueError:
            due_at = None
    error = (raw.get("error") or {}).get("message") if isinstance(raw.get("error"), dict) else None
    return ScheduledPost(
        id=str(raw.get("id", "")),
        text=raw.get("text") or "",
        status=raw.get("status") or "",
        due_at=due_at,
        channel=raw.get("channelName") or raw.get("channelService") or "",
        service=raw.get("channelService") or "",
        error=error,
    )


def _error_message(response: httpx.Response) -> str:
    try:
        return response.json().get("error") or response.reason_phrase
    except ValueError:
        return response.reason_phrase
