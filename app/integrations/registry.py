"""Situação de cada integração, para a tela /integrations e o dashboard.

Cada integração informa se está configurada (credenciais/URL presentes) e, quando faz sentido,
se está conectada. Integrações planejadas aparecem como "planned", sem fingir que funcionam.
"""
from dataclasses import dataclass
from typing import Literal

from flask import current_app

State = Literal["connected", "configured", "not_configured", "error", "planned"]


@dataclass(frozen=True)
class IntegrationStatus:
    key: str
    name: str
    description: str
    state: State
    detail: str = ""
    url: str | None = None  # tela da integração dentro do Shadow System


def all_statuses(check_remote: bool = True) -> list[IntegrationStatus]:
    """check_remote=False evita chamadas de rede (ex.: renderização rápida do dashboard)."""
    from .google_calendar import status as google_status
    from .kausa_scheduler import status as kausa_status

    return [
        google_status(),
        kausa_status(check_remote=check_remote),
        IntegrationStatus(
            key="buffer",
            name="Buffer",
            description="Publicação nas redes sociais. Feita pelo Kausa Social Scheduler, que já integra o Buffer.",
            state="configured" if current_app.config.get("KAUSA_SCHEDULER_URL") else "not_configured",
            detail="Usado através do Kausa Social Scheduler (não há chamada direta ao Buffer daqui).",
        ),
        IntegrationStatus(
            key="ai",
            name="Shadow AI",
            description="Assistente para transformar objetivos em quests, relatórios e sugestões.",
            state="planned",
            detail="Ainda não implementado. Ver ROADMAP.md.",
        ),
    ]
