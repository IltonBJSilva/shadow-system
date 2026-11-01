"""Gmail, Notion e WhatsApp com as APIs simuladas. Nenhum teste chama serviço real."""
import json
from datetime import date

import httpx
import pytest

from app.integrations import credentials, gmail, notion, whatsapp
from app.integrations.google_calendar import oauth
from app.integrations.notion import NotionError
from app.integrations.whatsapp import WhatsAppError
from app.integrations.whatsapp.client import normalize_number
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput

TOKEN = "secret_" + "a" * 40


# ============ Gmail ============

class _Req:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeGmail:
    MESSAGES = {
        "m1": {"snippet": "Segue a proposta", "payload": {"headers": [
            {"name": "From", "value": "Cliente <cliente@ex.com>"}, {"name": "Subject", "value": "Proposta"},
            {"name": "Date", "value": "Mon, 02 Nov 2026 12:00:00 +0000"}]}},
    }

    def users(self):
        fake = self

        class Users:
            def labels(self):
                return type("L", (), {"get": lambda s, userId, id: _Req({"messagesUnread": 7})})()

            def messages(self):
                class M:
                    def list(self, userId, q, maxResults):
                        assert "is:unread" in q
                        return _Req({"messages": [{"id": "m1"}]})

                    def get(self, userId, id, format, metadataHeaders):
                        return _Req(fake.MESSAGES[id])
                return M()
        return Users()


@pytest.fixture
def gmail_authorized(app, monkeypatch, tmp_path):
    token = tmp_path / "google_token.json"
    token.write_text(json.dumps({"scopes": oauth.SCOPES + [oauth.GMAIL_SCOPE]}))
    app.config["GOOGLE_TOKEN_FILE"] = str(token)
    monkeypatch.setattr(gmail, "_service_factory", FakeGmail)


def test_gmail_requires_gmail_scope(app, tmp_path):
    token = tmp_path / "google_token.json"
    token.write_text(json.dumps({"scopes": oauth.SCOPES}))
    app.config["GOOGLE_TOKEN_FILE"] = str(token)
    assert oauth.is_connected() and not gmail.is_authorized()


def test_gmail_lists_unread(gmail_authorized):
    client = gmail.get_client()
    assert client.unread_count() == 7
    mail = client.unread()[0]
    assert (mail.sender, mail.subject) == ("Cliente", "Proposta")
    assert mail.received_at.hour == 9  # 12:00 UTC = 09:00 em São Paulo
    assert mail.url.endswith("#inbox/m1")


def test_gmail_email_becomes_quest(client, gmail_authorized):
    client.post("/integrations/gmail/quest", data={"subject": "Proposta", "sender": "Cliente",
                                                   "url": "https://mail.google.com/mail/u/0/#inbox/m1"})
    quest = quests.list_quests("active")[0]
    assert quest.title == "Responder: Proposta" and "mail.google.com" in quest.description


def test_gmail_page_and_dashboard_widget(client, gmail_authorized):
    assert "Proposta" in client.get("/integrations/gmail/").get_data(as_text=True)
    assert "7 não lido(s)" in client.get("/").get_data(as_text=True)


def test_gmail_page_without_google(client):
    assert "Gmail desligado" in client.get("/integrations/gmail/").get_data(as_text=True)


# ============ Notion ============

class FakeNotion:
    def __init__(self, reject=False):
        self.reject = reject

    def __call__(self, request: httpx.Request) -> httpx.Response:
        assert request.headers["Notion-Version"] == "2022-06-28"
        if self.reject:
            return httpx.Response(401, json={"message": "API token is invalid."})
        if request.url.path == "/v1/users/me":
            return httpx.Response(200, json={"name": "Shadow System"})
        if request.url.path == "/v1/search":
            return httpx.Response(200, json={"results": [
                {"id": "a" * 32, "title": [{"plain_text": "Tarefas"}], "url": "https://notion.so/x"}]})
        if request.url.path.endswith("/query"):
            return httpx.Response(200, json={"results": [
                {"object": "page", "id": "p1", "url": "https://notion.so/p1", "properties": {
                    "Nome": {"type": "title", "title": [{"plain_text": "Estudar SQL"}]},
                    "Prazo": {"type": "date", "date": {"start": "2026-11-10"}},
                    "Status": {"type": "status", "status": {"name": "A fazer"}}}},
                {"object": "page", "id": "p2", "url": "https://notion.so/p2", "properties": {
                    "Nome": {"type": "title", "title": [{"plain_text": "Sem prazo"}]}}},
            ]})
        return httpx.Response(404, json={})


@pytest.fixture
def notion_ready(app, monkeypatch):
    monkeypatch.setattr(notion, "_transport", httpx.MockTransport(FakeNotion()))
    notion.save_token(TOKEN)


def test_notion_token_is_validated_and_masked(app, monkeypatch):
    monkeypatch.setattr(notion, "_transport", httpx.MockTransport(FakeNotion()))
    assert notion.save_token(TOKEN) == "Shadow System"
    assert notion.status().state == "connected" and TOKEN not in notion.status().detail


def test_notion_rejected_token_is_not_saved(app, monkeypatch):
    monkeypatch.setattr(notion, "_transport", httpx.MockTransport(FakeNotion(reject=True)))
    with pytest.raises(NotionError, match="recusou"):
        notion.save_token(TOKEN)
    assert not notion.is_configured()


def test_notion_pages_are_parsed(notion_ready):
    pages = notion.get_client().pages("a" * 32)
    assert pages[0].title == "Estudar SQL" and pages[0].due == date(2026, 11, 10) and pages[0].status == "A fazer"
    assert pages[1].due is None


def test_notion_rejects_strange_database_id(notion_ready):
    with pytest.raises(NotionError):
        notion.get_client().pages("../users")


def test_notion_import_does_not_duplicate(notion_ready):
    pages = notion.get_client().pages("a" * 32)
    assert notion.import_pages(pages) == 2
    assert notion.import_pages(pages) == 0
    titles = {q.title for q in quests.list_quests("active")}
    assert titles == {"Estudar SQL", "Sem prazo"}


def test_notion_pages_render(client, notion_ready):
    assert "Tarefas" in client.get("/integrations/notion/").get_data(as_text=True)
    assert "Estudar SQL" in client.get(f"/integrations/notion/databases/{'a' * 32}").get_data(as_text=True)
    client.post(f"/integrations/notion/databases/{'a' * 32}/import", data={"pages": ["p1"]})
    assert [q.title for q in quests.list_quests("active")] == ["Estudar SQL"]


def test_notion_page_asks_token_when_missing(client):
    assert "Internal Integration Secret" in client.get("/integrations/notion/").get_data(as_text=True)


# ============ WhatsApp ============

class FakeWhatsApp:
    def __init__(self, status=200):
        self.sent: list[dict] = []
        self.status = status

    def __call__(self, request: httpx.Request) -> httpx.Response:
        assert request.url.path.startswith("/v21.0/123456")
        if self.status != 200:
            return httpx.Response(self.status, json={"error": {"code": 190, "message": "Invalid OAuth"}})
        if request.method == "GET":
            return httpx.Response(200, json={"display_phone_number": "+1 555 0100", "verified_name": "Test"})
        body = json.loads(request.content)
        self.sent.append(body)
        return httpx.Response(200, json={"messages": [{"id": f"wamid.{len(self.sent)}"}]})


@pytest.fixture
def wa(app, monkeypatch):
    fake = FakeWhatsApp()
    monkeypatch.setattr(whatsapp, "_transport", httpx.MockTransport(fake))
    return fake


def test_normalize_number():
    assert normalize_number("+55 (11) 99999-9999") == "5511999999999"
    with pytest.raises(WhatsAppError):
        normalize_number("123")


def test_whatsapp_settings_are_validated(app, wa):
    assert whatsapp.save(TOKEN, "123456", "+55 11 99999-9999") == "+1 555 0100"
    assert whatsapp.is_configured()
    assert credentials.load("whatsapp")["my_number"] == "5511999999999"


def test_whatsapp_invalid_token(app, monkeypatch):
    monkeypatch.setattr(whatsapp, "_transport", httpx.MockTransport(FakeWhatsApp(status=401)))
    with pytest.raises(WhatsAppError, match="token"):
        whatsapp.save(TOKEN, "123456", "5511999999999")
    assert not whatsapp.is_configured()


def test_summary_only_goes_to_my_number(app, wa):
    whatsapp.save(TOKEN, "123456", "5511999999999")
    quests.create_quest(QuestInput(title="Treinar", quest_type="daily"))
    text = whatsapp.daily_summary()
    assert "Treinar" in text and "[SYSTEM]" in text
    whatsapp.send_to_me(text)
    assert wa.sent[0]["to"] == "5511999999999" and wa.sent[0]["type"] == "text"


def test_template_test_message(client, wa):
    whatsapp.save(TOKEN, "123456", "5511999999999")
    client.post("/integrations/whatsapp/test")
    assert wa.sent[0]["template"]["name"] == "hello_world"


def test_whatsapp_page_never_shows_token(client, wa):
    whatsapp.save(TOKEN, "123456", "5511999999999")
    html = client.get("/integrations/whatsapp/").get_data(as_text=True)
    assert TOKEN not in html and "Resumo do dia" in html


def test_keep_token_when_updating_numbers(app, wa):
    whatsapp.save(TOKEN, "123456", "5511999999999")
    whatsapp.save("", "123456", "5511888888888")
    assert credentials.load("whatsapp")["token"] == TOKEN


def test_integrations_page_lists_all(client):
    html = client.get("/integrations/").get_data(as_text=True)
    for name in ("Google Calendar", "Gmail", "Buffer", "Notion", "WhatsApp", "Shadow AI"):
        assert name in html
