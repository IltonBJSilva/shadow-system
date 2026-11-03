"""Finanças: valores em centavos, saldos, cartão, parcelas, recorrentes, orçamento, metas, relatórios,
missões financeiras e privacidade."""
from datetime import date, timedelta

import pytest

from app.core import accounts
from app.core.errors import DomainError
from app.core.tenancy import as_user
from app.modules.finance import missions, money, services as finance
from app.modules.finance.services import TxInput
from app.modules.hunter import services as hunter


@pytest.fixture
def setup(app):
    finance.ensure_defaults()
    checking = finance.accounts()[0]
    card = finance.save_account("Cartão", "credit_card", limit="3000")
    cats = {c.name: c for c in finance.categories()}
    return checking, card, cats


def _tx(kind, amount, account, category=None, day=None, **kw):
    return finance.add_transaction(TxInput(kind=kind, amount=amount, description=kw.pop("desc", "x"),
                                           day=day or date.today(), account_id=account.id,
                                           category_id=category.id if category else None, **kw))


@pytest.mark.parametrize("text,cents", [("1.234,56", 123456), ("R$ 10", 1000), ("9.9", 990), ("0,05", 5), (2500, 2500)])
def test_money_parse(text, cents):
    assert money.parse(text) == cents


def test_money_rejects_bad_values():
    for bad in ("", "abc", "-5", "0"):
        with pytest.raises(DomainError):
            money.parse(bad)
    assert money.brl(123456) == "R$ 1.234,56" and money.brl(-50) == "-R$ 0,50"


def test_balance_income_expense_and_transfer(setup):
    checking, card, cats = setup
    savings = finance.save_account("Reserva", "savings", opening="100,00")
    _tx("income", "3000", checking, cats["Salário"])
    _tx("expense", "45,90", checking, cats["Alimentação"])
    _tx("transfer", "500", checking, to_account_id=savings.id)
    assert finance.balance(checking) == 300000 - 4590 - 50000
    assert finance.balance(savings) == 10000 + 50000


def test_credit_card_invoice_and_payment(setup):
    checking, card, cats = setup
    _tx("expense", "200", card, cats["Lazer"])
    assert finance.balance(card) == 20000
    _tx("transfer", "200", checking, to_account_id=card.id)  # pagar a fatura
    assert finance.balance(card) == 0 and finance.balance(checking) == -20000


def test_installments_split_across_months(setup):
    checking, card, cats = setup
    rows = _tx("expense", "100", card, cats["Lazer"], installments=3, desc="Fone")
    assert [r.amount_cents for r in rows] == [3334, 3333, 3333]
    assert [r.description for r in rows][0] == "Fone (1/3)"
    assert len({r.day.month for r in rows}) == 3


def test_category_must_match_kind(setup):
    checking, _, cats = setup
    with pytest.raises(DomainError):
        _tx("income", "10", checking, cats["Alimentação"])


def test_recurring_generates_each_month_once(setup):
    checking, _, cats = setup
    start = date.today().replace(day=1) - timedelta(days=40)
    month = finance.month_key(start)
    finance.save_recurring("expense", "1200", "Aluguel", 1, checking.id, cats["Moradia"].id, month)
    first = len(finance.transactions(finance.month_key(date.today())))
    assert finance.generate_recurring() == 0  # idempotente
    assert first == 1
    assert len(finance.transactions(month)) == 1


def test_summary_budget_and_history(setup):
    checking, _, cats = setup
    _tx("income", "1000", checking, cats["Salário"])
    _tx("expense", "300", checking, cats["Alimentação"])
    _tx("expense", "50", checking, cats["Lazer"])
    finance.save_budget(cats["Alimentação"].id, "250")
    month = finance.month_key(date.today())
    s = finance.summary(month)
    assert (s.income, s.expense, s.net) == (100000, 35000, 65000)
    assert s.by_category[0][0] == "Alimentação"
    [status] = finance.budgets(month)
    assert status.over and status.percent == 120
    assert len(finance.history(month, 6)) == 6


def test_goal_with_manual_contributions_and_account(setup):
    checking, _, cats = setup
    goal = finance.save_goal("Reserva", "1000")
    finance.contribute(goal.id, "400")
    savings = finance.save_account("Poupança", "savings", opening="2000")
    finance.save_goal("Viagem", "1500", account_id=savings.id)
    statuses = {g.goal.name: g for g in finance.goals()}
    assert statuses["Reserva"].percent == 40 and statuses["Viagem"].reached


def test_daily_mission_once_per_day(setup):
    before = hunter.get_hunter().total_xp
    missions.claim_daily()
    with pytest.raises(DomainError):
        missions.claim_daily()
    assert hunter.get_hunter().total_xp == before + missions.XP["daily"]


def test_goal_mission_pays_once(setup):
    goal = finance.save_goal("Reserva", "100")
    finance.contribute(goal.id, "100")
    first = missions.evaluate()
    assert any("Reserva" in m for m, _ in first)
    assert not any("Reserva" in m for m, _ in missions.evaluate())


def test_week_mission_needs_real_logging(setup):
    checking, _, cats = setup
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    assert not any("Semana" in m for m, _ in missions.evaluate(today))  # sem registros: nada de XP por "não gastar"
    for i in range(5):
        _tx("expense", "20", checking, cats["Alimentação"], day=last_monday + timedelta(days=i))
    assert any("Semana" in m for m, _ in missions.evaluate(today))


def test_finance_is_private_per_user(setup, client):
    checking, _, cats = setup
    _tx("income", "5000", checking, cats["Salário"], desc="Salário secreto")
    user, code = accounts.invite_tester("fin@example.com")
    accounts.accept_invite(code, "F", "12345678")
    with as_user(user.id):
        finance.ensure_defaults()
        assert all(t.description != "Salário secreto" for t in finance.transactions(finance.month_key(date.today())))
        with pytest.raises(Exception):
            finance.delete_transaction(1)
    with client.session_transaction() as session:
        session["uid"] = user.id
    assert "Salário secreto" not in client.get("/financas/lancamentos").get_data(as_text=True)
    assert "Salário secreto" not in client.get("/arena/feed").get_data(as_text=True)


def test_pages_and_quick_add_route(setup, client):
    checking, _, cats = setup
    response = client.post("/financas/lancamentos", data={"kind": "expense", "amount": "12,50", "description": "Café",
                                                          "account_id": checking.id, "category_id": cats["Alimentação"].id})
    assert response.status_code == 302
    page = client.get("/financas/").get_data(as_text=True)
    assert "Café" in page and "R$ 12,50" in page and "Missões financeiras" in page
    assert client.get("/financas/configurar").status_code == 200
