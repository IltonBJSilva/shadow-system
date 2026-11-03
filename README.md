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

> **"SE ESSE SISTEMA QUER ME USAR, ENTÃO EU VOU USAR O SISTEMA."**

O Shadow System é o meu **RPG da vida real**: um sistema pessoal de evolução com a estética das janelas
de *System* dos animes de RPG. Faculdade, carreira, treino, estudos, finanças, música, hobbies,
espiritualidade e projetos pessoais viram **missões (quests)**, e cada atividade real registrada vira
**XP**, **níveis**, **ranks**, **atributos** e **conquistas**.

**A filosofia:** eu não sou um personagem controlado pelo sistema. **Eu sou o jogador.** O sistema
acompanha, mede, aponta padrões e sugere; quem decide sou eu. Por isso:

- nada vira missão sem eu aceitar (nem as sugestões do Arquiteto);
- punições existem, mas são justas: nunca fazem perder nível, e uma falha por **imprevisto** ou
  **limitação real** devolve o XP (*Zona de Falha*);
- toda conclusão do Arquiteto cita o dado que a gerou: nada é inventado.

**O problema:** tarefas, agenda, hábitos, treinos e metas ficam espalhados em apps diferentes, e é difícil
enxergar evolução ao longo do tempo.

**A ideia:** um lugar só, com uma camada de RPG que incentiva **constância** (bônus por sequência,
combos, conquistas) e um mentor, **o Arquiteto**, que lê os dados reais e ajuda a organizar a rotina.

**Por que foi feito assim:** além de ferramenta, o projeto é meu **manual de desenvolvimento**. O código é
organizado para ser lido e modificado sem depender de ninguém, com regras de negócio documentadas e
testadas.

## Funcionalidades

### Implementado

- [x] **Inicialização do System**: sequência de abertura com o manifesto, sons sintetizados, pula com clique ou Esc; uma vez por sessão, sempre no Dashboard ou desligada
- [x] **Áudio do System**: voz de entrada, música de fundo que não reinicia entre páginas, vozes de level up/conquista/falha e controles de volume
- [x] **Usuários de teste**: convite por link (sem Google), cada conta com os próprios dados isolados
- [x] **O Arquiteto**: mentor que analisa os dados reais (desempenho por área, falhas, sequências, atributos parados, metas), indica o que fazer primeiro e sugere missões para você aceitar; com uma chave da Anthropic, conversa e monta planos com o Claude
- [x] **Metas**: registre objetivos ("Passar em Cálculo II"); o Arquiteto sugere o próximo passo e uma sessão semanal
- [x] **Zona de Falha**: toda missão recorrente não feita fica registrada; você diz o motivo (procrastinação, planejamento, imprevisto, limitação real) e os motivos escolhidos devolvem o XP e cancelam a Penalty Quest
- [x] **Conquistas**: 21 conquistas com ícone, recompensa em XP (uma vez) e título; notificação especial ao desbloquear
- [x] **LEVEL UP** em tela cheia com o novo nível e o novo rank

- [x] **Hunter Profile**: nível, rank configurável (E → SS → especiais), XP com curva linear, 10 atributos (incluindo Sabedoria e Carisma), evolução semanal dos atributos, histórico
- [x] **Títulos**: cada conquista dá um título; você escolhe qual exibir e pode criar os seus
- [x] **Quest System**: 8 tipos (Daily, Weekly, Monthly, Main, Side, Habit, Emergency, Custom), categorias, prioridade, dificuldade, prazo, critérios, recompensas, atributos, histórico
- [x] **Categorias sugeridas**: Faculdade, Carreira, Estudos, Treino, Saúde, Finanças, Música e arte, Hobbies, Organização, Espiritualidade, Projetos pessoais e Conteúdo, já ligadas aos atributos
- [x] **Quests recorrentes** (diária, semanal, mensal) sem punição por dia perdido
- [x] **Ações em massa** nas quests: marcar várias e cancelar ou excluir
- [x] **Gamificação**: bônus, punições configuráveis, Penalty Quests com redenção, sons e janelas do *System*
- [x] **Hábitos**: todos os dias ou em dias escolhidos (folga não quebra a sequência), streak atual e recorde, correção de dias esquecidos, estorno exato de XP
- [x] **Treinos**: rotinas prontas (ABC, Full body, Superior/Inferior, PPL, em casa, corrida), texto colado ou documento (PDF, Word, texto) viram quests semanais, eventos no calendário, hábito de treino e sugestão de progressão de carga
- [x] **Calendário interno**: visão mensal, eventos ligados a quests, prazos de quests, aviso de conflito de horário
- [x] **Dashboard** estilo janela de status, com widgets configuráveis: sequência de dias evoluindo, semana atual x anterior, concluídas hoje, quanto falta para o próximo nível
- [x] **Google Calendar**: OAuth 2.0, importar e enviar eventos sem duplicar, disponibilidade (opcional)
- [x] **Gmail** (somente leitura): não lidos no dashboard, busca por texto com filtros (remetente, período, anexo, pasta), e-mail vira quest (opcional)
- [x] **Notion**: importar páginas de bancos de dados como quests, sem duplicar (opcional)
- [x] **WhatsApp** (Cloud API): resumo do dia enviado para o seu número (opcional)
- [x] **Postagens (Buffer pessoal)**: token cadastrado pela tela, canais, posts agendados/rascunhos/enviados, novo post com texto por rede, carrossel no Instagram (opcional)
- [x] Login opcional do dono, CSRF, cabeçalhos de segurança, backup do SQLite

### Planejado

- [ ] Fitness: peso e medidas, cardio, gráficos de evolução de carga (os treinos já existem)
- [ ] Financial System (receitas, despesas, contas, cartões, orçamento, metas, BRL)
- [ ] University System (disciplinas, provas, trabalhos, notas com regras configuráveis, frequência)
- [ ] Study System (cursos, sessões de estudo, revisões)
- [ ] Career System (pipeline de candidaturas)
- [ ] Hobbies (Gaming, Música, Game Dev, Writing e personalizados)
- [ ] Social Media e Instagram Stories (planejamento de sequências, calendário editorial)
- [ ] Automações agendadas e relatórios semanais

Detalhes e ordem em [ROADMAP.md](ROADMAP.md).

## Regras do jogo

Todas as regras ficam em funções puras e testadas; os valores são editáveis pela tela (Gamificação,
Hunter > Ranks) ou num arquivo só ([progression.py](app/modules/hunter/progression.py)).

### XP de uma missão

XP padrão = **dificuldade (esforço) × importância (prioridade)**, arredondado para múltiplo de 5. Você pode
digitar outro valor na missão.

| Dificuldade | XP base | × Baixa (0,8) | × Média (1,0) | × Alta (1,2) | × Crítica (1,4) |
|---|---|---|---|---|---|
| 1 Trivial | 10 | 10 | 10 | 10 | 15 |
| 2 Fácil | 25 | 20 | 25 | 30 | 35 |
| 3 Normal | 50 | 40 | 50 | 60 | 70 |
| 4 Difícil | 100 | 80 | 100 | 120 | 140 |
| 5 Extrema | 200 | 160 | 200 | 240 | 280 |

A importância pesa no máximo ±40%: uma tarefa trivial marcada como "crítica" continua valendo pouco. Bônus
(primeira missão do dia, combo das Daily Quests, adiantar prazo, sequência de hábitos) e recompensas de
conquista somam por cima; os valores ficam em Gamificação.

### Níveis e ranks

Para sair do nível N são precisos **100 + 50 × (N − 1) XP** (nível 1→2: 100; 2→3: 150; 10→11: 550). A curva
é linear de propósito: cresce, mas nunca fica impossível. Ranks padrão (editáveis): E (nível 1), D (10),
C (20), B (35), A (50), S (70), SS (90), National Level (120) e Shadow Monarch (150). Subir de nível abre a
janela de **LEVEL UP** com o novo nível e, se houver, o novo rank.

### Atributos

Cada missão concluída dá pontos aos atributos dela (ou aos da categoria, se ela não escolher), iguais à
dificuldade (1 a 5). Hábitos dão +1. A evolução semana a semana aparece no perfil do Hunter.

| Atributo | Desenvolvido por (categorias sugeridas) |
|---|---|
| Strength (Força) | Treino |
| Vitality (Vitalidade) | Treino, Saúde e bem-estar |
| Intelligence (Inteligência) | Faculdade, Carreira, Estudos, Projetos pessoais |
| Wisdom (Sabedoria) | Faculdade, Estudos, Espiritualidade |
| Focus (Foco) | Faculdade, Estudos, Hobbies, Organização pessoal |
| Discipline (Disciplina) | Carreira, Treino, Saúde, Finanças, Organização pessoal, Projetos pessoais |
| Charisma (Carisma) | Carreira, Música e arte, Conteúdo |
| Creativity (Criatividade) | Música e arte, Hobbies, Projetos pessoais, Conteúdo |
| Financial Intelligence | Finanças |
| Spirituality (Espiritualidade) | Espiritualidade |

Nomes e descrições são editáveis em Hunter > Atributos. São indicadores da sua evolução, não avaliação de
capacidade.

### Punições e Zona de Falha

Uma missão **recorrente** que passa do prazo vira *Não realizada*: tira um pouco de XP (padrão 10% do XP
dela, **nunca** faz cair de nível) e gera uma **Penalty Quest** que devolve o XP se for cumprida no dia. A
falha vai para a **Zona de Falha**, onde você escolhe o motivo:

| Motivo | O que acontece (padrão, configurável) |
|---|---|
| Procrastinação | A punição fica; o System sugere começar por 15 minutos |
| Falta de planejamento | A punição fica; o System sugere rever prazo e recorrência |
| Imprevisto | XP devolvido e Penalty Quest cancelada |
| Limitação real | XP devolvido e Penalty Quest cancelada |

Missões sem repetição e Penalty Quests não geram punição. Tudo pode ser desligado em Gamificação.

### Conquistas

21 conquistas, conferidas a cada XP ganho: primeira missão, primeiro level up, semana consistente (7 dias
seguidos com XP), 30 dias de evolução, primeiro projeto (Main Quest), 10/50/100/200 missões, sequências de
7/30/100 dias num hábito, 1/20/100 treinos, níveis 10/25/50/100 e 10.000 XP. Cada uma tem ícone, data, título
e uma recompensa em XP paga uma vez (desligável em Gamificação). Lista completa em
[docs/modules/hunter.md](docs/modules/hunter.md#conquistas-e-títulos).

## O Arquiteto

O mentor do sistema (menu **Arquiteto**). Ele não dá ordens nem frases motivacionais: lê os seus dados e
aponta o que fazer.

**Modo regras (sempre ligado, sem custo).** Funciona sem internet e sem chave:

- **Leitura do momento:** ritmo desta semana x a anterior, sequência de evolução, level up perto,
  missões atrasadas acumulando, sequências de hábito em risco, áreas com taxa de conclusão baixa (desafio
  acima do momento) ou alta com dificuldade baixa (pronto para subir), padrão nas falhas, atributos parados,
  treino da semana incompleto e metas sem nenhuma missão ligada. Cada item cita o número que o gerou.
- **Faça primeiro:** até 3 missões, na ordem atrasadas → prazo hoje → prioridade.
- **Missões sugeridas:** rascunhos com o motivo ("Só 0% das missões de Faculdade foram feitas..."). Você
  aceita (vira quest) ou descarta (a mesma regra não volta por 14 dias).
- **Metas:** sem missão ligada, a meta ganha a sugestão de um próximo passo e de uma sessão semanal.

**Modo IA (opcional, com o Claude da Anthropic).** Em Arquiteto > *Ligar a IA*, cadastre uma chave da API
(console.anthropic.com). Ela é conferida antes de salvar, fica só no servidor e nunca volta para a tela.
Com ela:

- **Conversa:** perguntas sobre rotina, prioridades e metas, respondidas com base nos seus dados reais. O
  Arquiteto lembra da conversa (últimas 20 falas).
- **Plano de missões:** de 3 a 6 missões para os próximos 7 dias, com foco opcional, em formato
  estruturado. Elas entram como sugestões: nada vira quest sem você aceitar.
- Modelo padrão: Claude Opus 5.5 (dá para trocar por Sonnet 5.5 ou Haiku 5.5, mais baratos). Se o filtro de
  segurança recusar um pedido, a própria API tenta num modelo alternativo (`fallbacks: "default"`).
- **Custo:** cobrado pela Anthropic na sua conta, por uso (em geral centavos por pergunta).
- **O que é enviado:** nível, atributos, missões ativas, desempenho por área, falhas por motivo, hábitos,
  treinos e metas. Tokens, senhas e e-mails nunca são enviados.

Detalhes em [docs/modules/architect.md](docs/modules/architect.md).

## Áudio e visual do System

### Como funciona o áudio

Tudo passa por um só lugar, `app/static/js/sounds.js` (`window.ShadowAudio`):

| Camada | O que é | Quando toca |
|---|---|---|
| **Áudio de entrada** | Voz "Se esse sistema tá querendo me usar, então eu vou usar o sistema." | Uma vez por sessão do navegador, ao entrar no System (junto da animação de inicialização). Navegar entre páginas não repete. |
| **Música de fundo** | DARK ARIA (SawanoHiroyuki[nZk]:XAI) em loop | Depois da voz de entrada. Continua tocando entre as páginas sem reiniciar. |
| **Vozes de eventos** | "Eu me esforcei tanto pra chegar até aqui!" (LEVEL UP), "Não é coincidência, nem boa vontade." (conquista), "Se eu tivesse mais uma chance..." (Zona de Falha) | Junto da janela do evento. A música abaixa enquanto a voz toca. |
| **Efeitos sintetizados** | Tons curtos gerados na hora (sem arquivo) | Missão concluída, bônus, notificação, abertura de painel, erro. Também substituem as vozes quando não há arquivo. |

- **Autoplay:** os navegadores bloqueiam som antes de uma interação. O que for bloqueado toca no primeiro toque
  ou tecla. Depois do login, como você clicou em *Entrar*, a entrada normalmente toca na hora.
- **A música não reinicia:** a navegação usa o [Turbo](https://turbo.hotwired.dev/) (`static/js/vendor/`), que troca
  só o conteúdo da página sem recarregar a janela. Num recarregamento completo (F5), a música continua do ponto
  em que parou.
- **Sem sobreposição:** uma voz nova interrompe a anterior, e o mesmo efeito não toca duas vezes seguidas.
- **iPhone/iPad:** o volume passa por um GainNode da Web Audio API, porque lá o volume do `<audio>` é só leitura.

### Configurações de áudio

Em **Configurações** (menu lateral) cada pessoa controla, neste aparelho: música de fundo (liga/desliga), volume
da música, efeitos sonoros (liga/desliga), volume dos efeitos e áudio de entrada (liga/desliga). Fica salvo no
navegador (`localStorage`). Atalhos no menu lateral: **♫ Música** e **🔊 Efeitos**. Com tudo desligado, o sistema
funciona igual, em silêncio.

### Mídias do System (onde ficam os arquivos)

Os áudios e as imagens **não estão no repositório**: ele é público e a trilha e as cenas do anime têm direitos
autorais. Eles ficam no banco (tabela `media_assets`) e são enviados pelo dono em
**Configurações > Mídias do System**. Todos os usuários ouvem e veem os mesmos arquivos; só a imagem da tela de
acesso pode ser lida sem login.

| Slot | Uso | Arquivo usado (extraído dos vídeos/imagens locais) |
|---|---|---|
| `entrance` | Voz de entrada | `entrance.mp3` (80 kbps mono, ~47 KB) |
| `music` | Música de fundo | `music.mp3` (DARK ARIA, 128 kbps, ~2,1 MB) |
| `levelup` | LEVEL UP | `levelup.mp3` (~33 KB) |
| `achievement` | Conquista / recompensa | `achievement.mp3` (~32 KB) |
| `penalty` | Zona de Falha | `penalty.mp3` (~44 KB) |
| `boot` | Arte da inicialização | `boot.webp` (~35 KB) |
| `background` | Arte discreta atrás da janela de status | `background.webp` (~50 KB) |
| `login` | Arte do login e do convite | `login.webp` (~74 KB) |

Para importar uma pasta de uma vez (nomes iguais aos slots): `flask --app wsgi media import instance/media`.
`flask --app wsgi media list` mostra o que está cadastrado. Sem arquivo num slot, o System usa o som
sintetizado e o visual em CSS (portal, névoa de sombras, cantos de HUD).

### Adicionar um efeito sonoro novo

1. Inclua o slot em `SLOTS` (`app/core/media.py`), com rótulo, tipo `audio` e descrição.
2. Se for uma voz de evento, inclua o nome em `VOICE_SLOTS` (`sounds.js`); se for um tom curto, crie a função em `SYNTH`.
3. Toque com `ShadowAudio.play("<slot>")` (ou mande uma mensagem flash da categoria correspondente).
4. Envie o arquivo em Configurações > Mídias do System.

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

### Usuários de teste (outra pessoa testar o sistema)

1. Entre como dono e abra **Usuários de teste** (menu lateral, embaixo).
2. Cadastre o e-mail da pessoa e clique em *Gerar link de convite*.
3. Copie o link ou envie direto pelo WhatsApp. Ele vale 7 dias e só funciona uma vez.
4. A pessoa abre o link, escolhe nome e senha e já cai no Dashboard, com um Hunter novo e vazio (uns 30 segundos).
   Depois ela entra pela tela de login com e-mail e senha.

Cada conta tem os próprios dados (Hunter, missões, hábitos, treinos, conquistas, configurações e tokens): ninguém vê
os dados de ninguém. Você pode bloquear, gerar link novo ou apagar a conta (com todos os dados) na mesma tela.

**Google é opcional.** O login do sistema é por senha; conectar Google Calendar ou Gmail é uma autorização separada,
em **Integrações**, feita por cada pessoa com a própria conta Google. Enquanto o app do Google estiver em modo teste,
o e-mail Google dela também precisa estar em *Google Cloud > Google Auth Platform > Público-alvo > Usuários de teste*.
Detalhes de segurança em [docs/security.md](docs/security.md#contas-e-isolamento-dos-dados).

### Online (sem o PC ligado)

Em produção o Shadow System roda no **Render** (app) com o banco no **Supabase** (PostgreSQL), os dois
no plano gratuito, e um keep-alive (cron-job.org + GitHub Actions) para o app não dormir. Cada
`git push` na `main` faz deploy sozinho. Passo a passo em [docs/deployment.md](docs/deployment.md);
erros comuns em [docs/troubleshooting.md](docs/troubleshooting.md).

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

**Integrações são opcionais.** Sem nenhuma, o app funciona por completo. Os tokens de Buffer, Notion e
WhatsApp são cadastrados **pela tela**, só quando você gerar (Integrações > escolha a integração). Como configurar cada uma:
[docs/integrations.md](docs/integrations.md). A chave da IA do Arquiteto também é cadastrada pela tela
(Arquiteto > Ligar a IA), não no `.env`.

## Arquitetura

**Monólito modular**: uma única aplicação Flask, um banco, um processo, organizada em módulos com
responsabilidades separadas.

| Tecnologia | Uso |
|---|---|
| Python 3.12, Flask 3 | Aplicação web (Application Factory + Blueprints) |
| SQLAlchemy 2, Flask-SQLAlchemy | Modelos e consultas |
| Flask-Migrate (Alembic) | Migrations |
| SQLite / PostgreSQL | SQLite local; PostgreSQL (Supabase) em produção, via `DATABASE_URL` |
| Flask-WTF | Formulários, validação e CSRF |
| httpx | Cliente HTTP do Buffer (GraphQL) |
| google-auth-oauthlib, google-api-python-client | Google Calendar e Gmail |
| anthropic (SDK oficial) | IA opcional do Arquiteto (Claude), só no servidor |
| pypdf | Ler rotinas de treino enviadas em PDF |
| HTML, CSS e JavaScript puros | Interface, sem framework de frontend nem CDN; sons sintetizados com Web Audio |
| pytest | Testes |
| waitress | Servidor WSGI (Windows e Render) |
| Turbo 8.0.12 (JS, MIT, em `app/static/js/vendor/`) | Navegação sem recarregar a página, para a música de fundo não reiniciar |

```
                 ┌──────────────── app (Flask) ─────────────────┐
 navegador ────▶ │ routes (Blueprints)  →  services  →  models   │ ──▶ banco
                 │        │                    │                 │
                 │        └── core: config, segurança, erros,    │
                 │            tempo, settings, templates         │
                 │                                               │
                 │ módulos: dashboard, architect → hunter,       │
                 │          quests, habits, training, calendar,  │
                 │          gamification   (via services.py)     │
                 │                                               │
                 │ integrations: google, gmail, buffer, notion,  │ ──▶ APIs externas
                 │               whatsapp · architect/ai → Claude │
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
│   │   ├── hunter/            perfil, XP, níveis, ranks, atributos, conquistas e títulos
│   │   ├── architect/         o Arquiteto: análise, sugestões, metas, chat (IA opcional)
│   │   ├── training/          rotinas de treino → quests, calendário, hábito, progressão
│   │   ├── quests/            quests, categorias, recorrência
│   │   ├── habits/            hábitos e streaks
│   │   ├── gamification/      bônus, punições, Penalty Quests, Zona de Falha (via eventos)
│   │   └── calendar/          calendário interno
│   ├── integrations/
│   │   ├── google_calendar/   OAuth, cliente da API, sincronização
│   │   ├── gmail/             leitura de não lidos (mesmo OAuth do Google)
│   │   ├── notion/            bancos de dados → quests
│   │   ├── whatsapp/          resumo do dia para o seu número
│   │   ├── credentials.py     tokens cadastrados pela tela (banco: stored_secrets)
│   │   └── buffer/            token, cliente GraphQL, regras por rede, agendamento
│   ├── templates/             Jinja2, uma pasta por módulo
│   └── static/                css/shadow.css, js/ (shadow, sounds, boot), img/
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
| [docs/integrations.md](docs/integrations.md) | Google Calendar, Gmail, Buffer, Notion, WhatsApp, como criar novas |
| [docs/security.md](docs/security.md) | Credenciais, login, CSRF, backups |
| [docs/deployment.md](docs/deployment.md) | Hospedar online de graça e só com seu acesso (Render + Supabase; PythonAnywhere como alternativa) |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Erros conhecidos (deploy, Google, Notion, Buffer) e como resolver |
| [docs/modules/](docs/modules/) | [Hunter](docs/modules/hunter.md), [Quests](docs/modules/quests.md), [Hábitos](docs/modules/habits.md), [Treinos](docs/modules/training.md), [Calendário](docs/modules/calendar.md), [Dashboard](docs/modules/dashboard.md), [Gamificação](docs/modules/gamification.md) |
| [docs/decisions/architecture-decisions.md](docs/decisions/architecture-decisions.md) | Decisões e seus motivos |

## Segurança

- Credenciais só no `.env` e em `instance/`; os dois estão no `.gitignore`. Nada sensível no código.
- O app guarda dados pessoais: com o login desligado, ele escuta só em `127.0.0.1`. Ligue o login antes
  de expor em qualquer rede.
- CSRF em todos os formulários, cabeçalhos de segurança (CSP, X-Frame-Options), redirecionamentos só internos.
- Logs não registram conteúdo pessoal nem tokens.
- Backups: `flask backup create` (SQLite) ou `pg_dump` (PostgreSQL).
- Online: tokens das integrações no banco com RLS ligado, segredos só no painel do Render (o repositório é público). Ver [docs/security.md](docs/security.md).

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
