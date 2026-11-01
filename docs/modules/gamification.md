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

## Como funciona por dentro

```
quests.complete_quest ──publish("quest.completed")──▶ handlers.on_quest_completed  → bônus
quests.roll_over      ──publish("quest.missed")─────▶ handlers.on_quest_missed     → penalidade + Penalty Quest
habits.check_in       ──publish("habit.checked")────▶ handlers.on_habit_checked    → bônus de sequência
habits.undo_check_in  ──publish("habit.unchecked")──▶ handlers.on_habit_unchecked  → estorno do bônus
```

- `rules.py`: regras puras e valores padrão (`Rules`). Mude os padrões ali.
- `handlers.py`: as reações aos eventos. Para um bônus novo, crie um handler com `@subscribe("evento")`.
- As mensagens devolvidas pelos handlers viram flashes com categoria `bonus`, `penalty` ou `levelup`,
  que tocam o som correspondente (`static/js/sounds.js`).
