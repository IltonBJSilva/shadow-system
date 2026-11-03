"""player items: equipment inventory

Revision ID: b3d8f2a6c915
Revises: a7c4e1f9b302
Create Date: 2026-11-03 13:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'b3d8f2a6c915'
down_revision = 'a7c4e1f9b302'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'player_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_key', sa.String(length=40), nullable=False),
        sa.Column('equipped', sa.Boolean(), nullable=False),
        sa.Column('source', sa.String(length=120), nullable=False),
        sa.Column('acquired_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_player_items_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_player_items')),
        sa.UniqueConstraint('user_id', 'item_key', name='uq_player_items_user_item'),
    )
    with op.batch_alter_table('player_items', schema=None) as batch_op:
        batch_op.create_index('ix_player_items_user_id', ['user_id'], unique=False)


def downgrade():
    op.drop_table('player_items')
