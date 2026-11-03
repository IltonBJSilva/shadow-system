"""Ligações das Sombras: bônus de XP, bônus de atributos e cartão da Arena."""
from app.modules.arena import services as arena
from app.modules.character import services as character
from app.modules.hunter import services as hunter

from . import services

hunter.register_bonus_provider(services.xp_bonus_lines)
character.register_stat_provider(services.stat_bonus_lines)


def _card_extension() -> dict:
    army = services.recruited()
    data = {"shadows": len(army)}
    if arena.privacy()["loadout"]:
        data["shadow_names"] = [f"{s.icon} {s.name}" for s in army]
    return data


arena.register_card_extension(_card_extension)
