from datetime import timedelta

from app.core import time
from app.modules.dashboard import services
from app.modules.habits import services as habits
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput


def test_dashboard_renders_empty_state(client):
    response = client.get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "STATUS" in html and "Daily Quest" in html


def test_dashboard_shows_real_data(client):
    quests.create_quest(QuestInput(title="Treinar pernas", quest_type="daily"))
    quests.create_quest(QuestInput(title="Projeto final", quest_type="main", due_date=time.today() - timedelta(days=1)))
    habits.save_habit("Ler 10 páginas", "", 10, [])
    html = client.get("/").get_data(as_text=True)
    assert "Treinar pernas" in html
    assert "Ler 10 páginas" in html
    assert "1 quest(s) com prazo vencido." in html
    assert "1 hábito(s) ainda não marcados hoje." in html


def test_completing_from_dashboard_returns_to_dashboard(client):
    quest = quests.create_quest(QuestInput(title="Daily", quest_type="daily"))
    response = client.post(f"/quests/{quest.id}/complete", data={"next": "/"})
    assert response.headers["Location"] == "/"


def test_widget_settings_are_saved_and_respected(client):
    client.post("/dashboard/settings", data={"widgets": ["status", "weekly_xp", "não-existe"]})
    assert services.enabled_widgets() == ["status", "weekly_xp"]
    html = client.get("/").get_data(as_text=True)
    assert "Evolução semanal" in html and "Daily Quest" not in html


def test_all_widgets_off(client):
    client.post("/dashboard/settings", data={})
    assert "Todos os widgets estão desligados" in client.get("/").get_data(as_text=True)


def test_build_only_loads_requested_widgets(app):
    data = services.build(["weekly_xp"])
    assert set(data) == {"widgets", "system_messages", "weekly_xp"}
    assert len(data["weekly_xp"]["series"]) == 7
