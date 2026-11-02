# Segurança

O Shadow System guarda dados pessoais (rotina, hábitos, agenda e, no futuro, finanças). As regras:

## Credenciais

- Só no `.env` e em `instance/`. Os dois estão no `.gitignore`, assim como `*.db`, `client_secret*.json`
  e `google_token*.json`.
- O `.env.example` vai para o git **sem valores**.
- Nada de chave ou senha no código, em teste ou em log.
- `SECRET_KEY` precisa ser aleatória (o `run.ps1` gera uma). Se vazar, troque: as sessões abertas caem.
- Tokens cadastrados pela tela (Buffer, Notion, WhatsApp e o refresh token do Google) ficam no banco,
  na tabela `stored_secrets`, em texto. Nunca são exibidos (só os 4 últimos caracteres). Quem tiver
  acesso ao banco tem acesso a eles: proteja a senha do banco e o arquivo `instance/shadow.db`.
  Arquivos antigos (`instance/*_token.json`, `instance/credentials/`) são importados e apagados na
  primeira leitura.
- **Supabase**: ele publica as tabelas do schema `public` numa API REST acessível com a chave
  pública do projeto. O `flask security lock-db` (roda sozinho no build do Render) liga RLS sem
  policies em todas as tabelas, e essa API não lê nem grava nada. O app não é afetado porque
  conecta como dono das tabelas. Rode o comando de novo sempre que uma migration criar uma tabela.
- Token do Buffer vence em 90 dias; para invalidar, apague-o no Buffer. Para revogar o Google,
  *Desconectar* no app e https://myaccount.google.com/permissions.

## Acesso

- Com `AUTH_ENABLED=false` (padrão), qualquer um que alcance a porta usa o app. Por isso o `run.ps1`
  escuta só em `127.0.0.1`.
- Antes de expor em rede (outro PC, servidor, internet):
  ```powershell
  .\.venv\Scripts\flask --app wsgi security hash-password
  ```
  e no `.env`: `AUTH_ENABLED=true`, `OWNER_USERNAME=...`, `OWNER_PASSWORD_HASH=<resultado>`.
  Todas as páginas passam a exigir login (menos `/health`).
- Em produção use HTTPS (cookie de sessão `Secure` em `ProductionConfig`).
- `SHADOW_ENV=production` não inicia sem `SECRET_KEY` própria, `AUTH_ENABLED=true` e
  `OWNER_PASSWORD_HASH`: o sistema nunca fica aberto na internet por engano.
- Login bloqueado por 15 minutos após 5 senhas erradas do mesmo IP (responde 429). O contador fica na
  memória do processo e zera ao reiniciar.
- Sessão do login dura 31 dias (`session.permanent`); **Sair** encerra na hora.

## Proteções da aplicação

| Proteção | Onde |
|---|---|
| CSRF em todo POST | `Flask-WTF CSRFProtect` (`app/extensions.py`) |
| `state` do OAuth conferido no retorno do Google | `integrations/google_calendar/routes.py` |
| Redirecionamento só para caminhos internos | `core/http.py`, `core/security.py`, `core/errors.py` |
| CSP sem script inline, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy` | `core/security.py` |
| Cookies `HttpOnly` e `SameSite=Lax` | `config.py` |
| Comparação de usuário em tempo constante e senha com hash | `core/security.py` |
| Validação de entrada em formulários e de novo nos serviços | `forms.py` + `services.py` |
| Constraints no banco para regras críticas | ver [database.md](database.md) |
| Erro 500 sem stack trace para o usuário e log sem dados pessoais | `core/errors.py` |

## Dados enviados para fora

- **Google Calendar**: só quando você conecta e clica em sincronizar/enviar. Vai título, descrição, local e
  horário dos eventos locais.
- **Buffer**: só quando você envia um post (texto, links das imagens, horário), depois de marcar a confirmação.
- **Gmail**: só leitura; nada é enviado ao Gmail.
- **Notion**: só leitura; nada é escrito no Notion.
- **WhatsApp**: o resumo do dia (nível, títulos de quests/hábitos/eventos de hoje) vai para o **seu**
  número, só quando você clica em enviar.
- **Supabase Storage** (se configurado): as imagens enviadas do computador ficam com link público.
- **IA (futuro)**: nenhum dado pessoal será enviado a um provedor sem configuração explícita e aviso.

## Backups e recuperação

```powershell
.\.venv\Scripts\flask --app wsgi backup create   # copia instance/shadow.db para instance/backups/
.\.venv\Scripts\flask --app wsgi backup list
```

Restaurar (SQLite): pare o app, copie o backup escolhido por cima de `instance/shadow.db`, inicie.
Guarde cópias fora do computador (ex.: pasta sincronizada criptografada). Os backups contêm dados pessoais.

PostgreSQL: `pg_dump -Fc shadow_system > shadow.dump` e `pg_restore -d shadow_system shadow.dump`.
