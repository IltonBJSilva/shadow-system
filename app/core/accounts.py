"""Contas: o dono e os usuários de teste convidados por ele.

- Dono (id 1): entra com OWNER_USERNAME e OWNER_PASSWORD_HASH do .env, como antes.
- Usuário de teste: o dono cadastra o e-mail em "Usuários de teste" e recebe um link de convite
  (vale 7 dias, uma vez só). A pessoa abre o link, escolhe nome e senha e já entra, sem precisar de
  conta Google. Depois entra com e-mail (ou usuário) e senha.

O login do sistema não tem relação com o Google: conectar Google Calendar/Gmail é uma autorização
opcional dentro de Integrações, feita por cada usuário para a própria conta.
"""
import hashlib
import hmac
import re
import secrets
from datetime import timedelta

from flask import current_app
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

from . import time
from .errors import DomainError, NotFoundError
from .models import User
from .tenancy import OWNER_ID

INVITE_DAYS = 7
MIN_PASSWORD = 8
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def ensure_owner() -> User:
    """Garante a linha do dono (id 1) com o usuário do .env."""
    owner = db.session.get(User, OWNER_ID)
    username = current_app.config.get("OWNER_USERNAME") or "hunter"
    if owner is None:
        owner = User(id=OWNER_ID, username=username, role="owner")
        db.session.add(owner)
        db.session.commit()
    elif owner.username != username and _username_free(username, OWNER_ID):
        owner.username = username
        db.session.commit()
    return owner


def get_user(user_id: int | None) -> User | None:
    return db.session.get(User, user_id) if user_id else None


def authenticate(login: str, password: str) -> User | None:
    """Confere usuário/e-mail e senha. Devolve a conta ou None (nunca diz qual dos dois errou)."""
    login = (login or "").strip()
    cfg = current_app.config
    owner_hash = cfg.get("OWNER_PASSWORD_HASH", "")
    if owner_hash and hmac.compare_digest(login.encode(), (cfg.get("OWNER_USERNAME") or "").encode()):
        return _logged(ensure_owner()) if check_password_hash(owner_hash, password) else None
    user = db.session.scalar(select(User).where(
        (User.email == login.lower()) | (User.username == login), User.role == "tester"))
    if user is None or not user.active or not user.password_hash:
        check_password_hash(generate_password_hash("x"), password)  # mesmo tempo de resposta
        return None
    return _logged(user) if check_password_hash(user.password_hash, password) else None


def all_user_ids() -> list[int]:
    """Dono e usuários ativos (para comandos que passam por todos, ex.: `flask quests rollover`)."""
    ensure_owner()
    return list(db.session.scalars(select(User.id).where(User.active.is_(True)).order_by(User.id)))


def list_testers() -> list[User]:
    return list(db.session.scalars(select(User).where(User.role == "tester").order_by(User.created_at.desc())))


def invite_tester(email: str, name: str = "") -> tuple[User, str]:
    """Cadastra (ou renova o convite de) um usuário de teste. Devolve a conta e o código do link."""
    email = (email or "").strip().lower()
    if not _EMAIL.match(email):
        raise DomainError("Informe um e-mail válido.")
    user = db.session.scalar(select(User).where(User.email == email))
    if user is not None and user.is_owner:
        raise DomainError("Esse e-mail é do dono do sistema.")
    if user is None:
        user = User(email=email, username=_unique_username(email), role="tester", display_name=name.strip()[:80])
        db.session.add(user)
    elif name.strip():
        user.display_name = name.strip()[:80]
    code = secrets.token_urlsafe(24)
    user.invite_hash = _hash(code)
    user.invite_expires_at = time.now() + timedelta(days=INVITE_DAYS)
    user.active = True
    db.session.commit()
    return user, code


def user_for_invite(code: str) -> User | None:
    user = db.session.scalar(select(User).where(User.invite_hash == _hash(code or "")))
    if user is None or not user.active or not user.invite_expires_at or user.invite_expires_at < time.now():
        return None
    return user


def accept_invite(code: str, name: str, password: str) -> User:
    user = user_for_invite(code)
    if user is None:
        raise DomainError("Convite inválido ou vencido. Peça um novo link para quem te convidou.")
    if len(password or "") < MIN_PASSWORD:
        raise DomainError(f"A senha precisa de pelo menos {MIN_PASSWORD} caracteres.")
    user.password_hash = generate_password_hash(password)
    if name.strip():
        user.display_name = name.strip()[:80]
    user.invite_hash = None
    user.invite_expires_at = None
    return _logged(user)


def set_tester_active(user_id: int, active: bool) -> User:
    user = _tester(user_id)
    user.active = active
    db.session.commit()
    return user


def delete_tester(user_id: int) -> None:
    """Apaga a conta e todos os dados dela (todas as tabelas com user_id)."""
    user = _tester(user_id)
    tables = list(reversed(db.metadata.sorted_tables))
    # Tabelas de ligação (sem user_id): apaga as linhas que apontam para dados desse usuário.
    for table in tables:
        if "user_id" in table.c:
            continue
        for fk in table.foreign_keys:
            parent = fk.column.table
            if "user_id" in parent.c and parent.name != "users":
                owned = select(fk.column).where(parent.c.user_id == user.id)
                db.session.execute(table.delete().where(fk.parent.in_(owned)))
    for table in tables:
        if "user_id" in table.c and table.name != "users":
            db.session.execute(table.delete().where(table.c.user_id == user.id))
    db.session.delete(user)
    db.session.commit()


def _tester(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if user is None or user.is_owner:
        raise NotFoundError("Usuário de teste não encontrado.")
    return user


def _logged(user: User) -> User:
    user.last_login_at = time.now()
    db.session.commit()
    return user


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _username_free(username: str, except_id: int | None = None) -> bool:
    other = db.session.scalar(select(User).where(User.username == username))
    return other is None or other.id == except_id


def _unique_username(email: str) -> str:
    base = re.sub(r"[^a-z0-9._-]", "", email.split("@")[0].lower())[:40] or "hunter"
    candidate, n = base, 1
    while not _username_free(candidate) or candidate == (current_app.config.get("OWNER_USERNAME") or ""):
        n += 1
        candidate = f"{base}{n}"
    return candidate
