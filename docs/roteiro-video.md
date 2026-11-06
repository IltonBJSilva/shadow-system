# ◈ Roteiro de Vídeo: Apresentação e Arquitetura do Shadow System

Documento de referência para gravação, produção e publicação do vídeo de apresentação completa do **Shadow System**: o RPG de evolução pessoal inspirado em *Solo Leveling*, cobrindo a filosofia, regras de jogo, arquitetura de software e decisões de engenharia.

---

## 1. Visão Geral e Ficha Técnica

* **Duração estimada:** 12 a 16 minutos.
* **Formato:** Dev Showcase / Tech Devlog / Manifesto de Autodesenvolvimento.
* **Tom:** Focado, maduro, autêntico, sem promessas vazias. Equilíbrio entre **paixão por programação**, **estética de anime de RPG** e **disciplina da vida real**.
* **Objetivo principal:** Apresentar a ferramenta criada para uso pessoal contínuo, explicando ponto a ponto como a união de engenharia de software com gamificação justa transforma a rotina e o autodesenvolvimento.

### Sugestões de Título
1. *Eu criei o meu próprio Sistema de Solo Leveling para a Vida Real (E como desenvolvi a arquitetura)*
2. *Como gamifiquei minha evolução pessoal criando um Monólito Modular em Python*
3. *Shadow System: Por que abandonei apps de produtividade e construí o meu próprio RPG real*

### Sugestão de Thumbnail
* **Lado esquerdo:** Tela da janela de status / Personagem com a HUD escura em azul neon, rank atual e avatar estilizado.
* **Lado direito:** VS Code aberto na estrutura modular do Flask e o terminal com testes passando, acompanhado do slogan: *"Se o sistema quer me usar, eu uso o sistema"*.

---

## 2. Mapa de Arquivos para Gravação (B-Roll de Código e Telas)

Para facilitar durante a gravação e a edição, use os seguintes arquivos e rotas como referência visual:

| Tema abordado | Tela no Navegador / Rota | Arquivos no VS Code para B-Roll |
|---|---|---|
| Abertura e HUD | `/` (Dashboard / Tela de Boot) | `app/static/css/shadow.css`, `app/static/js/sounds.js` |
| Arquitetura Modular | `/dashboard` | `app/__init__.py`, `app/modules/`, `docs/architecture.md` |
| Eventos Síncronos | `/quests/` | `app/core/events.py`, `app/modules/gamification/events.py` |
| XP por Tempo & Ranks | `/hunter/` e `/hunter/ranks` | `app/modules/hunter/progression.py`, `app/modules/quests/services.py` |
| Personagem & Atributos | `/character/` | `app/modules/character/services.py`, `app/modules/character/catalog.py` |
| Zona de Falha & Punição | `/gamification/failures` | `app/modules/gamification/failures.py`, `docs/decisions/architecture-decisions.md` (ADR-010, ADR-022) |
| Loja do Tempo | `/gamification/shop` | `app/modules/gamification/shop.py`, `app/templates/gamification/shop.html` |
| Sombras (ARISE) | `/shadows/` | `app/modules/shadows/catalog.py`, `app/modules/shadows/services.py` |
| O Arquiteto (Regras + IA) | `/architect/` e `/architect/chat` | `app/modules/architect/analysis.py`, `app/modules/architect/ai.py` |
| Finanças Pessoais | `/finance/` | `app/modules/finance/services.py`, `app/modules/finance/missions.py` |
| Memórias & Avatar | `/memories/` e `/hunter/edit` | `app/core/images.py`, `app/modules/hunter/avatar.py` |
| Arena & Integridade | `/arena/` e `/arena/feed` | `app/modules/arena/integrity.py`, `app/modules/quests/timeline.py` |
| Deploy & Keep-Alive | Dashboard do Render e Supabase | `render.yaml`, `wsgi.py`, `app/core/routes.py` (rota `/health`) |

---

## 3. Roteiro Cena a Cena

---

### BLOCO 1: Abertura & O Manifesto
**Timestamp estimado:** `00:00 - 01:25`  
**Objetivo:** Criar um gancho forte, apresentar a dor da desorganização e introduzir a premissa do projeto.

#### Cena 1.1: O Gancho (00:00 - 00:20)
* **Visual:** Tela preta. Sons sintetizados de inicialização do sistema tocando. O texto do manifesto surge no centro em estilo terminal/HUD azul. Corte rápido para a câmera com iluminação focada.
* **Áudio / Fala:**
  > *"Se esse sistema quer me usar... então eu vou usar o sistema."*  
  > Quem já assistiu ou leu Solo Leveling reconhece essa frase na hora. Mas enquanto para a maioria das pessoas isso é só uma história de fantasia, eu decidi fazer uma pergunta séria de engenheiro: e se eu construísse o meu próprio Sistema para gerenciar cada aspecto da minha vida real?

#### Cena 1.2: A Fragmentação da Vida Real (00:20 - 00:55)
* **Visual:** B-roll dinâmico gravando a tela do computador: alternando entre Notion desatualizado, Trello esquecido, app de treino avulso no celular, planilha financeira manual e Google Agenda.
* **Áudio / Fala:**
  > A realidade é que tentar se organizar hoje é exaustivo. Você tem um app para academia, outro para hábitos diários, um bloco de notas com metas da faculdade, uma planilha financeira que você esquece de preencher no terceiro dia e uma agenda que não conversa com nada disso.  
  > Você passa mais tempo pulando de ferramenta em ferramenta do que realmente executando. E o pior sintoma: **você nunca consegue enxergar a soma da sua evolução acumulada ao longo dos meses.**

#### Cena 1.3: Introdução ao Shadow System (00:55 - 01:25)
* **Visual:** Corte para o navegador com a tela cheia do Shadow System. Dashboard carregando com efeitos de entrada, Dark Aria tocando baixinho de fundo, mostrando widgets de nível, rank, missões e atributos.
* **Áudio / Fala:**
  > Para resolver isso na raiz, eu desenvolvi o **Shadow System**: uma plataforma modular completa de gestão pessoal e gamificação inspirada na estética das janelas de RPG.  
  > Isso aqui não é só um to-do list com skin escura. É um sistema completo com regras matemáticas de progressão, controle de integridade, penalidades justas, mentor automatizado e privacidade absoluta. Hoje eu vou te guiar por cada detalhe funcional e por todas as escolhas de arquitetura que fiz por trás do código.

---

### BLOCO 2: A Filosofia Central — "Eu sou o Jogador"
**Timestamp estimado:** `01:25 - 02:40`  
**Objetivo:** Estabelecer a maturidade do projeto e afastar a ideia de que é uma "brincadeira" ou autoengano.

#### Cena 2.1: Honestidade e Controle (01:25 - 02:05)
* **Visual:** Navegação pela página do Hunter (`/hunter`), mostrando o perfil, títulos conquistados e atributos.
* **Áudio / Fala:**
  > A primeira grande armadilha de gamificar a vida é o autoengano. Aplicativos convencionais te dão pontos fáceis para você se sentir produtivo sem ter feito nada relevante. No Shadow System, a premissa é inegociável: **eu não sou um fantoche controlado pelo sistema; eu sou o jogador.**  
  > O sistema está aqui para medir, rastrear padrões e sugerir otimizações, mas quem decide sou eu. Nenhuma missão vira compromisso sem meu aceite manual. Trapacear no registro só significaria mentir para mim mesmo.

#### Cena 2.2: Integração de Todas as Esferas (02:05 - 02:40)
* **Visual:** Tela de Quests > Categorias (`/quests/categories`), demonstrando a lista de categorias e atributos vinculados (Faculdade, Carreira, Estudos, Treino, Finanças, Espiritualidade, etc.).
* **Áudio / Fala:**
  > Todas as áreas da minha vida convergem para o mesmo lugar:  
  > Horas de estudo e dedicação na faculdade alimentam Inteligência e Sabedoria.  
  > Treinos de musculação e corrida aumentam Força e Vitalidade.  
  > Manter a consistência na organização pessoal e finanças alimenta Foco e Disciplina.  
  > Cada esforço real do dia se torna um dado mensurável.

---

### BLOCO 3: Escolhas Técnicas de Engenharia & Arquitetura
**Timestamp estimado:** `02:40 - 05:10`  
**Objetivo:** Demonstrar competência técnica em Python, Flask, arquitetura limpa e performance web.

#### Cena 3.1: Monólito Modular em Flask 3 (02:40 - 03:30)
* **Visual:** VS Code aberto mostrando a árvore do projeto em `app/modules/`. Destacar as pastas `hunter`, `quests`, `habits`, `architect`, `character`, `finance`. Mostrar o diagrama de camadas de `docs/architecture.md`.
* **Áudio / Fala:**
  > Falando de engenharia de software: hoje em dia existe uma tentação enorme de criar arquiteturas inchadas, com dezenas de microsserviços e filas para tarefas simples. Para este projeto, eu tomei uma decisão muito consciente documentada na ADR-001: **um Monólito Modular em Python 3.12 com Flask 3 e SQLAlchemy 2.**  
  > Como se trata de um sistema focado em uso pessoal, microsserviços só trariam gargalos de rede, complexidade de deploy e problemas de consistência distribuída.  
  > No entanto, mantive um isolamento rigoroso: cada módulo dentro de `app/modules` é autocontido e expõe uma API pública em `services.py`. O módulo de missões, por exemplo, não acessa diretamente o banco de dados do Hunter; ele invoca `hunter.services.award_xp()`. Se amanhã qualquer módulo precisar mudar internamente, o resto do sistema nem percebe.

#### Cena 3.2: Frontend Sem Frameworks & O Truque do Turbo (03:30 - 04:20)
* **Visual:** Inspecionar Elemento no navegador. Mostrar `app/static/js/sounds.js` e a pasta `app/static/js/vendor/turbo.js`. Fazer cliques entre páginas mostrando a URL mudando instantaneamente enquanto o reprodutor de áudio Web Audio continua tocando a música sem interrupção.
* **Áudio / Fala:**
  > No frontend, outra escolha técnica deliberada: **zero dependência de frameworks pesados de SPA (como React ou Angular) e zero chamadas para CDNs externas.** Toda a interface é renderizada no servidor com Jinja2, estilizada com CSS nativo e enriquecida com JavaScript vanilla. Isso garante segurança estrita de CSP, leveza absoluta e funcionamento offline.  
  > E para resolver um desafio clássico de apps web: como manter a música de fundo e os efeitos sonoros tocando de forma contínua enquanto você navega entre telas diferentes?  
  > A resposta foi utilizar o **Turbo**. Ele intercepta os links do navegador e atualiza apenas o conteúdo do DOM sem recarregar a janela. O resultado é uma navegação instantânea e uma trilha sonora imersiva que nunca corta.

#### Cena 3.3: Eventos em Processo (04:20 - 05:10)
* **Visual:** Código do arquivo `app/core/events.py` no VS Code. Mostrar o disparo de `events.publish("quest.completed", ...)` e os ouvintes da gamificação.
* **Áudio / Fala:**
  > Para evitar dependências circulares entre o módulo de tarefas e o módulo de gamificação, criei um despachante de eventos em memória (`events.py`).  
  > Quando uma missão é finalizada, ela dispara um evento `quest.completed`. A gamificação escuta esse evento síncrono, confere sequências, calcula bônus e concede moedas na mesma transação de banco. Simples, robusto e sem acoplamento entre regras de negócio.

---

### BLOCO 4: O Mecanismo do Jogo — Quests, XP e Tempo Real
**Timestamp estimado:** `05:10 - 07:15`  
**Objetivo:** Explicar como funciona o sistema de progressão matemática e a auditoria do esforço.

#### Cena 4.1: XP Baseado no Tempo (05:10 - 06:10)
* **Visual:** Formulário de conclusão de quest (`/quests/<id>`). Mostrar o campo de tempo estimado, tempo gasto, multiplicador de dificuldade e o evento imutável de XP gerado. Abrir `hunter/progression.py` no editor.
* **Áudio / Fala:**
  > Como o valor de XP é determinado? Eu adotei uma premissa clara: **o tempo é o ativo mais valioso que temos.**  
  > Por isso, no Shadow System, o XP é calculado exclusivamente no servidor: **1 XP por minuto de esforço estimado.** Uma tarefa de 15 minutos vale 15 XP; uma sessão de estudos pesada de 2 horas vale 120 XP.  
  > O valor é então ajustado pela dificuldade (de Trivial até Extrema) e pela categoria.  
  > E para impedir o chamado "farm de tarefas": se você repetir a mesma tarefa no mesmo dia, o ganho decai para 50%, depois 25% e zero. Além disso, há um teto diário de 16 horas líquidas auditadas. Ninguém produz 24 horas por dia. O cálculo é auditável, gera um evento imutável e não permite edições retroativas.

#### Cena 4.2: Curva Linear, Ranks & Atributos de Combate (06:10 - 07:15)
* **Visual:** Tela de Personagem (`/character/`). Mostrar a janela de status do Hunter, os Ranks (Rank E até Shadow Monarch) e a tabela de atributos de combate.
* **Áudio / Fala:**
  > A fórmula para subir de nível é intencionalmente linear: `100 + 50 * (Nível - 1)`. Ela escala o desafio com o tempo, mas nunca se torna uma barreira inalcançável.  
  > Conforme você sobe de nível, seu Rank evolui: de Hunter Rank E até o ápice como Monarca das Sombras.  
  > E recentemente, estruturei os **Atributos de Combate**: Ataque mede produtividade e execução; Defesa reflete consistência de hábitos; Inteligência reflete horas dedicadas a estudos e faculdade; Disciplina mede regularidade; e Vitalidade acompanha treinos e saúde. Seus números na tela são o espelho exato do seu comportamento no mundo real.

---

### BLOCO 5: A Realidade Dói — Zona de Falha & Loja do Tempo
**Timestamp estimado:** `07:15 - 09:10`  
**Objetivo:** Mostrar o lado rigoroso do sistema: punições honestas, tratamento de imprevistos e a Loja do Tempo.

#### Cena 5.1: Zona de Falha e Classificação de Motivo (07:15 - 08:15)
* **Visual:** Tela da Zona de Falha (`/gamification/failures`). Mostrar uma missão em atraso destacada em vermelho, as opções de justificativa (Procrastinação, Falta de Planejamento, Imprevisto, Limitação Real).
* **Áudio / Fala:**
  > A maioria dos aplicativos de rotina te pune zerando uma sequência arbitrária, o que gera frustração e abandono. Eu queria o peso das **Penalty Quests** de Solo Leveling, mas com inteligência psicológica.  
  > Se você perde o prazo de uma missão recorrente, ela cai na **Zona de Falha**. O sistema aplica uma pequena dedução de XP (limitada ao nível atual, nunca faz você regredir de nível) e gera uma missão de penalidade no mesmo dia.  
  > Mas aqui vem o diferencial: você precisa classificar o motivo da falha. Foi procrastinação pura ou falta de planejamento? A dedução permanece e o sistema te sugere começar com apenas 15 minutos. Foi um imprevisto incontrolável ou uma limitação real de saúde? O sistema reconhece o contexto, estorna o XP e cancela a penalidade. Disciplina rígida, mas justa.

#### Cena 5.2: A Loja do Tempo (08:15 - 09:10)
* **Visual:** Tela da Loja do Tempo (`/gamification/shop`). Mostrar os cartões do **Escudo do Tempo** e da **Ampulheta**, saldo de moedas e extrato de transações.
* **Áudio / Fala:**
  > Para complementar a mecânica, cada missão concluída gera **Moedas do Tempo** (1 moeda a cada 10 XP base).  
  > Na Loja do Tempo, essas moedas podem ser trocadas por proteção tática:  
  > O **Escudo do Tempo** absorve a próxima penalidade de um dia corrido, evitando perdas de XP.  
  > E a **Ampulheta** permite adiar em 24 horas uma missão que venceria hoje.  
  > Seu esforço e pontualidade passados compram respiro quando imprevistos acontecem.

---

### BLOCO 6: O Exército das Sombras (ARISE) & Equipamentos
**Timestamp estimado:** `09:10 - 10:45`  
**Objetivo:** Explicar a realização máxima da temática de Solo Leveling atrelada a marcos reais.

#### Cena 6.1: O Despertar das Sombras (09:10 - 10:00)
* **Visual:** Página de Sombras (`/shadows/`). Mostrar a lista: Igris, Iron, Tank, Tusk, Beru e Bellion. Destacar os requisitos em dados reais e o botão **ARISE**.
* **Áudio / Fala:**
  > O grande ápice temático do projeto é a **Loja das Sombras**. Aqui, você não compra sombras com dinheiro fictício. Cada sombra representa uma habilidade ou hábito que você dominou de verdade.  
  > Para erguer o **Igris**, você precisa cumprir 20 missões recorrentes e manter 7 dias seguidos de consistência.  
  > Para erguer o general **Beru**, são necessários 30 dias seguidos de evolução, 100 missões recorrentes e mais de 120 horas líquidas de foco.  
  > Quando todos os requisitos são atingidos, o botão **ARISE** se acende. O servidor valida novamente os dados, registra o marco e incorpora a sombra ao seu perfil, concedendo bônus passivos de especialização.

#### Cena 6.2: Equipamentos por Mérito (10:00 - 10:45)
* **Visual:** Visualização dos 8 slots de equipamentos na página do Personagem (`/character/`). Abrir `app/modules/character/catalog.py` para mostrar os 14 itens originais e suas metas.
* **Áudio / Fala:**
  > O mesmo conceito se aplica aos 14 equipamentos do inventário: elmos, armaduras, anéis e armas.  
  > Você só equipa o *Grimório do Conhecimento* se tiver acumulado dezenas de horas de estudo. Nenhum benefício cai do céu; tudo é consequência de hábitos sustentados no mundo real.

---

### BLOCO 7: O Arquiteto — Mentor Local + Inteligência Artificial
**Timestamp estimado:** `10:45 - 12:15`  
**Objetivo:** Explicar a arquitetura híbrida do mentor inteligente: análise local sem custos vs. planejamento via LLM.

#### Cena 7.1: Modo Regras — Análise Local e Determinística (10:45 - 11:35)
* **Visual:** Tela do Arquiteto (`/architect/`). Mostrar os blocos de análise: "Faça Primeiro", taxas de conclusão por categoria, identificação de gargalos. Mostrar `app/modules/architect/analysis.py` no VS Code.
* **Áudio / Fala:**
  > Todo sistema precisa de um mentor. No Shadow System, essa entidade é **O Arquiteto**.  
  > Para estruturá-lo, tomei uma decisão arquitetural muito importante (ADR-021): **uma operação em duas camadas.**  
  > A camada primária é puramente matemática e roda localmente, sem custos de API e sem depender de conexão externa. Ela analisa seus dados históricos dos últimos 14 dias: identifica áreas abandonadas, alerta sobre hábitos em risco e organiza a lista *"Faça Primeiro"*, priorizando missões com base em prazos e importância.

#### Cena 7.2: Modo IA com Claude (11:35 - 12:15)
* **Visual:** Tela do Chat com o Arquiteto (`/architect/chat`). Mostrar o envio de uma mensagem pedindo análise de rotina e a geração estruturada de um plano semanal de missões sugeridas.
* **Áudio / Fala:**
  > A segunda camada é uma extensão de IA generativa conectada ao Claude da Anthropic (usando Opus ou Sonnet).  
  > Você pode conversar com o Arquiteto sobre sua rotina, pedir recomendações estratégicas e solicitar um plano estruturado de missões para os próximos 7 dias. O Arquiteto recebe um retrato anonimizado dos seus hábitos e metas, sem expor dados confidenciais, e gera sugestões práticas. Mais uma vez: nada entra na sua rotina sem o seu consentimento.

---

### BLOCO 8: Finanças, Memórias & Integridade dos Dados
**Timestamp estimado:** `12:15 - 13:45`  
**Objetivo:** Apresentar recursos adicionais de privacidade, registro visual e controle contra trapaças.

#### Cena 8.1: Módulo Financeiro Privado (12:15 - 12:50)
* **Visual:** Tela de Finanças (`/finance/`). Mostrar contas, controle de faturas de cartão parceladas, orçamentos mensais e as *Missões Financeiras*.
* **Áudio / Fala:**
  > Para a gestão do dinheiro, criei um módulo financeiro nativo com valores armazenados em centavos inteiros, evitando qualquer erro de arredondamento.  
  > Mas a gamificação aqui tem uma lógica única: você nunca ganha XP por gastar. O XP é concedido por **disciplina**, como fechar o mês dentro do orçamento ou completar uma semana sem gastos desnecessários. Além disso, os dados financeiros são 100% privados: nenhum dado financeiro é compartilhado com outros módulos ou exibido em rankings.

#### Cena 8.2: Memórias Visuais & Auditoria da Arena (12:50 - 13:45)
* **Visual:** Galeria de Memórias (`/memories/`) com imagens WebP limpas. Em seguida, a Arena dos Hunters (`/arena/`), destacando o selo de *Integridade* e a timeline de horas de foco sem sobreposição.
* **Áudio / Fala:**
  > No módulo de **Memórias**, criei um diário visual de conquistas. Ao concluir um projeto ou treino importante, posso anexar uma foto. O backend processa o arquivo com a biblioteca Pillow, converte para WebP e limpa completamente metadados como GPS e modelo da câmera para preservar a privacidade.  
  > E para quando amigos ou outros usuários de teste acessam a plataforma, existe a **Arena dos Hunters**. Para manter a integridade, implementei um algoritmo que analisa intervalos de foco: ele detecta sobreposição de horários e padrões anômalos de conclusão rápida. O ranking mede constância real, e não automação ou trapaça.

---

### BLOCO 9: Deploy, PWA & Rotina de Uso
**Timestamp estimado:** `13:45 - 14:45`  
**Objetivo:** Explicar onde o sistema é executado e demonstrar a experiência mobile (PWA).

#### Cena 9.1: Deploy Gratuito no Render + Supabase (13:45 - 14:15)
* **Visual:** Dashboard do Render, Supabase e o arquivo `render.yaml` no VS Code. Mostrar o endpoint `/health`.
* **Áudio / Fala:**
  > Onde o sistema roda? Localmente, basta rodar `./run.ps1` no Windows e o ambiente sobe em segundos com SQLite.  
  > Em produção, o Shadow System fica hospedado no **Render** conectado a um banco PostgreSQL no **Supabase**, ambos no plano gratuito.  
  > Como serviços gratuitos costumam entrar em modo de suspensão após minutos de inatividade, configurei rotinas de keep-alive chamando a rota pública `/health` a cada 5 minutos, garantindo que o app esteja sempre ativo e pronto para uso sem nenhum custo fixo de infraestrutura.

#### Cena 9.2: PWA Instalado no Celular (14:15 - 14:45)
* **Visual:** Gravação de tela do smartphone abrindo o Shadow System como aplicativo nativo PWA, marcando um hábito diário e ouvindo o feedback sonoro instantâneo.
* **Áudio / Fala:**
  > E para usar no dia a dia com a máxima praticidade, configurei o sistema como um **Progressive Web App (PWA)**. Eu instalo o ícone diretamente na tela inicial do celular. Ele abre em tela cheia, com carregamento instantâneo via Service Workers, permitindo que eu marque missões, registre treinos e consulte o Arquiteto em qualquer lugar.

---

### BLOCO 10: Conclusão & O Impacto Real
**Timestamp estimado:** `14:45 - 16:00`  
**Objetivo:** Mensagem final inspiradora, planos futuros e encerramento elegante.

#### Cena 10.1: O Impacto Pessoal (14:45 - 15:30)
* **Visual:** Câmera principal focada no apresentador. B-rolls ocasionais intercalando dados do dashboard e gráficos de consistência das últimas semanas.
* **Áudio / Fala:**
  > Desenvolver o Shadow System transformou profundamente a minha relação com produtividade e disciplina.  
  > Primeiro, porque parei de tentar me encaixar nas limitações de aplicativos genéricos de terceiros e criei uma solução desenhada exatamente para a minha realidade.  
  > Segundo, porque isso me ensinou a encarar a minha própria rotina com a precisão de um arquiteto de software: você só consegue melhorar aquilo que tem a coragem de medir com honestidade.  
  > Este projeto se tornou meu laboratório diário de evolução pessoal.

#### Cena 10.2: Próximos Passos & Encerramento (15:30 - 16:00)
* **Visual:** Tela final com a identidade visual do Shadow System, links para documentação/GitHub e créditos.
* **Áudio / Fala:**
  > O desenvolvimento continua: os próximos módulos no roadmap incluem um sistema acadêmico completo para a faculdade, acompanhamento avançado de sobrecarga progressiva na academia e automações de relatórios.  
  > Se você achou a arquitetura e a proposta interessantes, toda a documentação técnica detalhada está no repositório no link da descrição.  
  > Deixe nos comentários o que você achou dessa abordagem e como você faz para organizar a sua própria evolução. Obrigado por acompanhar, e nos vemos no próximo level up!

---

## 4. Checklist de Produção e Gravação

- [ ] **Configuração do Ambiente de Testes:** Ter dados reais ou de demonstração preenchidos no banco local (`instance/shadow.db`) para que a HUD não pareça vazia.
- [ ] **Volume de Áudio do Sistema:** Ajustar a música DARK ARIA no sistema para ~20% e efeitos em ~40% nas configurações (`/settings`), para não competir com a voz do microfone.
- [ ] **Resolução de Tela:** Gravar a tela do navegador em 1080p ou 1440p com zoom de 110% a 125% para facilitar a leitura de código e métricas em telas de smartphones.
- [ ] **Gravação Mobile:** Capturar a tela do celular em modo retrato executando ações reais no PWA (concluir hábito, consultar Arquiteto).
- [ ] **B-Rolls de Terminal:** Capturar a execução de testes (`pytest`), o comando de inicialização (`run.ps1`) e as rotas sendo servidas.

---

## 5. Modelo de Descrição para o YouTube

```markdown
Construí meu próprio RPG da vida real inspirado em Solo Leveling: o Shadow System.
Neste vídeo, exploro a fundo como desenvolvi esse sistema modular em Python e Flask, integrando tarefas, treinos, finanças, hábitos e inteligência artificial para criar uma rotina de evolução pessoal consistente e justa.

◈ Repositório e Documentação:
https://github.com/IltonBJSilva/shadow-system

◈ Capítulos do Vídeo:
00:00 - O Manifesto: Por que criar o próprio Sistema?
01:25 - A Filosofia: "Eu sou o Jogador"
02:40 - Arquitetura de Software: Monólito Modular em Flask 3
03:30 - Frontend Puro, Web Audio & Turbo JS
04:20 - Desacoplamento com Eventos em Processo
05:10 - Quests, XP por Tempo e Atributos de Combate
07:15 - A Zona de Falha & Loja do Tempo
09:10 - O Exército das Sombras (ARISE) e Equipamentos
10:45 - O Arquiteto: Mentor por Regras + Claude IA
12:15 - Finanças Pessoais, Memórias e Integridade
13:45 - PWA no Celular, Render e Supabase Gratuito
14:45 - O Impacto Real na Minha Rotina & Conclusão

#sololeveling #python #flask #desenvolvimentoweb #produtividade #gamificacao #devlog
```

