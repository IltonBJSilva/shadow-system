"""Monta o dashboard a partir da API pública dos outros módulos.

O dashboard não tem tabelas próprias: só lê. A escolha de widgets fica em app_settings.
Para um widget novo: adicione em WIDGETS, crie o loader em `_LOADERS` e o template
templates/dashboard/widgets/<chave>.html.
"""
from typing import Any, Callable

from app.core import settings, time
from app.integrations import buffer
from app.modules.calendar import services as calendar
from app.modules.habits import services as habits
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests

SETTING_KEY = "dashboard.widgets"

# Ordem aqui = ordem na tela.
WIDGETS: dict[str, str] = {
    "status": "Status do Hunter (nível, rank, XP, atributos)",
    "notifications": "Notificações",
    "today_quests": "Missões do dia",
    "habits": "Hábitos de hoje",
    "priority_quests": "Missões prioritárias",
    "upcoming_events": "Próximos eventos",
    "weekly_xp": "Evolução semanal (XP por dia)",
    "recent_activity": "Atividades recentes",
    "scheduled_content": "Conteúdos agendados (Buffer)",
}
DEFAULT_WIDGETS = list(WIDGETS)


def enabled_widgets() -> list[str]:
    saved = settings.get_setting(SETTING_KEY)
    if not isinstance(saved, list):
        return DEFAULT_WIDGETS
    return [key for key in WIDGETS if key in saved]


def save_widgets(keys: list[str]) -> None:
    settings.set_setting(SETTING_KEY, [key for key in WIDGETS if key in keys])


def build(widgets: list[str] | None = None) -> dict[str, Any]:
    """Dados de cada widget ligado. Widgets desligados não fazem consulta nenhuma."""
    widgets = widgets if widgets is not None else enabled_widgets()
    _, system_messages = quests.roll_over_with_messages()
    data: dict[str, Any] = {"widgets": widgets, "system_messages": system_messages}
    for key in widgets:
        data[key] = _LOADERS[key]()
    return data


def _notifications() -> list[tuple[str, str]]:
    """(mensagem, nível) calculadas na hora. Nada é inventado: tudo vem dos dados registrados."""
    notes: list[tuple[str, str]] = []
    quest_stats = quests.stats()
    if quest_stats["overdue"]:
        notes.append((f"{quest_stats['overdue']} quest(s) com prazo vencido.", "warning"))
    penalties = [q for q in quests.quests_for_today() if q.title.startswith("[PENALTY]")]
    if penalties:
        notes.append((f"Penalty Zone: {len(penalties)} Penalty Quest(s) para cumprir hoje e recuperar XP.", "warning"))
    pending_habits = [h for h in habits.list_habits() if not h.done_today]
    if pending_habits:
        notes.append((f"{len(pending_habits)} hábito(s) ainda não marcados hoje.", "info"))
    today = time.today()
    events_today = [e for e in calendar.upcoming_events(days=1, limit=50) if e.start_at.date() == today]
    if events_today:
        notes.append((f"{len(events_today)} evento(s) hoje. Próximo: {events_today[0].title} "
                      f"às {events_today[0].start_at:%H:%M}.", "info"))
    return notes


def _weekly_xp() -> dict[str, Any]:
    series = hunter.xp_by_day(time.today(), days=7)
    peak = max([amount for _, amount in series] + [1])
    return {"series": series, "peak": peak, "total": sum(amount for _, amount in series)}


def _scheduled_content() -> dict[str, Any]:
    posts, error = buffer.scheduled_posts_safe(limit=5)
    return {"configured": buffer.is_configured(), "posts": posts, "error": error}


def _status() -> dict[str, Any]:
    return {
        "status": hunter.get_status(),
        "quest_stats": quests.stats(),
        "best_streak": habits.best_current_streak(),
    }


_LOADERS: dict[str, Callable[[], Any]] = {
    "status": _status,
    "notifications": _notifications,
    "today_quests": lambda: quests.quests_for_today(),
    "habits": lambda: habits.list_habits(),
    "priority_quests": lambda: quests.priority_quests(limit=5),
    "upcoming_events": lambda: calendar.upcoming_events(days=7, limit=6),
    "weekly_xp": _weekly_xp,
    "recent_activity": lambda: hunter.recent_events(limit=8),
    "scheduled_content": _scheduled_content,
}
