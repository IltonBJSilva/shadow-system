# Banco de dados

SQLAlchemy 2 + Flask-Migrate (Alembic). SQLite por padrão (`instance/shadow.db`); PostgreSQL quando
`DATABASE_URL` aponta para ele.

## Tabelas

| Tabela | Módulo | O que guarda |
|---|---|---|
| `app_settings` | core | Configurações do usuário em JSON (ex.: widgets do dashboard) |
| `hunters` | hunter | O perfil (nome, título, `total_xp`) |
| `ranks` | hunter | Ranks configuráveis (`code`, `min_level` únicos) |
| `attributes` | hunter | Atributos e seus pontos |
| `xp_events` | hunter | Histórico de XP (origem, valor, data) |
| `attribute_gains` | hunter | Pontos de atributo de cada `xp_event` |
| `quest_categories` | quests | Categorias |
| `quest_category_attributes` | quests | Atributos padrão de cada categoria |
| `quests` | quests | Quests (tipo, prioridade, dificuldade, XP, prazo, status, recorrência, `series_id`) |
| `quest_attributes` | quests | Atributos de cada quest |
| `quest_logs` | quests | Histórico de cada quest |
| `habits` | habits | Hábitos |
| `habit_attributes` | habits | Atributos de cada hábito |
| `habit_logs` | habits | Dias feitos (único por hábito+dia), com o XP dado |
| `calendar_events` | calendar | Eventos (origem local/google, `google_event_id` único, quest vinculada) |

## Relações principais

```
hunters (1)
attributes ──< attribute_gains >── xp_events
attributes ──< quest_attributes >── quests ──< quest_logs
attributes ──< quest_category_attributes >── quest_categories ──< quests
attributes ──< habit_attributes >── habits ──< habit_logs
quests ──< calendar_events (quest_id, ON DELETE SET NULL)
```

## Constraints que protegem regras de negócio

- `hunters.total_xp >= 0`
- `ranks.min_level >= 1`, `code` e `min_level` únicos
- `quests.difficulty BETWEEN 1 AND 5`, `xp_reward >= 0`
- `habit_logs (habit_id, day)` único: um check por dia
- `calendar_events.end_at >= start_at`, `google_event_id` único

Os nomes seguem a convenção em `app/extensions.py` (`ck_<tabela>_<nome>`, `fk_...`, `uq_...`), o que
mantém as migrations previsíveis.

## Migrations

```powershell
# depois de mudar um models.py
.\.venv\Scripts\flask --app wsgi db migrate -m "add workout tables"
# REVISE o arquivo gerado em migrations/versions/
.\.venv\Scripts\flask --app wsgi db upgrade
```

- `render_as_batch=True` está ligado: no SQLite, alterações de coluna recriam a tabela automaticamente.
- O modelo novo precisa estar importado no `__init__.py` do módulo (`from . import models`), senão o
  Alembic não o enxerga.
- `tests/test_migrations.py` aplica todas as migrations num banco vazio e falha se algum modelo ficou
  sem migration.
- Nunca edite uma migration já aplicada no seu banco; crie outra.
- Para desfazer a última: `flask --app wsgi db downgrade`.

## PostgreSQL

1. `pip install "psycopg[binary]==3.2.3"` (já listado, comentado, no `requirements.txt`).
2. Crie o banco: `createdb shadow_system`.
3. `.env`: `DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/shadow_system`
4. `flask --app wsgi db upgrade`.

Para levar os dados do SQLite para o PostgreSQL não há ferramenta pronta ainda; o volume de um uso
pessoal permite exportar/importar por script quando for necessário.
