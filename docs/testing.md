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
| `test_dashboard.py` | Renderização, dados reais, notificações, widgets configuráveis |
| `test_google_calendar.py` | Conversões, importação/remoção, envio sem duplicar, OAuth (URL e `state`), telas |
| `test_kausa_scheduler.py` | Parsing dos posts, fuso, erros (offline, login, 500), telas |
| `test_migrations.py` | Aplica todas as migrations num banco vazio e confere que todo modelo tem tabela |

## Princípios

- **Regras puras são testadas sem banco** (`progression.py`, `recurrence.py`, `streaks.py`).
- **Serviços** são testados com o banco em memória (fixture `app`).
- **Rotas** com `client`; o CSRF fica desligado em `TestingConfig` para simplificar os POSTs
  (ele é testado pelo próprio Flask-WTF).
- **Serviços externos nunca são chamados**: o Kausa é simulado com `httpx.MockTransport` e o Google com um
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
