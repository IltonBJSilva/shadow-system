"""Módulos de domínio do Shadow System.

Regra do monólito modular: cada módulo expõe sua API pública em `services.py`. Outros módulos
importam apenas `app.modules.<modulo>.services`, nunca models ou routes de outro módulo.
Para adicionar um módulo, crie a pasta e inclua o blueprint na lista abaixo.
"""
from flask import Flask


def register_modules(app: Flask) -> None:
    blueprints: list = []
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
