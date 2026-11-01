# Arquitetura

## Monólito modular

Uma aplicação Flask, um processo, um banco. Dentro dela, módulos com fronteiras claras. É o meio-termo
entre "tudo num arquivo" e microserviços: simples de rodar e de fazer deploy, mas organizado o bastante
para crescer módulo a módulo.

```
app/
├── core/          compartilhado, não conhece os módulos
├── modules/       domínio (hunter, quests, habits, calendar, dashboard)
└── integrations/  serviços externos (google_calendar, buffer)
```

## Camadas de um módulo

```
routes.py   ← recebe a requisição, valida o formulário, chama o serviço, renderiza/redireciona
forms.py    ← Flask-WTF: campos, validação de entrada, conversão para o tipo de entrada do serviço
services.py ← REGRAS DE NEGÓCIO e API pública do módulo
models.py   ← tabelas (SQLAlchemy)
```

Arquivos opcionais quando há regra pura que vale isolar: `progression.py` (Hunter), `recurrence.py`
(Quests), `streaks.py` (Hábitos), `constants.py`, `defaults.py`, `cli.py`.

Não há camada de repositório separada: com SQLAlchemy 2 as consultas nos serviços já são legíveis, e
uma camada extra só repetiria código. Se um módulo crescer muito, as consultas podem ir para
`queries.py` sem mudar a API pública.

## Regras de dependência

1. `core` não importa nada de `modules` nem de `integrations`.
2. Um módulo só importa de outro módulo o `services.py` dele (a API pública).
3. Funções públicas que outros módulos usam retornam *views* (dataclasses) quando o modelo não deve
   vazar, ex.: `QuestView`, `HabitView`, `HunterStatus`.
4. Integrações podem chamar `services.py` dos módulos (para gravar), nunca `models.py`.
5. Módulos podem usar integrações por funções "safe" que não quebram a página (ex.:
   `buffer.scheduled_posts_safe`).
6. Sem dependência circular. Hoje o grafo é:

```
dashboard ──▶ hunter, quests, habits, calendar, integrations.buffer
quests    ──▶ hunter
habits    ──▶ hunter
calendar  ──▶ quests
integrations.google_calendar ──▶ calendar
```

O banco é central, então tabelas de módulos diferentes podem ter FK entre si (ex.: `quest_attributes`
aponta para `attributes.id`). Isso é aceitável num monólito; o que não se faz é usar o *modelo* de outro
módulo no código.

## Ciclo de uma requisição

Exemplo: concluir uma quest pelo dashboard.

1. Formulário `POST /quests/7/complete` com `csrf_token` e `next=/`.
2. `CSRFProtect` valida o token. `security.require_login` confere a sessão (se o login estiver ligado).
3. `quests.routes.complete` chama `quests.services.complete_quest(7)`.
4. O serviço valida o status, marca como concluída, registra no log, chama
   `hunter.services.award_xp(...)`, cria a próxima ocorrência se for recorrente e faz **um** commit.
5. A rota mostra as mensagens (`+50 XP`, `LEVEL UP!`) e volta para `next` (só caminhos internos).
6. Se uma regra for violada, o serviço levanta `DomainError`; o handler global mostra a mensagem e volta.

## Transações

Serviços que alteram dados fazem o `commit`. Funções chamadas por outros serviços no meio de uma
operação (ex.: `award_xp`) **não** fazem commit, para que tudo seja salvo junto ou nada seja.

## Datas e horas

Gravadas sem fuso, no horário local de `TIMEZONE` (`app/core/time.py`). É um sistema de uma pessoa
em um fuso, então isso simplifica consultas e telas. Integrações convertem na fronteira
(`to_local_naive`, `to_aware`).

## Interface

Jinja2 renderizado no servidor, CSS e JS próprios (`app/static`), sem framework de frontend e sem CDN.
Ações que alteram dados são sempre `POST` com CSRF. A CSP bloqueia JavaScript inline, então
comportamentos ficam em `shadow.js` via atributos `data-*`.
