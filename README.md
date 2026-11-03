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
- [x] **Personagem**: 6 atributos de combate com regra real, inventário com 14 equipamentos, raridades e bônus
- [x] **Loja das Sombras**: Igris, Iron, Tank, Tusk, Beru e Bellion, com desafios reais, rank mínimo e bônus de XP com acúmulo controlado
- [x] **App no celular (PWA)**, Como usar, Novidades, matriz de prioridades e comando de voz no Arquiteto
- [x] **Finanças**: contas, cartões, lançamentos, parcelas, recorrentes, orçamentos, metas, relatórios e missões financeiras (privado)
- [x] **Avatar**: gerado da sua foto com estilos do System, moldura que evolui com o rank e foto original privada
- [x] **Memórias**: álbum de fotos das atividades, sem metadados, com filtros e privacidade
- [x] **Arena dos Hunters**: ranking com horas de atividade sem sobreposição, indicador de integridade e perfis públicos com privacidade
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

### XP de uma missão (por tempo)

> "O tempo é o que temos de mais valioso durante o dia." Quanto mais tempo uma missão exige, mais XP ela vale.

Toda missão tem **tempo estimado** (5 min a 8 h), definido antes de concluir. O XP é calculado no servidor
(`hunter/progression.py` + `quests.services.complete_quest`), nunca no navegador:

1. **Base:** 1 XP por minuto estimado (5 min = 5 XP, 30 min = 30 XP, 2 h = 120 XP).
2. **Dificuldade** (ajuste moderado): Trivial ×0,8 · Fácil ×0,9 · Normal ×1,0 · Difícil ×1,15 · Extrema ×1,3.
3. **Categoria:** ajuste configurável de ×0,8 a ×1,2 (Quests > Categorias).
4. **Repetição:** a mesma missão concluída de novo no mesmo dia rende 100%, 100%, 50%, 25% e depois 0 (sem farm).
5. **Teto diário:** no máximo 16 h de missões rendem XP base por dia (ninguém tem mais que 24 h).
6. **Bônus** de sombras e equipamentos por especialização da categoria, com teto: até 50% do XP base e 30 XP por
   missão, e 150 XP de bônus por dia.

O resultado fica num **evento de XP imutável** com XP base, bônus, total e as linhas do "por quê", visíveis na
página da missão. Mudar tempo, dificuldade ou categoria de uma missão já concluída é bloqueado (nada de XP
retroativo), e cada edição fica no histórico da missão. Ao concluir, você pode informar o **tempo gasto**: ele vira
um intervalo de atividade (hora do servidor), usado nas horas de atividade do ranking.

Missões criadas antes desta regra continuam com o XP fixo que tinham. Bônus da Gamificação (primeira missão do
dia, combo das Daily Quests, adiantar prazo, sequência de hábitos) e recompensas de conquista continuam somando
à parte; os valores ficam em Gamificação.

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

## Personagem: atributos de combate e equipamentos

Em **Personagem** fica a ficha completa do Hunter, no estilo dos menus de RPG: avatar no centro, os 8 slots de
equipamento em volta, a janela de status (nível, XP, rank), os atributos de combate, as missões diárias e
semanais, estatísticas e conquistas recentes.

**Atributos de combate** (`character/services.py`, função `base_stats`). Cada um tem regra clara e vem de dados
reais; equipamentos e sombras somam bônus por cima:

| Atributo | Representa | Base |
|---|---|---|
| Ataque | Produtividade e execução | 1 por hora dedicada em missões + 1 a cada 10 missões |
| Defesa | Consistência | 1 a cada 5 dias de hábito marcados + 1 por semana de sequência no melhor hábito |
| Inteligência | Aprendizado | 1 por hora em Estudos/Faculdade + 1 a cada 2 h em Projetos/Carreira |
| Disciplina | Regularidade | 1 a cada 5 missões recorrentes cumpridas + 1 por semana seguida evoluindo |
| Vitalidade | Corpo e saúde | 1 por hora em missões de Corpo + 1 a cada 3 treinos |
| Sabedoria | Experiência acumulada | 1 por nível alcançado + 1 por conquista |

Os 10 atributos antigos (Strength, Focus...) continuam valendo nas missões e categorias; os de combate são a
ficha do personagem.

**Equipamentos** (`character/catalog.py`): 14 itens originais em 8 tipos (arma, armadura, capacete, luvas, botas,
acessório, anel, amuleto) e 6 raridades (Comum a Mítico). Cada item tem rank mínimo para equipar, bônus de
atributos, às vezes um bônus de XP numa especialização (ex.: Grimório do Conhecimento, +3 XP em Estudos), e uma
meta real que o desbloqueia (ex.: 25 missões, 30 h de estudo, nível 40). Os itens chegam sozinhos ao inventário
quando a meta é atingida (sem duplicar). Um item por slot; o inventário mostra a comparação com o item equipado,
os bônus ativos e o progresso dos itens bloqueados. Bônus de XP de equipamento seguem os limites gerais de bônus.
Para criar um item novo, inclua um `Item(...)` em `EQUIPMENT`.

## Loja das Sombras

Em **Sombras**, cada sombra representa uma habilidade desenvolvida de verdade. Ela exige um **rank mínimo** e
**desafios medidos com dados reais**; com os dois cumpridos aparece o botão **ARISE** para recrutar (o servidor
confere tudo de novo, e cada sombra só pode ser recrutada uma vez por jogador). O recrutamento fica no histórico
com o retrato dos desafios no momento.

| Sombra | Rank | Desafios | Bônus de XP | Atributos |
|---|---|---|---|---|
| Igris | D | 20 recorrentes cumpridas + 7 dias seguidos evoluindo | +3 em Disciplina/Organização | +3 Disciplina, +1 Defesa |
| Iron | D | 10 h de Corpo + 8 treinos | +5 em Corpo | +3 Vitalidade, +1 Defesa |
| Tank | C | 30 h de Corpo + 14 dias seguidos num hábito | +4 em Corpo | +4 Defesa, +2 Vitalidade |
| Tusk | C | 25 h de Estudos/Faculdade + 60 missões | +5 em Estudos/Faculdade | +4 Inteligência, +1 Sabedoria |
| Beru | B | 30 dias seguidos evoluindo + 100 recorrentes + 120 h no total | +6 em Disciplina/Projetos/Carreira | +3 Ataque, +3 Disciplina |
| Bellion | S | nível 70 + 400 missões + 300 h no total | +10 em Maestria | +5 em todos |

**Bônus de XP das sombras** (`shadows/services.py`): aplicados sozinhos, no servidor, só nas missões da categoria
com a especialização da sombra. Várias sombras na mesma especialização acumulam de forma controlada: a mais
forte vale inteira e cada outra vale metade. Depois disso valem os tetos gerais (até 50% do XP base e 30 XP por
missão, 150 XP por dia). O detalhamento da missão mostra XP base, cada bônus e os limites aplicados. Para criar
uma sombra nova, inclua um `Shadow(...)` em `shadows/catalog.py`.

## Finanças

Em **Finanças**, a gestão financeira pessoal, **privada por padrão**: nenhum valor aparece na Arena, no feed ou para
outros usuários, e nenhum outro módulo lê essas tabelas. Sem integração bancária: tudo é lançado por você.

- **Contas e cartões:** conta corrente, poupança/reserva, carteira, investimentos e cartão de crédito (limite, dia
  de fechamento e vencimento). Saldo = saldo inicial + receitas - despesas ± transferências. No cartão, o valor é a
  fatura em aberto; pagar a fatura é uma transferência da conta para o cartão.
- **Lançamentos:** receitas, despesas e transferências, com categoria, data e conta. Compras parceladas no cartão
  são divididas em até 48 meses (centavos distribuídos sem perder nada). Busca e filtros por mês, conta, categoria e tipo.
- **Categorias** padrão (Alimentação, Transporte, Moradia, Faculdade, Saúde, Academia, Lazer, Assinaturas,
  Investimentos, Salário, Freelance, Outras receitas) e as suas; cada despesa pode ser marcada como não essencial.
- **Recorrentes:** salário, aluguel, assinaturas; lançadas sozinhas todo mês, uma vez só.
- **Orçamento mensal** por categoria, com barra de uso e alerta ao estourar.
- **Metas financeiras:** por aportes manuais ou acompanhando o saldo de uma conta.
- **Relatórios:** receitas, despesas e saldo do mês, gastos por categoria e comparação dos últimos 6 meses (gráficos em CSS).
- Valores guardados em **centavos inteiros** (sem erro de arredondamento); aceita "1.234,56", "R$ 10" ou "9.9".

**Missões financeiras** (`finance/missions.py`), com XP pequeno e uma vez por período, nunca por gastar:

| Missão | Quando paga | XP |
|---|---|---|
| Registrar todas as despesas do dia | Você confirma que anotou tudo hoje (uma vez por dia) | 10 |
| Semana sem gastos desnecessários | Nenhum gasto em categorias não essenciais na semana anterior, com lançamentos em pelo menos 5 dias | 30 |
| Cumprir o orçamento mensal | Mês anterior com todas as categorias dentro do limite e lançamentos em pelo menos 15 dias | 50 |
| Economizar no mês | Mês anterior com saldo (receitas - despesas) acima da sua meta de economia | 50 |
| Criar uma reserva financeira | Uma meta financeira alcançada (uma vez por meta) | 100 |

As missões de semana e mês exigem lançamentos registrados naquele período, para que não dê para ganhar XP
simplesmente deixando de anotar os gastos.

## Avatar do Hunter

Em **Hunter > Editar perfil > Avatar a partir da sua foto**: envie uma foto e escolha um estilo (Sombra, Monarca,
Holograma ou Clássico). O avatar é gerado **no próprio servidor** com processamento de imagem (Pillow), sem IA e
sem enviar a foto para outro serviço (`hunter/avatar.py`). A arquitetura tem provedores (`AvatarProvider`): para
usar um serviço externo de geração de imagens no futuro, basta criar outro provedor com a mesma interface.

- **Evolução por rank:** a moldura e a aura do avatar mudam com o rank (E cinza, D verde, C azul com anel, B índigo
  com brilho, A roxo pulsando, S dourado; SS, Nacional e Monarca com variações). No Personagem, os equipamentos
  aparecem nos slots ao redor do avatar.
- **Privacidade:** a foto original fica guardada sem metadados e só o dono vê. Dá para apagar a foto e manter o
  avatar, trocar o estilo (enquanto a foto existir), enviar outra ou voltar ao avatar padrão (sigla do rank). Os
  outros Hunters veem só o avatar estilizado.

## Memórias

Diário visual da evolução, em **Memórias**. Depois de concluir uma missão, a página dela mostra
**📸 Registrar memória**; também dá para criar uma memória solta. Cada memória tem foto, título, tipo de atividade
(treino, projeto, faculdade, livro, meta, espiritual, conquista), descrição, observação pessoal (sempre privada),
conquista ligada e, se veio de uma missão, a categoria e o título dela. O rank do dia fica registrado.

- **Galeria** com busca (título, missão, conquista) e filtros por tipo, categoria, rank, mês e privacidade.
- **Fotos otimizadas** (`core/images.py`): reduzidas para no máximo 1600 px, miniatura de 480 px, gravadas em WebP
  **sem metadados** (EXIF, GPS, modelo do celular). Até 10 MB por envio, 20 memórias por dia e cerca de 60 MB por conta.
- **Privacidade:** privadas por padrão. Uma memória pública pode ser vista pelos outros Hunters (foto e descrição,
  nunca a observação pessoal) e, se você marcar, vira um post no feed. Dá para trocar a privacidade ou apagar a
  memória (o post do feed vai junto) a qualquer momento. As fotos ficam no banco e só são servidas para o dono ou,
  se públicas, para quem estiver logado.
- O upload nunca é obrigatório.

## Arena dos Hunters

Ranking entre todas as contas (dono e usuários de teste), em **Arena** no menu. Cada Hunter mostra rank, nível,
XP total, XP hoje e na semana, **horas de atividade** hoje e na semana, missões concluídas (total e hoje), tempo
médio por missão e a especialização de maior evolução. Ordena por XP da semana, XP total, horas ou XP de hoje.
Clique num Hunter para abrir o **perfil público** (atributos, missões diárias e semanais, conquistas, evolução
recente e gráfico de horas dos últimos 7 dias).

**Horas de atividade confiáveis.** Cada missão concluída grava um intervalo com a hora do servidor (não a do
celular): termina na conclusão e dura o tempo gasto informado, ou o estimado. Intervalos que se sobrepõem contam
uma vez só e nenhum dia passa de 24 h (`quests/timeline.py`).

**Indicador de integridade** (`arena/integrity.py`), dos últimos 7 dias, de 0 a 100: *Íntegro* (80+), *Atenção*
(50 a 79) ou *Em análise* (abaixo de 50). Considera vários sinais juntos: dias com 16 h ou 20 h+, muitas missões no
mesmo horário, dezenas de missões de até 10 min num dia, a mesma missão repetida muitas vezes, conclusões com menos
de 15 s de intervalo (automação), edições depois de receber XP e XP por hora acima do esperado. Um dia de 24 h
sozinho não derruba ninguém: pode ser erro de registro. Os motivos ficam visíveis, com texto neutro.

**Feed dos Hunters** (Arena > Feed): missões concluídas (com XP e especialização), níveis, ranks,
conquistas, sombras recrutadas e equipamentos conquistados de todos os Hunters, com filtro por tipo. Cada post só
é gravado se o jogador permitir, e a permissão é conferida de novo na leitura: desligar esconde também os
posts antigos. Penalty Quests não aparecem e fotos nunca são publicadas sozinhas.

**Privacidade** (Arena > Minha privacidade): aparecer ou não no ranking, e mostrar ou não atributos, títulos das
missões, conquistas, histórico, equipamentos/sombras e atividades no feed. Finanças, memórias privadas, e-mail,
tokens e integrações nunca aparecem para outras pessoas.

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

### Instalar no celular (app)

O System é um **PWA**: no Android (Chrome) use *Instalar app* no menu do navegador ou o link **Instalar app** no
rodapé do menu; no iPhone (Safari) use Compartilhar > *Adicionar à Tela de Início*. Ele abre em tela cheia com ícone
próprio. O service worker (`static/js/sw.js`) guarda só os arquivos estáticos; páginas e dados sempre vêm do
servidor, e sem internet aparece uma tela de conexão perdida. Ajuda completa em **Como usar**, histórico de
mudanças em **Novidades** (rodapé do menu).

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
| Pillow | Fotos das Memórias e do avatar: reduzir, girar e gravar em WebP sem metadados |
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
