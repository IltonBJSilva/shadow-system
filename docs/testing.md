# Testes

```powershell
.\.venv\Scripts\python -m pytest            # tudo
.\.venv\Scripts\python -m pytest tests/test_quests.py
.\.venv\Scripts\python -m pytest -k streak  # por nome
```

## Organização

| Arquivo | Cobre |
|---|---|
| `conftest.py` | Fixtures `app`, `client`, `db`: app de teste com SQLite em memória, tabelas criadas e apagadas por teste |
| `test_core.py` | /health, cabeçalhos de segurança, settings, fuso, login opcional, open redirect |
| `test_hunter.py` | Curva de XP, níveis, ranks, award_xp, estorno, histórico por dia, telas |
| `test_quests.py` | Recorrência, XP por dificuldade, herança de atributos, conclusão, rollover sem punição, rotas |
| `test_habits.py` | Streaks, check-in, duplicidade, estorno exato, limites de data, arquivamento |
| `test_calendar.py` | Duração padrão, dia inteiro, conflitos, grade do mês, upsert sem duplicar |
| `test_gamification.py` | Bônus (primeira quest, prazo, combo, sequência + estorno), punição sem perder nível, Penalty Quest e redenção, tela |
| `test_dashboard.py` | Renderização, dados reais, notificações, widgets configuráveis |
| `test_google_calendar.py` | Conversões, importação/remoção, envio sem duplicar, OAuth (URL e `state`), telas |
| `test_buffer.py` | Regras por rede, token (conferido, mascarado, vencimento), posts, agendamento por canal, confirmação, telas |
| `test_gmail_notion_whatsapp.py` | Escopo do Gmail, não lidos, e-mail → quest; token do Notion, parsing e importação sem duplicar; WhatsApp: validação, só para o seu número, template |
| `test_migrations.py` | Aplica todas as migrations num banco vazio e confere que todo modelo tem tabela |

## Princípios

- **Regras puras são testadas sem banco** (`progression.py`, `recurrence.py`, `streaks.py`).
- **Serviços** são testados com o banco em memória (fixture `app`).
- **Rotas** com `client`; o CSRF fica desligado em `TestingConfig` para simplificar os POSTs
  (ele é testado pelo próprio Flask-WTF).
- **Serviços externos nunca são chamados**: o Buffer é simulado com `httpx.MockTransport` e o Google com um
  `FakeService` que imita o objeto do `google-api-python-client`. Nenhum teste precisa de credencial.
- Para variar a configuração num teste: `create_app("testing", {"AUTH_ENABLED": True, ...})`.

## Escrevendo um teste novo

```python
from app.modules.quests import services
from app.modules.quests.services import QuestInput


def test_main_quest_with_high_priority_is_listed_first(app):
    services.create_quest(QuestInput(title="Comum"))
    services.create_quest(QuestInput(title="Urgente", quest_type="main", priority="critical"))
    assert services.priority_quests()[0].title == "Urgente"
```

## Testar contra PostgreSQL

A suíte roda em SQLite em memória (rápida). Antes de mudar migrations, valide também num PostgreSQL
real, que é o banco de produção (Supabase):

1. Suba um PostgreSQL descartável (Docker: `docker run --rm -e POSTGRES_PASSWORD=pw -p 55432:5432 postgres:16`,
   ou o pacote `pgserver` instalado fora do projeto).
2. Rode as migrations nele:

   ```powershell
   $env:DATABASE_URL = "postgresql://postgres:pw@localhost:55432/postgres"
   .venv\Scriptslask --app wsgi db upgrade
   .venv\Scriptslask --app wsgi security lock-db
   .venv\Scriptslask --app wsgi db check
   ```

   Os comandos acima não leem tokens. Mas **não abra páginas do app** apontado para o banco
   descartável usando a `instance/` real: a importação de arquivos antigos (`app/core/secret_store.py`)
   moveria os tokens do PC para esse banco e apagaria os arquivos. Para navegar nas páginas, use um
   script com `create_app(overrides={"GOOGLE_TOKEN_FILE": ..., "BUFFER_TOKEN_FILE": ..., "CREDENTIALS_DIR": ...})`
   apontando para uma pasta temporária, como faz `tests/conftest.py`.
3. `db check` sem diferenças = modelos e migrations batem.

Os testes de integração nunca chamam serviços reais: Buffer, Notion e WhatsApp usam `httpx.MockTransport`.
