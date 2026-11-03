"""Separação dos dados por usuário (multiusuário).

Cada tabela de dados tem `user_id` (UserOwnedMixin, em core/models.py). Dois mecanismos garantem que
um usuário nunca veja nem altere os dados de outro, sem que cada consulta precise lembrar disso:

1. Toda consulta ORM (select, update e delete em massa, `session.get`) recebe automaticamente o
   filtro `user_id = usuário atual` (evento do_orm_execute + with_loader_criteria do SQLAlchemy).
2. Toda linha nova nasce com o `user_id` do usuário atual (default da coluna).
3. `session.get` confere o dono mesmo quando a linha já estava em memória (TenantSession).

Usuário atual: o da sessão de login (definido em core/security.py, em `g.user_id`). Fora de uma
requisição (comandos `flask`, testes) vale o dono (OWNER_ID), ou quem estiver em `as_user(...)`.
Para olhar todos os usuários de propósito (ex.: Arena), use `.execution_options(all_users=True)`.
"""
from contextlib import contextmanager
from contextvars import ContextVar

from flask import g, has_request_context
from flask_sqlalchemy.session import Session as FlaskSession
from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

OWNER_ID = 1

_override: ContextVar[int | None] = ContextVar("shadow_user_override", default=None)


def current_user_id() -> int:
    forced = _override.get()
    if forced is not None:
        return forced
    if has_request_context():
        return g.get("user_id") or OWNER_ID
    return OWNER_ID


@contextmanager
def as_user(user_id: int):
    """Executa um trecho como outro usuário (comandos que passam por todos, testes)."""
    token = _override.set(user_id)
    try:
        yield
    finally:
        _override.reset(token)


class TenantSession(FlaskSession):
    """`session.get(Modelo, id)` devolve a linha guardada em memória sem passar pelo filtro. Aqui ela
    só volta se for do usuário atual (a não ser com execution_options all_users=True)."""

    def get(self, entity, ident, **kwargs):
        obj = super().get(entity, ident, **kwargs)
        options = kwargs.get("execution_options") or {}
        owner = getattr(obj, "user_id", None) if obj is not None else None
        if owner is not None and not options.get("all_users") and owner != current_user_id():
            return None
        return obj


def install(owned_base: type) -> None:
    """Liga o filtro automático para todas as classes que herdam de `owned_base`."""

    @event.listens_for(Session, "do_orm_execute")
    def _filter_by_user(state):
        if state.is_column_load or state.is_relationship_load:
            return  # carregamentos a partir de uma linha já filtrada
        if not (state.is_select or state.is_update or state.is_delete):
            return
        if state.execution_options.get("all_users"):
            return
        uid = current_user_id()
        state.statement = state.statement.options(
            with_loader_criteria(owned_base, lambda cls: cls.user_id == uid, include_aliases=True)
        )
