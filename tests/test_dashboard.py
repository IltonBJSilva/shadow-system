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


def test_evolution_streak_and_progress_widget(client):
    from datetime import timedelta

    from app.core import time
    from app.extensions import db
    from app.modules.hunter import services as hunter_services
    from app.modules.hunter.models import XpEvent

    today = time.now()
    for back in (0, 1, 2, 4):
        db.session.add(XpEvent(amount=10, source="manual", description="x", created_at=today - timedelta(days=back)))
    db.session.add(XpEvent(amount=-10, source="penalty", description="y", created_at=today - timedelta(days=3)))
    db.session.commit()
    assert hunter_services.evolution_streak() == 3          # dia 3 ficou com XP líquido zero
    assert hunter_services.best_evolution_streak() == 3
    html = client.get("/").get_data(as_text=True)
    assert "dias evoluindo" in html and "Concluídas hoje" in html


def test_new_widgets_show_up_for_people_who_saved_before(app):
    from app.core import settings as app_settings
    from app.modules.dashboard import services as dashboard

    app_settings.set_setting(dashboard.SETTING_KEY, ["status", "habits"])  # salvo numa versão antiga
    assert dashboard.enabled_widgets() == ["status", "progress", "habits"]
    dashboard.save_widgets(["status"])                                 # depois de salvar de novo, vale a escolha
    assert dashboard.enabled_widgets() == ["status"]
