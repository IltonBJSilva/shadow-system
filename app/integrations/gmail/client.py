"""Leitura do Gmail pela biblioteca oficial google-api-python-client (Gmail API v1).

Métodos usados (https://developers.google.com/gmail/api/reference/rest):
    users.labels.get        quantidade de não lidos na caixa de entrada
    users.messages.list     ids dos e-mails não lidos (q="is:unread in:inbox")
    users.messages.get      remetente, assunto e data (format="metadata")

Somente leitura (escopo gmail.readonly): o Shadow System não envia, não marca e não apaga e-mails.
"""
from dataclasses import dataclass
from datetime import datetime
from email.utils import parseaddr, parsedate_to_datetime
from typing import Any

from googleapiclient.errors import HttpError

from app.core import time


class GmailError(Exception):
    """Erro da API do Gmail. A mensagem é mostrada ao usuário."""


@dataclass(frozen=True)
class EmailSummary:
    id: str
    sender: str
    subject: str
    received_at: datetime | None
    snippet: str

    @property
    def url(self) -> str:
        return f"https://mail.google.com/mail/u/0/#inbox/{self.id}"


def build_service(credentials) -> Any:
    from googleapiclient.discovery import build

    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


class GmailClient:
    def __init__(self, service: Any):
        self._service = service

    def unread_count(self) -> int:
        label = self._run(self._service.users().labels().get(userId="me", id="INBOX"))
        return int(label.get("messagesUnread", 0))

    def unread(self, limit: int = 10) -> list[EmailSummary]:
        listing = self._run(self._service.users().messages().list(userId="me", q="is:unread in:inbox",
                                                                  maxResults=limit))
        return [self._summary(item["id"]) for item in listing.get("messages", [])]

    def _summary(self, message_id: str) -> EmailSummary:
        data = self._run(self._service.users().messages().get(
            userId="me", id=message_id, format="metadata", metadataHeaders=["From", "Subject", "Date"]))
        headers = {h["name"].lower(): h["value"] for h in data.get("payload", {}).get("headers", [])}
        name, address = parseaddr(headers.get("from", ""))
        return EmailSummary(
            id=message_id,
            sender=name or address or "(desconhecido)",
            subject=headers.get("subject") or "(sem assunto)",
            received_at=_parse_date(headers.get("date")),
            snippet=data.get("snippet", ""),
        )

    @staticmethod
    def _run(request) -> dict:
        try:
            return request.execute() or {}
        except HttpError as exc:
            status = str(getattr(exc.resp, "status", "?"))
            body = (exc.content or b"").decode("utf-8", "replace") + str(exc)
            if status == "403" and ("accessNotConfigured" in body or "SERVICE_DISABLED" in body):
                raise GmailError(
                    "A Gmail API está desativada no seu projeto do Google Cloud. Ative em "
                    "APIs e serviços → Biblioteca → Gmail API → Ativar, espere alguns minutos e recarregue."
                ) from exc
            if status in ("401", "403"):
                raise GmailError("Sem permissão no Gmail. Autorize o Gmail de novo e confira se a Gmail API está ativa.") from exc
            raise GmailError(f"O Gmail respondeu com erro {status}.") from exc


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return time.to_local_naive(parsedate_to_datetime(value))
    except (TypeError, ValueError):
        return None
