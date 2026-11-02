"""Análise por regras do Arquiteto (funções puras sobre o Snapshot). Funciona sem IA.

Cada conclusão cita o número que a gerou, para você conferir. Nada é inventado: sem dados, a regra
fica quieta. As sugestões de missão são rascunhos; só viram quest quando você aceita.
"""
from dataclasses import dataclass, field

from .context import Snapshot

MIN_SAMPLES = 4  # menos que isso numa categoria = pouco dado para tirar conclusão


@dataclass(frozen=True)
class Insight:
    level: str   # "good" | "warning" | "info"
    title: str
    text: str


@dataclass(frozen=True)
class Draft:
    """Missão sugerida (vira ArchitectSuggestion; só vira quest se você aceitar)."""

    rule_key: str
    title: str
    reason: str
    category: str = ""
    difficulty: int = 2
    priority: str = "medium"
    recurrence: str = "none"
    due_in_days: int = 1
    description: str = ""
    goal_id: int | None = None


@dataclass
class Report:
    insights: list[Insight] = field(default_factory=list)
    priorities: list[dict] = field(default_factory=list)
    drafts: list[Draft] = field(default_factory=list)


PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def analyze(s: Snapshot) -> Report:
    report = Report()
    _momentum(s, report)
    _overdue(s, report)
    _habits_at_risk(s, report)
    _categories(s, report)
    _failures(s, report)
    _attributes(s, report)
    _training(s, report)
    _goals(s, report)
    _empty_day(s, report)
    report.priorities = _priorities(s)
    return report


def _momentum(s: Snapshot, r: Report) -> None:
    if s.evolution_streak >= 3:
        r.insights.append(Insight("good", "Sequência de evolução",
                                  f"{s.evolution_streak} dias seguidos com XP. Proteja a sequência com uma missão pequena hoje."))
    if s.xp_last_week and s.xp_week < s.xp_last_week * 0.6:
        r.insights.append(Insight("warning", "Ritmo abaixo da semana passada",
                                  f"{s.xp_week} XP nesta semana contra {s.xp_last_week} no mesmo trecho da anterior."))
    elif s.xp_week > s.xp_last_week > 0:
        r.insights.append(Insight("good", "Ritmo acima da semana passada",
                                  f"{s.xp_week} XP nesta semana contra {s.xp_last_week} no mesmo trecho da anterior."))
    missing = s.xp_for_next - s.xp_into_level
    if 0 < missing <= 60:
        r.insights.append(Insight("info", "Level up perto",
                                  f"Faltam {missing} XP para o nível {s.level + 1}."))


def _overdue(s: Snapshot, r: Report) -> None:
    overdue = [q for q in s.active_quests if q["overdue"]]
    if len(overdue) >= 3:
        r.insights.append(Insight("warning", "Missões atrasadas acumulando",
                                  f"{len(overdue)} missões passaram do prazo. Reveja prazos ou cancele o que perdeu o sentido."))
        r.drafts.append(Draft("review_overdue", "Revisar missões atrasadas (15 min)",
                              f"{len(overdue)} missões atrasadas: decidir para cada uma se faz, adia ou cancela.",
                              category="Organização pessoal", difficulty=1, priority="high", due_in_days=0))


def _habits_at_risk(s: Snapshot, r: Report) -> None:
    for h in s.habits:
        if h["expected_today"] and not h["done_today"] and h["streak"] >= 3:
            r.insights.append(Insight("warning", f"Sequência em risco: {h['name']}",
                                      f"{h['streak']} dias seguidos. Marque hoje para não perder."))


def _categories(s: Snapshot, r: Report) -> None:
    for p in s.category_performance:
        total = p["completed"] + p["missed"]
        if total < MIN_SAMPLES or p["rate"] is None:
            continue
        rate = round(p["rate"] * 100)
        if rate < 50:
            r.insights.append(Insight("warning", f"{p['category']}: desafio acima do momento",
                                      f"{rate}% concluídas em 30 dias ({p['completed']} de {total}), dificuldade média "
                                      f"{p['avg_difficulty']}. Diminua a dificuldade ou divida as missões."))
            r.drafts.append(Draft(f"smaller:{p['category']}", f"{p['category']}: versão curta (20 min)",
                                  f"Só {rate}% das missões de {p['category']} foram feitas: uma missão menor reconstrói o ritmo.",
                                  category=p["category"], difficulty=max(1, round(p["avg_difficulty"]) - 1), due_in_days=1))
        elif rate >= 90 and p["avg_difficulty"] <= 2.5:
            r.insights.append(Insight("good", f"{p['category']}: pronto para subir de nível",
                                      f"{rate}% concluídas ({p['completed']} de {total}) com dificuldade média "
                                      f"{p['avg_difficulty']}. Tente uma missão mais difícil."))
            r.drafts.append(Draft(f"harder:{p['category']}", f"{p['category']}: desafio maior",
                                  f"{rate}% de conclusão com dificuldade baixa: hora de subir o desafio.",
                                  category=p["category"], difficulty=min(5, round(p["avg_difficulty"]) + 2), due_in_days=3))


def _failures(s: Snapshot, r: Report) -> None:
    if not s.failures_60d:
        return
    total = sum(s.failures_60d.values())
    known = {k: v for k, v in s.failures_60d.items() if k != "Sem motivo registrado"}
    top, count = max(known.items(), key=lambda item: item[1]) if known else ("", 0)
    if total >= 3 and known:
        r.insights.append(Insight("info", "Padrão nas falhas",
                                  f"{total} falhas em 60 dias; o motivo mais comum é \"{top}\" ({count})."))
    pending = s.failures_60d.get("Sem motivo registrado", 0)
    if pending:
        r.insights.append(Insight("warning", "Falhas sem motivo",
                                  f"{pending} falha(s) sem motivo na Zona de Falha. Imprevistos registrados devolvem o XP."))
    if top == "Falta de planejamento" and count >= 2:
        r.drafts.append(Draft("weekly_planning", "Planejar a semana (20 min)",
                              f"{count} falhas por falta de planejamento: um planejamento semanal fixo ataca a causa.",
                              category="Organização pessoal", difficulty=2, recurrence="weekly", due_in_days=0))
    if top == "Procrastinação" and count >= 2:
        r.drafts.append(Draft("first_15", "Primeiros 15 minutos da missão mais adiada",
                              f"{count} falhas por procrastinação: começar pequeno é o que mais destrava.",
                              difficulty=1, priority="high", due_in_days=0))


def _attributes(s: Snapshot, r: Report) -> None:
    if not s.attributes or sum(s.attributes.values()) < 10:
        return
    weakest = sorted(s.attributes_gained_4w.items(), key=lambda item: (item[1], s.attributes.get(item[0], 0)))[:2]
    for name, gained in weakest:
        categories = s.attribute_categories.get(name, [])
        if not categories:
            continue
        r.insights.append(Insight("info", f"{name} parado",
                                  f"+{gained} ponto(s) em 4 semanas. Missões de {', '.join(categories[:2])} desenvolvem {name}."))
        r.drafts.append(Draft(f"attribute:{name}", f"{categories[0]}: sessão de 25 minutos",
                              f"{name} ganhou só {gained} ponto(s) em 4 semanas.", category=categories[0],
                              difficulty=2, due_in_days=2))


def _training(s: Snapshot, r: Report) -> None:
    for plan in s.training:
        if s.today.weekday() >= 4 and plan["done_this_week"] < plan["per_week"]:
            left = plan["per_week"] - plan["done_this_week"]
            r.insights.append(Insight("info", f"Treino: {plan['plan']}",
                                      f"{plan['done_this_week']}/{plan['per_week']} nesta semana. Faltam {left} para fechar "
                                      "a semana e liberar a progressão de carga."))


def _goals(s: Snapshot, r: Report) -> None:
    active_titles = " ".join(q["title"].lower() for q in s.active_quests)
    for g in s.goals:
        # Ligada = alguma missão ativa cita a meta (palavras do título) ou é da mesma área.
        words = [w for w in g["title"].lower().split() if len(w) > 3]
        same_area = bool(g["area"]) and any(q["category"] == g["area"] and not q["title"].startswith("[PENALTY]")
                                             for q in s.active_quests)
        linked = same_area or any(w in active_titles for w in words)
        if not linked:
            r.insights.append(Insight("warning", f"Meta sem missão: {g['title']}",
                                      "Nenhuma missão ativa ligada a esta meta. Uma meta sem próximo passo não anda."))
            r.drafts.append(Draft(f"goal_step:{g['id']}", f"Próximo passo: {g['title']}"[:160],
                                  "Meta sem missão ativa: defina e faça o menor passo concreto.",
                                  category=g["area"], difficulty=2, priority="high", due_in_days=1, goal_id=g["id"]))
            r.drafts.append(Draft(f"goal_weekly:{g['id']}", f"Sessão semanal: {g['title']}"[:160],
                                  "Um horário fixo por semana mantém a meta viva.", category=g["area"],
                                  difficulty=3, recurrence="weekly", due_in_days=2, goal_id=g["id"]))


def _empty_day(s: Snapshot, r: Report) -> None:
    today = s.today.isoformat()
    for_today = [q for q in s.active_quests if q["due"] is None or q["due"] <= today]
    if not for_today:
        r.insights.append(Insight("info", "Dia sem missões",
                                  "Nenhuma missão para hoje. Escolha uma sugestão abaixo ou crie a sua."))


def _priorities(s: Snapshot) -> list[dict]:
    """Até 3 missões para fazer primeiro: atrasadas, depois prazo hoje, depois prioridade."""
    today = s.today.isoformat()
    ranked = sorted(
        (q for q in s.active_quests if q["due"] is None or q["due"] <= today or q["priority"] in ("high", "critical")),
        key=lambda q: (not q["overdue"], q["due"] != today, PRIORITY_ORDER.get(q["priority"], 2), -q["xp"]),
    )
    return ranked[:3]
