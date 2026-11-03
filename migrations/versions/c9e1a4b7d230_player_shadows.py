"""player shadows: recruited shadows

Revision ID: c9e1a4b7d230
Revises: b3d8f2a6c915
Create Date: 2026-11-03 14:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'c9e1a4b7d230'
down_revision = 'b3d8f2a6c915'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'player_shadows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shadow_key', sa.String(length=40), nullable=False),
        sa.Column('recruited_at', sa.DateTime(), nullable=False),
        sa.Column('proof', sa.String(length=300), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_player_shadows_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_player_shadows')),
        sa.UniqueConstraint('user_id', 'shadow_key', name='uq_player_shadows_user_shadow'),
    )
    with op.batch_alter_table('player_shadows', schema=None) as batch_op:
        batch_op.create_index('ix_player_shadows_user_id', ['user_id'], unique=False)


def downgrade():
    op.drop_table('player_shadows')
