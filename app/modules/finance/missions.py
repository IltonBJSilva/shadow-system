"""Missões financeiras: XP por bons hábitos com dinheiro, nunca por gastar.

Cada missão vale uma vez por período (dia, semana, mês ou meta) e é conferida com os lançamentos
reais. Valores pequenos de propósito: finanças evoluem o jogador, mas não viram farm de XP. As missões
de semana e mês só pagam se você registrou seus lançamentos de verdade naquele período (evita ganhar
XP simplesmente deixando de anotar os gastos). Nenhum valor em reais vai para o feed ou a Arena.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from app.core import time
from app.core.errors import DomainError
from app.extensions import db
from app.modules.hunter import services as hunter

from . import money, services

XP = {"daily": 10, "week": 30, "budget": 50, "saving": 50, "goal": 100}
SOURCES = {"daily": "finance_daily", "week": "finance_week", "budget": "finance_budget",
           "saving": "finance_saving", "goal": "finance_goal"}
MIN_LOGGED_DAYS_WEEK = 5
MIN_LOGGED_DAYS_MONTH = 15


@dataclass(frozen=True)
class Mission:
    key: str
    title: str
    detail: str
    xp: int
    state: str  # done | ready | pending


def _claimed(kind: str, period_id: int) -> bool:
    return hunter.event_for(SOURCES[kind], period_id) is not None


def _award(kind: str, period_id: int, description: str) -> hunter.AwardResult:
    return hunter.award_xp(XP[kind], source=SOURCES[kind], source_id=period_id, description=description[:200],
                           base=XP[kind], bonus=0, breakdown=[hunter.progression.XpLine(description[:80], XP[kind])])


def claim_daily(today: date | None = None) -> hunter.AwardResult:
    """"Registrei todas as despesas de hoje" (ou "hoje não gastei"): uma vez por dia."""
    today = today or time.today()
    period = int(today.strftime("%Y%m%d"))
    if _claimed("daily", period):
        raise DomainError("A missão de hoje já foi registrada.")
    result = _award("daily", period, "Missão financeira: registrei as despesas do dia")
    db.session.commit()
    return result


def evaluate(today: date | None = None) -> list[tuple[str, str]]:
    """Confere as missões de semana, mês e metas e paga as cumpridas (uma vez). Devolve mensagens."""
    today = today or time.today()
    messages: list[tuple[str, str]] = []
    week_start = today - timedelta(days=today.weekday() + 7)
    week_end = week_start + timedelta(days=6)
    week_id = week_start.isocalendar().year * 100 + week_start.isocalendar().week
    if not _claimed("week", week_id) and _week_ok(week_start, week_end):
        _award("week", week_id, "Missão financeira: semana sem gastos desnecessários")
        messages.append((f"[Finanças] Semana sem gastos desnecessários: +{XP['week']} XP.", "bonus"))

    last_month = services.shift_month(services.month_key(today), -1)
    month_id = int(last_month.replace("-", ""))
    if not _claimed("budget", month_id) and _budget_ok(last_month):
        _award("budget", month_id, f"Missão financeira: orçamento de {last_month} cumprido")
        messages.append((f"[Finanças] Orçamento do mês cumprido: +{XP['budget']} XP.", "bonus"))
    target = services.monthly_saving_target()
    if target and not _claimed("saving", month_id) and _logged_enough(last_month) and services.summary(last_month).net >= target:
        _award("saving", month_id, f"Missão financeira: economizou {money.brl(target)} em {last_month}")
        messages.append((f"[Finanças] Meta de economia do mês alcançada: +{XP['saving']} XP.", "bonus"))

    for status in services.goals():
        if status.reached and not _claimed("goal", status.goal.id):
            _award("goal", status.goal.id, f"Missão financeira: meta “{status.goal.name}” alcançada")
            messages.append((f"[Finanças] Meta “{status.goal.name}” alcançada: +{XP['goal']} XP.", "achievement"))
    if messages:
        db.session.commit()
    return messages


def board(today: date | None = None) -> list[Mission]:
    today = today or time.today()
    week_start = today - timedelta(days=today.weekday())
    month = services.month_key(today)
    target = services.monthly_saving_target()
    day_done = _claimed("daily", int(today.strftime("%Y%m%d")))
    week_logged = len(services.logged_days(week_start, today))
    budgets = services.budgets(month)
    goals = services.goals()
    return [
        Mission("daily", "Registrar todas as despesas do dia", "Anote os gastos de hoje e confirme (ou confirme que não gastou).",
                XP["daily"], "done" if day_done else "ready"),
        Mission("week", "Semana sem gastos desnecessários",
                f"Nenhum gasto em categorias não essenciais de segunda a domingo, com lançamentos em pelo menos "
                f"{MIN_LOGGED_DAYS_WEEK} dias. Esta semana: {week_logged} dia(s) registrados, "
                f"{money.brl(services.nonessential_spent(week_start, today))} em não essenciais.", XP["week"], "pending"),
        Mission("budget", "Cumprir o orçamento mensal",
                "Todas as categorias com orçamento dentro do limite no mês (pago no mês seguinte)."
                + ("" if budgets else " Crie um orçamento para começar."), XP["budget"], "pending"),
        Mission("saving", "Economizar no mês",
                (f"Saldo do mês (receitas - despesas) de pelo menos {money.brl(target)}." if target
                 else "Defina quanto quer economizar por mês."), XP["saving"], "pending"),
        Mission("goal", "Criar uma reserva financeira",
                f"Alcançar uma meta financeira ({sum(1 for g in goals if g.reached)}/{len(goals)} alcançadas).",
                XP["goal"], "pending"),
    ]


def _week_ok(start: date, end: date) -> bool:
    return len(services.logged_days(start, end)) >= MIN_LOGGED_DAYS_WEEK and services.nonessential_spent(start, end) == 0


def _logged_enough(month: str) -> bool:
    start, end = services.month_range(month)
    return len(services.logged_days(start, end - timedelta(days=1))) >= MIN_LOGGED_DAYS_MONTH


def _budget_ok(month: str) -> bool:
    statuses = services.budgets(month)
    return bool(statuses) and _logged_enough(month) and not any(s.over for s in statuses)
