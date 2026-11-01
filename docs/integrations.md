# Integrações

Todas são **opcionais**. Sem nenhuma configurada, o Shadow System funciona normalmente.

| Integração | Pasta | Estado |
|---|---|---|
| Google Calendar | `app/integrations/google_calendar/` | OAuth 2.0, importar/enviar eventos, disponibilidade |
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

## Google Calendar

Bibliotecas oficiais: `google-auth-oauthlib` (OAuth) e `google-api-python-client` (Calendar API v3).
Nenhum endpoint é montado à mão.

| Arquivo | Responsabilidade |
|---|---|
| `oauth.py` | Fluxo OAuth 2.0 (Authorization Code + PKCE), salvar/renovar token |
| `client.py` | `GoogleCalendarClient`: `calendars`, `list_events`, `insert_event`, `patch_event`, `delete_event`, `busy_periods`, `find_by_shadow_id` |
| `sync.py` | Importar eventos do Google e enviar eventos locais, sem duplicar |
| `routes.py` | `/integrations/google/` (conectar, sincronizar, desconectar) |

### Configurar (uma vez)

1. Acesse https://console.cloud.google.com/ e crie um projeto (ex.: `shadow-system`).
2. **APIs e serviços > Biblioteca**: ative a **Google Calendar API**.
3. **Tela de consentimento OAuth**: tipo *Externo*, deixe em *Teste* e adicione seu e-mail em
   *Usuários de teste*.
4. **Credenciais > Criar credenciais > ID do cliente OAuth**, tipo **Aplicativo da Web**.
   Em *URIs de redirecionamento autorizados* coloque exatamente:
   `http://localhost:5050/integrations/google/callback`
5. Baixe o JSON e salve como `instance/google_client_secret.json` (a pasta `instance/` não vai para o git).
6. No `.env`:
   ```
   GOOGLE_CLIENT_SECRETS_FILE=instance/google_client_secret.json
   GOOGLE_REDIRECT_URI=http://localhost:5050/integrations/google/callback
   GOOGLE_CALENDAR_ID=primary
   ```
7. Reinicie o app, abra `/integrations/google/` e clique em **Conectar conta Google**.

> Abra o app por `http://localhost:5050` (não `127.0.0.1`) para o cookie da sessão sobreviver ao retorno
> do Google, já que a URI de redirecionamento usa `localhost`.

### Como funciona

- **Escopos**: `calendar.events` (ler/criar/editar/excluir eventos) e `calendar.readonly` (listar
  calendários e consultar disponibilidade).
- **Token**: `instance/google_token.json`, com refresh token. É uma credencial: não compartilhe e não
  suba para o git. *Desconectar* apaga o arquivo; para revogar no Google use
  https://myaccount.google.com/permissions.
- **HTTP em localhost**: o `oauthlib` exige HTTPS; liberamos HTTP (`OAUTHLIB_INSECURE_TRANSPORT`)
  somente quando a URI de redirecionamento é `http://localhost` ou `http://127.0.0.1`.
- **Proteção do retorno**: o `state` do OAuth fica na sessão e é conferido no callback.

### Sincronização sem duplicar

- **Importar** (Google → Shadow): eventos de 7 dias atrás até 60 dias à frente, com recorrentes
  expandidos. O id do Google é a chave (`calendar_events.google_event_id`, único): importar de novo
  atualiza. Eventos apagados ou cancelados no Google somem do calendário interno.
- **Enviar** (Shadow → Google): cada evento local enviado leva `extendedProperties.private.shadowEventId`.
  Antes de criar, o Shadow procura essa marca no Google; se achar, só vincula. Eventos com essa marca
  são ignorados na importação (já existem aqui).
- Editar no Shadow um evento que veio do Google só muda a cópia local; a próxima importação traz a
  versão do Google de novo. Remover um evento local **não** apaga no Google (escolha segura).

### Limitações

- Sincronização manual (botão *Sincronizar agora*). Agendar automático é parte da camada de automações
  (ver `ROADMAP.md`).
- Um calendário por vez (`GOOGLE_CALENDAR_ID`).
- Eventos importados entram com tipo "Outro"; vincular a quests é feito no Shadow.

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
