"""Hospedagem das imagens enviadas do computador para o Buffer.

O Buffer não recebe arquivo diretamente: ele busca cada imagem por um link público que não expira.
O Shadow System suporta duas formas automáticas:
1. Armazenamento interno no banco de dados (tabela `buffer_uploads`), servido publicamente via endpoint
   `/integrations/buffer/uploads/<token>/<filename>` sem necessidade de serviços externos.
2. Supabase Storage (opcional, bucket público configurado no .env via SUPABASE_URL, SUPABASE_SECRET_KEY e SUPABASE_BUCKET).
"""
import re
import secrets
import unicodedata
import uuid
from datetime import date

import httpx
from flask import current_app, has_request_context, url_for

from app.core.models import BufferUpload
from app.extensions import db
from app.integrations.network import connection_message

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 20 * 1024 * 1024


class StorageError(Exception):
    pass


def is_supabase_configured() -> bool:
    """Indica se as credenciais do bucket público do Supabase Storage estão no .env."""
    cfg = current_app.config
    return bool(cfg.get("SUPABASE_URL") and cfg.get("SUPABASE_SECRET_KEY") and cfg.get("SUPABASE_BUCKET"))


def is_configured() -> bool:
    """O armazenamento de imagens do computador está sempre ativo (via banco ou Supabase)."""
    return True


def get_upload(token: str) -> BufferUpload | None:
    """Busca uma imagem salva no banco pelo token público."""
    return db.session.get(BufferUpload, token)


def upload(filename: str, content: bytes, content_type: str, transport: httpx.BaseTransport | None = None) -> str:
    """Valida a imagem, armazena (no Supabase se configurado, ou no banco de dados) e devolve o link público."""
    if content_type not in ALLOWED_TYPES:
        raise StorageError(f"{filename}: formato não aceito (use JPG, PNG, WEBP ou GIF).")
    if len(content) > MAX_BYTES:
        raise StorageError(f"{filename}: imagem maior que 20 MB.")

    if is_supabase_configured():
        return _upload_supabase(filename, content, content_type, transport=transport)
    return _upload_local(filename, content, content_type)


def _upload_local(filename: str, content: bytes, content_type: str) -> str:
    """Salva a imagem no banco de dados com token criptográfico seguro e gera o link público."""
    safe_name = _safe_name(filename)
    token = secrets.token_urlsafe(32)
    upload_row = BufferUpload(
        token=token,
        filename=safe_name,
        mimetype=content_type,
        size=len(content),
        data=content,
    )
    db.session.add(upload_row)
    db.session.commit()

    if has_request_context():
        return url_for("buffer.serve_upload", token=token, filename=safe_name, _external=True)
    return f"/integrations/buffer/uploads/{token}/{safe_name}"


def _upload_supabase(filename: str, content: bytes, content_type: str,
                     transport: httpx.BaseTransport | None = None) -> str:
    """Envia para o bucket público do Supabase Storage."""
    cfg = current_app.config
    base, bucket, key = cfg["SUPABASE_URL"].rstrip("/"), cfg["SUPABASE_BUCKET"], cfg["SUPABASE_SECRET_KEY"]
    path = f"{date.today():%Y/%m}/{uuid.uuid4().hex[:12]}-{_safe_name(filename)}"
    with httpx.Client(timeout=60.0, transport=transport,
                      headers={"apikey": key, "Authorization": f"Bearer {key}"}) as http:
        try:
            response = http.post(f"{base}/storage/v1/object/{bucket}/{path}", content=content,
                                 headers={"Content-Type": content_type})
        except httpx.HTTPError as exc:
            raise StorageError(f"{filename}: {connection_message('armazenamento', base, exc)}") from exc
    if response.status_code >= 400:
        raise StorageError(f"{filename}: a hospedagem recusou a imagem ({response.status_code}).")
    return f"{base}/storage/v1/object/public/{bucket}/{path}"


def _safe_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-").lower()
    return name or "imagem"
