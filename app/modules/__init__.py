"""Módulos de domínio do Shadow System.

Regra do monólito modular: cada módulo expõe sua API pública em `services.py`. Outros módulos
importam apenas `app.modules.<modulo>.services`, nunca models ou routes de outro módulo.
Para adicionar um módulo, crie a pasta e inclua o blueprint na lista abaixo.
"""
from flask import Flask


def register_modules(app: Flask) -> None:
    from .architect import bp as architect_bp
    from .arena import bp as arena_bp
    from .calendar import bp as calendar_bp
    from .character import bp as character_bp
    from .dashboard import bp as dashboard_bp
    from .gamification import bp as gamification_bp
    from .habits import bp as habits_bp
    from .hunter import bp as hunter_bp
    from .quests import bp as quests_bp
    from .training import bp as training_bp

    blueprints = [dashboard_bp, hunter_bp, character_bp, arena_bp, architect_bp, quests_bp, habits_bp, training_bp, calendar_bp, gamification_bp]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
