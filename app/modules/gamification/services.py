"""API pública da gamificação: regras, histórico de bônus e punições e a Zona de Falha."""
from collections import Counter

from sqlalchemy import select

from app.core import settings, time
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests

from .models import QuestFailure
from .rules import FAILURE_REASONS, Rules

SETTING_KEY = "gamification.rules"
SOURCES = ["bonus", "combo", "habit_bonus", "penalty", "penalty_refund"]


def get_rules() -> Rules:
    return Rules.from_dict(settings.get_setting(SETTING_KEY))


def save_rules(rules: Rules) -> None:
    settings.set_setting(SETTING_KEY, rules.to_dict())


def history(limit: int = 30):
    """Últimos bônus e punições (XpEvent)."""
    return hunter.recent_events(limit=limit, sources=SOURCES)


# ---------- Zona de Falha ----------

def record_failure(quest, *, penalty_xp: int, penalty_quest_id: int | None) -> QuestFailure:
    """Chamado quando uma quest recorrente vence sem ser feita. Sem commit (roda no rollover)."""
    failure = QuestFailure(quest_id=quest.id, quest_title=quest.title[:200], due_date=quest.due_date,
                           penalty_xp=penalty_xp, penalty_quest_id=penalty_quest_id)
    db.session.add(failure)
    db.session.flush()
    return failure


def list_failures(pending_only: bool = False, limit: int = 50) -> list[QuestFailure]:
    query = select(QuestFailure).order_by(QuestFailure.created_at.desc()).limit(limit)
    if pending_only:
        query = query.where(QuestFailure.reason.is_(None))
    return list(db.session.scalars(query))


def pending_failures_count() -> int:
    return len(list_failures(pending_only=True, limit=500))


def failure_stats(days: int = 60) -> dict[str, int]:
    """Quantas falhas por motivo nos últimos `days` dias ("unknown" = ainda sem motivo)."""
    from datetime import timedelta

    since = time.now() - timedelta(days=days)
    rows = db.session.scalars(select(QuestFailure.reason).where(QuestFailure.created_at >= since))
    return dict(Counter(reason or "unknown" for reason in rows))


def classify_failure(failure_id: int, reason: str, note: str = "") -> tuple[str, str]:
    """Registra o motivo. Devolve (mensagem, categoria). Motivos de reembolso desfazem a punição."""
    if reason not in FAILURE_REASONS:
        raise DomainError("Motivo inválido.")
    failure = db.session.get(QuestFailure, failure_id)
    if failure is None:
        raise NotFoundError("Falha não encontrada.")
    failure.reason, failure.note, failure.classified_at = reason, note.strip()[:500], time.now()
    label, advice = FAILURE_REASONS[reason]
    message = f"Motivo registrado: {label}. {advice}"
    refund = reason in get_rules().refund_reasons
    if refund and not failure.refunded:
        if failure.penalty_xp:
            hunter.award_xp(failure.penalty_xp, source="penalty_refund", source_id=failure.id,
                            description=f"Punição desfeita ({label}): {failure.quest_title}"[:200])
            message += f" +{failure.penalty_xp} XP devolvidos."
        if failure.penalty_quest_id:
            quests.cancel_quests([failure.penalty_quest_id])
        failure.refunded = True
    db.session.commit()
    return message, "bonus" if refund and failure.penalty_xp else "info"
