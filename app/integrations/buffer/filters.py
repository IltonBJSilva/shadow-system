"""Modelagem unificada, filtros detalhados, ordenação e agrupamento de postagens.

Unifica publicações da Fila do Sistema, do Buffer (Agendados, Rascunhos, Enviados,
Com erro) e do YouTube (YouTube Data API v3) para permitir buscas, filtros por rede,
origem, formato de mídia, status, período de datas e comparação lado a lado.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, time as dtime
from urllib.parse import unquote, urlparse

from app.core import time
from app.core.models import BufferQueuePost
from app.integrations.youtube.client import YouTubeVideo

from .client import Post

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_SHORTS_TAG = re.compile(r"#shorts?\b", re.IGNORECASE)
_BUFFER_BACKFILL = re.compile(r"^[0-9a-f]{24}_(photo|thumbnail)", re.IGNORECASE)

STATUS_LABELS = {
    "pending": "Pendente na Fila",
    "dispatched": "Despachado ao Buffer",
    "scheduled": "Agendado",
    "sent": "Publicado / Enviado",
    "draft": "Rascunho",
    "error": "Com erro",
}

ORIGIN_LABELS = {
    "queue": "Fila do Sistema",
    "buffer": "Buffer",
    "youtube": "YouTube Direto",
}

MEDIA_LABELS = {
    "video": "Vídeo",
    "image": "Imagem",
    "text": "Texto",
}


@dataclass(frozen=True)
class FilterParams:
    services: tuple[str, ...] = ()
    source: str = ""
    media_type: str = ""
    post_status: str = ""
    date_from: date | None = None
    date_to: date | None = None
    q: str = ""
    sort: str = "date_asc"
    view: str = "list"

    @property
    def has_active_filters(self) -> bool:
        return bool(
            self.services
            or self.source
            or self.media_type
            or self.post_status
            or self.date_from
            or self.date_to
            or self.q
        )

    @property
    def has_advanced_filters(self) -> bool:
        return bool(
            self.source
            or self.media_type
            or self.post_status
            or self.date_from
            or self.date_to
            or (self.sort and self.sort != "date_asc")
        )


@dataclass(frozen=True)
class PostItem:
    uid: str
    origin: str  # "queue" | "buffer" | "youtube"
    origin_label: str
    id: str
    service: str
    channel_id: str
    channel_name: str
    text: str
    title: str
    status: str
    status_label: str
    due_at: datetime | None
    media_type: str  # "video" | "image" | "text"
    video_url: str | None
    poster_url: str | None
    thumbnail: str | None
    media_filename: str | None
    error_message: str | None
    external_url: str | None
    group_key: str
    group_title: str
    can_edit: bool = False
    can_share_now: bool = False
    can_dispatch: bool = False
    can_delete: bool = False
    is_video: bool = False

    @property
    def buffer_channel_url(self) -> str:
        if self.channel_id:
            return f"https://publish.buffer.com/channels/{self.channel_id}"
        return "https://publish.buffer.com/"


@dataclass(frozen=True)
class PostGroup:
    key: str
    title: str
    media_type: str
    video_url: str | None
    poster_url: str | None
    thumbnail: str | None
    media_filename: str | None
    items: tuple[PostItem, ...]
    services: tuple[str, ...]
    earliest_due: datetime | None


def normalize_text(value: str) -> str:
    """Normaliza texto para busca e agrupamento (sem acentos, minúsculas)."""
    ascii_text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower().strip()


def _slug_words(value: str) -> str:
    cleaned = _SHORTS_TAG.sub(" ", value or "")
    norm = normalize_text(cleaned)
    return _NON_ALNUM.sub(" ", norm).strip()


def _extract_filename(url: str | None) -> str | None:
    if not url:
        return None
    try:
        path = unquote(urlparse(url).path)
        name = path.rsplit("/", 1)[-1].strip()
        if not name or len(name) > 120:
            return None
        return name
    except Exception:
        return None


def _compute_group(
    *,
    uid: str,
    title: str,
    text: str,
    media_filename: str | None,
) -> tuple[str, str]:
    if media_filename and not _BUFFER_BACKFILL.match(media_filename):
        stem = media_filename.rsplit(".", 1)[0]
        key = _slug_words(stem)
        if key:
            pretty = stem.replace("-", " ").replace("_", " ").strip()
            return key, pretty[:90]

    candidate = title or (text.splitlines()[0] if text else "")
    key = _slug_words(candidate)[:64].strip()
    if key:
        pretty = _SHORTS_TAG.sub("", candidate).strip()
        return key, (pretty[:90] or candidate[:90])
    return uid, "Publicação sem título"


def _parse_queue_due(post: BufferQueuePost) -> datetime | None:
    if not post.target_date:
        return None
    t_str = (post.target_time or "18:30").strip()
    try:
        h, m = [int(x) for x in t_str.split(":")[:2]]
        return datetime.combine(post.target_date, dtime(h, m))
    except Exception:
        return datetime.combine(post.target_date, dtime(18, 30))


def from_queue_post(post: BufferQueuePost) -> PostItem:
    v_url = post.video_url
    p_url = post.poster_url
    thumb = post.thumbnail
    m_type = "video" if post.is_video else ("image" if thumb else "text")
    media_url = v_url or thumb
    filename = _extract_filename(media_url)
    has_err = bool(post.error_message or post.status == "error")
    eff_status = "error" if has_err and post.status != "dispatched" else post.status
    st_label = STATUS_LABELS.get(eff_status, eff_status)
    headline = (post.text or "").strip().splitlines()[0] if post.text else (filename or "Sem texto")
    g_key, g_title = _compute_group(uid=f"queue:{post.id}", title="", text=post.text or "", media_filename=filename)

    return PostItem(
        uid=f"queue:{post.id}",
        origin="queue",
        origin_label=ORIGIN_LABELS["queue"],
        id=str(post.id),
        service=post.service,
        channel_id=post.channel_id,
        channel_name=post.channel_name,
        text=post.text or "",
        title=headline[:120],
        status=eff_status,
        status_label=st_label,
        due_at=_parse_queue_due(post),
        media_type=m_type,
        video_url=v_url,
        poster_url=p_url,
        thumbnail=thumb,
        media_filename=filename,
        error_message=post.error_message,
        external_url=None,
        group_key=g_key,
        group_title=g_title,
        can_edit=post.status in ("pending", "error"),
        can_share_now=post.status in ("pending", "error"),
        can_dispatch=post.status in ("pending", "error"),
        can_delete=True,
        is_video=post.is_video,
    )


def from_buffer_post(post: Post, default_status: str = "scheduled") -> PostItem:
    st = (post.status or default_status).lower()
    if post.error and st != "sent":
        st = "error"
    v_url = post.video_url
    p_url = post.poster_url
    thumb = post.thumbnail
    m_type = "video" if post.is_video else ("image" if (thumb or post.image_urls) else "text")
    media_url = v_url or (post.image_urls[0] if post.image_urls else thumb)
    filename = _extract_filename(media_url)
    headline = (post.text or "").strip().splitlines()[0] if post.text else (filename or "Sem texto")
    g_key, g_title = _compute_group(uid=f"buffer:{post.id}", title="", text=post.text or "", media_filename=filename)

    return PostItem(
        uid=f"buffer:{post.id}",
        origin="buffer",
        origin_label=ORIGIN_LABELS["buffer"],
        id=post.id,
        service=post.service,
        channel_id=post.channel_id,
        channel_name=post.channel_name or post.service,
        text=post.text or "",
        title=headline[:120],
        status=st,
        status_label=STATUS_LABELS.get(st, st),
        due_at=post.due_at,
        media_type=m_type,
        video_url=v_url,
        poster_url=p_url,
        thumbnail=thumb,
        media_filename=filename,
        error_message=post.error,
        external_url=f"https://publish.buffer.com/channels/{post.channel_id}" if post.channel_id else None,
        group_key=g_key,
        group_title=g_title,
        can_edit=st in ("scheduled", "draft", "error"),
        can_share_now=st in ("scheduled", "draft", "error"),
        can_dispatch=False,
        can_delete=st in ("scheduled", "draft", "error"),
        is_video=post.is_video,
    )


def from_youtube_video(vid: YouTubeVideo, channel_name: str = "YouTube") -> PostItem:
    raw_dt = vid.publish_at if vid.publish_at else vid.published_at
    due_local = None
    if raw_dt:
        due_local = time.to_local_naive(raw_dt) if raw_dt.tzinfo else raw_dt

    st = "scheduled" if vid.is_scheduled else "sent"
    st_label = "Agendado no YouTube" if vid.is_scheduled else "Publicado no YouTube"
    full_text = f"{vid.title}\n\n{vid.description}".strip() if vid.description else vid.title
    g_key, g_title = _compute_group(uid=f"youtube:{vid.id}", title=vid.title, text=full_text, media_filename=None)

    return PostItem(
        uid=f"youtube:{vid.id}",
        origin="youtube",
        origin_label=ORIGIN_LABELS["youtube"],
        id=vid.id,
        service="youtube",
        channel_id="youtube",
        channel_name=channel_name or "YouTube",
        text=full_text,
        title=vid.title,
        status=st,
        status_label=st_label,
        due_at=due_local,
        media_type="video",
        video_url=None,
        poster_url=vid.thumbnail_url,
        thumbnail=vid.thumbnail_url,
        media_filename="YouTube Short" if vid.is_short else "YouTube Vídeo",
        error_message=None,
        external_url=vid.url,
        group_key=g_key,
        group_title=g_title,
        is_video=True,
    )


def parse_filter_params(args) -> FilterParams:
    raw_services = [s.strip().lower() for s in args.getlist("service") if s and s.strip()]
    services = tuple(dict.fromkeys(raw_services))
    source = (args.get("source") or "").strip().lower()
    if source not in ("", "queue", "buffer", "youtube"):
        source = ""
    media_type = (args.get("media_type") or "").strip().lower()
    if media_type not in ("", "video", "image", "text"):
        media_type = ""
    post_status = (args.get("post_status") or "").strip().lower()
    if post_status not in ("", *STATUS_LABELS.keys()):
        post_status = ""

    date_from = _parse_date(args.get("date_from"))
    date_to = _parse_date(args.get("date_to"))
    q = (args.get("q") or "").strip()
    sort = (args.get("sort") or "date_asc").strip()
    if sort not in ("date_asc", "date_desc", "service", "title"):
        sort = "date_asc"
    view = (args.get("view") or "list").strip()
    if view not in ("list", "grouped", "grid"):
        view = "list"

    return FilterParams(
        services=services,
        source=source,
        media_type=media_type,
        post_status=post_status,
        date_from=date_from,
        date_to=date_to,
        q=q,
        sort=sort,
        view=view,
    )


def _parse_date(raw: str | None) -> date | None:
    val = (raw or "").strip()
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except ValueError:
        return None


def apply_filters(items: list[PostItem], params: FilterParams) -> list[PostItem]:
    q_norm = normalize_text(params.q)
    out: list[PostItem] = []
    for item in items:
        if params.services and item.service.lower() not in params.services:
            continue
        if params.source and item.origin != params.source:
            continue
        if params.media_type and item.media_type != params.media_type:
            continue
        if params.post_status and item.status != params.post_status:
            continue
        if params.date_from:
            if not item.due_at or item.due_at.date() < params.date_from:
                continue
        if params.date_to:
            if not item.due_at or item.due_at.date() > params.date_to:
                continue
        if q_norm:
            haystack = normalize_text(
                " ".join(
                    filter(
                        None,
                        [
                            item.title,
                            item.text,
                            item.channel_name,
                            item.service,
                            item.origin_label,
                            item.status_label,
                            item.media_filename,
                            item.group_title,
                            item.group_key,
                            item.error_message,
                        ],
                    )
                )
            )
            if q_norm not in haystack:
                continue
        out.append(item)
    return out


def sort_items(items: list[PostItem], sort_mode: str) -> list[PostItem]:
    if sort_mode == "date_desc":
        return sorted(items, key=lambda i: i.due_at or datetime.min, reverse=True)
    if sort_mode == "service":
        return sorted(items, key=lambda i: (i.service, i.due_at or datetime.max))
    if sort_mode == "title":
        return sorted(items, key=lambda i: (normalize_text(i.group_title), i.service))
    return sorted(items, key=lambda i: i.due_at or datetime.max)


def group_posts(items: list[PostItem]) -> list[PostGroup]:
    """Agrupa postagens equivalentes entre redes (ex.: Instagram, LinkedIn, TikTok, YouTube)."""
    buckets: dict[str, list[PostItem]] = {}
    for item in items:
        buckets.setdefault(item.group_key, []).append(item)

    groups: list[PostGroup] = []
    for key, grp_items in buckets.items():
        # Prefere título do YouTube se existir, senão usa o maior título legível
        yt_items = [i for i in grp_items if i.origin == "youtube"]
        best_title = yt_items[0].group_title if yt_items else grp_items[0].group_title

        v_url = next((i.video_url for i in grp_items if i.video_url), None)
        p_url = next((i.poster_url for i in grp_items if i.poster_url), None)
        thumb = next((i.thumbnail for i in grp_items if i.thumbnail), None)
        m_file = next((i.media_filename for i in grp_items if i.media_filename and i.origin != "youtube"), None) or grp_items[0].media_filename
        m_type = "video" if any(i.media_type == "video" for i in grp_items) else (
            "image" if any(i.media_type == "image" for i in grp_items) else "text"
        )
        dates = [i.due_at for i in grp_items if i.due_at]
        earliest = min(dates) if dates else None
        services = tuple(dict.fromkeys(i.service for i in grp_items))

        # Ordena itens dentro do grupo na ordem padrão de leitura das redes
        order = {"youtube": 0, "linkedin": 1, "instagram": 2, "tiktok": 3}
        sorted_grp = tuple(sorted(grp_items, key=lambda i: (order.get(i.service, 9), i.due_at or datetime.max)))

        groups.append(
            PostGroup(
                key=key,
                title=best_title,
                media_type=m_type,
                video_url=v_url,
                poster_url=p_url,
                thumbnail=thumb,
                media_filename=m_file,
                items=sorted_grp,
                services=services,
                earliest_due=earliest,
            )
        )

    return sorted(groups, key=lambda g: g.earliest_due or datetime.max)


def count_by_service(items: list[PostItem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item.service] = counts.get(item.service, 0) + 1
    return counts

