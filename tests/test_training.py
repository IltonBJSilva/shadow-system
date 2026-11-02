"""Treinos: parser, rotinas prontas, documentos, automações (quests, calendário, hábito) e progressão."""
import io
import zipfile
from datetime import date, datetime, timedelta

import pytest

from app.core import time
from app.core.errors import DomainError
from app.modules.calendar import services as calendar
from app.modules.gamification import services as gamification
from app.modules.gamification.rules import Rules
from app.modules.habits import services as habits
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests
from app.modules.training import documents, library, parser, progression, services
from app.modules.training.services import PlanOptions

ROUTINE = """Plano: Teste ABC
Segunda: Treino A - Peito
- Supino reto 4x8-12 40kg descanso 90s
- Flexão 3x12
Quarta: Treino B - Costas
- Remada 4x10 30kg
Sexta: Treino C - Pernas
- Agachamento 4x8 60kg
- Prancha 3x45s
"""


@pytest.fixture(autouse=True)
def no_bonus(app):
    gamification.save_rules(Rules(bonuses_enabled=False, penalties_enabled=False))


# ---------- parser (funções puras) ----------

def test_parser_reads_days_sets_loads_rest_and_notes():
    plan = parser.parse("""Plano: X
Segunda: Treino A - Peito e tríceps
- Supino reto 4x8-12 40kg descanso 90s
- Tríceps na polia 3x12 (pegada neutra)
Quarta-feira - Costas
1. Puxada frontal 4 x 10 @ 35,5 kg desc 2min
• Corrida leve 20min
texto solto
""")
    assert plan.name == "X" and [d.weekday for d in plan.days] == [0, 2]
    supino, triceps = plan.days[0].exercises
    assert (supino.sets, supino.reps, supino.load_kg, supino.rest_seconds) == (4, "8-12", 40.0, 90)
    assert triceps.notes == "pegada neutra"
    puxada, corrida = plan.days[1].exercises
    assert (puxada.load_kg, puxada.rest_seconds) == (35.5, 120)
    assert (corrida.sets, corrida.reps) == (1, "20min")
    assert plan.warnings and "texto solto" in plan.warnings[0]


def test_parser_spreads_days_without_weekday():
    plan = parser.parse("Treino A:\n- Supino 3x10\nTreino B:\n- Remada 3x10\nTreino C:\n- Agachamento 3x10")
    assert [d.weekday for d in plan.days] == [0, 2, 4]


def test_parser_round_trip():
    plan = parser.parse(ROUTINE)
    again = parser.parse(parser.to_text(plan.name, plan.days))
    assert [(d.weekday, d.name, [e.describe() for e in d.exercises]) for d in again.days] == \
           [(d.weekday, d.name, [e.describe() for e in d.exercises]) for d in plan.days]


def test_every_ready_routine_parses():
    for template in library.TEMPLATES:
        plan = parser.parse(template.text)
        assert plan.name and len(plan.days) >= 3 and not plan.warnings, template.key
        assert len({d.weekday for d in plan.days}) == len(plan.days), template.key


# ---------- progressão (funções puras) ----------

@pytest.mark.parametrize("reps, load, expected", [
    ("8-12", 40.0, ("8-12", 42.5)),
    ("12", None, ("13", None)),
    ("8-12", None, ("9-13", None)),
    ("45s", None, ("50s", None)),
    ("20min", None, ("21min", None)),
    ("max", None, None),
    ("30", None, None),
])
def test_progression_rules(reps, load, expected):
    assert progression.next_values(reps, load, 2.5) == expected


# ---------- documentos ----------

def test_extract_text_from_txt_docx_and_rejects_others():
    assert "Supino" in documents.extract_text("treino.txt", "Segunda: A\n- Supino 3x10".encode("cp1252"))
    docx = io.BytesIO()
    with zipfile.ZipFile(docx, "w") as z:
        w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        z.writestr("word/document.xml", f'<w:document xmlns:w="{w}"><w:body>'
                   f'<w:p><w:r><w:t>Segunda: Treino A</w:t></w:r></w:p>'
                   f'<w:p><w:pPr><w:numPr/></w:pPr><w:r><w:t>Supino 4x10</w:t></w:r></w:p>'
                   f'</w:body></w:document>')
    text = documents.extract_text("plano.docx", docx.getvalue())
    assert text.splitlines() == ["Segunda: Treino A", "- Supino 4x10"]
    with pytest.raises(documents.DocumentError):
        documents.extract_text("virus.exe", b"x")
    with pytest.raises(documents.DocumentError):
        documents.extract_text("grande.txt", b"x" * (documents.MAX_BYTES + 1))


# ---------- automações ----------

def _plan(**options):
    defaults = dict(name="", session_time="07:00", start_date=time.today())
    defaults.update(options)
    return services.create_plan(ROUTINE, PlanOptions(**defaults))


def test_activation_creates_weekly_quests_events_and_habit(app):
    plan = _plan()
    assert plan.active and plan.name == "Teste ABC"
    active = [q for q in quests.list_quests("active") if q.title.startswith("Treino:")]
    assert len(active) == 3
    assert all(q.recurrence == "weekly" and q.quest_type == "daily" for q in active)
    assert {q.due_date.weekday() for q in active} == {0, 2, 4}
    assert "Supino reto: 4x8-12 · 40 kg · descanso 90s" in next(q for q in active if "Peito" in q.title).description
    events = [e for e in calendar.events_between(datetime.now(), datetime.now() + timedelta(weeks=5))
              if e.title.startswith("Treino:")]
    assert 10 <= len(events) <= 12 and all(e.kind == "workout" and e.start_at.hour == 7 for e in events)
    habit = habits.get_habit(plan.habit_id)
    assert habits.weekdays_for(habit) == {0, 2, 4}


def test_events_are_not_duplicated(app):
    plan = _plan()
    assert services.ensure_calendar(plan.id) == 0


def test_options_turn_automations_off(app):
    plan = _plan(make_events=False, make_habit=False)
    assert plan.habit_id is None
    assert not [e for e in calendar.events_between(datetime.now(), datetime.now() + timedelta(weeks=5))
                if e.title.startswith("Treino:")]


def test_completing_the_quest_records_workout_checks_habit_and_unlocks_title(app):
    plan = _plan()
    quest = next(q for q in quests.list_quests("active") if "Peito" in q.title)
    result = quests.complete_quest(quest.id)
    texts = " ".join(text for text, _ in result.extra)
    assert "Treino registrado: Treino A - Peito" in texts
    assert services.sessions_count(plan.id) == 1
    assert habits.get_habit(plan.habit_id).logs  # hábito marcado sozinho
    assert next(t for t in hunter.list_titles() if t.name == "Primeiro Treino").unlocked
    # a próxima ocorrência da mesma quest semanal também conta como treino do plano
    nxt = quests.active_in_series(quest.series_id)
    assert nxt and nxt.id != quest.id


def test_full_week_offers_progression_and_apply_updates_quests(app):
    plan = _plan()
    for q in [q for q in quests.list_quests("active") if q.title.startswith("Treino:")]:
        quests.complete_quest(q.id)
    plan = services.get_plan(plan.id)
    assert plan.pending_progression_week is not None
    suggestions = {s.name: s.after for s in services.progression_suggestions(plan)}
    assert suggestions["Treino A - Peito: Supino reto"] == "4x8-12 · 42,5 kg"
    assert suggestions["Treino A - Peito: Flexão"] == "3x13"
    assert services.apply_progression(plan.id) == 5
    peito = next(d for d in services.get_plan(plan.id).days if d.weekday == 0)
    assert peito.exercises[0].load_kg == 42.5
    nxt = quests.active_in_series(peito.quest_series_id)
    assert "42,5 kg" in nxt.description


def test_deactivate_cancels_quests_removes_future_events_and_archives_habit(app):
    plan = _plan()
    services.deactivate_plan(plan.id)
    assert not [q for q in quests.list_quests("active") if q.title.startswith("Treino:")]
    assert not [e for e in calendar.events_between(datetime.now(), datetime.now() + timedelta(weeks=5))
                if e.title.startswith("Treino:")]
    assert not habits.get_habit(plan.habit_id).active
    services.activate_plan(plan.id)  # reativar reaproveita o mesmo hábito
    assert habits.get_habit(services.get_plan(plan.id).habit_id).active


def test_two_active_plans_cannot_share_a_weekday(app):
    _plan()
    other = services.create_plan("Segunda: Corrida\n- Corrida leve 20min", PlanOptions(name="Corrida"),
                                 activate=False)
    with pytest.raises(DomainError, match="Segunda"):
        services.activate_plan(other.id)


def test_invalid_text_and_duplicate_weekday_are_rejected(app):
    with pytest.raises(DomainError):
        services.create_plan("nada de treino aqui", PlanOptions(name="x"))
    with pytest.raises(DomainError, match="mesmo dia"):
        services.preview("Segunda: A\n- Supino 3x10\nSegunda: B\n- Remada 3x10")


def test_update_active_plan_rebuilds_quests(app):
    plan = _plan()
    services.update_plan(plan.id, "Terça: Novo\n- Burpee 3x10", PlanOptions(name="Novo plano", make_events=False))
    titles = [q.title for q in quests.list_quests("active") if q.title.startswith("Treino:")]
    assert titles == ["Treino: Novo"]
    assert services.get_plan(plan.id).name == "Novo plano"


# ---------- telas ----------

def test_pages(client):
    assert "Rotinas de treino" in client.get("/training/").get_data(as_text=True)
    page = client.get("/training/new").get_data(as_text=True)
    assert "Full body" in page and "Ler documento" in page
    page = client.get("/training/new?template=abc").get_data(as_text=True)
    assert "Prévia" in page and "Agachamento livre" in page


def test_create_through_form_and_detail(client):
    response = client.post("/training/new", data={
        "text": ROUTINE, "name": "", "session_time": "6:30", "session_minutes": "45", "load_increment_kg": "2.5",
        "make_quests": "y", "make_habit": "y", "progression": "y", "action": "create"})
    assert response.status_code == 302
    plan = services.list_plans()[0]
    assert plan.session_time == "06:30" and not plan.make_events
    html = client.get(f"/training/{plan.id}").get_data(as_text=True)
    assert "Supino reto" in html and "40 kg" in html
    assert "Treino A - Peito" in client.get(f"/training/{plan.id}/edit").get_data(as_text=True)


def test_preview_action_does_not_save(client):
    html = client.post("/training/new", data={"text": ROUTINE, "session_time": "18:00", "session_minutes": "60",
                                              "action": "preview"}).get_data(as_text=True)
    assert "Prévia" in html and not services.list_plans()


def test_upload_document(client):
    data = {"document": (io.BytesIO(ROUTINE.encode()), "meu-treino.txt")}
    html = client.post("/training/upload", data=data, content_type="multipart/form-data").get_data(as_text=True)
    assert "Texto extraído do documento" in html and "Treino A - Peito" in html


def test_workouts_metric_feeds_titles(app):
    _plan()
    assert next(t for t in hunter.list_titles() if t.name == "Corpo em Forja").current == 0
