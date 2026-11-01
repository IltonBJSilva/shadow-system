"""Ponto de entrada: `flask --app wsgi run` ou `waitress-serve --call wsgi:create_app`."""
from app import create_app

app = create_app()
