# Estrutura do projeto

```
shadow-system/
├── app/
│   ├── __init__.py              create_app(): config → extensões → core → módulos → integrações
│   ├── config.py                Config, DevelopmentConfig, ProductionConfig, TestingConfig (lê .env)
│   ├── extensions.py            db (SQLAlchemy com naming convention), migrate, csrf
│   │
│   ├── core/
│   │   ├── models.py            TimestampMixin, AppSetting
│   │   ├── settings.py          get_setting / set_setting (JSON em app_settings)
│   │   ├── time.py              now(), today(), conversões de fuso
│   │   ├── errors.py            DomainError, NotFoundError, páginas 404/500
│   │   ├── http.py              redirect_back(): volta para `next` interno
│   │   ├── security.py          login opcional, cabeçalhos HTTP, `flask security hash-password`
│   │   ├── routes.py            /health
│   │   ├── template_helpers.py  filtros (date_br, datetime_br, hour) e menu lateral
│   │   └── cli.py               `flask backup create|list`
│   │
│   ├── modules/
│   │   ├── __init__.py          register_modules(): lista de blueprints
│   │   ├── hunter/              progression.py, defaults.py, models, services, forms, routes, cli
│   │   ├── quests/              constants.py, recurrence.py, models, services, forms, routes, cli
│   │   ├── habits/              streaks.py, models, services, forms, routes
│   │   ├── calendar/            models, services, forms, routes
│   │   └── dashboard/           services (widgets), routes
│   │
│   ├── integrations/
│   │   ├── __init__.py          register_integrations()
│   │   ├── registry.py          IntegrationStatus e lista de integrações
│   │   ├── routes.py            /integrations/, /integrations/kausa
│   │   ├── google_calendar/     oauth.py, client.py, sync.py, routes.py
│   │   └── kausa_scheduler/     client.py
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
│       ├── js/shadow.js         menu mobile, colapsáveis, autosubmit
│       └── img/favicon.svg
│
├── migrations/
│   ├── env.py, alembic.ini, script.py.mako
│   └── versions/                core_app_settings → hunter_profile → quest_system → habit_tracking → internal_calendar
│
├── tests/                       conftest.py + um arquivo por módulo/integração + test_migrations.py
├── docs/                        esta documentação
├── instance/                    shadow.db, google_token.json, backups/ (tudo fora do git)
├── .env.example                 modelo do .env
├── run.ps1                      instala e roda no Windows
├── wsgi.py                      `app = create_app()`
├── requirements.txt             dependências com versão fixa
├── pyproject.toml               metadados e configuração do pytest
├── README.md
└── ROADMAP.md
```
