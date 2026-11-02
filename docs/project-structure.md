# Estrutura do projeto

```
shadow-system/
├── app/
│   ├── __init__.py              create_app(): config → extensões → core → módulos → integrações
│   ├── config.py                Config, DevelopmentConfig, ProductionConfig, TestingConfig (lê .env)
│   ├── extensions.py            db (SQLAlchemy com naming convention), migrate, csrf
│   │
│   ├── core/
│   │   ├── models.py            TimestampMixin, AppSetting, StoredSecret
│   │   ├── secret_store.py      tokens das integrações no banco (importa arquivos antigos de instance/)
│   │   ├── settings.py          get_setting / set_setting (JSON em app_settings)
│   │   ├── time.py              now(), today(), conversões de fuso
│   │   ├── errors.py            DomainError, NotFoundError, páginas 404/500
│   │   ├── http.py              redirect_back(): volta para `next` interno
│   │   ├── events.py            publish/subscribe entre módulos
│   │   ├── security.py          login opcional, cabeçalhos HTTP, `flask security hash-password` e `lock-db`
│   │   ├── routes.py            /health (público, faz SELECT 1; usado pelo keep-alive)
│   │   ├── template_helpers.py  filtros (date_br, datetime_br, hour), menu lateral e modo da inicialização
│   │   ├── experience.py        modo da inicialização do System e o manifesto
│   │   └── cli.py               `flask backup create|list`
│   │
│   ├── modules/
│   │   ├── __init__.py          register_modules(): lista de blueprints
│   │   ├── hunter/              progression.py, defaults.py, models, services, forms, routes, cli
│   │   ├── quests/              constants.py, recurrence.py, models, services, forms, routes, cli
│   │   ├── habits/              streaks.py (com dias de folga), models, services, forms, routes
│   │   ├── architect/           context.py (retrato real), analysis.py (regras), ai.py (Claude), models,
│   │   │                        services, forms, routes
│   │   ├── training/            parser.py (texto → plano), library.py (rotinas prontas), documents.py
│   │   │                        (txt/md/docx/pdf), progression.py, handlers.py, models, services, forms, routes
│   │   ├── gamification/        rules.py, handlers.py (eventos), models (Zona de Falha), services, routes
│   │   ├── calendar/            models, services, forms, routes
│   │   └── dashboard/           services (widgets), routes
│   │
│   ├── integrations/
│   │   ├── __init__.py          register_integrations()
│   │   ├── registry.py          IntegrationStatus e lista de integrações
│   │   ├── routes.py            /integrations/
│   │   ├── google_calendar/     oauth.py, client.py, sync.py, routes.py
│   │   ├── credentials.py       tokens cadastrados pela tela (banco: stored_secrets)
│   │   ├── network.py           mensagens de falha de rede (ex.: bloqueio do proxy do PythonAnywhere)
│   │   ├── gmail/               client.py, routes.py (usa o OAuth do Google)
│   │   ├── notion/              client.py, routes.py
│   │   ├── whatsapp/            client.py, routes.py
│   │   └── buffer/              client.py, posting.py, token_store.py, storage.py, routes.py
│   │
│   ├── templates/
│   │   ├── base.html            layout com sidebar
│   │   ├── partials/            _flash.html, _macros.html (field, progress, post_button, empty)
│   │   ├── errors/  security/
│   │   ├── hunter/  quests/  habits/  calendar/  integrations/
│   │   └── dashboard/           index.html, settings.html, widgets/<widget>.html
│   │
│   └── static/
│       ├── css/shadow.css       tema (variáveis de cor no topo)
│       ├── js/shadow.js         menu mobile, colapsáveis, autosubmit, som das mensagens, seleção em massa,
│       │                        janela de LEVEL UP, botões "trabalhando" em formulários demorados
│       ├── js/sounds.js         efeitos sonoros (Web Audio, sintetizados): quest, level up, conquista, boot...
│       ├── js/boot.js           sequência de inicialização com o manifesto
│       └── img/                 favicon.svg, emblem.svg (arte original)
│
├── migrations/
│   ├── env.py, alembic.ini, script.py.mako
│   └── versions/                core_app_settings → hunter_profile → quest_system → habit_tracking → internal_calendar → hunter_avatar → stored_secrets
│
├── tests/                       conftest.py + um arquivo por módulo/integração + test_migrations.py
├── .github/workflows/
│   └── keep-alive.yml           chama /health a cada 10 min (reserva do cron-job.org)
├── docs/                        esta documentação (troubleshooting.md: erros conhecidos)
├── instance/                    shadow.db, backups/ (tudo fora do git)
├── .env.example                 modelo do .env
├── render.yaml                  Blueprint do Render (serviço web, build com migrations, variáveis)
├── run.ps1                      instala e roda no Windows
├── wsgi.py                      `app = create_app()`
├── requirements.txt             dependências com versão fixa
├── pyproject.toml               metadados e configuração do pytest
├── README.md
└── ROADMAP.md
```
