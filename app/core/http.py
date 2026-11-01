"""Helpers HTTP compartilhados pelas rotas."""
from flask import redirect, request


def is_safe_path(target: str | None) -> bool:
    """Aceita só caminhos internos ("/quests"), nunca outro site ("//evil.com", "https://...")."""
    return bool(target) and target.startswith("/") and not target.startswith("//")


def redirect_back(default: str):
    """Redireciona para o campo `next` do formulário (se for interno) ou para `default`.

    Permite que botões como "Concluir" funcionem tanto na lista de quests quanto no dashboard.
    """
    target = request.form.get("next") or request.args.get("next")
    return redirect(target if is_safe_path(target) else default)
