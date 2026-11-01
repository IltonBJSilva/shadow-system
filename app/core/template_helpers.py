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
    ("Quests", "quests.index", "⚔"),
    ("Hábitos", "habits.index", "✦"),
    ("Calendário", "calendar.index", "▦"),
    ("Integrações", "integrations.index", "⇄"),
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
        nav = [
            {"label": label, "url": url_for(endpoint), "icon": icon,
             "active": (request.endpoint or "").split(".")[0] == endpoint.split(".")[0]}
            for label, endpoint, icon in NAV_ITEMS
            if endpoint in app.view_functions
        ]
        return {"nav_items": nav, "today": time.today()}
