# Integrações

Todas são **opcionais**. Sem nenhuma configurada, o Shadow System funciona normalmente.

| Integração | Pasta | Estado |
|---|---|---|
| Kausa Social Scheduler (e Buffer, por meio dele) | `app/integrations/kausa_scheduler/` | Leitura de canais e posts agendados |
| Shadow AI | — | Planejada (ver `ROADMAP.md`) |

A tela `/integrations/` mostra a situação de cada uma (`app/integrations/registry.py`).

## Regras da camada de integrações

- Cada integração fica em `app/integrations/<nome>/`, com um **cliente** que fala com a API externa e
  não conhece os modelos dos módulos.
- Os módulos podem usar integrações; integrações podem chamar a API pública dos módulos
  (`services.py`) para gravar dados. Integrações nunca importam `models.py` de módulos.
- Erros externos viram uma exceção própria da integração (ex.: `KausaSchedulerError`) com mensagem
  para o usuário. Telas que mostram dados externos usam versões "safe" que nunca quebram a página.
- Credenciais só no `.env` ou em `instance/` (fora do git). Nunca no código, nunca em log.
- Testes nunca chamam serviços reais: usam `httpx.MockTransport` ou objetos falsos.

## Como adicionar uma integração

1. Crie `app/integrations/<nome>/client.py` com uma classe cliente e uma exceção própria.
2. Em `app/integrations/<nome>/__init__.py`, exponha `status()` retornando `IntegrationStatus`
   e funções de alto nível que o resto do app vai usar.
3. Adicione o `status()` em `registry.all_statuses()`.
4. Se tiver telas, crie um blueprint e registre em `app/integrations/__init__.py`.
5. Variáveis novas vão no `.env.example` (vazias) e em `app/config.py`.
6. Testes em `tests/test_<nome>.py` com a API externa simulada.

---

## Kausa Social Scheduler

O Kausa é um projeto separado (`E:\Repositorio\kausa-social-scheduler`, Flask + Buffer GraphQL +
Supabase Storage). Ele continua responsável por publicar; o Shadow System **lê** o que está agendado.

### Análise do projeto (feita em 01/11/2026, sem alterar nada nele)

| Item | Encontrado |
|---|---|
| Stack | Python, Flask 3, httpx, waitress, pytest. Sem banco: estado no Buffer e em `instance/settings.json`. |
| Estrutura | `app/buffer.py` (cliente GraphQL do Buffer), `publisher.py` (motor de agendamento), `storage.py` (upload no Supabase), `routes.py` (telas e API), `cli.py` (`flask agendar <pasta>`), `auth.py` (login opcional). |
| Buffer | API GraphQL `https://api.buffer.com`, chave pessoal que vence a cada 90 dias. Imagens precisam de link público (por isso o Supabase). Mais de uma imagem vira carrossel no Instagram. |
| API | `GET /saude`, `GET /api/canais`, `GET /api/posts?status=`, `POST /api/posts` (multipart com imagens), `GET/POST /api/chave`. |
| Porta | 5000 (o Shadow System usa 5050 para não conflitar). |

### O que a integração faz

- `GET /saude`: mostra se o Kausa está no ar.
- `GET /api/canais`: lista as redes conectadas no Buffer.
- `GET /api/posts?status=scheduled`: posts agendados, mostrados em `/integrations/kausa` e no dashboard.

Configure com `KAUSA_SCHEDULER_URL=http://localhost:5000` no `.env` e rode os dois apps.

### Limitações encontradas

- **Login do Kausa**: quando `AUTH_ENABLED=true` no Kausa, a API dele exige a sessão do navegador
  (cookie). Não existe token para outro app. Hoje a integração só funciona com o login do Kausa
  desligado (uso local). Plano proposto, **não aplicado** no Kausa: aceitar um cabeçalho
  `Authorization: Bearer <KAUSA_API_TOKEN>` em `auth.require_login` para rotas `/api/`.
- **Criar posts pelo Shadow System**: `POST /api/posts` exige enviar as imagens (multipart). É possível,
  mas o fluxo de criação já existe e funciona no painel do Kausa; por isso o Shadow System só abre o
  painel por enquanto, sem recriar a funcionalidade.
- **Stories**: o Kausa monta posts de imagem/carrossel. Ele não trata Stories, e não foi verificado se a API
  pública do Buffer agenda Stories do Instagram. Antes de implementar, conferir na documentação oficial do
  Buffer. Até lá, Stories serão planejamento manual no módulo Social Media (futuro).
- **Collab e marcação de pessoas no Instagram** não existem na API pública do Buffer (anotado no
  `CLAUDE.md` do Kausa). Continuam manuais.
- **Métricas**: o Kausa não consulta métricas; a integração não tem de onde lê-las.
- O cliente devolve no máximo os 30 posts que o Kausa pede ao Buffer (`first: 30` em `buffer.py`).

### Buffer direto?

Não. O Buffer é acessado **através do Kausa**, que já tem a chave, o upload das imagens e as regras de
cada rede (ex.: limite de 5 hashtags no Instagram). Recriar isso no Shadow System duplicaria código
e credenciais.
