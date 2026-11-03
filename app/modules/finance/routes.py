"""Telas de Finanças: painel do mês, lançamentos e configuração (contas, categorias, recorrentes,
orçamentos e metas)."""
from datetime import date

from flask import flash, redirect, render_template, request, url_for

from app.core import time
from app.core.errors import DomainError
from app.core.http import redirect_back

from . import bp, missions, money, services


@bp.app_template_filter("brl")
def brl(cents):
    return money.brl(cents)


def _month() -> str:
    month = request.values.get("mes") or services.month_key(time.today())
    services.month_range(month)  # valida
    return month


def _int(name: str) -> int | None:
    value = request.form.get(name, "").strip()
    return int(value) if value.isdigit() else None


def _date(name: str) -> date | None:
    value = request.form.get(name, "").strip()
    try:
        return date.fromisoformat(value) if value else None
    except ValueError as exc:
        raise DomainError("Data inválida.") from exc


@bp.get("/")
def index():
    services.ensure_defaults()
    services.generate_recurring()
    for message, category in missions.evaluate():
        flash(message, category)
    month = _month()
    accounts = services.accounts()
    history = services.history(month)
    return render_template(
        "finance/index.html", month=month, prev_month=services.shift_month(month, -1),
        next_month=services.shift_month(month, 1), summary=history[-1], history=history,
        peak=max([max(m.income, m.expense) for m in history] + [1]),
        balances=[(a, services.balance(a)) for a in accounts], budgets=services.budgets(month),
        goals=services.goals(), missions=missions.board(), accounts=accounts,
        categories=services.categories(), recent=services.transactions(month)[:12], kinds=services.TX_KINDS,
        today=time.today(),
    )


@bp.get("/lancamentos")
def transactions():
    services.ensure_defaults()
    month = _month()
    filters = {"account_id": request.args.get("conta", type=int), "category_id": request.args.get("categoria", type=int),
               "kind": request.args.get("tipo") or None, "search": request.args.get("busca", "")}
    rows = services.transactions(month, **filters)
    return render_template("finance/transactions.html", month=month, rows=rows, filters=filters,
                           accounts=services.accounts(active_only=False), categories=services.categories(),
                           kinds=services.TX_KINDS, prev_month=services.shift_month(month, -1),
                           next_month=services.shift_month(month, 1),
                           total_in=sum(r.amount_cents for r in rows if r.kind == "income"),
                           total_out=sum(r.amount_cents for r in rows if r.kind == "expense"))


@bp.post("/lancamentos")
def add_transaction():
    try:
        rows = services.add_transaction(services.TxInput(
            kind=request.form.get("kind", "expense"), amount=request.form.get("amount", ""),
            description=request.form.get("description", ""), day=_date("day") or time.today(),
            account_id=_int("account_id") or 0, category_id=_int("category_id"), to_account_id=_int("to_account_id"),
            installments=_int("installments") or 1))
        flash(f"Lançado: {rows[0].description}" + (f" em {len(rows)} parcelas." if len(rows) > 1 else "."), "success")
    except DomainError as exc:
        flash(str(exc), "error")
    return redirect_back(url_for("finance.index"))


@bp.post("/lancamentos/<int:tx_id>/apagar")
def delete_transaction(tx_id: int):
    services.delete_transaction(tx_id)
    flash("Lançamento apagado.", "info")
    return redirect_back(url_for("finance.transactions"))


@bp.post("/missoes/diaria")
def claim_daily():
    try:
        for message, category in services_award_messages(missions.claim_daily()):
            flash(message, category)
    except DomainError as exc:
        flash(str(exc), "info")
    return redirect(url_for("finance.index"))


def services_award_messages(result):
    from app.modules.hunter import services as hunter

    return hunter.award_messages(result)


@bp.get("/configurar")
def settings():
    services.ensure_defaults()
    return render_template("finance/settings.html", accounts=services.accounts(active_only=False),
                           account_kinds=services.ACCOUNT_KINDS, categories=services.categories(),
                           recurring=services.recurring_list(), budgets=services.budgets(services.month_key(time.today())),
                           goals=services.goals(), saving_target=services.monthly_saving_target(),
                           this_month=services.month_key(time.today()))


@bp.post("/configurar/<what>")
def save(what: str):
    form = request.form
    try:
        if what == "conta":
            services.save_account(form.get("name", ""), form.get("kind", "checking"), form.get("opening", "0"),
                                  form.get("limit", "0"), _int("closing_day"), _int("due_day"))
        elif what == "arquivar-conta":
            services.archive_account(_int("id") or 0)
        elif what == "categoria":
            services.save_category(form.get("name", ""), form.get("kind", "expense"), form.get("color", "#38bdf8"),
                                   form.get("essential") == "1")
        elif what == "recorrente":
            services.save_recurring(form.get("kind", "expense"), form.get("amount", ""), form.get("description", ""),
                                    _int("day_of_month") or 1, _int("account_id") or 0, _int("category_id"),
                                    form.get("start_month") or services.month_key(time.today()))
        elif what == "parar-recorrente":
            services.stop_recurring(_int("id") or 0)
        elif what == "orcamento":
            services.save_budget(_int("category_id") or 0, form.get("limit", ""))
        elif what == "apagar-orcamento":
            services.delete_budget(_int("id") or 0)
        elif what == "meta":
            services.save_goal(form.get("name", ""), form.get("target", ""), _int("account_id"), _date("deadline"))
        elif what == "aporte":
            services.contribute(_int("id") or 0, form.get("amount", ""))
        elif what == "apagar-meta":
            services.delete_goal(_int("id") or 0)
        elif what == "economia":
            services.set_monthly_saving_target(form.get("amount", "0"))
        else:
            raise DomainError("Ação desconhecida.")
        flash("Salvo.", "success")
    except DomainError as exc:
        flash(str(exc), "error")
    return redirect(url_for("finance.settings") + f"#{what}")
