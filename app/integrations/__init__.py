"""Integrações com serviços externos.

Cada integração fica isolada na sua pasta, com um cliente que fala com a API externa e não conhece
os modelos dos módulos. Os módulos usam as integrações; o contrário não acontece.
"""
from flask import Flask


def register_integrations(app: Flask) -> None:
    blueprints: list = []
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
