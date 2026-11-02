# Banco de dados

SQLAlchemy 2 + Flask-Migrate (Alembic). SQLite por padrão (`instance/shadow.db`); PostgreSQL quando
`DATABASE_URL` aponta para ele.

## Tabelas

| Tabela | Módulo | O que guarda |
|---|---|---|
| `app_settings` | core | Configurações do usuário em JSON (ex.: widgets do dashboard) |
| `stored_secrets` | core | Tokens das integrações cadastrados pela tela, em JSON (`google_token`, `buffer_token`, `credentials:<nome>`). Ver [security.md](security.md) |
| `hunters` | hunter | O perfil (nome, título exibido, `total_xp`) |
| `titles` | hunter | Títulos: regra de desbloqueio (`rule` + `threshold`), `unlocked_at`; `rule="custom"` = criado por você |
| `ranks` | hunter | Ranks configuráveis (`code`, `min_level` únicos) |
| `attributes` | hunter | Atributos e seus pontos |
| `xp_events` | hunter | Histórico de XP (origem, valor, data) |
| `attribute_gains` | hunter | Pontos de atributo de cada `xp_event` |
| `quest_categories` | quests | Categorias |
| `quest_category_attributes` | quests | Atributos padrão de cada categoria |
| `quests` | quests | Quests (tipo, prioridade, dificuldade, XP, prazo, status, recorrência, `series_id`) |
| `quest_attributes` | quests | Atributos de cada quest |
| `quest_logs` | quests | Histórico de cada quest |
| `habits` | habits | Hábitos (`weekdays`: dias esperados, vazio = todos) |
| `habit_attributes` | habits | Atributos de cada hábito |
| `habit_logs` | habits | Dias feitos (único por hábito+dia), com o XP dado |
| `calendar_events` | calendar | Eventos (origem local/google, `google_event_id` único, quest vinculada) |
| `workout_plans` | training | Planos de treino: horário, duração, automações, aumento de carga, hábito ligado |
| `workout_days` | training | Dias de treino (dia da semana, nome, `quest_series_id` da quest semanal) |
| `workout_exercises` | training | Exercícios (séries, repetições, carga, descanso, observação) |
| `workout_sessions` | training | Treinos feitos (data, dia, quest) |

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

Em produção o banco é o PostgreSQL do Supabase (ver [deployment.md](deployment.md)). O driver
`psycopg[binary]` já está no `requirements.txt`.

- O `DATABASE_URL` pode vir como `postgresql://` ou `postgres://`; o app converte para
  `postgresql+psycopg://` (`app/config.py`).
- Com PostgreSQL o app usa `pool_pre_ping` e `pool_recycle=300`: conexões paradas (app dormindo,
  pooler do Supabase) são testadas e renovadas antes do uso.
- Depois de `flask db upgrade`, rode `flask --app wsgi security lock-db` para ligar RLS em todas as
  tabelas (o build do Render já faz isso). Necessário sempre que uma migration criar tabela nova.
- `flask --app wsgi db check` confere se os modelos e o banco batem. As migrations foram validadas num
  PostgreSQL real, não só no SQLite.

PostgreSQL local, se quiser:

1. Crie o banco: `createdb shadow_system`.
2. `.env`: `DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/shadow_system`
3. `flask --app wsgi db upgrade`.

**Backup do Supabase:** o plano gratuito não guarda backups que você possa baixar. De vez em quando:
`pg_dump "URI_DO_SESSION_POOLER" -Fc -f shadow-backup.dump`.

Para levar os dados do SQLite para o PostgreSQL não há ferramenta pronta ainda; o volume de um uso
pessoal permite exportar/importar por script quando for necessário.
