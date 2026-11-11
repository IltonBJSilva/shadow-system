"""Filtros e variáveis disponíveis em todos os templates."""
from datetime import date, datetime

from flask import Flask, request, url_for

from . import time
from .routes import bp as core_bp

# Menu lateral. Cada item aparece só se o endpoint existir, então um módulo novo entra no menu
# assim que seu blueprint é registrado. (label, endpoint, ícone-texto)
NAV_ITEMS: list[tuple[str, str, str]] = [
    ("Dashboard", "dashboard.index", "◈"),
    ("Hunter", "hunter.profile", "◆"),
    ("Personagem", "character.index", "⛨"),
    ("Sombras", "shadows.index", "☾"),
    ("Arena", "arena.index", "♛"),
    ("Memórias", "memories.index", "▣"),
    ("Arquiteto", "architect.index", "◬"),
    ("Quests", "quests.index", "⚔"),
    ("Hábitos", "habits.index", "✦"),
    ("Treinos", "training.index", "⚒"),
    ("Gamificação", "gamification.index", "⚡"),
    ("Loja do Tempo", "gamification.shop", "⏳"),
    ("Finanças", "finance.index", "＄"),
    ("Calendário", "calendar.index", "▦"),
    ("Postagens", "buffer.index", "✎"),
    ("YouTube", "youtube.index", "▶"),
    ("Integrações", "integrations.index", "⇄"),
    ("Configurações", "core.preferences", "⚙"),
]


def register(app: Flask) -> None:
    app.register_blueprint(core_bp)

    @app.template_filter("date_br")
    def date_br(value: date | datetime | None) -> str:
        return value.strftime("%d/%m/%Y") if value else ""

    @app.template_filter("datetime_br")
    def datetime_br(value: datetime | None) -> str:
        return value.strftime("%d/%m/%Y %H:%M") if value else ""

    @app.template_filter("hour")
    def hour(value: datetime | None) -> str:
        return value.strftime("%H:%M") if value else ""

    @app.context_processor
    def inject_globals():
        current = request.endpoint or ""
        exact = any(endpoint == current for _, endpoint, _ in NAV_ITEMS)
        nav = [
            # Item ativo: a própria página, ou o módulo dela quando a página não tem item próprio no menu.
            {"label": label, "url": url_for(endpoint), "icon": icon,
             "active": endpoint == current if exact else current.split(".")[0] == endpoint.split(".")[0]}
            for label, endpoint, icon in NAV_ITEMS
            if endpoint in app.view_functions
        ]
        from . import experience, media

        try:
            boot = experience.boot_mode()
            versions = media.versions()
        except Exception:  # noqa: BLE001 (banco ainda sem tabelas: a página abre sem a animação)
            from app.extensions import db

            db.session.rollback()
            boot, versions = "off", {}
        return {"nav_items": nav, "today": time.today(), "boot_mode": boot, "manifesto": experience.MANIFESTO,
                "media_versions": versions}
