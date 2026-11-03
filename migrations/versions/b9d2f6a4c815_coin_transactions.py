"""coin transactions: time shop wallet

Revision ID: b9d2f6a4c815
Revises: a8c1e5f3b204
Create Date: 2026-11-03 19:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'b9d2f6a4c815'
down_revision = 'a8c1e5f3b204'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'coin_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=80), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_coin_transactions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_coin_transactions')),
    )
    with op.batch_alter_table('coin_transactions', schema=None) as batch_op:
        batch_op.create_index('ix_coin_transactions_created_at', ['created_at'], unique=False)
        batch_op.create_index('ix_coin_transactions_user_id', ['user_id'], unique=False)


def downgrade():
    op.drop_table('coin_transactions')
