"""buffer_queue_posts

Revision ID: c4d9e8f1a234
Revises: 5ee5318e3253
Create Date: 2026-11-09 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d9e8f1a234'
down_revision = '5ee5318e3253'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'buffer_queue_posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.String(length=64), nullable=False),
        sa.Column('channel_name', sa.String(length=100), server_default='', nullable=False),
        sa.Column('service', sa.String(length=30), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('image_urls', sa.Text(), server_default='[]', nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('target_time', sa.String(length=10), server_default='18:30', nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('buffer_post_id', sa.String(length=64), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_buffer_queue_posts_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_buffer_queue_posts')),
    )
    with op.batch_alter_table('buffer_queue_posts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_buffer_queue_posts_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_buffer_queue_posts_channel_id'), ['channel_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_buffer_queue_posts_service'), ['service'], unique=False)
        batch_op.create_index(batch_op.f('ix_buffer_queue_posts_status'), ['status'], unique=False)


def downgrade():
    with op.batch_alter_table('buffer_queue_posts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_buffer_queue_posts_status'))
        batch_op.drop_index(batch_op.f('ix_buffer_queue_posts_service'))
        batch_op.drop_index(batch_op.f('ix_buffer_queue_posts_channel_id'))
        batch_op.drop_index(batch_op.f('ix_buffer_queue_posts_user_id'))
    op.drop_table('buffer_queue_posts')
