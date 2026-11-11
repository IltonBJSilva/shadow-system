"""Integração com o YouTube (YouTube Data API v3).

Permite conectar canal via Google OAuth, visualizar estatísticas,
enviar e agendar YouTube Shorts / Vídeos sem consumir vagas no Buffer.
"""
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from ..google_calendar import oauth
from ..google_calendar.oauth import GoogleAuthError
from ..registry import IntegrationStatus
from .client import ChannelInfo, YouTubeClient, YouTubeError, YouTubeVideo, build_service

_service_factory = None


def is_authorized() -> bool:
    """Indica se a conta Google conectada possui permissão de upload no YouTube."""
    return oauth.is_connected() and oauth.has_scope(oauth.YOUTUBE_UPLOAD_SCOPE)


def get_client() -> YouTubeClient:
    """Retorna o cliente autenticado do YouTube."""
    if not is_authorized():
        raise GoogleAuthError("YouTube não autorizado. Conecte sua conta do YouTube.")
    factory = _service_factory or (lambda: build_service(oauth.load_credentials()))
    return YouTubeClient(factory())


def status() -> IntegrationStatus:
    base = dict(
        key="youtube",
        name="YouTube",
        description="Publicação e agendamento nativo de vídeos e Shorts via YouTube Data API v3.",
        url="/integrations/youtube/",
    )
    if not oauth.is_configured():
        return IntegrationStatus(
            **base,
            state="not_configured",
            detail="Usa o mesmo cliente OAuth do Google (GOOGLE_CLIENT_SECRETS_FILE).",
        )
    if not is_authorized():
        return IntegrationStatus(
            **base,
            state="configured",
            detail="Falta autorizar o YouTube.",
        )
    return IntegrationStatus(
        **base,
        state="connected",
        detail="Canal do YouTube conectado.",
    )


def channel_info() -> ChannelInfo | None:
    if not is_authorized():
        return None
    return get_client().channel_info()


def recent_videos(max_results: int = 15) -> list[YouTubeVideo]:
    if not is_authorized():
        return []
    return get_client().recent_videos(max_results)


def upload_video(
    media_source: str | Path | bytes | BinaryIO,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "28",
    privacy_status: str = "public",
    publish_at_utc: datetime | None = None,
    is_short: bool = True,
) -> YouTubeVideo:
    client = get_client()
    return client.upload_video(
        media_source=media_source,
        title=title,
        description=description,
        tags=tags,
        category_id=category_id,
        privacy_status=privacy_status,
        publish_at_utc=publish_at_utc,
        is_short=is_short,
    )


__all__ = [
    "ChannelInfo",
    "YouTubeClient",
    "YouTubeError",
    "YouTubeVideo",
    "channel_info",
    "get_client",
    "is_authorized",
    "recent_videos",
    "status",
    "upload_video",
]
