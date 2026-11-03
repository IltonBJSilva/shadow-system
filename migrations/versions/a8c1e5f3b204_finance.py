"""finance: accounts, categories, transactions, recurring, budgets and goals

Revision ID: a8c1e5f3b204
Revises: f6b2d4e8a913
Create Date: 2026-11-03 18:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'a8c1e5f3b204'
down_revision = 'f6b2d4e8a913'
branch_labels = None
depends_on = None


def _owner(table):
    return [sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f(f'fk_{table}_user_id_users'), ondelete='CASCADE')]


def _index(table, *columns):
    with op.batch_alter_table(table, schema=None) as batch_op:
        for column in columns:
            batch_op.create_index(f'ix_{table}_{column}', [column], unique=False)


def upgrade():
    op.create_table(
        'finance_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('kind', sa.String(length=12), nullable=False),
        sa.Column('opening_cents', sa.Integer(), nullable=False),
        sa.Column('limit_cents', sa.Integer(), nullable=False),
        sa.Column('closing_day', sa.Integer(), nullable=True),
        sa.Column('due_day', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        *_owner('finance_accounts'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_finance_accounts')),
    )
    _index('finance_accounts', 'user_id')
    op.create_table(
        'finance_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=40), nullable=False),
        sa.Column('kind', sa.String(length=8), nullable=False),
        sa.Column('color', sa.String(length=9), nullable=False),
        sa.Column('essential', sa.Boolean(), nullable=False),
        *_owner('finance_categories'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_finance_categories')),
    )
    _index('finance_categories', 'user_id')
    op.create_table(
        'finance_recurring',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=8), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=120), nullable=False),
        sa.Column('day_of_month', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('start_month', sa.String(length=7), nullable=False),
        sa.Column('last_month', sa.String(length=7), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        *_owner('finance_recurring'),
        sa.CheckConstraint('amount_cents > 0', name=op.f('ck_finance_recurring_recurring_amount_positive')),
        sa.CheckConstraint('day_of_month BETWEEN 1 AND 28', name=op.f('ck_finance_recurring_recurring_day_range')),
        sa.ForeignKeyConstraint(['account_id'], ['finance_accounts.id'], name=op.f('fk_finance_recurring_account_id_finance_accounts'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['finance_categories.id'], name=op.f('fk_finance_recurring_category_id_finance_categories'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_finance_recurring')),
    )
    _index('finance_recurring', 'user_id')
    op.create_table(
        'finance_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=8), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=120), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('to_account_id', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('recurring_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        *_owner('finance_transactions'),
        sa.CheckConstraint('amount_cents > 0', name=op.f('ck_finance_transactions_amount_positive')),
        sa.ForeignKeyConstraint(['account_id'], ['finance_accounts.id'], name=op.f('fk_finance_transactions_account_id_finance_accounts'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_account_id'], ['finance_accounts.id'], name=op.f('fk_finance_transactions_to_account_id_finance_accounts'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['finance_categories.id'], name=op.f('fk_finance_transactions_category_id_finance_categories'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recurring_id'], ['finance_recurring.id'], name=op.f('fk_finance_transactions_recurring_id_finance_recurring'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_finance_transactions')),
    )
    _index('finance_transactions', 'user_id', 'day', 'account_id', 'category_id')
    op.create_table(
        'finance_budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('limit_cents', sa.Integer(), nullable=False),
        *_owner('finance_budgets'),
        sa.CheckConstraint('limit_cents > 0', name=op.f('ck_finance_budgets_budget_limit_positive')),
        sa.ForeignKeyConstraint(['category_id'], ['finance_categories.id'], name=op.f('fk_finance_budgets_category_id_finance_categories'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_finance_budgets')),
        sa.UniqueConstraint('user_id', 'category_id', name='uq_finance_budgets_user_category'),
    )
    _index('finance_budgets', 'user_id')
    op.create_table(
        'finance_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('target_cents', sa.Integer(), nullable=False),
        sa.Column('saved_cents', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        *_owner('finance_goals'),
        sa.CheckConstraint('target_cents > 0', name=op.f('ck_finance_goals_goal_target_positive')),
        sa.ForeignKeyConstraint(['account_id'], ['finance_accounts.id'], name=op.f('fk_finance_goals_account_id_finance_accounts'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_finance_goals')),
    )
    _index('finance_goals', 'user_id')


def downgrade():
    for table in ('finance_goals', 'finance_budgets', 'finance_transactions', 'finance_recurring',
                  'finance_categories', 'finance_accounts'):
        op.drop_table(table)
