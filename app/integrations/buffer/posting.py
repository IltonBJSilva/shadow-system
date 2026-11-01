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
MAX_TEXT = {"instagram": 2200, "linkedin": 3000, "twitter": 280, "threads": 500, "bluesky": 300}
INSTAGRAM_MAX_HASHTAGS = 5
KEEP_HASHTAG = "#PraTodosVerem"
_HASHTAG = re.compile(r"#\w+")


class PostValidationError(ValueError):
    """Post inválido antes de chegar ao Buffer."""


def due_at_utc(local: datetime, now: datetime | None = None) -> str:
    """Converte o horário local (sem fuso) para o formato UTC do Buffer. Precisa estar no futuro."""
    now = now or time.now()
    if local <= now:
        raise PostValidationError("A data e a hora precisam estar no futuro.")
    return time.to_aware(local).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def build_post_input(*, channel_id: str, service: str, text: str, image_urls: list[str], mode: str,
                     due_at: str | None = None) -> dict:
    if mode not in MODES:
        raise PostValidationError("Modo de publicação inválido.")
    if mode == "customScheduled" and not due_at:
        raise PostValidationError("Escolha a data e a hora do agendamento.")
    if service == "instagram":
        text = limit_instagram_hashtags(text)
        if not image_urls:
            raise PostValidationError("O Instagram precisa de pelo menos uma imagem.")
    if not text.strip() and not image_urls:
        raise PostValidationError("Escreva um texto ou adicione uma imagem.")
    limit = MAX_TEXT.get(service)
    if limit and len(text) > limit:
        raise PostValidationError(f"O texto para {service} passou de {limit} caracteres.")
    if len(image_urls) > MAX_IMAGES:
        raise PostValidationError(f"No máximo {MAX_IMAGES} imagens por post.")

    post: dict = {
        "channelId": channel_id,
        "text": text,
        "schedulingType": "automatic",
        "mode": mode,
        "needsApproval": False,
        "assets": [{"image": {"url": url}} for url in image_urls],
    }
    if mode == "customScheduled":
        post["dueAt"] = due_at
    if service == "instagram":
        post["metadata"] = {"instagram": {"type": "post", "shouldShareToFeed": True}}
    elif service == "facebook":
        post["metadata"] = {"facebook": {"type": "post"}}
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


def parse_image_urls(raw: str) -> list[str]:
    """Uma URL por linha. Só http(s): o Buffer busca a imagem por um link público."""
    urls = [line.strip() for line in raw.splitlines() if line.strip()]
    for url in urls:
        if not url.startswith(("https://", "http://")):
            raise PostValidationError(f"Link de imagem inválido: {url[:60]}")
    return urls
