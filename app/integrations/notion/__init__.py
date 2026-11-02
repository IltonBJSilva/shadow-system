"""Notion: ler bancos de dados e importar páginas como quests (sem duplicar).

O token é cadastrado pela tela, conferido no Notion e guardado em instance/credentials/notion.json.
"""
from app.core import settings
from app.modules.quests import services as quests
from app.modules.quests.services import QuestInput

from .. import credentials
from ..registry import IntegrationStatus
from .client import NotionClient, NotionDatabase, NotionError, NotionPage

NAME = "notion"
IMPORTED_KEY = "notion.imported_pages"

# Testes trocam por um httpx.MockTransport.
_transport = None


def token() -> str:
    return credentials.load(NAME).get("token", "")


def is_configured() -> bool:
    return bool(token())


def get_client(token_value: str | None = None) -> NotionClient:
    return NotionClient(token_value or token(), transport=_transport)


def save_token(token_value: str) -> str:
    """Confere no Notion antes de salvar. Retorna o nome do bot da integração."""
    token_value = token_value.strip()
    if len(token_value) < 20:
        raise NotionError("Esse token parece incompleto. Copie o 'Internal Integration Secret' inteiro.")
    bot = get_client(token_value).me()
    credentials.save(NAME, {"token": token_value, "bot": bot})
    return bot


def status() -> IntegrationStatus:
    base = dict(key="notion", name="Notion", description="Importa páginas de bancos de dados do Notion como quests.",
                url="/integrations/notion/")
    data = credentials.load(NAME)
    if not data.get("token"):
        return IntegrationStatus(**base, state="not_configured", detail="Cadastre o token quando gerar.")
    return IntegrationStatus(**base, state="connected",
                             detail=f"{data.get('bot', 'integração')} · token {credentials.mask(data['token'])}")


def imported_ids() -> set[str]:
    return set(settings.get_setting(IMPORTED_KEY, []))


def import_pages(pages: list[NotionPage]) -> int:
    """Cria uma quest por página ainda não importada. Retorna quantas foram criadas.

    Páginas sem título são puladas: viraria uma quest "(sem título)" sem como saber o que é.
    """
    done = imported_ids()
    created = 0
    for page in pages:
        if page.id in done or not page.title:
            continue
        quests.create_quest(QuestInput(
            title=page.title[:160],
            quest_type="side",
            due_date=page.due,
            description=f"Importada do Notion: {page.url}",
        ), note="Quest importada do Notion")
        done.add(page.id)
        created += 1
    settings.set_setting(IMPORTED_KEY, sorted(done))
    return created


__all__ = ["NotionClient", "NotionDatabase", "NotionError", "NotionPage", "get_client", "import_pages",
           "imported_ids", "is_configured", "save_token", "status"]
