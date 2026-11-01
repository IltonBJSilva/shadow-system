# Integrações

Todas são **opcionais**. Sem nenhuma configurada, o Shadow System funciona normalmente.

| Integração | Pasta | Estado |
|---|---|---|
| Google Calendar | `app/integrations/google_calendar/` | OAuth 2.0, importar/enviar eventos, disponibilidade |
| Gmail | `app/integrations/gmail/` | Somente leitura: não lidos, e-mail vira quest |
| Buffer (conta pessoal) | `app/integrations/buffer/` | Token pela tela, canais, posts, novo agendamento |
| Notion | `app/integrations/notion/` | Token pela tela, bancos de dados, importar páginas como quests |
| WhatsApp (Cloud API) | `app/integrations/whatsapp/` | Credenciais pela tela, resumo do dia para o seu número |
| Shadow AI | — | Planejada (ver `ROADMAP.md`) |

A tela `/integrations/` mostra a situação de cada uma (`app/integrations/registry.py`).

## Regras da camada de integrações

- Cada integração fica em `app/integrations/<nome>/`, com um **cliente** que fala com a API externa e
  não conhece os modelos dos módulos.
- Os módulos podem usar integrações; integrações podem chamar a API pública dos módulos
  (`services.py`) para gravar dados. Integrações nunca importam `models.py` de módulos.
- Erros externos viram uma exceção própria da integração (ex.: `BufferError`) com mensagem
  para o usuário. Telas que mostram dados externos usam versões "safe" que nunca quebram a página.
- Credenciais só no `.env` ou em `instance/` (fora do git). Nunca no código, nunca em log.
- **Token só quando você gerar**: nenhuma integração é obrigatória. Cada uma tem uma tela que explica como
  gerar o token e um campo para colar; o token é conferido na API antes de salvar e nunca volta para a tela.
  Os de Notion e WhatsApp ficam em `instance/credentials/<nome>.json` (`app/integrations/credentials.py`).
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

## Buffer (conta pessoal)

Integração direta com o **seu** Buffer, para os seus perfis pessoais (LinkedIn, Instagram...).
Substitui o leitor do Kausa Social Scheduler, que é da Kausa e continua separado e intocado.

| Arquivo | Responsabilidade |
|---|---|
| `client.py` | `BufferClient`: GraphQL em `https://api.buffer.com` (organização, canais, posts, `createPost`) |
| `posting.py` | Regras por rede: metadados do Instagram/Facebook, limite de hashtags e de texto, `dueAt` em UTC |
| `token_store.py` | Token salvo pela tela em `instance/buffer_token.json`, mascarado, aviso de vencimento |
| `storage.py` | Hospedagem opcional das imagens enviadas do computador (Supabase Storage) |
| `__init__.py` | Funções de alto nível: `save_token`, `channels`, `posts`, `schedule`, `scheduled_posts_safe` |
| `routes.py` | `/integrations/buffer/` (posts por status), `/token`, `/new` |

### Cadastrar o token (pela tela)

1. No Buffer da sua conta pessoal, abra https://publish.buffer.com/settings/api e crie um token com
   todas as permissões.
2. No Shadow System: menu **Postagens** (ou Integrações > Buffer) > **Token**, cole o token e a data de criação.
3. O token é **conferido no Buffer antes de salvar**. Fica em `instance/buffer_token.json` (fora do git),
   nunca aparece de novo na tela (só `••••` + 4 últimos caracteres) e nunca vai para log.
4. Tokens do Buffer vencem em **90 dias**: a tela e a integração avisam 15 dias antes.

Alternativa: `BUFFER_API_KEY` e `BUFFER_KEY_CREATED_AT` no `.env`. O token da tela tem prioridade.

### Novo post

- Escolha os canais, um **texto padrão** e, se quiser, um **texto por rede** (ex.: LinkedIn mais longo,
  Instagram com emojis e hashtags), como nos posts de `E:\Repositorio\postagens`.
- **Imagens**: links públicos (um por linha, na ordem do carrossel) ou, com hospedagem configurada,
  arquivos do computador. O Buffer não recebe arquivo: ele baixa a imagem por um link público.
- **Modo**: data e hora definidas (horário de Brasília), próximo horário da fila ou publicar agora.
- É preciso marcar a **confirmação** antes de enviar (publicar é uma ação pública).
- Tudo é validado **antes** de enviar qualquer coisa. Se um canal falhar (ex.: fila cheia do plano
  gratuito), os outros continuam e cada resultado aparece na tela.

### Regras por rede (já validadas na API real)

- **Instagram**: `metadata.instagram = {type: "post", shouldShareToFeed: true}`; várias imagens viram
  carrossel; no máximo 5 hashtags (as extras são removidas, `#PraTodosVerem` sempre fica); até 2.200
  caracteres; precisa de imagem.
- **Facebook**: `metadata.facebook = {type: "post"}`.
- **LinkedIn**: até 3.000 caracteres.
- **YouTube** não aparece para posts de imagem (pede vídeo).

### Hospedagem das imagens (opcional)

Para enviar imagens do computador, configure um bucket **público** no Supabase Storage:

```
SUPABASE_URL=https://<projeto>.supabase.co
SUPABASE_SECRET_KEY=<service role / secret key>
SUPABASE_BUCKET=<nome do bucket>
```

Tudo que vai para um bucket público fica acessível por link: não envie nada privado.

### Limitações

- **Stories**: não implementado. Não foi verificado se a API pública do Buffer agenda Stories do
  Instagram; conferir na documentação oficial antes.
- **Collab e marcação de pessoas no Instagram** não existem na API pública do Buffer.
- **Plano gratuito**: limite de posts agendados por canal (a fila enche; o Buffer devolve erro e a tela mostra).
- **Limite de uso da API**: muitas chamadas seguidas dão erro 429; espere alguns minutos.
- Editar ou apagar posts já agendados ainda é feito no Buffer.
- A listagem mostra até 50 posts por status.

### Segurança dos scripts antigos

Os scripts em `E:\Repositorio\postagens` (`check_buffer.js`, `check_posts.js`, `promover_rascunhos.js`)
têm um token do Buffer escrito no código. Depois de cadastrar um token novo no Shadow System, apague o
antigo no Buffer e remova-o desses arquivos.

---

## Gmail (somente leitura)

Usa a **mesma conta e o mesmo cliente OAuth do Google Calendar**. O escopo do Gmail
(`gmail.readonly`) só é pedido quando você clica em **Autorizar Gmail** em `/integrations/gmail/`.

1. No mesmo projeto do Google Cloud Console, ative a **Gmail API**.
2. Abra `/integrations/gmail/` > **Autorizar Gmail** (o Google mostra a permissão de leitura).

O que faz: mostra os não lidos da caixa de entrada (também no widget do dashboard) e o botão
**Virar quest** cria `Responder: <assunto>` com prazo hoje. Não envia, não marca e não apaga e-mails.

API (biblioteca oficial): `users.labels.get` (contagem), `users.messages.list` (`q="is:unread in:inbox"`),
`users.messages.get` (`format="metadata"`, só remetente/assunto/data e o trecho).

---

## Notion

1. Em https://www.notion.so/my-integrations crie uma integração **interna** com *Read content*.
2. Copie o **Internal Integration Secret** e cole em `/integrations/notion/` (conferido com `GET /v1/users/me`).
3. No Notion, em cada banco de dados: **••• > Conexões** > escolha a integração.

O que faz: lista os bancos compartilhados (`POST /v1/search`), mostra as páginas
(`POST /v1/databases/{id}/query`) e importa as escolhidas como quests: título → título, primeira
propriedade de data → prazo, link da página na descrição. Páginas já importadas não duplicam (ids em
`app_settings`, chave `notion.imported_pages`). Versão da API fixada em `2022-06-28`.

Limitações: só leitura (nada é escrito no Notion); até 50 páginas por banco; status da quest não volta
para o Notion.

---

## WhatsApp (Cloud API da Meta)

1. Em https://developers.facebook.com/apps crie um app **Empresa** e adicione o produto **WhatsApp**.
2. Em **WhatsApp > Configuração da API**: copie o **token de acesso** e o **Phone number ID** do número
   de teste, e adicione o seu número na lista de destinatários.
3. Cole em `/integrations/whatsapp/` com o seu número (DDI + DDD + número). É conferido com
   `GET /{phone-number-id}`.

O que faz: **Enviar resumo para mim** manda o resumo do dia (nível, quests de hoje, hábitos pendentes,
agenda) e **Enviar teste** manda o template `hello_world`. Envio por `POST /{phone-number-id}/messages`
(Graph API `v21.0`).

Regras e segurança:
- Mensagens só vão para **o seu número cadastrado** e só quando você clica. Nada é enviado sozinho.
- Texto livre só é entregue se você mandou mensagem para o número da empresa nas **últimas 24h**
  (regra do WhatsApp). Fora disso, só templates aprovados.
- O token temporário do painel vale 24h. Para um permanente, gere um token de *usuário do sistema* no
  Gerenciador de Negócios com a permissão `whatsapp_business_messaging`.
