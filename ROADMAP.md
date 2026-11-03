# Roadmap

Estado em 03/11/2026. Marque aqui conforme as features forem concluídas.

## Fase 1: MVP ✅

- [x] Estrutura do monólito modular (Application Factory, Blueprints, core)
- [x] Configuração por `.env`, SQLite local, PostgreSQL suportado
- [x] Migrations (Alembic) e teste que garante migration para todo modelo
- [x] Hunter Profile: XP, níveis, ranks configuráveis, atributos, histórico
- [x] Quest System: tipos, categorias, prioridade, dificuldade, prazos, recorrência, histórico
- [x] Hábitos diários com streaks
- [x] Gamificação: bônus, punições configuráveis, Penalty Quests, sons e janelas do System
- [x] Calendário interno com conflitos e quests com prazo
- [x] Dashboard configurável
- [x] Camada de integrações e tela de status
- [x] Google Calendar (OAuth 2.0, importar/enviar, disponibilidade)
- [x] Postagens no Buffer pessoal: token pela tela, canais, posts, novo agendamento com texto por rede
- [x] Gmail (leitura), Notion (importar quests), WhatsApp (resumo do dia), tokens cadastrados pela tela
- [x] Login opcional, CSRF, cabeçalhos de segurança, backup
- [x] Títulos por conquista (nível, XP, quests, sequência de hábito, treinos) e títulos próprios
- [x] Ações em massa nas quests; busca e filtros no Gmail; Notion pula páginas sem título
- [x] Hábitos em dias escolhidos da semana (folga não quebra a sequência)
- [x] Treinos: rotinas prontas, texto ou documento → quests semanais, calendário, hábito e progressão de carga
- [x] Online de graça: Render + Supabase (`render.yaml`), tokens no banco com RLS, keep-alive (cron-job.org + GitHub Actions)
- [x] Documentação técnica

## RPG da vida real ✅

- [x] Inicialização do System com o manifesto ("Se esse sistema quer me usar, então eu vou usar o sistema")
- [x] Identidade visual de HUD: azul profundo, azul elétrico, ciano e roxo nos detalhes
- [x] LEVEL UP em tela cheia e notificação especial de conquista, com sons sintetizados
- [x] Atributos Sabedoria e Carisma; categorias sugeridas ligadas aos atributos; evolução semanal dos atributos
- [x] XP por dificuldade × importância
- [x] Painel: dias seguidos evoluindo, semana atual x anterior, concluídas hoje, XP para o próximo nível
- [x] Zona de Falha: motivo da falha (procrastinação, planejamento, imprevisto, limitação real) com XP devolvido configurável
- [x] Conquistas com ícone, recompensa em XP e título (21 padrão)
- [x] O Arquiteto: análise por regras com dados reais, prioridades, missões sugeridas, metas; IA opcional (Claude) para conversa e planos

## Grande evolução (03/11/2026) ✅

- [x] Multiusuário com usuários de teste por convite (sem Google) e dados isolados por conta
- [x] Áudio do System: voz de entrada, música de fundo persistente entre páginas, vozes de eventos, configurações
- [x] XP por tempo com detalhamento imutável, repetição decrescente, teto diário e limites de bônus
- [x] Arena dos Hunters: horas de atividade sem sobreposição, indicador de integridade, perfis públicos, privacidade
- [x] Personagem: atributos de combate com regra real e 14 equipamentos
- [x] Loja das Sombras (Igris, Iron, Tank, Tusk, Beru, Bellion) com bônus de XP controlado
- [x] Feed dos Hunters, Memórias (fotos sem metadados), avatar gerado da foto com evolução por rank
- [x] Finanças privadas com missões financeiras
- [x] Loja do Tempo (moedas, Escudo, Ampulheta), PWA, Como usar, Novidades, matriz de prioridades, voz no Arquiteto

### Próximos passos desta linha

- [ ] Virtudes desbloqueadas por nível ligadas ao atributo mais forte; fragmentos de lore do Arquiteto
- [ ] Pausar e arquivar missões (hoje: cancelar ou apagar)
- [ ] Concluir missões direto pelo calendário
- [ ] Cliente OAuth do Google próprio de cada usuário (opcional)
- [ ] Provedor de avatar com IA de imagem (a interface `AvatarProvider` já existe)

## Fase 2: Vida acadêmica

- [ ] **Study**: cursos, conteúdos, sessões de estudo (horas), revisões, metas, anotações
- [ ] **University**: universidade, curso, semestres, disciplinas, professores, horários de aula
- [ ] Avaliações (provas, trabalhos, listas, apresentações) com prazos no calendário
- [ ] Regras de nota **configuráveis por disciplina** (média ponderada, substitutiva, etc., sem regra fixa)
- [ ] Frequência
- [ ] Dashboard acadêmico (próximas provas e entregas, progresso por disciplina)
- [ ] Gerar quests de revisão a partir de uma prova (usa `quests.services.create_quest`)
- [ ] Sessões de estudo da faculdade usam o módulo Study (sem duplicar)

## Fase 3: Corpo e dinheiro

- [ ] **Fitness** (continuação dos Treinos): carga por série registrada no treino, peso e medidas, cardio, gráficos de evolução
- [ ] Converter texto livre em rotina com IA (opcional, por cima do parser atual)
- [x] **Finance**: contas, cartões, receitas/despesas, categorias, parcelamentos, recorrentes, orçamento, metas (03/11/2026)
- [ ] Importação de CSV (extratos)
- [ ] Widgets de treino e resumo financeiro no dashboard

## Fase 4: Conteúdo e redes

- [ ] **Social Media**: contas por rede, ideias, posts, reels, carrosséis, legendas, hashtags, campanhas
- [ ] **Instagram Stories**: sequências ordenadas por campanha, roteiros, mídias, status (planejamento manual)
- [ ] Conferir na documentação oficial do Buffer o que pode ser agendado para Stories antes de automatizar
- [ ] Calendário editorial unificado com o calendário interno
- [ ] Editar e apagar posts agendados do Buffer pela tela
- [ ] Importar lotes de posts (texto por rede + imagens), como os de `E:\Repositorio\postagens`
- [ ] Daily Quest de conteúdo concluída automaticamente quando o post é agendado
- [ ] **Content Creator**: canais/projetos separados, roteiros, thumbnails, métricas quando disponíveis

## Fase 5: Carreira, hobbies e desenvolvimento pessoal

- [ ] **Career**: vagas, empresas, pipeline de candidaturas, entrevistas, testes técnicos, propostas
- [ ] **Hobbies** genéricos com dados próprios (Gaming, Música, Game Dev, Writing, personalizados)
- [ ] **Personal Development**: diário, reflexões, revisão semanal e mensal

## Fase 6: Inteligência e automação

- [x] **Arquiteto** (a antiga "Shadow AI"): regras + Claude opcional; metas → missões para o jogador aceitar
- [ ] Relatório semanal automático do Arquiteto e sugestões agendadas
- [ ] Transformar uma frase livre ("estudar cálculo amanhã à noite") em missão, por texto ou voz
- [ ] Temas de cor trocáveis (hoje as cores ficam nas variáveis do `shadow.css`)
- [ ] **Automações**: agendador no próprio processo ou via Agendador de Tarefas do Windows chamando comandos `flask`, com log de execução, liga/desliga e trava contra execução duplicada
- [ ] Sincronização automática com o Google Calendar

## Melhorias técnicas

- [ ] Hábitos com meta de N vezes por semana em dias livres
- [ ] Reabrir quest concluída com estorno de XP
- [ ] Criptografia dos tokens em repouso (`stored_secrets`)
- [ ] Testes rodando também contra PostgreSQL no CI (hoje as migrations foram validadas à mão num PostgreSQL real)
- [ ] Backup automático do Supabase (o plano gratuito não guarda backups para baixar)
- [ ] Ler `instance/` de uma variável de ambiente, para scripts nunca tocarem nos tokens reais
- [ ] Screenshots reais no README
