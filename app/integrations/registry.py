"""Situação de cada integração, para a tela /integrations.

Cada integração informa se está configurada (credenciais presentes) e, quando faz sentido, se está
conectada. Integrações planejadas aparecem como "planned", sem fingir que funcionam.
"""
from dataclasses import dataclass
from typing import Literal

State = Literal["connected", "configured", "not_configured", "error", "planned"]


@dataclass(frozen=True)
class IntegrationStatus:
    key: str
    name: str
    description: str
    state: State
    detail: str = ""
    url: str | None = None  # tela da integração dentro do Shadow System


def all_statuses() -> list[IntegrationStatus]:
    from .buffer import status as buffer_status
    from .gmail import status as gmail_status
    from .google_calendar import status as google_status
    from .notion import status as notion_status
    from .whatsapp import status as whatsapp_status

    return [
        google_status(),
        gmail_status(),
        buffer_status(),
        notion_status(),
        whatsapp_status(),
        IntegrationStatus(
            key="ai",
            name="Shadow AI",
            description="Assistente para transformar objetivos em quests, relatórios e sugestões.",
            state="planned",
            detail="Ainda não implementado. Ver ROADMAP.md.",
        ),
    ]
