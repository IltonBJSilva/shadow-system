# Quest System

Missões com tipo, categoria, prioridade, dificuldade, XP, prazo, recorrência, critérios de conclusão,
recompensa pessoal, atributos e histórico.

| | |
|---|---|
| Pasta | `app/modules/quests/` |
| URL | `/quests/` |
| API pública | `app/modules/quests/services.py` |
| Tabelas | `quests`, `quest_categories`, `quest_attributes`, `quest_category_attributes`, `quest_logs` |
| Depende de | `hunter.services` (concede XP) |

## Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `constants.py` | Tipos, prioridades, status e recorrências (chave no banco → rótulo na tela). |
| `recurrence.py` | Próxima data de uma quest recorrente (funções puras). |
| `models.py` | Tabelas. |
| `services.py` | Regras: criar, editar, iniciar, concluir, cancelar, rolar recorrentes, categorias, consultas. |
| `forms.py` / `routes.py` | Telas. `QuestForm.to_input()` converte o formulário em `QuestInput`. |
| `cli.py` | `flask quests rollover`. |

## Tipos

Daily, Weekly, Monthly, Main, Side, Habit, Emergency e Custom. O tipo organiza e filtra; quem faz
a quest repetir é o campo **Repetição** (diária, semanal, mensal). Assim uma Main Quest pode ser
mensal, ou uma Daily Quest pode ser feita uma vez só.

## Ciclo de vida

```
pending ──start──▶ in_progress ──complete──▶ completed  (+XP, +atributos)
   │                    │
   └──────cancel────────┴──▶ cancelled                   (sem perda de XP)

recorrente vencida ──rollover──▶ missed                  (sem perda de XP) + próxima ocorrência
```

## Regras

- **XP**: se o campo XP ficar vazio, vale dificuldade × prioridade: base 10/25/50/100/200, vezes 0,8
  (baixa), 1,0 (média), 1,2 (alta) ou 1,4 (crítica), arredondado para múltiplo de 5
  (`hunter.progression.xp_for_difficulty`).
- **Categorias sugeridas** (Quests > Categorias > *Criar categorias sugeridas*): Faculdade, Carreira,
  Estudos, Treino, Saúde e bem-estar, Finanças, Música e arte, Hobbies, Organização pessoal,
  Espiritualidade, Projetos pessoais e Conteúdo, cada uma ligada aos atributos que desenvolve
  (`constants.SUGGESTED_CATEGORIES`). Só cria as que faltam pelo nome; as suas ficam como estão.
- **Atributos**: se a quest não escolher atributos, herda os da categoria. Ao concluir, cada atributo
  ganha pontos iguais à dificuldade (1 a 5).
- **Concluir duas vezes** não é permitido (evita XP duplicado).
- **Recorrência**: ao concluir, a próxima ocorrência é criada para depois de hoje. Todas as
  ocorrências compartilham `series_id`.
- **Sem punição**: uma ocorrência recorrente que vence sem ser feita vira *Não realizada*, sem tirar
  XP, e a próxima aparece já para hoje (não acumula uma pilha de atrasadas). Isso roda ao abrir a lista
  de quests ou o dashboard, e também por `flask quests rollover` (idempotente).
- **Remover** uma quest apaga ela e o histórico dela, mas o XP já ganho continua no histórico do Hunter.
- **Em massa** (lista de Quests): marque as caixas (ou *Marcar todas*) e use **Cancelar selecionadas**
  (só as ativas; sem perda de XP) ou **Excluir selecionadas**. Rota `POST /quests/bulk`, funções
  `cancel_quests(ids)` e `delete_quests(ids)`. As caixas ficam fora do formulário de cada linha e se
  ligam ao formulário de ações pelo atributo `form="bulk-quests"`.

## Para outros módulos

| Função | Retorno | Uso |
|---|---|---|
| `quests_for_today()` | `list[QuestView]` | Dashboard: ativas até hoje + Daily Quests sem data |
| `priority_quests(limit)` | `list[QuestView]` | Dashboard: alta/crítica, Main e Emergency |
| `quests_due_between(start, end)` | `list[QuestView]` | Calendário |
| `quest_choices()` / `quest_title(id)` | | Vincular eventos a quests |
| `create_quest(QuestInput)` | `Quest` | Ex.: University gerando quests de revisão, IA no futuro |
| `stats()` | `dict` | Contadores |
| `completed_count(tipo=None)` | `int` | Quests concluídas, de um tipo ou todas (métricas das conquistas) |
| `completed_between(início, fim)` | `int` | Concluídas num período (widget Progresso) |
| `category_performance(dias)` | `list[CategoryPerformance]` | Concluídas x não realizadas por categoria (Arquiteto) |
| `create_suggested_categories()` | `list[str]` | Cria as categorias sugeridas que faltam |
| `active_in_series(series_id)` | `Quest \| None` | Ocorrência ativa de uma recorrente (Treinos) |
| `update_description(id, text)` | | Troca a descrição; a próxima ocorrência herda (Treinos) |
| `cancel_quests(ids)` / `delete_quests(ids)` | `int` | Ações em massa |

`QuestView.series_id` diz a que série recorrente a quest pertence. É assim que o módulo Treinos
reconhece, no evento `quest.completed`, que a quest concluída é um treino.

## Geração com IA (futuro)

`create_quest(QuestInput(...))` já é a porta de entrada: a camada de IA vai propor uma lista de
`QuestInput` e o usuário confirma antes de salvar.
