"""Cliente da YouTube Data API v3 pela biblioteca oficial google-api-python-client.

Permite listar canal, listar vídeos enviados e fazer upload de vídeos/shorts
(com publicação imediata ou agendada para data/hora futura).
"""
import io
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

from app.integrations.network import connection_message

API_NAME = "youtube"
API_VERSION = "v3"


class YouTubeError(Exception):
    """Falha de comunicação com a YouTube API ou validação de vídeo."""


@dataclass(frozen=True)
class ChannelInfo:
    id: str
    title: str
    description: str
    custom_url: str | None
    avatar_url: str | None
    video_count: int
    subscriber_count: int


@dataclass(frozen=True)
class YouTubeVideo:
    id: str
    title: str
    description: str
    thumbnail_url: str | None
    published_at: datetime | None
    privacy_status: str
    url: str
    is_short: bool = False


def build_service(credentials):
    """Cria o cliente da biblioteca oficial com o access token renovável."""
    return build(API_NAME, API_VERSION, credentials=credentials, cache_discovery=False)


class YouTubeClient:
    def __init__(self, service):
        self._service = service

    def channel_info(self) -> ChannelInfo | None:
        """Obtém detalhes do canal autenticado."""
        try:
            res = self._service.channels().list(part="snippet,statistics", mine=True).execute()
        except HttpError as exc:
            raise YouTubeError(f"YouTube: {exc.reason or exc}") from exc

        items = res.get("items") or []
        if not items:
            return None

        ch = items[0]
        snippet = ch.get("snippet", {})
        stats = ch.get("statistics", {})
        thumbs = snippet.get("thumbnails", {})
        avatar = thumbs.get("default", {}).get("url") or thumbs.get("medium", {}).get("url")

        return ChannelInfo(
            id=ch.get("id", ""),
            title=snippet.get("title", "Canal do YouTube"),
            description=snippet.get("description", ""),
            custom_url=snippet.get("customUrl"),
            avatar_url=avatar,
            video_count=int(stats.get("videoCount", 0)),
            subscriber_count=int(stats.get("subscriberCount", 0)),
        )

    def recent_videos(self, max_results: int = 15) -> list[YouTubeVideo]:
        """Lista os vídeos mais recentes do canal via playlist de uploads (economiza cota: 1 unidade vs 100 de search)."""
        try:
            # 1. Buscar o ID da playlist de uploads do canal
            ch_res = self._service.channels().list(part="contentDetails", mine=True).execute()
            items = ch_res.get("items") or []
            if not items:
                return []
            uploads_playlist = items[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
            if not uploads_playlist:
                return []

            # 2. Buscar itens da playlist de uploads
            pl_res = self._service.playlistItems().list(
                part="snippet,status",
                playlistId=uploads_playlist,
                maxResults=max_results,
            ).execute()
        except HttpError as exc:
            raise YouTubeError(f"YouTube: {exc.reason or exc}") from exc

        videos = []
        for it in pl_res.get("items") or []:
            snip = it.get("snippet", {})
            st = it.get("status", {})
            vid_id = snip.get("resourceId", {}).get("videoId")
            if not vid_id:
                continue

            thumbs = snip.get("thumbnails", {})
            thumb_url = thumbs.get("medium", {}).get("url") or thumbs.get("default", {}).get("url")
            raw_pub = snip.get("publishedAt")
            pub_date = None
            if raw_pub:
                try:
                    pub_date = datetime.fromisoformat(raw_pub.replace("Z", "+00:00"))
                except ValueError:
                    pub_date = None

            title = snip.get("title", "")
            videos.append(
                YouTubeVideo(
                    id=vid_id,
                    title=title,
                    description=snip.get("description", ""),
                    thumbnail_url=thumb_url,
                    published_at=pub_date,
                    privacy_status=st.get("privacyStatus", "public"),
                    url=f"https://youtu.be/{vid_id}",
                    is_short="#shorts" in title.lower() or "#short" in title.lower(),
                )
            )
        return videos

    def upload_video(
        self,
        media_source: str | Path | bytes | BinaryIO,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        category_id: str = "28",  # 28 = Ciência e Tecnologia
        privacy_status: str = "public",
        publish_at_utc: datetime | None = None,
        is_short: bool = True,
    ) -> YouTubeVideo:
        """Envia um vídeo para o YouTube.
        
        Se publish_at_utc for fornecido:
          - A privacyStatus é automaticamente configurada como 'private' (obrigatório da API do YouTube para agendados).
          - O YouTube publicará automaticamente o vídeo na data e hora informada.
        """
        title = (title or "").strip()
        if not title:
            raise YouTubeError("O título do vídeo é obrigatório.")

        # Garantir #Shorts na descrição ou título se for short
        clean_tags = [t.strip().lstrip("#") for t in (tags or []) if t.strip()]
        if is_short:
            if "#Shorts" not in title and "#shorts" not in title:
                if len(title) <= 90:
                    title = f"{title} #Shorts"
                elif "#Shorts" not in description:
                    description = f"{description}\n\n#Shorts".strip()
            if "Shorts" not in clean_tags:
                clean_tags.append("Shorts")

        snippet_body: dict[str, Any] = {
            "title": title[:100],
            "description": description[:5000],
            "tags": clean_tags,
            "categoryId": category_id,
        }

        status_body: dict[str, Any] = {}
        if publish_at_utc:
            status_body["privacyStatus"] = "private"
            status_body["publishAt"] = publish_at_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            status_body["privacyStatus"] = privacy_status if privacy_status in ("public", "unlisted", "private") else "public"

        # Preparar media_body
        if isinstance(media_source, (str, Path)):
            p = Path(media_source)
            if not p.is_file():
                raise YouTubeError(f"Arquivo de vídeo não encontrado: {p}")
            media = MediaFileUpload(str(p), mimetype="video/mp4", resumable=True, chunksize=10 * 1024 * 1024)
        elif isinstance(media_source, bytes):
            media = MediaIoBaseUpload(io.BytesIO(media_source), mimetype="video/mp4", resumable=True)
        else:
            media = MediaIoBaseUpload(media_source, mimetype="video/mp4", resumable=True)

        try:
            req = self._service.videos().insert(
                part="snippet,status",
                body={"snippet": snippet_body, "status": status_body},
                media_body=media,
            )
            res = req.execute()
        except HttpError as exc:
            raise YouTubeError(f"YouTube recusou o upload: {exc.reason or exc}") from exc

        vid_id = res.get("id")
        if not vid_id:
            raise YouTubeError("O YouTube não retornou o ID do vídeo criado.")

        snip = res.get("snippet", {})
        thumbs = snip.get("thumbnails", {})
        thumb = thumbs.get("medium", {}).get("url") or thumbs.get("default", {}).get("url")

        return YouTubeVideo(
            id=vid_id,
            title=snip.get("title", title),
            description=snip.get("description", description),
            thumbnail_url=thumb,
            published_at=datetime.utcnow() if not publish_at_utc else publish_at_utc,
            privacy_status=status_body.get("privacyStatus", "public"),
            url=f"https://youtu.be/{vid_id}",
            is_short=is_short,
        )

    def create_playlist(
        self,
        title: str,
        description: str = "",
        privacy_status: str = "public",
    ) -> str:
        """Cria uma nova playlist no canal do YouTube e retorna o ID dela."""
        try:
            res = self._service.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                    },
                    "status": {
                        "privacyStatus": privacy_status,
                    },
                },
            ).execute()
        except HttpError as exc:
            raise YouTubeError(f"Falha ao criar playlist no YouTube: {exc.reason or exc}") from exc

        pl_id = res.get("id")
        if not pl_id:
            raise YouTubeError("O YouTube não retornou o ID da playlist criada.")
        return pl_id

    def add_video_to_playlist(self, playlist_id: str, video_id: str, position: int | None = None) -> str:
        """Adiciona um vídeo existente à playlist especificada."""
        snippet = {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id,
            },
        }
        if position is not None:
            snippet["position"] = position

        try:
            res = self._service.playlistItems().insert(
                part="snippet",
                body={"snippet": snippet},
            ).execute()
        except HttpError as exc:
            raise YouTubeError(f"Falha ao adicionar vídeo {video_id} à playlist: {exc.reason or exc}") from exc

        return res.get("id", "")

