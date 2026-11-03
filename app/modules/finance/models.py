"""Tabelas de finanças pessoais. Valores em centavos (inteiros) para nunca errar arredondamento.

Tudo é privado do usuário (user_id) e nenhum outro módulo lê estas tabelas: Arena e feed não têm
acesso a dados financeiros.
"""
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import time
from app.core.models import UserOwnedMixin
from app.extensions import db


class FinanceAccount(UserOwnedMixin, db.Model):
    """Conta (corrente, poupança, carteira, investimento) ou cartão de crédito."""

    __tablename__ = "finance_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    kind: Mapped[str] = mapped_column(String(12), default="checking", nullable=False)
    opening_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    limit_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # cartões
    closing_day: Mapped[int | None] = mapped_column(Integer, nullable=True)        # cartões
    due_day: Mapped[int | None] = mapped_column(Integer, nullable=True)            # cartões
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FinanceCategory(UserOwnedMixin, db.Model):
    __tablename__ = "finance_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    kind: Mapped[str] = mapped_column(String(8), nullable=False)  # income | expense
    color: Mapped[str] = mapped_column(String(9), default="#38bdf8", nullable=False)
    essential: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # não essencial: lazer, assinaturas...


class FinanceTransaction(UserOwnedMixin, db.Model):
    __tablename__ = "finance_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(8), nullable=False)  # income | expense | transfer
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(120), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("finance_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    to_account_id: Mapped[int | None] = mapped_column(ForeignKey("finance_accounts.id", ondelete="CASCADE"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("finance_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    recurring_id: Mapped[int | None] = mapped_column(ForeignKey("finance_recurring.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)

    account: Mapped[FinanceAccount] = relationship(foreign_keys=[account_id])
    to_account: Mapped[FinanceAccount | None] = relationship(foreign_keys=[to_account_id])
    category: Mapped[FinanceCategory | None] = relationship()

    __table_args__ = (CheckConstraint("amount_cents > 0", name="amount_positive"),)


class FinanceRecurring(UserOwnedMixin, db.Model):
    """Receita ou despesa que se repete todo mês (salário, aluguel, assinatura)."""

    __tablename__ = "finance_recurring"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(8), nullable=False)  # income | expense
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(120), nullable=False)
    day_of_month: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("finance_accounts.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("finance_categories.id", ondelete="SET NULL"), nullable=True)
    start_month: Mapped[str] = mapped_column(String(7), nullable=False)       # "2026-11"
    last_month: Mapped[str | None] = mapped_column(String(7), nullable=True)  # último mês gerado
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="recurring_amount_positive"),
        CheckConstraint("day_of_month BETWEEN 1 AND 28", name="recurring_day_range"),
    )


class FinanceBudget(UserOwnedMixin, db.Model):
    """Orçamento mensal de uma categoria de despesa (vale para todos os meses)."""

    __tablename__ = "finance_budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("finance_categories.id", ondelete="CASCADE"), nullable=False, unique=False)
    limit_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    category: Mapped[FinanceCategory] = relationship()

    __table_args__ = (
        CheckConstraint("limit_cents > 0", name="budget_limit_positive"),
        db.UniqueConstraint("user_id", "category_id", name="uq_finance_budgets_user_category"),
    )


class FinanceGoal(UserOwnedMixin, db.Model):
    """Meta financeira (reserva, viagem...). O valor guardado é o saldo de uma conta ou aportes manuais."""

    __tablename__ = "finance_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    target_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    saved_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("finance_accounts.id", ondelete="SET NULL"), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=time.now, nullable=False)

    account: Mapped[FinanceAccount | None] = relationship()

    __table_args__ = (CheckConstraint("target_cents > 0", name="goal_target_positive"),)
