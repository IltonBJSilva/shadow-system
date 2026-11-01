"""Hospedagem opcional das imagens enviadas do computador (Supabase Storage, bucket público).

O Buffer não recebe arquivo: ele busca cada imagem por um link público que não expira. Sem
hospedagem configurada, use links públicos de imagens (campo "Links das imagens").
Mesma abordagem usada no Kausa Social Scheduler.
"""
import re
import unicodedata
import uuid
from datetime import date

import httpx
from flask import current_app

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 20 * 1024 * 1024


class StorageError(Exception):
    pass


def is_configured() -> bool:
    cfg = current_app.config
    return bool(cfg.get("SUPABASE_URL") and cfg.get("SUPABASE_SECRET_KEY") and cfg.get("SUPABASE_BUCKET"))


def upload(filename: str, content: bytes, content_type: str, transport: httpx.BaseTransport | None = None) -> str:
    """Envia a imagem e devolve o link público."""
    if not is_configured():
        raise StorageError("Hospedagem de imagens não configurada. Use links públicos das imagens.")
    if content_type not in ALLOWED_TYPES:
        raise StorageError(f"{filename}: formato não aceito (use JPG, PNG, WEBP ou GIF).")
    if len(content) > MAX_BYTES:
        raise StorageError(f"{filename}: imagem maior que 20 MB.")
    cfg = current_app.config
    base, bucket, key = cfg["SUPABASE_URL"].rstrip("/"), cfg["SUPABASE_BUCKET"], cfg["SUPABASE_SECRET_KEY"]
    path = f"{date.today():%Y/%m}/{uuid.uuid4().hex[:12]}-{_safe_name(filename)}"
    with httpx.Client(timeout=60.0, transport=transport,
                      headers={"apikey": key, "Authorization": f"Bearer {key}"}) as http:
        try:
            response = http.post(f"{base}/storage/v1/object/{bucket}/{path}", content=content,
                                 headers={"Content-Type": content_type})
        except httpx.HTTPError as exc:
            raise StorageError(f"{filename}: não foi possível enviar a imagem.") from exc
    if response.status_code >= 400:
        raise StorageError(f"{filename}: a hospedagem recusou a imagem ({response.status_code}).")
    return f"{base}/storage/v1/object/public/{bucket}/{path}"


def _safe_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-").lower()
    return name or "imagem"
