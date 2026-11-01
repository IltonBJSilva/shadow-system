# Segurança

O Shadow System guarda dados pessoais (rotina, hábitos, agenda e, no futuro, finanças). As regras:

## Credenciais

- Só no `.env` e em `instance/`. Os dois estão no `.gitignore`, assim como `*.db`, `client_secret*.json`
  e `google_token*.json`.
- O `.env.example` vai para o git **sem valores**.
- Nada de chave ou senha no código, em teste ou em log.
- `SECRET_KEY` precisa ser aleatória (o `run.ps1` gera uma). Se vazar, troque: as sessões abertas caem.
- Token do Buffer: `instance/buffer_token.json`, cadastrado pela tela, nunca exibido (só os 4 últimos
  caracteres). Vence em 90 dias; para invalidar, apague-o no Buffer.
- Token do Google: `instance/google_token.json` contém o refresh token em texto. Proteja a pasta;
  para revogar, *Desconectar* no app e https://myaccount.google.com/permissions.

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
