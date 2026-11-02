"""Arquiteto: retrato real, regras, sugestões, metas e IA com cliente falso (nunca chama a Anthropic)."""
import json
from datetime import timedelta
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from app.core import time
from app.extensions import db
from app.modules.architect import ai, analysis, context, services
from app.modules.architect.ai import ArchitectAIError
from app.modules.gamification import services as gamification
from app.modules.gamification.rules import Rules
from app.modules.habits import services as habits
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput

KEY = "sk-ant-api03-" + "x" * 40


@pytest.fixture(autouse=True)
def calm_rules(app):
    gamification.save_rules(Rules(bonuses_enabled=False, penalties_enabled=False))


class FakeClient:
    """Imita o pedaço do SDK que o Arquiteto usa e guarda os pedidos."""

    def __init__(self, text="ok", stop_reason="end_turn", fail=None):
        self.calls = []
        fake = self

        class Messages:
            def create(self, **kwargs):
                fake.calls.append(kwargs)
                if fail:
                    raise fail
                return SimpleNamespace(stop_reason=stop_reason,
                                       content=[SimpleNamespace(type="thinking", thinking=""),
                                                SimpleNamespace(type="text", text=text)])

        class Models:
            def retrieve(self, model_id):
                fake.calls.append({"retrieve": model_id})
                if fail:
                    raise fail
                return SimpleNamespace(id=model_id)

        self.beta = SimpleNamespace(messages=Messages())
        self.models = Models()

    def __call__(self, api_key):
        self.key = api_key
        return self


def _connected(fake: FakeClient) -> None:
    ai.save_key(KEY, ai.DEFAULT_MODEL, client_factory=fake)


# ---------- retrato e regras ----------

def test_snapshot_uses_real_data(app):
    cat = quests.save_category("Faculdade", "#fff", [])
    quests.create_quest(QuestInput(title="Lista de Cálculo", category_id=cat.id, due_date=time.today() - timedelta(days=1)))
    habits.save_habit("Ler", "", 10, [])
    snap = context.build()
    assert snap.level == 1 and snap.quest_stats["overdue"] == 1
    assert snap.active_quests[0]["title"] == "Lista de Cálculo" and snap.active_quests[0]["overdue"]
    assert snap.habits[0]["name"] == "Ler"
    json.dumps(snap.as_prompt_data())  # serializável para a IA


def test_low_completion_category_suggests_smaller_missions(app):
    cat = quests.save_category("Estudos", "#fff", [])
    yesterday = time.today() - timedelta(days=1)
    for i in range(5):
        q = quests.create_quest(QuestInput(title=f"E{i}", category_id=cat.id, difficulty=4, recurrence="daily",
                                           due_date=yesterday))
    quests.roll_over_recurring()  # as 5 viram "não realizadas"
    quests.complete_quest(quests.list_quests("active")[0].id)
    report = analysis.analyze(context.build())
    assert any("Estudos: desafio acima do momento" == i.title for i in report.insights)
    assert any(d.rule_key == "smaller:Estudos" and d.difficulty == 3 for d in report.drafts)


def test_goal_without_mission_gets_next_step_and_weekly_session(app):
    goal = services.save_goal("Passar em Cálculo II", "Faculdade")
    report = analysis.analyze(context.build())
    keys = {d.rule_key for d in report.drafts}
    assert f"goal_step:{goal.id}" in keys and f"goal_weekly:{goal.id}" in keys


def test_suggestions_are_stored_once_and_accept_creates_quest(app):
    cat = quests.save_category("Faculdade", "#fff", [])
    services.save_goal("Passar em Cálculo II", "Faculdade")
    services.report()
    services.report()  # rodar de novo não duplica
    pending = services.pending_suggestions()
    assert len([s for s in pending if s.title.startswith("Próximo passo")]) == 1
    step = next(s for s in pending if s.title.startswith("Próximo passo"))
    quest_id = services.accept_suggestion(step.id)
    quest = quests.get_quest(quest_id)
    assert quest.category_id == cat.id and quest.priority == "high" and "Por que o Arquiteto sugeriu" in quest.description
    with pytest.raises(Exception):
        services.accept_suggestion(step.id)  # não cria duas vezes


def test_dismissed_rule_does_not_come_back(app):
    services.save_goal("Correr 5 km", "Treino")
    services.report()
    for s in services.pending_suggestions():
        services.dismiss_suggestion(s.id)
    services.report()
    assert services.pending_suggestions() == []


# ---------- IA ----------

def test_key_is_validated_without_spending_tokens(app):
    fake = FakeClient()
    _connected(fake)
    assert fake.calls == [{"retrieve": "claude-opus-5-5"}] and ai.is_configured()
    assert KEY not in ai.masked_key() and ai.masked_key().endswith(KEY[-4:])


def test_bad_key_is_rejected_and_not_saved(app):
    with pytest.raises(ArchitectAIError):
        ai.save_key("chave-qualquer", ai.DEFAULT_MODEL, client_factory=FakeClient())
    request = httpx.Request("GET", "https://api.anthropic.com/v1/models/x")
    denied = anthropic.AuthenticationError("no", response=httpx.Response(401, request=request), body=None)
    with pytest.raises(ArchitectAIError, match="recusou a chave"):
        ai.save_key(KEY, ai.DEFAULT_MODEL, client_factory=FakeClient(fail=denied))
    assert not ai.is_configured()


def test_chat_sends_real_data_server_side_with_fallback_and_remembers(app):
    fake = FakeClient(text="Priorize a lista de Cálculo: está 1 dia atrasada.")
    _connected(fake)
    quests.create_quest(QuestInput(title="Lista de Cálculo", due_date=time.today() - timedelta(days=1)))
    answer = services.ask("O que faço primeiro?", client_factory=fake)
    assert answer.startswith("Priorize")
    call = fake.calls[-1]
    assert call["model"] == "claude-opus-5-5" and call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"] and call["output_config"]["effort"] == "low"
    assert "Lista de Cálculo" in call["messages"][-1]["content"] and "<dados_do_sistema>" in call["messages"][-1]["content"]
    services.ask("E depois?", client_factory=fake)
    history = fake.calls[-1]["messages"]
    assert [m["role"] for m in history] == ["user", "assistant", "user"]
    assert history[0]["content"] == "O que faço primeiro?"  # o histórico guarda só a pergunta, não os dados
    assert [m.role for m in services.conversation()] == ["user", "assistant", "user", "assistant"]


def test_haiku_goes_without_server_fallback(app):
    fake = FakeClient()
    ai.save_key(KEY, "claude-haiku-5-5", client_factory=fake)
    services.ask("Oi", client_factory=fake)
    assert "fallbacks" not in fake.calls[-1] and fake.calls[-1]["model"] == "claude-haiku-5-5"


def test_refusal_is_reported_not_shown_as_answer(app):
    fake = FakeClient(text="", stop_reason="refusal")
    _connected(fake)
    with pytest.raises(ArchitectAIError, match="recusado"):
        services.ask("?", client_factory=fake)
    assert services.conversation() == []


def test_plan_with_ai_creates_validated_suggestions(app):
    goal = services.save_goal("Lançar portfólio", "Carreira")
    payload = {"summary": "Foque no portfólio.", "missions": [
        {"title": "Escrever a página Sobre", "description": "300 palavras", "reason": "meta sem missão",
         "category": "Carreira", "difficulty": 9, "priority": "urgentíssima", "recurrence": "none",
         "due_in_days": 99, "goal_id": goal.id},
        {"title": "", "description": "", "reason": "", "category": "", "difficulty": 1, "priority": "low",
         "recurrence": "none", "due_in_days": 1, "goal_id": 0},
    ]}
    fake = FakeClient(text=json.dumps(payload))
    _connected(fake)
    summary, created = services.plan_with_ai("portfólio", client_factory=fake)
    assert summary == "Foque no portfólio." and created == 1
    assert fake.calls[-1]["output_config"]["format"]["type"] == "json_schema"
    s = next(x for x in services.pending_suggestions() if x.source == "ai")
    assert (s.difficulty, s.priority, s.due_in_days, s.goal_id) == (5, "medium", 30, goal.id)  # valores saneados


def test_no_key_means_no_call(app):
    with pytest.raises(ArchitectAIError, match="não configurada"):
        services.ask("oi", client_factory=FakeClient())


# ---------- telas ----------

def test_pages_without_ai(client):
    html = client.get("/architect/").get_data(as_text=True)
    assert "Leitura do momento" in html and "Modo regras" in html and "Ligar a IA" in html
    client.post("/architect/goals", data={"title": "Passar em Cálculo II", "area": ""})
    html = client.get("/architect/").get_data(as_text=True)
    assert "Passar em Cálculo II" in html and "Aceitar" in html
    ai.save_key(KEY, ai.DEFAULT_MODEL, client_factory=FakeClient())
    settings_html = client.get("/architect/settings").get_data(as_text=True)
    assert KEY not in settings_html and "configurada" in settings_html  # a chave nunca volta para a página


def test_ai_error_shows_as_flash(client):
    html = client.post("/architect/ask", data={"question": "oi"}, follow_redirects=True).get_data(as_text=True)
    assert "não configurada" in html


def test_goal_status_route(client):
    goal = services.save_goal("Ler 12 livros")
    client.post(f"/architect/goals/{goal.id}/status", data={"status": "done"})
    assert services.list_goals() == []


def test_failure_pattern_ignores_unclassified(app):
    from app.modules.architect.context import Snapshot

    snap = context.build()
    snap.failures_60d = {"Sem motivo registrado": 5}
    report = analysis.analyze(snap)
    assert not any(i.title == "Padrão nas falhas" for i in report.insights)
    assert any(i.title == "Falhas sem motivo" for i in report.insights)


def test_goal_counts_as_linked_when_area_has_active_mission(app):
    cat = quests.save_category("Faculdade", "#fff", [])
    quests.create_quest(QuestInput(title="Lista 3", category_id=cat.id))
    services.save_goal("Passar em Cálculo II", "Faculdade")
    report = analysis.analyze(context.build())
    assert not any(i.title.startswith("Meta sem missão") for i in report.insights)
