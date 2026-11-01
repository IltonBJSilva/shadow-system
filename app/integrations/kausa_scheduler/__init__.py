"""Integração com o Kausa Social Scheduler (leitura de canais e posts agendados no Buffer)."""
import logging

from flask import current_app

from ..registry import IntegrationStatus
from .client import KausaSchedulerClient, KausaSchedulerError, ScheduledPost

log = logging.getLogger(__name__)

__all__ = ["KausaSchedulerClient", "KausaSchedulerError", "ScheduledPost", "get_client", "status",
           "scheduled_posts_safe"]


def get_client() -> KausaSchedulerClient:
    return KausaSchedulerClient(current_app.config.get("KAUSA_SCHEDULER_URL", ""))


def is_configured() -> bool:
    return bool(current_app.config.get("KAUSA_SCHEDULER_URL"))


def status(check_remote: bool = True) -> IntegrationStatus:
    base = dict(
        key="kausa",
        name="Kausa Social Scheduler",
        description="Seu painel de agendamento de posts (Buffer). O Shadow System lê os posts agendados.",
        url="/integrations/kausa",
    )
    if not is_configured():
        return IntegrationStatus(**base, state="not_configured", detail="Defina KAUSA_SCHEDULER_URL no .env.")
    if not check_remote:
        return IntegrationStatus(**base, state="configured", detail=current_app.config["KAUSA_SCHEDULER_URL"])
    online = get_client().health()
    return IntegrationStatus(
        **base,
        state="connected" if online else "error",
        detail=current_app.config["KAUSA_SCHEDULER_URL"] + ("" if online else " · não respondeu"),
    )


def scheduled_posts_safe(limit: int = 5) -> tuple[list[ScheduledPost], str | None]:
    """Posts agendados para o dashboard. Nunca quebra a página: devolve (posts, erro)."""
    if not is_configured():
        return [], None
    try:
        return get_client().posts("scheduled")[:limit], None
    except KausaSchedulerError as exc:
        log.info("Kausa indisponível: %s", type(exc).__name__)
        return [], str(exc)
