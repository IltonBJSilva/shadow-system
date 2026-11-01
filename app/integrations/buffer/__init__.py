"""Integração direta com o Buffer da sua conta pessoal.

Funções de alto nível usadas pelas telas e pelo dashboard. O cliente HTTP fica em client.py,
as regras de montagem dos posts em posting.py e o token em token_store.py.
"""
import logging
from dataclasses import dataclass, replace
from datetime import date, datetime

from ..registry import IntegrationStatus
from . import posting, storage, token_store
from .client import BufferClient, BufferError, Channel, Post
from .posting import PostValidationError
from .storage import StorageError

log = logging.getLogger(__name__)

# Testes trocam isto por um httpx.MockTransport.
_transport = None


@dataclass(frozen=True)
class Upload:
    filename: str
    content: bytes
    content_type: str


@dataclass(frozen=True)
class ChannelResult:
    channel: str
    service: str
    ok: bool
    message: str


# ---------- conexão ----------

def is_configured() -> bool:
    return bool(token_store.api_key())


def get_client(api_key: str | None = None) -> BufferClient:
    return BufferClient(api_key or token_store.api_key(), transport=_transport)


def organization_id(client: BufferClient) -> str:
    org = token_store.organization_id()
    if not org:
        org = client.organization_id()
        token_store.remember_organization(org)
    return org


def save_token(api_key: str, created_at: date) -> int:
    """Confere o token no Buffer antes de salvar. Retorna quantos canais a conta tem."""
    api_key = api_key.strip()
    if len(api_key) < 20:
        raise BufferError("Esse token parece incompleto. Copie o token inteiro do Buffer.")
    client = get_client(api_key)
    org = client.organization_id()
    channel_count = len(client.channels(org))
    token_store.save(api_key, created_at, org)
    log.info("Token do Buffer atualizado (%d canais).", channel_count)
    return channel_count


def status() -> IntegrationStatus:
    token = token_store.status()
    base = dict(
        key="buffer",
        name="Buffer",
        description="Sua conta pessoal do Buffer: canais, posts agendados e novos agendamentos.",
        url="/integrations/buffer/",
    )
    if not token.configured:
        return IntegrationStatus(**base, state="not_configured", detail="Cadastre o token em Integrações > Buffer.")
    if token.level == "expired":
        return IntegrationStatus(**base, state="error", detail="Token vencido. Gere um novo no Buffer.")
    detail = f"Token {token.masked}"
    if token.days_left is not None:
        detail += f" · vence em {token.days_left} dia(s)"
    return IntegrationStatus(**base, state="connected" if token.level != "warning" else "configured", detail=detail)


# ---------- leitura ----------

def channels() -> list[Channel]:
    client = get_client()
    return client.channels(organization_id(client))


def posts(statuses: list[str] | None) -> list[Post]:
    """Posts com o nome do canal preenchido, ordenados por data."""
    client = get_client()
    org = organization_id(client)
    names = {ch.id: ch.name for ch in client.channels(org)}
    result = [
        replace(p, channel_name=names.get(p.channel_id, p.service))
        for p in client.posts(org, statuses)
    ]
    return sorted(result, key=lambda p: p.due_at or datetime.max)


def scheduled_posts_safe(limit: int = 5) -> tuple[list[Post], str | None]:
    """Para o dashboard: nunca quebra a página. Devolve (posts, erro)."""
    if not is_configured():
        return [], None
    try:
        return posts(["scheduled"])[:limit], None
    except BufferError as exc:
        return [], str(exc)


# ---------- agendamento ----------

def schedule(*, text: str, overrides: dict[str, str], channel_ids: list[str], mode: str,
             due_local: datetime | None, image_urls: list[str], uploads: list[Upload]) -> list[ChannelResult]:
    """Cria o post em cada canal escolhido. Um canal falhar não impede os outros.

    overrides: texto específico por rede (ex.: {"linkedin": "...", "instagram": "..."}).
    Validações que valem para todos são feitas antes de qualquer envio.
    """
    if not channel_ids:
        raise PostValidationError("Escolha pelo menos um canal.")
    due = posting.due_at_utc(due_local) if mode == "customScheduled" and due_local else None
    if mode == "customScheduled" and not due:
        raise PostValidationError("Escolha a data e a hora do agendamento.")
    if len(image_urls) + len(uploads) > posting.MAX_IMAGES:
        raise PostValidationError(f"No máximo {posting.MAX_IMAGES} imagens por post.")

    client = get_client()
    available = {ch.id: ch for ch in client.channels(organization_id(client))}
    targets = []
    for channel_id in channel_ids:
        channel = available.get(channel_id)
        if channel is None or not channel.usable:
            raise PostValidationError("Um dos canais escolhidos não está disponível. Recarregue a página.")
        targets.append(channel)

    # Valida o texto de cada canal antes de subir imagens (evita upload à toa).
    for channel in targets:
        posting.build_post_input(
            channel_id=channel.id, service=channel.service, text=overrides.get(channel.service) or text,
            # uploads ainda não têm link; contam como imagem só para a validação.
            image_urls=image_urls + ["https://upload.pendente"] * len(uploads), mode=mode, due_at=due,
        )

    urls = list(image_urls)
    for item in uploads:
        urls.append(storage.upload(item.filename, item.content, item.content_type))

    results: list[ChannelResult] = []
    for channel in targets:
        body = posting.build_post_input(
            channel_id=channel.id, service=channel.service, text=overrides.get(channel.service) or text,
            image_urls=urls, mode=mode, due_at=due,
        )
        try:
            post = client.create_post(body)
            when = post.get("dueAt") or "fila"
            results.append(ChannelResult(channel.name, channel.service, True, f"{post.get('status', 'ok')} ({when})"))
        except BufferError as exc:
            results.append(ChannelResult(channel.name, channel.service, False, str(exc)))
    return results


def storage_enabled() -> bool:
    return storage.is_configured()


__all__ = [
    "BufferClient", "BufferError", "Channel", "ChannelResult", "Post", "PostValidationError",
    "StorageError", "Upload", "channels", "get_client", "is_configured", "posts", "save_token",
    "schedule", "scheduled_posts_safe", "status", "storage_enabled",
]
