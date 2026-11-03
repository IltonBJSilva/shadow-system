"""hunter avatars: avatar generated from the player's photo

Revision ID: f6b2d4e8a913
Revises: e5a9c3d1f742
Create Date: 2026-11-03 17:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'f6b2d4e8a913'
down_revision = 'e5a9c3d1f742'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hunter_avatars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('style', sa.String(length=20), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('image', sa.LargeBinary(), nullable=False),
        sa.Column('photo', sa.LargeBinary(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_hunter_avatars_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_hunter_avatars')),
        sa.UniqueConstraint('user_id', name='uq_hunter_avatars_user'),
    )
    with op.batch_alter_table('hunter_avatars', schema=None) as batch_op:
        batch_op.create_index('ix_hunter_avatars_user_id', ['user_id'], unique=False)


def downgrade():
    op.drop_table('hunter_avatars')
