<div align="center">

# ◈ Shadow System

**A personal life management and evolution system inspired by Solo Leveling.**

Transform your goals into quests, track your progress, and build your own system of evolution.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![Status](https://img.shields.io/badge/status-MVP%20em%20desenvolvimento-8b5cf6)

</div>

---

## Sobre o projeto

O Shadow System é o meu **centro de controle pessoal**. Ele transforma áreas da vida (treino, estudos,
faculdade, finanças, carreira, hobbies, criação de conteúdo) em **quests**, e cada atividade real
registrada vira **XP**, **níveis**, **ranks** e **atributos**, como a janela de *System* de Sung Jin-Woo.

**O problema:** tarefas, agenda, hábitos e metas ficam espalhados em apps diferentes, e é difícil enxergar
evolução ao longo do tempo.

**A ideia:** um lugar só, com uma camada de RPG que incentiva **constância**, não perfeição. Dias
improdutivos não tiram XP: uma Daily Quest não feita vira "Não realizada" e a de hoje aparece normalmente.

**Por que foi feito assim:** além de ferramenta, o projeto é meu **manual de desenvolvimento**. O código é
organizado para ser lido e modificado sem depender de ninguém para entendê-lo, com regras de negócio
documentadas e testadas.

Ele também cuida das **minhas postagens pessoais**: conecta direto no meu Buffer (LinkedIn, Instagram...),
mostra o que está agendado e agenda posts novos, com texto diferente por rede.

## Funcionalidades

### Implementado (MVP)

- [x] **Hunter Profile**: nível, rank configurável (E → SS → especiais), XP com curva linear, 8 atributos, histórico de evolução
- [x] **Quest System**: 8 tipos (Daily, Weekly, Monthly, Main, Side, Habit, Emergency, Custom), categorias, prioridade, dificuldade, prazo, critérios, recompensas, atributos, histórico
- [x] **Quests recorrentes** (diária, semanal, mensal) sem punição por dia perdido
- [x] **Hábitos diários**: check-in, streak atual e recorde, correção de dias esquecidos, estorno exato de XP
- [x] **Calendário interno**: visão mensal, eventos ligados a quests, prazos de quests, aviso de conflito de horário
- [x] **Dashboard** estilo janela de status, com widgets configuráveis
- [x] **Google Calendar**: OAuth 2.0, importar e enviar eventos sem duplicar, disponibilidade (opcional)
- [x] **Postagens (Buffer pessoal)**: token cadastrado pela tela, canais, posts agendados/rascunhos/enviados, novo post com texto por rede, carrossel no Instagram (opcional)
- [x] Login opcional do dono, CSRF, cabeçalhos de segurança, backup do SQLite

### Planejado

- [ ] Fitness System (treinos, séries, cargas, divisões ABC/ABCD/Full Body, evolução)
- [ ] Financial System (receitas, despesas, contas, cartões, orçamento, metas, BRL)
- [ ] University System (disciplinas, provas, trabalhos, notas com regras configuráveis, frequência)
- [ ] Study System (cursos, sessões de estudo, revisões)
- [ ] Career System (pipeline de candidaturas)
- [ ] Hobbies (Gaming, Música, Game Dev, Writing e personalizados)
- [ ] Social Media e Instagram Stories (planejamento de sequências, calendário editorial)
- [ ] Shadow AI (objetivos → quests, relatórios, sugestões)
- [ ] Automações agendadas e relatórios semanais

Detalhes e ordem em [ROADMAP.md](ROADMAP.md).

## Screenshots

> Ainda sem capturas. Quando houver, ficarão em `docs/images/` e serão referenciadas aqui com caminhos
> relativos (ex.: `![Dashboard](docs/images/dashboard.png)`).

## Como executar

### Windows (recomendado)

Pré-requisitos: **Python 3.12+** e **Git**.

```powershell
git clone https://github.com/IltonBJSilva/shadow-system.git
cd shadow-system
.\run.ps1
```

Pronto. Na primeira vez o `run.ps1`:

1. cria o ambiente virtual `.venv` e instala as dependências;
2. cria o `.env` a partir do `.env.example`, com uma `SECRET_KEY` aleatória;
3. cria o banco SQLite em `instance/shadow.db` (`flask db upgrade`);
4. abre **http://localhost:5050** no navegador.

Nas próximas vezes, `.\run.ps1` só aplica migrations novas e abre o app.
Para desenvolver (recarrega ao salvar e mostra erros detalhados): `.\run.ps1 --dev`.
Para parar: `Ctrl+C` no terminal.

> Se o PowerShell bloquear o script, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Passo a passo manual (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env          # depois edite SECRET_KEY
flask --app wsgi db upgrade
flask --app wsgi run --debug --port 5050
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # depois edite SECRET_KEY
flask --app wsgi db upgrade
flask --app wsgi run --debug --port 5050
```

### Primeiros passos no app

1. **Hunter** → *Editar perfil*: coloque seu nome e título.
2. **Quests** → *Categorias*: crie categorias (Treino, Estudos, Finanças...) e ligue cada uma aos atributos que ela desenvolve.
3. **Quests** → *+ Nova quest*: crie suas Daily Quests com repetição diária.
4. **Hábitos** → *+ Novo hábito*: hábitos pequenos e diários.
5. **Postagens** → cole o token da API do seu Buffer (gerado em https://publish.buffer.com/settings/api).
   O token é conferido no Buffer antes de salvar e nunca é mostrado de novo. Depois disso você vê os posts
   agendados e cria posts novos, com texto diferente para LinkedIn e Instagram.
6. Volte ao **Dashboard** e conclua quests e hábitos direto de lá.

## Configuração

Tudo fica no `.env` (veja os comentários no [.env.example](.env.example)).

| Variável | Para quê | Obrigatória |
|---|---|---|
| `SECRET_KEY` | Assina a sessão e os tokens CSRF | Sim (o `run.ps1` gera) |
| `DATABASE_URL` | Vazio = SQLite em `instance/`. PostgreSQL: `postgresql+psycopg://...` | Não |
| `TIMEZONE` | Fuso de "hoje" e dos prazos (padrão `America/Sao_Paulo`) | Não |
| `AUTH_ENABLED`, `OWNER_USERNAME`, `OWNER_PASSWORD_HASH` | Login do dono | Não (ligue antes de expor em rede) |
| `GOOGLE_CLIENT_SECRETS_FILE`, `GOOGLE_REDIRECT_URI`, `GOOGLE_CALENDAR_ID` | Google Calendar | Não |
| `BUFFER_API_KEY`, `BUFFER_KEY_CREATED_AT` | Alternativa ao token cadastrado pela tela (Postagens > Token) | Não |
| `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_BUCKET` | Hospedar imagens enviadas do computador para o Buffer | Não |

**Integrações são opcionais.** Sem nenhuma, o app funciona por completo. Como configurar cada uma:
[docs/integrations.md](docs/integrations.md). A Shadow AI ainda não foi implementada, então não há
configuração de IA por enquanto.

## Arquitetura

**Monólito modular**: uma única aplicação Flask, um banco, um processo, organizada em módulos com
responsabilidades separadas.

| Tecnologia | Uso |
|---|---|
| Python 3.12, Flask 3 | Aplicação web (Application Factory + Blueprints) |
| SQLAlchemy 2, Flask-SQLAlchemy | Modelos e consultas |
| Flask-Migrate (Alembic) | Migrations |
| SQLite / PostgreSQL | SQLite local; PostgreSQL suportado via `DATABASE_URL` |
| Flask-WTF | Formulários, validação e CSRF |
| httpx | Cliente HTTP do Buffer (GraphQL) |
| google-auth-oauthlib, google-api-python-client | Google Calendar |
| HTML, CSS e JavaScript puros | Interface, sem framework de frontend nem CDN |
| pytest | Testes |
| waitress | Servidor WSGI no Windows |

```
                 ┌──────────────── app (Flask) ─────────────────┐
 navegador ────▶ │ routes (Blueprints)  →  services  →  models   │ ──▶ banco
                 │        │                    │                 │
                 │        └── core: config, segurança, erros,    │
                 │            tempo, settings, templates         │
                 │                                               │
                 │ módulos: dashboard → hunter, quests, habits,  │
                 │          calendar     (via services.py)       │
                 │                                               │
                 │ integrations: google_calendar, buffer         │ ──▶ APIs externas
                 └───────────────────────────────────────────────┘
```

**Como os módulos conversam:** cada módulo expõe sua API pública em `services.py`. Outros módulos
importam só isso, nunca `models.py` ou `routes.py` alheios. Exemplo: ao concluir uma quest, `quests`
chama `hunter.services.award_xp(...)`; o dashboard só lê os `services` de todos.
Detalhes em [docs/architecture.md](docs/architecture.md).

## Estrutura do projeto

```
shadow-system/
├── app/
│   ├── __init__.py            create_app (Application Factory)
│   ├── config.py              configuração por ambiente, lida do .env
│   ├── extensions.py          db, migrate, csrf
│   ├── core/                  compartilhado: models base, settings, time, errors, security, cli
│   ├── modules/
│   │   ├── dashboard/         janela de status e widgets
│   │   ├── hunter/            perfil, XP, níveis, ranks, atributos
│   │   ├── quests/            quests, categorias, recorrência
│   │   ├── habits/            hábitos e streaks
│   │   └── calendar/          calendário interno
│   ├── integrations/
│   │   ├── google_calendar/   OAuth, cliente da API, sincronização
│   │   └── buffer/            token, cliente GraphQL, regras por rede, agendamento
│   ├── templates/             Jinja2, uma pasta por módulo
│   └── static/                css/shadow.css, js/shadow.js, img/
├── migrations/                Alembic (uma migration por feature)
├── tests/                     pytest
├── docs/                      documentação técnica
├── instance/                  banco SQLite, tokens e backups (fora do git)
├── run.ps1                    executar no Windows
├── wsgi.py                    ponto de entrada
├── requirements.txt / pyproject.toml
└── ROADMAP.md
```

Arquivo por arquivo: [docs/project-structure.md](docs/project-structure.md).

## Desenvolvimento

| Tarefa | Comando / Guia |
|---|---|
| Rodar em modo dev | `.\run.ps1 --dev` |
| Testes | `.\.venv\Scripts\python -m pytest` |
| Criar migration | `.\.venv\Scripts\flask --app wsgi db migrate -m "descrição"` e depois `db upgrade` |
| Backup do banco | `.\.venv\Scripts\flask --app wsgi backup create` |
| Rolar quests recorrentes | `.\.venv\Scripts\flask --app wsgi quests rollover` |
| Adicionar módulo, rota, serviço, modelo | [docs/development-guide.md](docs/development-guide.md) |
| Adicionar integração | [docs/integrations.md](docs/integrations.md#como-adicionar-uma-integração) |
| Mudar a interface | [docs/development-guide.md](docs/development-guide.md#interface) |

**Commits:** Conventional Commits em inglês (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`), um
commit por feature concluída, com testes passando e documentação atualizada.

## Roadmap

1. ✅ MVP: estrutura, Hunter, Quests, Hábitos, Calendário, Dashboard, Google Calendar, Postagens no Buffer
2. ⏭ University + Study (provas, trabalhos, notas configuráveis, quests de revisão geradas)
3. Fitness e Financial
4. Social Media / Instagram Stories e calendário editorial
5. Career e Hobbies
6. Shadow AI e automações agendadas

Completo em [ROADMAP.md](ROADMAP.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/README.md](docs/README.md) | Índice |
| [docs/architecture.md](docs/architecture.md) | Monólito modular, camadas, regras de dependência |
| [docs/project-structure.md](docs/project-structure.md) | Cada pasta e arquivo |
| [docs/database.md](docs/database.md) | Tabelas, relações, migrations, PostgreSQL |
| [docs/development-guide.md](docs/development-guide.md) | Como criar módulo, rota, serviço, modelo, tela |
| [docs/testing.md](docs/testing.md) | Como os testes são organizados e rodados |
| [docs/integrations.md](docs/integrations.md) | Google Calendar, Buffer, como criar novas |
| [docs/security.md](docs/security.md) | Credenciais, login, CSRF, backups |
| [docs/deployment.md](docs/deployment.md) | Rodar fora do ambiente de desenvolvimento |
| [docs/modules/](docs/modules/) | [Hunter](docs/modules/hunter.md), [Quests](docs/modules/quests.md), [Hábitos](docs/modules/habits.md), [Calendário](docs/modules/calendar.md), [Dashboard](docs/modules/dashboard.md) |
| [docs/decisions/architecture-decisions.md](docs/decisions/architecture-decisions.md) | Decisões e seus motivos |

## Segurança

- Credenciais só no `.env` e em `instance/`; os dois estão no `.gitignore`. Nada sensível no código.
- O app guarda dados pessoais: com o login desligado, ele escuta só em `127.0.0.1`. Ligue o login antes
  de expor em qualquer rede.
- CSRF em todos os formulários, cabeçalhos de segurança (CSP, X-Frame-Options), redirecionamentos só internos.
- Logs não registram conteúdo pessoal nem tokens.
- Backups: `flask backup create` (SQLite) ou `pg_dump` (PostgreSQL).

Detalhes em [docs/security.md](docs/security.md).

## Contribuição e manutenção

É um projeto pessoal, mas segue regras para continuar fácil de manter:

1. Regra de negócio em `services.py`, nunca na rota.
2. Módulos conversam só pela API pública (`services.py`).
3. Toda feature vem com testes e com a documentação do módulo atualizada.
4. Mudou o modelo? Gere a migration no mesmo commit.
5. Nada de credenciais, dados pessoais ou financeiros no repositório.
6. Nada de funcionalidade simulada apresentada como real.

## Licença

Ainda **não há licença definida**. Até que uma seja escolhida, todos os direitos são reservados ao autor.

Shadow System é um projeto pessoal inspirado em *Solo Leveling*, sem afiliação com a obra ou seus
detentores, e não usa imagens da obra.
