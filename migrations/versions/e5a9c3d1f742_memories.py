"""memories: visual diary of completed activities

Revision ID: e5a9c3d1f742
Revises: d4f7b2c8e561
Create Date: 2026-11-03 16:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'e5a9c3d1f742'
down_revision = 'd4f7b2c8e561'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quest_id', sa.Integer(), nullable=True),
        sa.Column('quest_title', sa.String(length=160), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('specialty', sa.String(length=20), nullable=False),
        sa.Column('achievement', sa.String(length=80), nullable=False),
        sa.Column('rank_code', sa.String(length=4), nullable=False),
        sa.Column('visibility', sa.String(length=10), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('image', sa.LargeBinary(), nullable=False),
        sa.Column('thumb', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], name=op.f('fk_memories_quest_id_quests'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_memories_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_memories')),
    )
    with op.batch_alter_table('memories', schema=None) as batch_op:
        batch_op.create_index('ix_memories_day', ['day'], unique=False)
        batch_op.create_index('ix_memories_quest_id', ['quest_id'], unique=False)
        batch_op.create_index('ix_memories_user_id', ['user_id'], unique=False)


def downgrade():
    op.drop_table('memories')
