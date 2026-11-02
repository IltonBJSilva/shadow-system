"""Leitura do Gmail pela biblioteca oficial google-api-python-client (Gmail API v1).

Métodos usados (https://developers.google.com/gmail/api/reference/rest):
    users.labels.get        quantidade de não lidos na caixa de entrada
    users.messages.list     ids dos e-mails de uma busca (q = sintaxe de busca do Gmail, ver MailFilter)
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


PERIODS = {"any": "Qualquer data", "1d": "Últimas 24 horas", "7d": "Últimos 7 dias", "30d": "Últimos 30 dias"}
STATUSES = {"unread": "Não lidos", "all": "Lidos e não lidos"}
PLACES = {"inbox": "Caixa de entrada", "all": "Todos (inclui arquivados)"}


def _clean(value: str, limit: int = 120) -> str:
    """Tira caracteres que quebram a sintaxe de busca do Gmail (parênteses, aspas, chaves)."""
    return " ".join(value.translate({ord(c): " " for c in '()"{}'}).split())[:limit]


@dataclass(frozen=True)
class MailFilter:
    """Filtros da tela, convertidos na busca do Gmail (os mesmos operadores da caixa de busca do Gmail)."""

    text: str = ""
    status: str = "unread"
    period: str = "any"
    sender: str = ""
    attachment: bool = False
    place: str = "inbox"

    @classmethod
    def from_args(cls, args) -> "MailFilter":
        def pick(key: str, options: dict, default: str) -> str:
            value = args.get(key, default)
            return value if value in options else default

        return cls(text=_clean(args.get("q", ""), 200), status=pick("status", STATUSES, "unread"),
                   period=pick("period", PERIODS, "any"), sender=_clean(args.get("from", ""), 80),
                   attachment=args.get("attachment") == "1", place=pick("place", PLACES, "inbox"))

    @property
    def is_default(self) -> bool:
        return self == MailFilter()

    def query(self) -> str:
        parts = []
        if self.status == "unread":
            parts.append("is:unread")
        if self.place == "inbox":
            parts.append("in:inbox")
        if self.period != "any":
            parts.append(f"newer_than:{self.period}")
        if self.sender:
            parts.append(f"from:({self.sender})")
        if self.attachment:
            parts.append("has:attachment")
        if self.text:
            parts.append(self.text)
        return " ".join(parts) or "in:anywhere"


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
        return self.search(MailFilter(), limit)[0]

    def search(self, mail_filter: MailFilter, limit: int = 15) -> tuple[list[EmailSummary], int]:
        """E-mails que batem com o filtro e a estimativa de quantos existem no total."""
        listing = self._run(self._service.users().messages().list(userId="me", q=mail_filter.query(),
                                                                  maxResults=limit))
        found = [self._summary(item["id"]) for item in listing.get("messages", [])]
        return found, int(listing.get("resultSizeEstimate", len(found)))

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
