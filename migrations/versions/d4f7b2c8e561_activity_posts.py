"""activity posts: hunters feed

Revision ID: d4f7b2c8e561
Revises: c9e1a4b7d230
Create Date: 2026-11-03 15:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4f7b2c8e561'
down_revision = 'c9e1a4b7d230'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'activity_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('text', sa.String(length=240), nullable=False),
        sa.Column('specialty', sa.String(length=20), nullable=False),
        sa.Column('xp', sa.Integer(), nullable=False),
        sa.Column('reward', sa.String(length=120), nullable=False),
        sa.Column('icon', sa.String(length=8), nullable=False),
        sa.Column('memory_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_activity_posts_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_activity_posts')),
    )
    with op.batch_alter_table('activity_posts', schema=None) as batch_op:
        batch_op.create_index('ix_activity_posts_created_at', ['created_at'], unique=False)
        batch_op.create_index('ix_activity_posts_user_id', ['user_id'], unique=False)


def downgrade():
    op.drop_table('activity_posts')
