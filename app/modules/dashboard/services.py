"""Monta o dashboard a partir da API pública dos outros módulos.

O dashboard não tem tabelas próprias: só lê. A escolha de widgets fica em app_settings.
Para um widget novo: adicione em WIDGETS, crie o loader em `_LOADERS` e o template
templates/dashboard/widgets/<chave>.html.
"""
from typing import Any, Callable

from app.core import settings, time
from app.integrations import buffer, gmail
from app.modules.calendar import services as calendar
from app.modules.gamification import services as gamification
from app.modules.habits import services as habits
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests

SETTING_KEY = "dashboard.widgets"

# Ordem aqui = ordem na tela.
WIDGETS: dict[str, str] = {
    "status": "Status do Hunter (nível, rank, XP, atributos)",
    "notifications": "Notificações",
    "progress": "Progresso: sequência de evolução, semana atual x anterior, concluídas hoje",
    "today_quests": "Missões do dia",
    "habits": "Hábitos de hoje",
    "priority_quests": "Missões prioritárias",
    "upcoming_events": "Próximos eventos",
    "weekly_xp": "Evolução semanal (XP por dia)",
    "recent_activity": "Atividades recentes",
    "scheduled_content": "Conteúdos agendados (Buffer)",
    "emails": "E-mails não lidos (Gmail)",
}
DEFAULT_WIDGETS = list(WIDGETS)


KNOWN_KEY = "dashboard.widgets_known"
# Widgets que existiam antes de KNOWN_KEY ser gravado: quem salvou antes disso já os conhecia.
_LEGACY_WIDGETS = ["status", "notifications", "today_quests", "habits", "priority_quests", "upcoming_events",
                   "weekly_xp", "recent_activity", "scheduled_content", "emails"]


def enabled_widgets() -> list[str]:
    """Widgets ligados. Um widget novo (que você ainda não viu na tela de Personalizar) aparece ligado."""
    saved = settings.get_setting(SETTING_KEY)
    if not isinstance(saved, list):
        return DEFAULT_WIDGETS
    known = settings.get_setting(KNOWN_KEY)
    known = set(known) if isinstance(known, list) else set(_LEGACY_WIDGETS)
    return [key for key in WIDGETS if key in saved or key not in known]


def save_widgets(keys: list[str]) -> None:
    settings.set_setting(SETTING_KEY, [key for key in WIDGETS if key in keys])
    settings.set_setting(KNOWN_KEY, list(WIDGETS))


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
    pending_failures = gamification.pending_failures_count()
    if pending_failures:
        notes.append((f"Zona de Falha: {pending_failures} missão(ões) não realizada(s) esperando o motivo "
                      "(imprevisto e limitação real devolvem o XP).", "warning"))
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


def _emails() -> dict[str, Any]:
    unread, emails, error = gmail.unread_safe(limit=5)
    return {"authorized": gmail.is_authorized(), "unread": unread, "emails": emails, "error": error}


def _progress() -> dict[str, Any]:
    """Comparação desta semana (segunda até hoje) com o mesmo trecho da semana passada."""
    from datetime import timedelta

    today = time.today()
    monday = today - timedelta(days=today.weekday())
    last_monday, last_same_day = monday - timedelta(days=7), today - timedelta(days=7)
    return {
        "streak": hunter.evolution_streak(today),
        "best_streak": hunter.best_evolution_streak(),
        "xp_week": hunter.xp_between(monday, today),
        "xp_last_week": hunter.xp_between(last_monday, last_same_day),
        "quests_week": quests.completed_between(monday, today),
        "quests_last_week": quests.completed_between(last_monday, last_same_day),
        "done_today": quests.completed_on(today),
    }


def _status() -> dict[str, Any]:
    return {
        "status": hunter.get_status(),
        "quest_stats": quests.stats(),
        "best_streak": habits.best_current_streak(),
    }


_LOADERS: dict[str, Callable[[], Any]] = {
    "status": _status,
    "progress": _progress,
    "notifications": _notifications,
    "today_quests": lambda: quests.quests_for_today(),
    "habits": lambda: habits.list_habits(),
    "priority_quests": lambda: quests.priority_quests(limit=5),
    "upcoming_events": lambda: calendar.upcoming_events(days=7, limit=6),
    "weekly_xp": _weekly_xp,
    "recent_activity": lambda: hunter.recent_events(limit=8),
    "scheduled_content": _scheduled_content,
    "emails": _emails,
}
