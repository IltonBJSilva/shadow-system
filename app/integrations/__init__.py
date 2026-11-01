"""Integrações com serviços externos.

Cada integração fica isolada na sua pasta, com um cliente que fala com a API externa e não conhece
os modelos dos módulos. Integrações podem chamar a API pública dos módulos (services.py) para gravar
dados, nunca os models.
"""
from flask import Flask


def register_integrations(app: Flask) -> None:
    from .buffer.routes import bp as buffer_bp
    from .gmail.routes import bp as gmail_bp
    from .google_calendar import oauth as google_oauth
    from .google_calendar.routes import bp as google_bp
    from .notion.routes import bp as notion_bp
    from .routes import bp as integrations_bp
    from .whatsapp.routes import bp as whatsapp_bp

    blueprints = [integrations_bp, google_bp, gmail_bp, buffer_bp, notion_bp, whatsapp_bp]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    @app.context_processor
    def inject_integrations():
        # Permite que telas de módulos mostrem ações opcionais (ex.: "Enviar ao Google").
        return {"google_connected": google_oauth.is_connected()}
