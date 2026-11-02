# Deploy

Localmente: `.\run.ps1` (http://localhost:5050). Para ter o sistema online com o PC desligado, de graça
e só com o seu acesso, o caminho recomendado é **Render + Supabase** (abaixo). O PythonAnywhere
gratuito também funciona, mas bloqueia Buffer, Notion e WhatsApp até o suporte liberar os domínios.

## Segurança em produção (automática)

Com `SHADOW_ENV=production` o app **se recusa a iniciar** se faltar qualquer um destes:

- `SECRET_KEY` aleatória (não a de exemplo);
- `AUTH_ENABLED=true`;
- `OWNER_PASSWORD_HASH` (gere com `flask --app wsgi security hash-password`).

Também em produção: cookie de sessão só por HTTPS, `TRUST_PROXY=true` (lê `X-Forwarded-Proto` do
proxy HTTPS) e login bloqueado por 15 minutos após 5 senhas erradas. Ver [security.md](security.md).

---

## Render + Supabase (recomendado)

- **Render** (plano gratuito) roda o app Flask. Ele não restringe a internet de saída, então Buffer,
  Notion e WhatsApp funcionam. O disco é apagado a cada deploy e reinício, por isso **nada fica em
  arquivo**: os dados e os tokens ficam no banco.
- **Supabase** (plano gratuito) guarda o banco PostgreSQL.
- **GitHub Actions** (`.github/workflows/keep-alive.yml`) chama `/health` a cada 10 minutos. Assim o
  Render não dorme (o gratuito dorme após 15 min sem acesso) e o Supabase não pausa (o gratuito pausa
  após 7 dias sem uso).

A configuração do Render está em `render.yaml` (Blueprint). Nenhum segredo fica no repositório.

### 1. Banco no Supabase

1. https://supabase.com/dashboard > **New project**. Use um projeto só para o Shadow System, separado
   do da Kausa. Região: **East US (Ohio)** (`us-east-2`), a mesma do Render (`region: ohio` no `render.yaml`).
2. Gere uma senha do banco **só com letras e números** (caracteres como `@`, `#` e `/` quebram a URL).
3. Depois de criado: botão **Connect** (topo) > aba **Connection String** > **Method: Session pooler**
   (aparece como *Shared pooler*) e copie a URI:
   `postgresql://postgres.REF:[YOUR-PASSWORD]@aws-0-us-east-2.pooler.supabase.com:5432/postgres`.
   Use o *Session pooler*, não a *Direct connection*: a direta só tem IPv6, e o Render não alcança.
4. Troque `[YOUR-PASSWORD]` pela senha **sem os colchetes**. A URI final tem um único `@`.

**Esqueceu a senha?** O Supabase não mostra a senha depois de criar o projeto. Gere outra em
**Database** (ícone de cilindro no menu da esquerda) > **Settings** > **Database password** >
**Reset database password** (endereço direto: `supabase.com/dashboard/project/REF/database/settings`).
Ela **não** fica em *Project Settings > General*.

**Não use** o que a aba *App Frameworks* do botão Connect sugere (`pip install supabase`,
`SUPABASE_KEY=sb_publishable_...`, `create_client`): aquilo é para falar com a API REST do Supabase.
O Shadow System conecta direto no PostgreSQL pelo `DATABASE_URL`.

As tabelas não são criadas à mão: o build do Render roda as migrations.

### 2. Hash da senha de login

No seu PC, na pasta do projeto:

```powershell
.venv\Scripts\flask --app wsgi security hash-password
```

Guarde o resultado (começa com `scrypt:`). Ele vira o `OWNER_PASSWORD_HASH`.

### 3. Criar o serviço no Render

1. https://dashboard.render.com > **New** > **Blueprint** > conecte o GitHub e escolha o repositório
   `shadow-system`. O Render lê o `render.yaml`.
2. Ele pede os valores marcados como `sync: false`:
   - `OWNER_USERNAME`: o seu usuário de login;
   - `OWNER_PASSWORD_HASH`: o hash do passo 2;
   - `DATABASE_URL`: a URI do Session pooler do passo 1;
   - `GOOGLE_REDIRECT_URI`: `https://SEU-APP.onrender.com/integrations/google/callback`
     (o endereço aparece no topo da página do serviço no Render; se o nome já existir, ele ganha um final, como `shadow-system-ab12`);
   - `SUPABASE_URL`, `SUPABASE_SECRET_KEY` e `SUPABASE_BUCKET`: só se for enviar imagens do
     computador nos posts; senão deixe vazio.
3. **Apply**. O build instala as dependências, roda `flask db upgrade` e `flask security lock-db`.
   Leva uns 3 a 5 minutos. No log, deu certo quando aparecem, nesta ordem:
   `Running upgrade ... -> d82ccedcb0a2, stored secrets`, `RLS ligado em 17 tabelas.` e
   `==> Your service is live`.
4. Abra `https://SEU-APP.onrender.com/health`: deve aparecer `{"database":true,"ok":true}`. Depois abra
   `https://SEU-APP.onrender.com`: deve aparecer a tela de login.

**O endereço do app não é sempre `shadow-system.onrender.com`.** Endereços no Render são únicos para
todo mundo; como `shadow-system` já era de outra pessoa, o serviço ganhou um final aleatório (no nosso
caso `shadow-system-5v0w.onrender.com`). O endereço certo é o link roxo no topo da página do serviço.
Use **esse** endereço no `GOOGLE_REDIRECT_URI`, no Google Cloud e no keep-alive. Se abrir um endereço
de outra pessoa, aparece algo como `Cannot GET /...` (resposta de um app Node/Express, não do Flask).

Variáveis do serviço (**Environment**):

| Variável | Valor | Quem define |
|---|---|---|
| `SHADOW_ENV` | `production` | `render.yaml` |
| `AUTH_ENABLED` | `true` | `render.yaml` |
| `SECRET_KEY` | aleatória | Render (`generateValue`); não troque, senão as sessões caem |
| `PYTHON_VERSION` | `3.12.7` | `render.yaml` |
| `TIMEZONE` | `America/Sao_Paulo` | `render.yaml` |
| `GOOGLE_CLIENT_SECRETS_FILE` | `/etc/secrets/google_client_secret.json` | `render.yaml` |
| `OWNER_USERNAME` | seu usuário de login | você |
| `OWNER_PASSWORD_HASH` | `scrypt:...` do passo 2 | você |
| `DATABASE_URL` | URI do Session pooler com a senha | você |
| `GOOGLE_REDIRECT_URI` | `https://SEU-APP.onrender.com/integrations/google/callback` | você |
| `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_BUCKET` | vazias (só para enviar imagens do PC) | você |

Depois de mudar uma variável: **Save, rebuild, and deploy**.

### 4. Google no Render

1. No serviço: **Environment** > **Secret Files** > **Add Secret File**. Nome
   `google_client_secret.json`, conteúdo igual ao `instance/google_client_secret.json` do seu PC.
   (O `render.yaml` já aponta `GOOGLE_CLIENT_SECRETS_FILE` para `/etc/secrets/google_client_secret.json`.)
   Dá para reaproveitar o mesmo cliente OAuth do PC, desde que seja do tipo **Aplicativo da Web**
   (no JSON a chave de cima é `"web"`). Não precisa criar projeto nem cliente novo.
2. Google Cloud > **Google Auth Platform** > **Clientes** > seu cliente Web > **URIs de
   redirecionamento autorizados** > **+ Adicionar URI** com a mesma URL do `GOOGLE_REDIRECT_URI`.
   Mantenha a do `localhost` para continuar usando no PC.
3. **Salvar**. Se o botão estiver cinza, há um campo vazio em vermelho (geralmente em *Origens
   JavaScript autorizadas*): apague-o ou preencha com `https://SEU-APP.onrender.com`. Enquanto o
   botão estiver cinza, **nada foi salvo**. A mudança leva de 5 minutos a algumas horas para valer.
4. No sistema online: **Integrações > Google Calendar > Conectar** e **Gmail > Autorizar**. No aviso
   *"O Google não verificou este app"*: **Avançado** > **Acessar**. É o normal no modo Teste.

Se um cliente tiver duas chaves secretas ativas, não apague a que está no JSON enviado ao Render.

O retorno do Google é montado a partir do `GOOGLE_REDIRECT_URI`, e não do endereço que o app vê:
atrás do proxy do Render o app recebe a requisição como `http://`, e o oauthlib recusaria com
`InsecureTransportError` (`app/integrations/google_calendar/routes.py`).

### 5. Keep-alive (o app não dormir)

O Render gratuito desliga o app após **15 minutos sem acesso**, e o próximo acesso leva de 30 a 60 s.
O keep-alive é um robô que abre `/health` de tempos em tempos. Como o `/health` faz um `SELECT 1`, ele
também impede o Supabase gratuito de pausar o projeto (o que acontece após 7 dias sem uso).

São usados dois robôs. Os dois juntos não atrapalham.

**Principal: cron-job.org (pontual, a cada 5 minutos)**

1. https://cron-job.org > **Sign up** (conta pessoal) e confirme o e-mail.
2. **CREATE CRONJOB**:
   - Title: `Shadow System`
   - URL: `https://SEU-APP.onrender.com/health`
   - Execution schedule: **Every 5 minutes**
3. **CREATE**. Em alguns minutos, *Last execution* mostra **200 OK**.

**Reserva: GitHub Actions** (`.github/workflows/keep-alive.yml`, nos minutos 4, 14, 24, ... de cada hora)

1. A URL fica numa variável do repositório. Pelo terminal:
   `gh variable set APP_URL --body "https://SEU-APP.onrender.com"`. Ou pelo site: **Settings** >
   **Secrets and variables** > **Actions** > aba **Variables** (a aba *Secrets* também serve; o
   workflow lê as duas).
2. Teste: **Actions** > **keep-alive** > **Run workflow**, ou `gh workflow run keep-alive.yml`. Deve
   terminar verde e mostrar `{"database":true,"ok":true}` no log.

Por que o GitHub não basta sozinho:

- Execuções agendadas **não têm horário garantido**. Em horários de pico o GitHub atrasa ou pula, e um
  workflow novo pode levar horas para rodar a primeira vez. No primeiro dia, o agendamento a cada
  10 minutos (`*/10`) não rodou nenhuma vez em 3 horas e o app dormiu. Por isso o cron saiu da hora
  cheia e o cron-job.org virou o principal.
- Em repositório público, o GitHub **desliga workflows agendados após 60 dias sem commits** (avisa por
  e-mail; reative em Actions > keep-alive > *Enable workflow*).

Para ver se está rodando: `gh run list --workflow keep-alive.yml` (execuções `schedule` são as
automáticas; `workflow_dispatch` são as manuais).

O Render gratuito dá 750 horas por mês somadas entre os serviços gratuitos. Um serviço ligado o mês
inteiro usa cerca de 744 h, então **não crie outro serviço gratuito** na mesma conta.

### Atualizar

Cada `git push` na `main` faz deploy sozinho (`autoDeploy`), já rodando as migrations.

### Backup

O Supabase gratuito não guarda backups que você possa baixar. Faça um de vez em quando no seu PC:

```powershell
pg_dump "URI_DO_SESSION_POOLER" -Fc -f shadow-backup.dump
```

(`pg_dump` vem com o PostgreSQL: https://www.postgresql.org/download/windows/)

---

## PythonAnywhere (gratuito)

Plano gratuito: app sempre no ar em `https://SEU_USUARIO.pythonanywhere.com`, disco persistente
(o SQLite fica salvo), HTTPS incluso, sem cartão de crédito.

Limites do plano gratuito:

- **Internet de saída restrita** a uma lista de sites liberados (https://www.pythonanywhere.com/whitelist/).
  As APIs do Google estão na lista. Se um domínio não estiver, o app mostra "O servidor bloqueou o
  acesso a ...". Domínios usados: `api.buffer.com` (Buffer), `api.notion.com` (Notion),
  `graph.facebook.com` (WhatsApp) e o seu `*.supabase.co` (imagens). Para liberar, peça no fórum
  (https://www.pythonanywhere.com/forums/) ou por e-mail (support@pythonanywhere.com) informando o
  domínio e o link da documentação pública da API (ex.: https://developers.buffer.com); ou use o
  plano pago, que não tem restrição.
- É preciso entrar no painel e clicar em **"Run until 3 months from today"** a cada 3 meses, senão o
  site é pausado (os dados não se perdem).
- 512 MB de disco e CPU limitada: suficiente para um usuário.

### 1. Criar a conta

Em https://www.pythonanywhere.com > **Pricing & signup** > **Create a Beginner account**.
O nome de usuário vira o endereço (`usuario.pythonanywhere.com`).

### 2. Baixar o código

No painel: **Consoles** > **Bash**:

```bash
git clone https://github.com/IltonBJSilva/shadow-system.git
cd shadow-system
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

(Repositório privado: use `git clone https://SEU_USUARIO_GITHUB:TOKEN@github.com/...` com um token
de acesso do GitHub só de leitura.)

### 3. Criar o `.env` no servidor

Ainda no Bash, dentro de `shadow-system`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"     # copie: é a SECRET_KEY
flask --app wsgi security hash-password                      # digite sua senha; copie o hash
nano .env
```

Conteúdo do `.env` (troque `SEU_USUARIO`):

```
SHADOW_ENV=production
SECRET_KEY=<valor gerado>
TIMEZONE=America/Sao_Paulo
AUTH_ENABLED=true
OWNER_USERNAME=<seu login>
OWNER_PASSWORD_HASH=<hash gerado>
GOOGLE_CLIENT_SECRETS_FILE=instance/google_client_secret.json
GOOGLE_REDIRECT_URI=https://SEU_USUARIO.pythonanywhere.com/integrations/google/callback
GOOGLE_CALENDAR_ID=primary
```

Salve (Ctrl+O, Enter, Ctrl+X) e crie o banco:

```bash
flask --app wsgi db upgrade
```

**Levar seus dados do PC (opcional):** na aba **Files**, envie o seu `instance/shadow.db` para
`/home/SEU_USUARIO/shadow-system/instance/` (substitui o banco vazio). Envie também
`instance/google_client_secret.json`. Os tokens (Buffer, Notion, WhatsApp) você cadastra de novo pelas
telas do sistema.

### 4. Criar o site

**Web** > **Add a new web app** > **Manual configuration** > **Python 3.12**. Depois, na página do app:

- **Virtualenv**: `/home/SEU_USUARIO/shadow-system/.venv`
- **Source code**: `/home/SEU_USUARIO/shadow-system`
- **Static files**: URL `/static/` → Directory `/home/SEU_USUARIO/shadow-system/app/static`
- **Force HTTPS**: ligado
- **WSGI configuration file**: clique no link e troque todo o conteúdo por:

```python
import sys
path = "/home/SEU_USUARIO/shadow-system"
if path not in sys.path:
    sys.path.insert(0, path)

from wsgi import app as application  # noqa: E402
```

Clique em **Reload**. Abra `https://SEU_USUARIO.pythonanywhere.com`: deve aparecer a tela de login.
Se der erro, veja o **Error log** na aba Web (por exemplo, "Produção sem segurança" = falta algo no `.env`).

### 5. Google no servidor

No Google Cloud > **Google Auth Platform** > **Clientes** > seu cliente Web > **URIs de
redirecionamento autorizados** > adicione
`https://SEU_USUARIO.pythonanywhere.com/integrations/google/callback` (mantenha a do localhost).
Depois, no sistema online: **Integrações > Google Calendar > Conectar** e **Gmail > Autorizar**.

### Atualizar para uma versão nova

```bash
cd ~/shadow-system && git pull && source .venv/bin/activate
pip install -r requirements.txt && flask --app wsgi db upgrade
```

E clique em **Reload** na aba Web.

### Backup

`flask --app wsgi backup create` no Bash, ou baixe `instance/shadow.db` pela aba **Files**.

---

## Outro servidor (VPS)

1. Mesmo `.env` de produção acima (`DATABASE_URL` para PostgreSQL, se quiser; ver [database.md](database.md)).
2. `flask --app wsgi db upgrade` a cada versão nova.
3. `waitress-serve --listen=127.0.0.1:5050 --call app:create_app` atrás de um proxy HTTPS (Caddy, Nginx).
4. Adicione a URI de redirecionamento do domínio no Google Cloud e em `GOOGLE_REDIRECT_URI`.

## Ainda não feito

- Dockerfile / docker-compose.
- Agendador para `flask quests rollover` e sincronização do Google (hoje o rollover roda ao abrir o
  dashboard ou a lista de quests).
