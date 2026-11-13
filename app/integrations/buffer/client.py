"""Cliente da API GraphQL do Buffer (https://developers.buffer.com), conta pessoal.

As consultas e mutations usadas aqui são as mesmas já validadas contra a API real no Kausa Social
Scheduler (30/10/2026) e nos scripts de E:\\Repositorio\\postagens:

    query  account { organizations { id name } }
    query  channels(input: {organizationId})
    query  posts(first, input: {organizationId, filter: {status, channelIds}})
    mutation createPost(input: CreatePostInput!)

O transporte HTTP é injetável para os testes nunca chamarem o Buffer de verdade.
"""
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.core import time
from app.integrations.network import connection_message

from .posting import is_video_url

API_URL = "https://api.buffer.com"

# Redes que aceitam post com imagem ou vídeo.
IMAGE_SERVICES = {
    "instagram", "facebook", "linkedin", "tiktok", "threads", "twitter",
    "bluesky", "mastodon", "pinterest", "googlebusiness",
}


class BufferError(Exception):
    """Falha ao falar com o Buffer. A mensagem é mostrada ao usuário e nunca contém o token."""


@dataclass(frozen=True)
class Channel:
    id: str
    name: str
    service: str
    avatar: str | None
    disconnected: bool
    queue_paused: bool

    @property
    def usable(self) -> bool:
        return self.service in IMAGE_SERVICES and not self.disconnected


@dataclass(frozen=True)
class Post:
    id: str
    text: str
    status: str
    due_at: datetime | None  # horário local
    channel_id: str
    service: str
    error: str | None
    thumbnail: str | None
    channel_name: str = ""
    image_urls: tuple[str, ...] = ()
    due_at_raw: str | None = None
    is_video: bool = False

    @property
    def video_url(self) -> str | None:
        for u in self.image_urls:
            if is_video_url(u):
                return u
        if self.thumbnail and is_video_url(self.thumbnail):
            return self.thumbnail
        if self.is_video and self.image_urls:
            return self.image_urls[0]
        return None

    @property
    def poster_url(self) -> str | None:
        if self.thumbnail and not is_video_url(self.thumbnail):
            return self.thumbnail
        return None


class BufferClient:
    def __init__(self, api_key: str, timeout: float = 30.0, transport: httpx.BaseTransport | None = None):
        if not api_key:
            raise BufferError("Token do Buffer não configurado. Cadastre em Integrações > Buffer > Token.")
        self._http = httpx.Client(
            base_url=API_URL,
            timeout=timeout,
            transport=transport,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )

    # ---------- leitura ----------

    def organization_id(self) -> str:
        data = self._query("query { account { organizations { id name } } }")
        orgs = data["account"]["organizations"]
        if not orgs:
            raise BufferError("A conta do Buffer não tem nenhuma organização.")
        return orgs[0]["id"]

    def channels(self, organization_id: str) -> list[Channel]:
        data = self._query(
            """query($org: OrganizationId!) {
                channels(input: {organizationId: $org}) {
                    id name displayName service avatar isQueuePaused isDisconnected
                }
            }""",
            {"org": organization_id},
        )
        return [
            Channel(
                id=ch["id"],
                name=ch.get("displayName") or ch.get("name") or ch["service"],
                service=ch["service"],
                avatar=ch.get("avatar"),
                disconnected=bool(ch.get("isDisconnected")),
                queue_paused=bool(ch.get("isQueuePaused")),
            )
            for ch in data["channels"]
        ]

    def posts(self, organization_id: str, statuses: list[str] | None = None, first: int = 50) -> list[Post]:
        data = self._query(
            """query($org: OrganizationId!, $first: Int, $filter: PostsFiltersInput) {
                posts(first: $first, input: {organizationId: $org, filter: $filter}) {
                    edges { node {
                        id text status dueAt channelId channelService
                        error { message }
                        assets {
                            __typename
                            ... on ImageAsset { source thumbnail }
                            ... on VideoAsset { source thumbnail }
                        }
                    } }
                }
            }""",
            {"org": organization_id, "first": first, "filter": {"status": statuses} if statuses else None},
        )
        return [_parse_post(edge["node"]) for edge in data["posts"]["edges"]]

    def post(self, post_id: str) -> Post:
        data = self._query(
            """query($id: PostId!) {
                post(input: {id: $id}) {
                    id text status dueAt channelId channelService
                    error { message }
                    assets {
                        __typename
                        ... on ImageAsset { source thumbnail }
                        ... on VideoAsset { source thumbnail }
                    }
                }
            }""",
            {"id": post_id},
        )
        post_data = data.get("post")
        if not post_data:
            raise BufferError("Post não encontrado no Buffer.")
        return _parse_post(post_data)

    # ---------- escrita ----------

    def create_post(self, post_input: dict) -> dict:
        data = self._query(
            """mutation($input: CreatePostInput!) {
                createPost(input: $input) {
                    ... on PostActionSuccess { post { id status dueAt } }
                    ... on MutationError { message }
                }
            }""",
            {"input": post_input},
        )
        result = data["createPost"]
        if "post" not in result:
            raise BufferError(result.get("message") or "O Buffer não aceitou o post.")
        return result["post"]

    def edit_post(self, post_input: dict) -> dict:
        data = self._query(
            """mutation($input: EditPostInput!) {
                editPost(input: $input) {
                    ... on PostActionSuccess { post { id status dueAt text } }
                    ... on MutationError { message }
                }
            }""",
            {"input": post_input},
        )
        result = data["editPost"]
        if "post" not in result:
            raise BufferError(result.get("message") or "O Buffer não aceitou a alteração do post.")
        return result["post"]

    def delete_post(self, post_id: str) -> str:
        data = self._query(
            """mutation($input: DeletePostInput!) {
                deletePost(input: $input) {
                    ... on DeletePostSuccess { id }
                    ... on MutationError { message }
                }
            }""",
            {"input": {"id": post_id}},
        )
        result = data["deletePost"]
        if "id" not in result:
            raise BufferError(result.get("message") or "O Buffer não permitiu excluir o post.")
        return result["id"]

    # ---------- interno ----------

    def _query(self, query: str, variables: dict | None = None) -> dict:
        try:
            response = self._http.post("", json={"query": query, "variables": variables or {}})
        except httpx.HTTPError as exc:
            raise BufferError(connection_message("Buffer", API_URL, exc)) from exc
        if response.status_code == 401:
            raise BufferError("O Buffer recusou o token (venceu ou foi apagado). Cadastre um novo.")
        if response.status_code == 429:
            raise BufferError("Limite de uso da API do Buffer atingido. Tente de novo em alguns minutos.")
        if response.status_code >= 400:
            raise BufferError(f"O Buffer respondeu com erro {response.status_code}.")
        try:
            body = response.json()
        except ValueError as exc:
            raise BufferError("Resposta inesperada do Buffer.") from exc
        if body.get("errors"):
            raise BufferError("; ".join(e.get("message", "erro") for e in body["errors"]))
        return body["data"]


def _parse_post(raw: dict) -> Post:
    due_at = None
    due_at_raw = raw.get("dueAt")
    if due_at_raw:
        try:
            due_at = time.to_local_naive(datetime.fromisoformat(due_at_raw.replace("Z", "+00:00")))
        except ValueError:
            due_at = None
    error = raw.get("error")
    thumbs = [a.get("thumbnail") for a in raw.get("assets") or [] if isinstance(a, dict) and a.get("thumbnail")]
    thumb = thumbs[0] if thumbs else None
    if thumb and thumb.startswith("http://") and not thumb.startswith(("http://localhost", "http://127.0.0.1")):
        thumb = "https://" + thumb[len("http://"):]

    urls = []
    has_video = False
    for a in raw.get("assets") or []:
        if isinstance(a, dict):
            if a.get("__typename") == "VideoAsset":
                has_video = True
            u = a.get("source") or a.get("thumbnail")
            if u:
                if u.startswith("http://") and not u.startswith(("http://localhost", "http://127.0.0.1")):
                    u = "https://" + u[len("http://"):]
                urls.append(u)
                if is_video_url(u):
                    has_video = True

    if not has_video and thumb and is_video_url(thumb):
        has_video = True

    return Post(
        id=raw["id"],
        text=raw.get("text") or "",
        status=raw.get("status") or "",
        due_at=due_at,
        channel_id=raw.get("channelId") or "",
        service=raw.get("channelService") or "",
        error=error.get("message") if isinstance(error, dict) else None,
        thumbnail=thumb,
        image_urls=tuple(urls),
        due_at_raw=due_at_raw,
        is_video=has_video,
    )
