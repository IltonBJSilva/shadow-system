# Roadmap

Estado em 01/11/2026. Marque aqui conforme as features forem concluídas.

## Fase 1: MVP ✅

- [x] Estrutura do monólito modular (Application Factory, Blueprints, core)
- [x] Configuração por `.env`, SQLite local, PostgreSQL suportado
- [x] Migrations (Alembic) e teste que garante migration para todo modelo
- [x] Hunter Profile: XP, níveis, ranks configuráveis, atributos, histórico
- [x] Quest System: tipos, categorias, prioridade, dificuldade, prazos, recorrência, histórico
- [x] Hábitos diários com streaks
- [x] Calendário interno com conflitos e quests com prazo
- [x] Dashboard configurável
- [x] Camada de integrações e tela de status
- [x] Google Calendar (OAuth 2.0, importar/enviar, disponibilidade)
- [x] Kausa Social Scheduler (leitura de canais e posts agendados)
- [x] Login opcional, CSRF, cabeçalhos de segurança, backup
- [x] Documentação técnica

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

- [ ] **Fitness**: exercícios, treinos, séries/reps/cargas, divisões (ABC, ABCD, ABCDE, Full Body, Upper/Lower, custom), peso e medidas, cardio, gráficos de evolução
- [ ] **Finance**: contas, cartões, receitas/despesas, categorias, parcelamentos, recorrentes, orçamento, metas, reserva de emergência, fluxo de caixa (BRL)
- [ ] Importação de CSV (extratos)
- [ ] Widgets de treino e resumo financeiro no dashboard

## Fase 4: Conteúdo e redes

- [ ] **Social Media**: contas por rede, ideias, posts, reels, carrosséis, legendas, hashtags, campanhas
- [ ] **Instagram Stories**: sequências ordenadas por campanha, roteiros, mídias, status (planejamento manual)
- [ ] Conferir na documentação oficial do Buffer o que pode ser agendado para Stories antes de automatizar
- [ ] Calendário editorial unificado com o calendário interno
- [ ] Criar posts no Kausa a partir do Shadow System (`POST /api/posts`), com confirmação antes de enviar
- [ ] Propor ao Kausa autenticação por token para a API (plano em `docs/integrations.md`)
- [ ] **Content Creator**: canais/projetos separados, roteiros, thumbnails, métricas quando disponíveis

## Fase 5: Carreira, hobbies e desenvolvimento pessoal

- [ ] **Career**: vagas, empresas, pipeline de candidaturas, entrevistas, testes técnicos, propostas
- [ ] **Hobbies** genéricos com dados próprios (Gaming, Música, Game Dev, Writing, personalizados)
- [ ] **Personal Development**: diário, reflexões, revisão semanal e mensal, conquistas (achievements)

## Fase 6: Inteligência e automação

- [ ] **Shadow AI**: camada de provedor configurável; objetivos → lista de `QuestInput` para o usuário confirmar
- [ ] Relatórios diários/semanais, análise de rotina, tarefas atrasadas, conflitos de agenda
- [ ] **Automações**: agendador no próprio processo ou via Agendador de Tarefas do Windows chamando comandos `flask`, com log de execução, liga/desliga e trava contra execução duplicada
- [ ] Sincronização automática com o Google Calendar

## Melhorias técnicas

- [ ] Hábitos semanais (meta de N vezes por semana)
- [ ] Reabrir quest concluída com estorno de XP
- [ ] Criptografia do token do Google em repouso
- [ ] Testes rodando também contra PostgreSQL
- [ ] Screenshots reais no README
