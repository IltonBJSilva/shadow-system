# Gamificação: bônus, punições e Penalty Zone

| | |
|---|---|
| Pasta | `app/modules/gamification/` |
| URL | `/gamification/` (regras e histórico) |
| Tabelas | nenhuma: regras em `app_settings` (`gamification.rules`), histórico em `xp_events` |
| Depende de | `hunter.services`, `quests.services` |
| Como é acionado | Eventos de `app/core/events.py` (não é chamado diretamente) |

## Bônus

| Bônus | Quando | Padrão | Origem no histórico |
|---|---|---|---|
| Primeira quest do dia | Primeira quest concluída no dia | +10 XP | `bonus` |
| Adiantar o prazo | Quest concluída antes do dia do prazo | +10% do XP | `bonus` |
| Combo diário | Todas as Daily Quests do dia concluídas (1x por dia) | +20% do XP delas (mín. 20) | `combo` |
| Sequência de hábitos | Check com streak de 7 / 30 / 100 dias | +25% / +50% / +100% | `habit_bonus` |

Desmarcar um hábito estorna também o bônus de sequência daquele dia.

## Punições (Penalty Zone)

Quando uma **quest recorrente** vence sem ser feita (o *rollover* roda ao abrir o dashboard ou as quests):

1. Perde **10% do XP** dela (configurável), **limitado ao XP do nível atual**. Você nunca cai de nível.
2. Nasce uma **Penalty Quest** (`[PENALTY] <título>`, Emergency, crítica, prazo hoje) que vale o XP
   perdido (mínimo 5). Cumprir no dia devolve o que foi tirado.
3. Aparece a janela `[SYSTEM] PENALTY` com som de alarme, e o dashboard avisa a Penalty Zone.

Não geram punição: quests sem repetição (só ficam "atrasadas"), quests canceladas e as próprias
Penalty Quests (não há efeito cascata).

Tudo pode ser desligado ou ajustado em `/gamification/`.

## Zona de Falha (`/gamification/failures`)

Toda quest recorrente não feita vira uma linha em `quest_failures` (título, prazo, XP perdido, Penalty
Quest gerada), mesmo com as punições desligadas. Você registra o **motivo**, com uma observação opcional:

| Motivo (`FAILURE_REASONS`) | Sugestão do System | Devolve o XP? (padrão) |
|---|---|---|
| `procrastination`: Procrastinação | começar pela parte de 15 minutos | não |
| `planning`: Falta de planejamento | rever prazo e recorrência | não |
| `unexpected`: Imprevisto | seguir na próxima ocorrência | **sim** |
| `real_limit`: Limitação real | ajustar a meta ao momento | **sim** |

- Os motivos que devolvem o XP ficam em `Rules.refund_reasons` (caixas na tela de Regras). Devolver
  significa: `+XP` com `source="penalty_refund"` e a Penalty Quest cancelada. Mudar de ideia depois não
  devolve duas vezes (`refunded`).
- O dashboard avisa quantas falhas estão sem motivo; o Arquiteto usa as contagens por motivo para
  sugerir ajustes ("Planejar a semana", "Primeiros 15 minutos").
- `services`: `record_failure`, `list_failures`, `pending_failures_count`, `failure_stats(dias)`,
  `classify_failure(id, motivo, observação)`.

## Conquistas

A caixa *"Dar o XP de recompensa ao desbloquear uma conquista"* liga ou desliga a recompensa
(`hunter.set_achievement_rewards`). As conquistas em si são do módulo Hunter
([hunter.md](hunter.md#conquistas-e-títulos)).

## Como funciona por dentro

```
quests.complete_quest ──publish("quest.completed")──▶ handlers.on_quest_completed  → bônus
quests.roll_over      ──publish("quest.missed")─────▶ handlers.on_quest_missed     → penalidade + Penalty Quest + registro na Zona de Falha
habits.check_in       ──publish("habit.checked")────▶ handlers.on_habit_checked    → bônus de sequência
habits.undo_check_in  ──publish("habit.unchecked")──▶ handlers.on_habit_unchecked  → estorno do bônus
```

- `rules.py`: regras puras e valores padrão (`Rules`). Mude os padrões ali.
- `handlers.py`: as reações aos eventos. Para um bônus novo, crie um handler com `@subscribe("evento")`.
- As mensagens devolvidas pelos handlers viram flashes com categoria `bonus`, `penalty`, `levelup` ou
  `achievement`, que tocam o som correspondente (`static/js/sounds.js`). `levelup` com "LEVEL UP" abre a
  janela de tela cheia (`showLevelUp` em `static/js/shadow.js`).
