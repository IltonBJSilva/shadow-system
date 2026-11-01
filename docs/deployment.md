# Deploy

Hoje o Shadow System roda localmente (`.\run.ps1`). Para rodar em outro lugar:

## Checklist

1. `SHADOW_ENV=production` (ativa `ProductionConfig`: cookie de sessão só por HTTPS).
2. `SECRET_KEY` aleatória e exclusiva do servidor.
3. Login ligado (`AUTH_ENABLED=true` + hash da senha). Ver [security.md](security.md).
4. Banco: PostgreSQL recomendado (`DATABASE_URL`). Ver [database.md](database.md).
5. `flask --app wsgi db upgrade` a cada versão nova.
6. HTTPS na frente (proxy reverso: Caddy, Nginx ou Traefik).
7. Google Calendar: adicione a URI de redirecionamento do domínio no Google Cloud e em `GOOGLE_REDIRECT_URI`.
8. Backups automáticos do banco.

## Servidor WSGI

Windows:
```powershell
.\.venv\Scripts\waitress-serve --listen=127.0.0.1:5050 --call app:create_app
```

Linux (waitress também funciona; gunicorn é a alternativa comum):
```bash
waitress-serve --listen=127.0.0.1:5050 --call app:create_app
```

O proxy reverso recebe HTTPS na porta 443 e repassa para `127.0.0.1:5050`.

## Ainda não feito

- Dockerfile / docker-compose.
- Agendador para `flask quests rollover` e sincronização do Google (hoje o rollover roda ao abrir o
  dashboard ou a lista de quests; no Windows dá para agendar o comando no Agendador de Tarefas).
