"""Ligações do Personagem com o resto do sistema (eventos e bônus de XP)."""
from app.core import events
from app.modules.arena import services as arena
from app.modules.hunter import services as hunter

from . import services

hunter.register_bonus_provider(services.xp_bonus_lines)


@events.subscribe("quest.completed")
def deliver_items(**_payload):
    return [(f"[Equipamento] Novo item no inventário: {name}.", "achievement") for name in services.sync_inventory()]


def _card_extension() -> dict:
    if not arena.privacy()["loadout"]:
        return {}
    return {"equipment": [f"{i.icon} {i.name}" for i in services.equipped_items()]}


arena.register_card_extension(_card_extension)
