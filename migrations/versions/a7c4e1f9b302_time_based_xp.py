"""time based xp: estimated minutes, xp breakdown, category specialty and activity sessions

Revision ID: a7c4e1f9b302
Revises: 8f3a1d6c2b77
Create Date: 2026-11-03 12:00:00

Missões antigas ficam com estimated_minutes vazio e mantêm o XP fixo que tinham.
"""
from alembic import op
import sqlalchemy as sa


revision = 'a7c4e1f9b302'
down_revision = '8f3a1d6c2b77'
branch_labels = None
depends_on = None

LEGACY_SPECIALTY_BY_NAME = {
    "treino": "body", "saúde e bem-estar": "body", "corpo": "body", "estudos": "studies",
    "faculdade": "college", "carreira": "career", "finanças": "finance", "música e arte": "hobbies",
    "hobbies": "hobbies", "organização pessoal": "organization", "espiritualidade": "spirituality",
    "projetos pessoais": "projects", "projetos": "projects", "conteúdo": "social", "social": "social",
    "disciplina": "discipline",
}


def upgrade():
    with op.batch_alter_table('quests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('estimated_minutes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('actual_minutes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('started_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('xp_base', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('xp_bonus', sa.Integer(), nullable=True))

    with op.batch_alter_table('quest_categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('specialty', sa.String(length=20), server_default='other', nullable=False))
        batch_op.add_column(sa.Column('xp_multiplier', sa.Float(), server_default='1', nullable=False))

    categories = sa.table('quest_categories', sa.column('id', sa.Integer), sa.column('name', sa.String),
                          sa.column('specialty', sa.String))
    bind = op.get_bind()
    for category_id, name in bind.execute(sa.select(categories.c.id, categories.c.name)).all():
        specialty = LEGACY_SPECIALTY_BY_NAME.get((name or "").strip().lower())
        if specialty:
            bind.execute(categories.update().where(categories.c.id == category_id).values(specialty=specialty))

    with op.batch_alter_table('xp_events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('base_amount', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('bonus_amount', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('breakdown', sa.Text(), server_default='', nullable=False))

    op.create_table(
        'activity_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quest_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=False),
        sa.Column('minutes', sa.Integer(), nullable=False),
        sa.Column('credited_minutes', sa.Integer(), nullable=False),
        sa.Column('specialty', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.CheckConstraint('ended_at >= started_at', name=op.f('ck_activity_sessions_session_end_after_start')),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], name=op.f('fk_activity_sessions_quest_id_quests'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_activity_sessions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_activity_sessions')),
    )
    with op.batch_alter_table('activity_sessions', schema=None) as batch_op:
        batch_op.create_index('ix_activity_sessions_quest_id', ['quest_id'], unique=False)
        batch_op.create_index('ix_activity_sessions_started_at', ['started_at'], unique=False)
        batch_op.create_index('ix_activity_sessions_ended_at', ['ended_at'], unique=False)
        batch_op.create_index('ix_activity_sessions_user_id', ['user_id'], unique=False)


def downgrade():
    op.drop_table('activity_sessions')
    with op.batch_alter_table('xp_events', schema=None) as batch_op:
        batch_op.drop_column('breakdown')
        batch_op.drop_column('bonus_amount')
        batch_op.drop_column('base_amount')
    with op.batch_alter_table('quest_categories', schema=None) as batch_op:
        batch_op.drop_column('xp_multiplier')
        batch_op.drop_column('specialty')
    with op.batch_alter_table('quests', schema=None) as batch_op:
        batch_op.drop_column('xp_bonus')
        batch_op.drop_column('xp_base')
        batch_op.drop_column('started_at')
        batch_op.drop_column('actual_minutes')
        batch_op.drop_column('estimated_minutes')
