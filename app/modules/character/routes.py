"""Tela do Personagem: ficha, equipamentos e inventário."""
from flask import flash, redirect, render_template, url_for

from app.modules.hunter import services as hunter
from app.modules.quests import services as quests

from . import bp, catalog, services


@bp.get("/")
def index():
    for name in services.sync_inventory():
        flash(f"[Equipamento] Novo item no inventário: {name}.", "achievement")
    services.db_commit()
    status = hunter.get_status()
    return render_template(
        "character/index.html", sheet=services.sheet(), catalog=catalog, status=status,
        avatar_url=status.avatar_url, rank_color=status.rank.color if status.rank else None,
        daily=quests.quests_for_period("daily"), weekly=quests.quests_for_period("weekly"),
        achievements=[t for t in hunter.list_titles() if t.unlocked][-8:], quest_stats=quests.stats(),
        streak=hunter.evolution_streak(),
    )


@bp.post("/equipar/<item_key>")
def equip(item_key: str):
    item = services.equip(item_key)
    flash(f"{item.icon} {item.name} equipado.", "success")
    return redirect(url_for("character.index"))


@bp.post("/desequipar/<item_key>")
def unequip(item_key: str):
    services.unequip(item_key)
    flash("Item guardado no inventário.", "info")
    return redirect(url_for("character.index"))
