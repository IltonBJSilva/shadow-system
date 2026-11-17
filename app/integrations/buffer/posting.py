"""Montagem dos posts no formato que o Buffer exige, por rede. Funções puras.

Regras herdadas do que já foi validado na API real:
- Instagram: metadata.instagram {type: "post", shouldShareToFeed: true}; várias imagens = carrossel;
  no máximo 5 hashtags (#PraTodosVerem nunca é cortada); precisa de pelo menos uma imagem.
- Facebook: metadata.facebook {type: "post"}.
- dueAt em UTC no formato 2026-11-02T09:00:00.000Z.
"""
import re
from datetime import datetime, timezone

from app.core import time

MODES = {
    "customScheduled": "Data e hora definidas",
    "addToQueue": "Próximo horário da fila do Buffer",
    "shareNow": "Publicar agora",
}
MAX_IMAGES = 10
MAX_TEXT = {"instagram": 2200, "linkedin": 3000, "twitter": 280, "threads": 500, "bluesky": 300, "tiktok": 2200}
INSTAGRAM_MAX_HASHTAGS = 5
KEEP_HASHTAG = "#PraTodosVerem"
_HASHTAG = re.compile(r"#\w+")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".m4v")


def is_video_url(url: str) -> bool:
    """Verifica se a URL aponta para um arquivo de vídeo suportado."""
    clean_url = url.split("?")[0].lower()
    return any(clean_url.endswith(ext) for ext in VIDEO_EXTENSIONS)


class PostValidationError(ValueError):
    """Post inválido antes de chegar ao Buffer."""


def due_at_utc(local: datetime, now: datetime | None = None) -> str:
    """Converte o horário local (sem fuso) para o formato UTC do Buffer. Precisa estar no futuro."""
    now = now or time.now()
    if local <= now:
        raise PostValidationError("A data e a hora precisam estar no futuro.")
    return time.to_aware(local).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def build_post_input(*, channel_id: str, service: str, text: str,
                     image_urls: list[str] | None = None,
                     media_urls: list[str] | None = None,
                     mode: str, due_at: str | None = None) -> dict:
    if mode not in MODES:
        raise PostValidationError("Modo de publicação inválido.")
    if mode == "customScheduled" and not due_at:
        raise PostValidationError("Escolha a data e a hora do agendamento.")

    urls = list(media_urls if media_urls is not None else (image_urls or []))

    if service == "instagram":
        text = limit_instagram_hashtags(text)
        if not urls:
            raise PostValidationError("O Instagram precisa de pelo menos uma mídia (imagem ou vídeo).")
    if not text.strip() and not urls:
        raise PostValidationError("Escreva um texto ou adicione uma mídia (imagem ou vídeo).")
    limit = MAX_TEXT.get(service)
    if limit and len(text) > limit:
        raise PostValidationError(f"O texto para {service} passou de {limit} caracteres.")
    if len(urls) > MAX_IMAGES:
        raise PostValidationError(f"No máximo {MAX_IMAGES} mídias por post.")

    has_video = any(is_video_url(u) for u in urls)
    assets = []
    for u in urls:
        if is_video_url(u):
            assets.append({"video": {"url": u}})
        else:
            assets.append({"image": {"url": u}})

    post: dict = {
        "channelId": channel_id,
        "text": text,
        "schedulingType": "automatic",
        "mode": mode,
        "needsApproval": False,
        "assets": assets,
    }
    if mode == "customScheduled":
        post["dueAt"] = due_at

    metadata: dict = {}
    if service == "instagram":
        metadata["instagram"] = {
            "type": "reel" if has_video else "post",
            "shouldShareToFeed": True,
        }
    elif service == "facebook":
        metadata["facebook"] = {"type": "reel" if has_video else "post"}
    elif service == "tiktok":
        metadata["tiktok"] = {"title": text[:100]}

    if metadata:
        post["metadata"] = metadata

    return post


def limit_instagram_hashtags(text: str, limit: int = INSTAGRAM_MAX_HASHTAGS) -> str:
    """Mantém no máximo `limit` hashtags: #PraTodosVerem sempre, depois as primeiras da legenda."""
    tags = _HASHTAG.findall(text)
    if len(tags) <= limit:
        return text
    keep = {KEEP_HASHTAG.lower()} if any(t.lower() == KEEP_HASHTAG.lower() for t in tags) else set()
    for tag in tags:
        if len(keep) >= limit:
            break
        keep.add(tag.lower())
    out = _HASHTAG.sub(lambda m: m.group(0) if m.group(0).lower() in keep else "", text)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return "\n".join(line.rstrip() for line in out.splitlines()).strip()


def extract_hashtags(text: str) -> list[str]:
    """Retorna lista de hashtags únicas encontradas no texto, preservando a ordem."""
    tags = _HASHTAG.findall(text or "")
    return list(dict.fromkeys(tags))


def adapt_text_for_tiktok(
    text: str,
    *,
    mode: str = "title_only",
    title: str = "",
    max_chars: int = 150,
) -> str:
    """Adapta textos longos (ex.: de LinkedIn ou Instagram) para o formato do TikTok.

    modos:
    - 'title_only': descarta todo o comentário/corpo longo e mantém apenas o título (ou 1ª linha) + hashtags.
    - 'smart': gancho/primeira frase limpa de URLs + hashtags, até `max_chars`.
    - 'original': retorna o texto original sem alterações.
    """
    raw_text = (text or "").strip()
    if not raw_text and not title:
        return ""
    if mode == "original":
        return raw_text

    tags = extract_hashtags(raw_text)
    tag_str = " ".join(tags[:4]) if tags else ""

    if mode == "title_only":
        hook = (title or "").strip()
        if not hook and raw_text:
            hook = raw_text.splitlines()[0].strip()
        hook = _HASHTAG.sub("", hook).strip()
        hook = re.sub(r"https?://\S+", "", hook).strip()
        hook = re.sub(r"[ \t]+", " ", hook).strip()
        if not hook and raw_text:
            hook = raw_text[:80].strip()
        if tag_str:
            return f"{hook}\n\n{tag_str}".strip()
        return hook

    # mode == "smart": limpa URLs e reduz tamanho preservando gancho e hashtags
    clean = re.sub(r"https?://\S+", "", raw_text)
    clean = _HASHTAG.sub("", clean)
    clean = re.sub(r"[ \t]+", " ", clean).strip()

    first_part = (title or (clean.splitlines()[0] if clean else "")).strip()
    budget = max_chars - (len(tag_str) + 2 if tag_str else 0)
    if budget <= 10:
        budget = max_chars

    if len(first_part) > budget:
        first_part = first_part[: budget - 1].rstrip() + "…"

    if tag_str:
        return f"{first_part}\n\n{tag_str}".strip()
    return first_part


def parse_image_urls(raw: str) -> list[str]:
    """Uma URL por linha. Só http(s): o Buffer busca a imagem por um link público."""
    urls = [line.strip() for line in raw.splitlines() if line.strip()]
    for url in urls:
        if not url.startswith(("https://", "http://")):
            raise PostValidationError(f"Link de imagem inválido: {url[:60]}")
    return urls
