"""media assets: system audio and images stored in the database

Revision ID: 8f3a1d6c2b77
Revises: 5b7e2c9d4a10
Create Date: 2026-11-03 10:00:00

"""
from alembic import op
import sqlalchemy as sa


revision = '8f3a1d6c2b77'
down_revision = '5b7e2c9d4a10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'media_assets',
        sa.Column('slot', sa.String(length=30), nullable=False),
        sa.Column('filename', sa.String(length=200), nullable=False),
        sa.Column('mimetype', sa.String(length=60), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('etag', sa.String(length=40), nullable=False),
        sa.Column('data', sa.LargeBinary(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('slot', name=op.f('pk_media_assets')),
    )


def downgrade():
    op.drop_table('media_assets')
