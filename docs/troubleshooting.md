# Problemas e soluções

Erros reais que apareceram ao colocar o Shadow System no ar, com a causa e a correção. Cada linha
diz **onde** a mensagem aparece, para achar rápido.

## Hospedagem e banco

| Mensagem | Onde | Causa | Solução |
|---|---|---|---|
| `Blueprint file render.yaml not found on main branch` | Render, criando o Blueprint | O `render.yaml` ainda não estava no GitHub | `git push` e **Retry** |
| `psycopg.OperationalError: [Errno -2] Name or service not known` | Log de build do Render, em `flask db upgrade` | O endereço do banco no `DATABASE_URL` não existe. Quase sempre é a senha com `@`/`/`/`#` (a URI quebra), os colchetes de `[YOUR-PASSWORD]` que ficaram, ou o uso da *Direct connection* (só IPv6) | Senha só com letras e números; URI do **Session pooler** com um único `@`; ver [deployment.md](deployment.md#1-banco-no-supabase) |
| `password authentication failed` | Log de build do Render | Senha do banco errada | Reset da senha em Supabase > Database > Settings e atualizar o `DATABASE_URL` |
| `Tenant or user not found` | Log de build do Render | Usuário `postgres` em vez de `postgres.REF` no pooler | Copiar a URI do Session pooler sem editar o usuário |
| `Produção sem segurança. Defina no .env: ...` | Log do Render ou do PythonAnywhere | Falta `SECRET_KEY`, `AUTH_ENABLED=true` ou `OWNER_PASSWORD_HASH` | Preencher a variável que a mensagem cita |
| `{"database":false,"ok":false}` (HTTP 503) | `/health` | O app está no ar, mas não alcança o banco | Conferir `DATABASE_URL` e se o projeto do Supabase não está pausado |
| O app demora 30 a 60 s para abrir | Navegador | O Render gratuito dormiu (15 min sem acesso) | Conferir o keep-alive ([deployment.md](deployment.md#5-keep-alive-o-app-não-dormir)) |
| `Cannot GET /integrations/google/callback` | Navegador, depois do login do Google | O endereço usado (`shadow-system.onrender.com`) é de outra pessoa; o seu tem um final, como `shadow-system-5v0w` | Usar o link roxo do topo do serviço no Render em todos os lugares |

## Google

| Mensagem | Onde | Causa | Solução |
|---|---|---|---|
| `Erro 400: redirect_uri_mismatch` | Tela de login do Google | A URI enviada pelo app não está cadastrada **exatamente igual** no cliente OAuth | Em "consulte os detalhes do erro" aparece a `redirect_uri` enviada; cadastre-a igual em *URIs de redirecionamento autorizados* e **Salvar** |
| Botão **Salvar** cinza no cliente OAuth | Google Cloud | Há um campo vazio em vermelho (normalmente em *Origens JavaScript autorizadas*) e nada foi salvo | Apagar ou preencher o campo vazio; aí o botão fica azul |
| `O Google não autorizou: InsecureTransportError.` | Shadow System, depois de autorizar | Atrás do proxy do Render o app via o retorno como `http://` | Corrigido no código: o retorno é montado a partir do `GOOGLE_REDIRECT_URI` |
| *"O Google não verificou este app"* | Tela do Google | App em modo Teste | **Avançado** > **Acessar** |
| *"Acesso bloqueado"* (sem `redirect_uri_mismatch`) | Tela do Google | A conta não está nos usuários de teste | Google Auth Platform > **Público-alvo** > **Usuários de teste** > **+ Add users** |
| A tela do Google no app manda editar o `.env` | Shadow System, Integrações > Google | Versão antiga da tela | Já corrigido: no Render a tela mostra o passo do **Secret File** |

## Buffer, Notion, WhatsApp

| Mensagem | Onde | Causa | Solução |
|---|---|---|---|
| `O servidor bloqueou o acesso a api.buffer.com...` | Shadow System | PythonAnywhere gratuito: internet de saída só para sites liberados | Usar o Render, ou pedir a liberação ao PythonAnywhere |
| `Não foi possível falar com o Buffer. Confira a internet.` | Shadow System (versões antigas) | Mesma causa acima; a mensagem antiga não explicava | Atualizado: agora diz qual domínio foi bloqueado |
| `Nenhum banco compartilhado.` | Shadow System, Integrações > Notion | Nada foi compartilhado com a integração, ou o banco está em outro workspace, ou é uma *visualização vinculada* | No Notion, na página ou no banco original: **••• > Conexões > Shadow System**. A integração só enxerga o workspace onde foi criada |

## Como diagnosticar

- **O app está no ar?** Abra `https://SEU-APP.onrender.com/health`.
- **Qual versão está no ar?** No Render, em **Events**, o último *Deploy live* mostra o commit. Pelo
  terminal: `gh api repos/IltonBJSilva/shadow-system/deployments --jq '.[0].sha'`.
- **O keep-alive está rodando?** `gh run list --workflow keep-alive.yml` e o painel do cron-job.org.
- **O token do Notion enxerga o quê?** No Shadow System, Integrações > Notion lista os bancos que a
  integração vê. Lista vazia = nada compartilhado no Notion.
- Ao colar um log no chat ou numa issue, **troque a senha do banco por `***`**.
