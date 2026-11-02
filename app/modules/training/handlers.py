"""Reação a eventos de outros módulos: quest de treino concluída vira um treino registrado."""
from datetime import datetime

from app.core.events import subscribe

from . import services


@subscribe("quest.completed")
def on_quest_completed(quest, completed_at: datetime):
    return services.record_workout(quest.series_id, quest.id, completed_at.date())
