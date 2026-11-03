"""Regras de finanças: contas e cartões, transações, recorrentes, orçamentos, metas, relatórios e
missões financeiras (XP com limites, nunca por gastar).

Saldo de conta = saldo inicial + receitas - despesas + transferências recebidas - enviadas.
Cartão de crédito: o "saldo" é a fatura em aberto (despesas no cartão menos pagamentos recebidos).
"""
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select

from app.core import settings, time
from app.core.errors import DomainError, NotFoundError
from app.extensions import db

from . import money
from .models import (FinanceAccount, FinanceBudget, FinanceCategory, FinanceGoal, FinanceRecurring,
                     FinanceTransaction)

ACCOUNT_KINDS = {"checking": "Conta corrente", "savings": "Poupança / reserva", "cash": "Carteira",
                 "investment": "Investimentos", "credit_card": "Cartão de crédito"}
TX_KINDS = {"expense": "Despesa", "income": "Receita", "transfer": "Transferência / pagamento de fatura"}
# (nome, tipo, cor, essencial)
DEFAULT_CATEGORIES = [
    ("Alimentação", "expense", "#f97316", True), ("Transporte", "expense", "#38bdf8", True),
    ("Moradia", "expense", "#a78bfa", True), ("Faculdade", "expense", "#22d3ee", True),
    ("Saúde", "expense", "#34d399", True), ("Academia", "expense", "#fb7185", True),
    ("Lazer", "expense", "#f472b6", False), ("Assinaturas", "expense", "#c084fc", False),
    ("Investimentos", "expense", "#facc15", True), ("Outras despesas", "expense", "#94a3b8", True),
    ("Salário", "income", "#34d399", True), ("Freelance", "income", "#22d3ee", True),
    ("Outras receitas", "income", "#a3e635", True),
]
MONTHLY_SAVING_KEY = "finance.monthly_saving_cents"


def month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def month_range(key: str) -> tuple[date, date]:
    """Primeiro dia do mês e primeiro dia do mês seguinte."""
    try:
        year, month = int(key[:4]), int(key[5:7])
        start = date(year, month, 1)
    except (ValueError, IndexError) as exc:
        raise DomainError("Mês inválido.") from exc
    end = date(year + (month == 12), month % 12 + 1, 1)
    return start, end


def shift_month(key: str, delta: int) -> str:
    start, _ = month_range(key)
    index = start.year * 12 + start.month - 1 + delta
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


# ---------- Cadastros ----------

def ensure_defaults() -> None:
    """Categorias padrão e uma conta inicial na primeira vez."""
    if not db.session.scalar(select(func.count(FinanceCategory.id))):
        for name, kind, color, essential in DEFAULT_CATEGORIES:
            db.session.add(FinanceCategory(name=name, kind=kind, color=color, essential=essential))
    if not db.session.scalar(select(func.count(FinanceAccount.id))):
        db.session.add(FinanceAccount(name="Conta principal", kind="checking"))
    db.session.commit()


def accounts(active_only: bool = True) -> list[FinanceAccount]:
    query = select(FinanceAccount).order_by(FinanceAccount.kind == "credit_card", FinanceAccount.name)
    if active_only:
        query = query.where(FinanceAccount.active.is_(True))
    return list(db.session.scalars(query))


def categories(kind: str | None = None) -> list[FinanceCategory]:
    query = select(FinanceCategory).order_by(FinanceCategory.kind, FinanceCategory.name)
    if kind:
        query = query.where(FinanceCategory.kind == kind)
    return list(db.session.scalars(query))


def save_account(name: str, kind: str, opening: str = "0", limit: str = "0", closing_day: int | None = None,
                 due_day: int | None = None, account_id: int | None = None) -> FinanceAccount:
    if not name.strip():
        raise DomainError("Dê um nome para a conta.")
    if kind not in ACCOUNT_KINDS:
        raise DomainError("Tipo de conta inválido.")
    for day in (closing_day, due_day):
        if day is not None and not 1 <= day <= 31:
            raise DomainError("Dia de fechamento/vencimento deve ser de 1 a 31.")
    account = _get(FinanceAccount, account_id) if account_id else FinanceAccount()
    account.name, account.kind = name.strip()[:60], kind
    account.opening_cents = money.parse(opening or "0", allow_zero=True) if kind != "credit_card" else 0
    account.limit_cents = money.parse(limit or "0", allow_zero=True) if kind == "credit_card" else 0
    account.closing_day, account.due_day = (closing_day, due_day) if kind == "credit_card" else (None, None)
    db.session.add(account)
    db.session.commit()
    return account


def archive_account(account_id: int) -> None:
    _get(FinanceAccount, account_id).active = False
    db.session.commit()


def save_category(name: str, kind: str, color: str = "#38bdf8", essential: bool = True,
                  category_id: int | None = None) -> FinanceCategory:
    if not name.strip():
        raise DomainError("Dê um nome para a categoria.")
    if kind not in ("income", "expense"):
        raise DomainError("Tipo de categoria inválido.")
    clash = db.session.scalar(select(FinanceCategory).where(
        func.lower(FinanceCategory.name) == name.strip().lower(), FinanceCategory.kind == kind,
        FinanceCategory.id != (category_id or 0)))
    if clash:
        raise DomainError("Já existe uma categoria com esse nome.")
    category = _get(FinanceCategory, category_id) if category_id else FinanceCategory()
    category.name, category.kind, category.color, category.essential = name.strip()[:40], kind, color, essential
    db.session.add(category)
    db.session.commit()
    return category


# ---------- Transações ----------

@dataclass
class TxInput:
    kind: str
    amount: str
    description: str
    day: date
    account_id: int
    category_id: int | None = None
    to_account_id: int | None = None
    installments: int = 1  # compra parcelada no cartão: divide em N meses


def add_transaction(data: TxInput) -> list[FinanceTransaction]:
    if data.kind not in TX_KINDS:
        raise DomainError("Tipo de lançamento inválido.")
    if not data.description.strip():
        raise DomainError("Descreva o lançamento.")
    if not 1 <= data.installments <= 48:
        raise DomainError("Parcelas: de 1 a 48.")
    account = _get(FinanceAccount, data.account_id)
    cents = money.parse(data.amount)
    category = _get(FinanceCategory, data.category_id) if data.category_id else None
    to_account = None
    if data.kind == "transfer":
        to_account = _get(FinanceAccount, data.to_account_id) if data.to_account_id else None
        if to_account is None or to_account.id == account.id:
            raise DomainError("Escolha a conta de destino (diferente da origem).")
        category = None
    elif category is not None and category.kind != data.kind:
        raise DomainError("A categoria não combina com o tipo do lançamento.")
    if data.day > time.today() + timedelta(days=366):
        raise DomainError("Data muito no futuro.")
    parts = _split(cents, data.installments)
    rows = []
    for index, part in enumerate(parts):
        label = data.description.strip()[:100] + (f" ({index + 1}/{len(parts)})" if len(parts) > 1 else "")
        start, _ = month_range(shift_month(month_key(data.day), index))
        day = start.replace(day=min(data.day.day, 28)) if index else data.day
        rows.append(FinanceTransaction(kind=data.kind, amount_cents=part, description=label, day=day, account_id=account.id,
                                       category_id=category.id if category else None,
                                       to_account_id=to_account.id if to_account else None))
    db.session.add_all(rows)
    db.session.commit()
    return rows


def delete_transaction(tx_id: int) -> None:
    db.session.delete(_get(FinanceTransaction, tx_id))
    db.session.commit()


def transactions(month: str, account_id: int | None = None, category_id: int | None = None,
                 kind: str | None = None, search: str = "") -> list[FinanceTransaction]:
    start, end = month_range(month)
    query = (select(FinanceTransaction).where(FinanceTransaction.day >= start, FinanceTransaction.day < end)
             .order_by(FinanceTransaction.day.desc(), FinanceTransaction.id.desc()))
    if account_id:
        query = query.where((FinanceTransaction.account_id == account_id) | (FinanceTransaction.to_account_id == account_id))
    if category_id:
        query = query.where(FinanceTransaction.category_id == category_id)
    if kind in TX_KINDS:
        query = query.where(FinanceTransaction.kind == kind)
    if search.strip():
        query = query.where(func.lower(FinanceTransaction.description).like(f"%{search.strip().lower()}%"))
    return list(db.session.scalars(query))


# ---------- Recorrentes ----------

def save_recurring(kind: str, amount: str, description: str, day_of_month: int, account_id: int,
                   category_id: int | None, start_month: str) -> FinanceRecurring:
    if kind not in ("income", "expense"):
        raise DomainError("Recorrente é receita ou despesa.")
    if not 1 <= day_of_month <= 28:
        raise DomainError("Dia do mês de 1 a 28.")
    month_range(start_month)
    _get(FinanceAccount, account_id)
    row = FinanceRecurring(kind=kind, amount_cents=money.parse(amount), description=description.strip()[:120] or "Recorrente",
                           day_of_month=day_of_month, account_id=account_id, category_id=category_id or None,
                           start_month=start_month)
    db.session.add(row)
    db.session.commit()
    generate_recurring()
    return row


def stop_recurring(recurring_id: int) -> None:
    _get(FinanceRecurring, recurring_id).active = False
    db.session.commit()


def recurring_list() -> list[FinanceRecurring]:
    return list(db.session.scalars(select(FinanceRecurring).where(FinanceRecurring.active.is_(True))
                                   .order_by(FinanceRecurring.day_of_month)))


def generate_recurring(today: date | None = None) -> int:
    """Lança as recorrentes de todos os meses até o atual que ainda não foram lançados. Idempotente."""
    today = today or time.today()
    current = month_key(today)
    created = 0
    for row in recurring_list():
        month = shift_month(row.last_month, 1) if row.last_month else row.start_month
        while month <= current:
            start, _ = month_range(month)
            day = start.replace(day=row.day_of_month)
            if day <= today:
                db.session.add(FinanceTransaction(kind=row.kind, amount_cents=row.amount_cents, description=row.description,
                                                  day=day, account_id=row.account_id, category_id=row.category_id,
                                                  recurring_id=row.id))
                row.last_month = month
                created += 1
            month = shift_month(month, 1)
    if created:
        db.session.commit()
    return created


# ---------- Saldos e relatórios ----------

def balance(account: FinanceAccount, until: date | None = None) -> int:
    """Saldo da conta (ou fatura em aberto do cartão) até a data, inclusive."""
    until = until or time.today()

    def total(kind: str, column) -> int:
        return int(db.session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount_cents), 0)).where(
            FinanceTransaction.kind == kind, column == account.id, FinanceTransaction.day <= until)) or 0)

    income = total("income", FinanceTransaction.account_id)
    expense = total("expense", FinanceTransaction.account_id)
    sent = total("transfer", FinanceTransaction.account_id)
    received = total("transfer", FinanceTransaction.to_account_id)
    if account.kind == "credit_card":
        return expense - received - income  # fatura: o que foi gasto menos pagamentos/estornos
    return account.opening_cents + income - expense + received - sent


@dataclass(frozen=True)
class MonthSummary:
    month: str
    income: int
    expense: int
    by_category: list[tuple[str, str, int]]  # (nome, cor, centavos), despesas

    @property
    def net(self) -> int:
        return self.income - self.expense


def summary(month: str) -> MonthSummary:
    start, end = month_range(month)
    rows = db.session.execute(
        select(FinanceTransaction.kind, FinanceCategory.name, FinanceCategory.color, func.sum(FinanceTransaction.amount_cents))
        .outerjoin(FinanceCategory, FinanceCategory.id == FinanceTransaction.category_id)
        .where(FinanceTransaction.day >= start, FinanceTransaction.day < end, FinanceTransaction.kind != "transfer")
        .group_by(FinanceTransaction.kind, FinanceCategory.name, FinanceCategory.color)).all()
    income = sum(int(t) for kind, _, _, t in rows if kind == "income")
    expense = sum(int(t) for kind, _, _, t in rows if kind == "expense")
    by_category = sorted(((name or "Sem categoria", color or "#64748b", int(t)) for kind, name, color, t in rows
                          if kind == "expense"), key=lambda r: r[2], reverse=True)
    return MonthSummary(month, income, expense, by_category)


def history(month: str, months: int = 6) -> list[MonthSummary]:
    return [summary(shift_month(month, -i)) for i in reversed(range(months))]


@dataclass(frozen=True)
class BudgetStatus:
    budget_id: int
    category: str
    color: str
    limit: int
    spent: int

    @property
    def percent(self) -> int:
        return round(100 * self.spent / self.limit) if self.limit else 0

    @property
    def over(self) -> bool:
        return self.spent > self.limit


def budgets(month: str) -> list[BudgetStatus]:
    spent = {}
    start, end = month_range(month)
    for category_id, total in db.session.execute(
            select(FinanceTransaction.category_id, func.sum(FinanceTransaction.amount_cents))
            .where(FinanceTransaction.kind == "expense", FinanceTransaction.day >= start, FinanceTransaction.day < end)
            .group_by(FinanceTransaction.category_id)):
        spent[category_id] = int(total or 0)
    rows = db.session.scalars(select(FinanceBudget))
    return [BudgetStatus(b.id, b.category.name, b.category.color, b.limit_cents, spent.get(b.category_id, 0)) for b in rows]


def save_budget(category_id: int, limit: str) -> FinanceBudget:
    category = _get(FinanceCategory, category_id)
    if category.kind != "expense":
        raise DomainError("Orçamento é para categorias de despesa.")
    row = db.session.scalar(select(FinanceBudget).where(FinanceBudget.category_id == category_id)) or FinanceBudget(category_id=category_id)
    row.limit_cents = money.parse(limit)
    db.session.add(row)
    db.session.commit()
    return row


def delete_budget(budget_id: int) -> None:
    db.session.delete(_get(FinanceBudget, budget_id))
    db.session.commit()


# ---------- Metas ----------

@dataclass(frozen=True)
class GoalStatus:
    goal: FinanceGoal
    saved: int

    @property
    def percent(self) -> int:
        return min(100, round(100 * self.saved / self.goal.target_cents))

    @property
    def reached(self) -> bool:
        return self.saved >= self.goal.target_cents


def goals() -> list[GoalStatus]:
    rows = db.session.scalars(select(FinanceGoal).order_by(FinanceGoal.created_at))
    return [GoalStatus(g, max(0, balance(g.account)) if g.account else g.saved_cents) for g in rows]


def save_goal(name: str, target: str, account_id: int | None = None, deadline: date | None = None) -> FinanceGoal:
    if not name.strip():
        raise DomainError("Dê um nome para a meta.")
    if account_id:
        _get(FinanceAccount, account_id)
    goal = FinanceGoal(name=name.strip()[:80], target_cents=money.parse(target), account_id=account_id or None, deadline=deadline)
    db.session.add(goal)
    db.session.commit()
    return goal


def contribute(goal_id: int, amount: str) -> FinanceGoal:
    goal = _get(FinanceGoal, goal_id)
    if goal.account_id:
        raise DomainError("Esta meta acompanha o saldo de uma conta: lance uma transferência para ela.")
    goal.saved_cents += money.parse(amount)
    db.session.commit()
    return goal


def delete_goal(goal_id: int) -> None:
    db.session.delete(_get(FinanceGoal, goal_id))
    db.session.commit()


def monthly_saving_target() -> int:
    return int(settings.get_setting(MONTHLY_SAVING_KEY, 0) or 0)


def set_monthly_saving_target(amount: str) -> None:
    settings.set_setting(MONTHLY_SAVING_KEY, money.parse(amount or "0", allow_zero=True))


def logged_days(start: date, end: date) -> set[date]:
    """Dias (start..end, inclusive) com pelo menos um lançamento registrado."""
    return set(db.session.scalars(select(FinanceTransaction.day).distinct().where(
        FinanceTransaction.day >= start, FinanceTransaction.day <= end)))


def nonessential_spent(start: date, end: date) -> int:
    return int(db.session.scalar(select(func.coalesce(func.sum(FinanceTransaction.amount_cents), 0))
                                 .join(FinanceCategory, FinanceCategory.id == FinanceTransaction.category_id)
                                 .where(FinanceTransaction.kind == "expense", FinanceCategory.essential.is_(False),
                                        FinanceTransaction.day >= start, FinanceTransaction.day <= end)) or 0)


# ---------- Internos ----------

def _get(model, row_id):
    row = db.session.get(model, row_id) if row_id else None
    if row is None:
        raise NotFoundError("Registro financeiro não encontrado.")
    return row


def _split(cents: int, parts: int) -> list[int]:
    base, rest = divmod(cents, parts)
    return [base + (1 if i < rest else 0) for i in range(parts)]
