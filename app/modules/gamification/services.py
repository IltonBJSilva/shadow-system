"""API pública da gamificação: ler/salvar regras e histórico de bônus e punições."""
from app.core import settings
from app.modules.hunter import services as hunter

from .rules import Rules

SETTING_KEY = "gamification.rules"
SOURCES = ["bonus", "combo", "habit_bonus", "penalty"]


def get_rules() -> Rules:
    return Rules.from_dict(settings.get_setting(SETTING_KEY))


def save_rules(rules: Rules) -> None:
    settings.set_setting(SETTING_KEY, rules.to_dict())


def history(limit: int = 30):
    """Últimos bônus e punições (XpEvent)."""
    return hunter.recent_events(limit=limit, sources=SOURCES)
