"""Reações aos eventos dos outros módulos: é aqui que bônus e punições acontecem.

Cada handler devolve mensagens (texto, categoria do flash) que aparecem com som na tela.
Os handlers não fazem commit próprio (a exceção é create_quest, que salva a Penalty Quest);
o resto entra na transação de quem publicou o evento.
"""
from datetime import date, datetime

from app.core.events import subscribe
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput

from . import rules as r
from .services import get_rules, record_failure


def _bonus(amount: int, source: str, description: str, source_id: int | None = None) -> list[tuple[str, str]]:
    if amount <= 0:
        return []
    result = hunter.award_xp(amount, source=source, source_id=source_id, description=description)
    messages = [(f"{description}: +{amount} XP", "bonus")]
    if result.leveled_up:
        messages.append((f"LEVEL UP! Você alcançou o nível {result.new_level}.", "levelup"))
    if result.new_rank:
        messages.append((f"Novo rank desbloqueado: {result.new_rank.name}.", "levelup"))
    return messages


@subscribe("quest.completed")
def on_quest_completed(quest: quests.QuestView, completed_at: datetime):
    rules = get_rules()
    if not rules.bonuses_enabled:
        return []
    day = completed_at.date()
    messages: list[tuple[str, str]] = []

    # Primeira quest concluída no dia
    if hunter.count_events_on(day, "quest") == 1:
        messages += _bonus(rules.first_quest_bonus_xp, "bonus", "Bônus da primeira quest do dia", quest.id)

    # Concluída antes do dia do prazo
    if quest.due_date and day < quest.due_date:
        messages += _bonus(r.percent_of(quest.xp_reward, rules.early_bonus_percent), "bonus",
                           "Bônus por adiantar o prazo", quest.id)

    # Combo: todas as Daily Quests de hoje concluídas (uma vez por dia)
    if quest.quest_type == "daily" and hunter.count_events_on(day, "combo") == 0:
        remaining = [q for q in quests.quests_for_today(day) if q.quest_type == "daily"]
        if not remaining:
            done = [q for q in quests.completed_on(day) if q.quest_type == "daily"]
            total = sum(q.xp_reward for q in done)
            amount = max(rules.daily_combo_min_xp, r.percent_of(total, rules.daily_combo_percent))
            messages += _bonus(amount, "combo", f"COMBO! Todas as {len(done)} Daily Quests de hoje")
    return messages


@subscribe("quest.missed")
def on_quest_missed(quest: quests.QuestView, today: date):
    rules = get_rules()
    if r.is_penalty_quest(quest.title):
        return []
    if not rules.penalties_enabled:
        record_failure(quest, penalty_xp=0, penalty_quest_id=None)
        return [(f"'{quest.title}' não foi realizada. Registre o motivo na Zona de Falha.", "info")]
    status = hunter.get_status()
    loss = r.penalty_amount(quest.xp_reward, rules.penalty_xp_percent, status.progress.xp_into_level)
    messages: list[tuple[str, str]] = []
    if loss:
        hunter.award_xp(-loss, source="penalty", source_id=quest.id,
                        description=f"Penalidade: '{quest.title}' não realizada")
    text = f"'{quest.title}' não foi realizada ({quest.due_date:%d/%m})." + (f" -{loss} XP." if loss else "")
    penalty_quest = None
    if rules.penalty_quest_enabled:
        penalty_quest = quests.create_quest(QuestInput(
            title=f"{r.PENALTY_PREFIX} {quest.title}"[:160],
            quest_type="emergency",
            priority="critical",
            difficulty=quest.difficulty,
            xp_reward=max(loss, 5),
            due_date=today,
            description="Penalty Zone: cumpra a quest perdida hoje para recuperar o XP.",
            completion_criteria=f"Fazer hoje o que '{quest.title}' pedia.",
        ), note="Penalty Quest gerada pelo System")
        text += " Penalty Quest liberada: cumpra hoje para recuperar."
    record_failure(quest, penalty_xp=loss, penalty_quest_id=penalty_quest.id if penalty_quest else None)
    text += " Foi imprevisto? Registre o motivo na Zona de Falha."
    messages.append((text, "penalty"))
    return messages


@subscribe("habit.checked")
def on_habit_checked(habit_id: int, habit_name: str, log_id: int, streak: int, base_xp: int):
    rules = get_rules()
    if not rules.bonuses_enabled:
        return []
    percent = r.streak_bonus_percent(streak, rules.streak_tiers)
    return _bonus(r.percent_of(base_xp, percent), "habit_bonus",
                  f"Sequência de {streak} dias em {habit_name} (+{percent}%)", log_id)


@subscribe("habit.unchecked")
def on_habit_unchecked(habit_id: int, log_id: int):
    hunter.revert_events("habit_bonus", log_id, "Bônus de sequência estornado")
    return []

