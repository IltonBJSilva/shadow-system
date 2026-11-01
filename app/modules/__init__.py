"""Módulos de domínio do Shadow System.

Regra do monólito modular: cada módulo expõe sua API pública em `services.py`. Outros módulos
importam apenas `app.modules.<modulo>.services`, nunca models ou routes de outro módulo.
Para adicionar um módulo, crie a pasta e inclua o blueprint na lista abaixo.
"""
from flask import Flask


def register_modules(app: Flask) -> None:
    from .habits import bp as habits_bp
    from .hunter import bp as hunter_bp
    from .quests import bp as quests_bp

    blueprints = [hunter_bp, quests_bp, habits_bp]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
