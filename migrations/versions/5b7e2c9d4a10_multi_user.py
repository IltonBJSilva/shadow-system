"""multi user: users table and user_id on every data table

Revision ID: 5b7e2c9d4a10
Revises: 0a84c265cf34
Create Date: 2026-11-03 09:00:00

Todos os dados que já existem passam a ser do dono (users.id = 1). As constraints únicas que eram
globais (código do rank, nome da categoria...) passam a valer por usuário.
"""
import os

from alembic import op
import sqlalchemy as sa


revision = '5b7e2c9d4a10'
down_revision = '0a84c265cf34'
branch_labels = None
depends_on = None

OWNED_TABLES = [
    'architect_goals', 'architect_suggestions', 'architect_messages', 'calendar_events', 'quest_failures',
    'habits', 'habit_logs', 'hunters', 'ranks', 'attributes', 'xp_events', 'attribute_gains', 'titles',
    'quest_categories', 'quests', 'quest_logs', 'workout_plans', 'workout_days', 'workout_exercises',
    'workout_sessions',
]
# (tabela, constraint antiga, colunas antigas, constraint nova)
UNIQUES = [
    ('ranks', 'uq_ranks_code', ['code'], 'uq_ranks_user_code'),
    ('ranks', 'uq_ranks_min_level', ['min_level'], 'uq_ranks_user_min_level'),
    ('attributes', 'uq_attributes_key', ['key'], 'uq_attributes_user_key'),
    ('titles', 'uq_titles_key', ['key'], 'uq_titles_user_key'),
    ('titles', 'uq_titles_name', ['name'], 'uq_titles_user_name'),
    ('quest_categories', 'uq_quest_categories_name', ['name'], 'uq_quest_categories_user_name'),
    ('calendar_events', 'uq_calendar_events_google_event_id', ['google_event_id'], 'uq_calendar_events_user_google_event'),
]
KEY_VALUE_TABLES = [('app_settings', 'key'), ('stored_secrets', 'name')]


def upgrade():
    users = op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=160), nullable=True),
        sa.Column('display_name', sa.String(length=80), server_default='', nullable=False),
        sa.Column('role', sa.String(length=10), server_default='tester', nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('invite_hash', sa.String(length=64), nullable=True),
        sa.Column('invite_expires_at', sa.DateTime(), nullable=True),
        sa.Column('active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('username', name=op.f('uq_users_username')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
        sa.UniqueConstraint('invite_hash', name=op.f('uq_users_invite_hash')),
    )
    from datetime import datetime

    op.bulk_insert(users, [{
        'id': 1, 'username': os.getenv('OWNER_USERNAME', 'hunter') or 'hunter', 'display_name': '',
        'role': 'owner', 'active': True, 'created_at': datetime.now(),
    }])
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users))")

    for table in OWNED_TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('user_id', sa.Integer(), server_default='1', nullable=False))
            batch_op.create_index(f'ix_{table}_user_id', ['user_id'], unique=False)
            batch_op.create_foreign_key(f'fk_{table}_user_id_users', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    for table, key in KEY_VALUE_TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('user_id', sa.Integer(), server_default='1', nullable=False))
            batch_op.drop_constraint(f'pk_{table}', type_='primary')
            batch_op.create_primary_key(f'pk_{table}', ['user_id', key])
            batch_op.create_foreign_key(f'fk_{table}_user_id_users', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    for table, old, columns, new in UNIQUES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(old, type_='unique')
            batch_op.create_unique_constraint(new, ['user_id', *columns])

    # O default '1' só serviu para os dados antigos. Daqui em diante o app sempre informa o dono da linha.
    for table in OWNED_TABLES + [t for t, _ in KEY_VALUE_TABLES]:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column('user_id', existing_type=sa.Integer(), server_default=None, existing_nullable=False)


def downgrade():
    for table, old, columns, new in UNIQUES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(new, type_='unique')
            batch_op.create_unique_constraint(old, columns)
    for table, key in KEY_VALUE_TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(f'fk_{table}_user_id_users', type_='foreignkey')
            batch_op.drop_constraint(f'pk_{table}', type_='primary')
            batch_op.create_primary_key(f'pk_{table}', [key])
            batch_op.drop_column('user_id')
    for table in OWNED_TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(f'fk_{table}_user_id_users', type_='foreignkey')
            batch_op.drop_index(f'ix_{table}_user_id')
            batch_op.drop_column('user_id')
    op.drop_table('users')
