# Hábitos

Hábitos diários com check-in, sequência (streak) e XP.

| | |
|---|---|
| Pasta | `app/modules/habits/` |
| URL | `/habits/` |
| API pública | `app/modules/habits/services.py` |
| Tabelas | `habits`, `habit_logs`, `habit_attributes` |
| Depende de | `hunter.services` |

## Regras

- Cada dia feito é uma linha em `habit_logs`, com **um único check por hábito por dia** (constraint
  `uq_habit_logs_habit_day`). Clique duplo não gera XP duplicado.
- Cada check dá o XP do hábito e **+1 ponto** em cada atributo ligado.
- **Desmarcar** estorna exatamente o XP daquele dia (`xp_awarded`), mesmo que o XP do hábito tenha mudado.
- Dá para marcar dias esquecidos de **até 7 dias atrás** (`MAX_BACKFILL_DAYS`); dias futuros, não.
- **Streak** (`streaks.py`): dias seguidos até hoje. Se hoje ainda não foi feito, conta até ontem; a
  sequência só quebra quando o dia acaba sem check. Não há perda de XP por quebrar sequência.
- **Arquivar** esconde o hábito sem apagar o histórico. **Remover** apaga o hábito e os checks, mas o XP
  já ganho continua no histórico do Hunter.

## Para outros módulos

| Função | Uso |
|---|---|
| `list_habits(active=True)` | `list[HabitView]` com feito hoje, streak atual, recorde e últimos 7 dias |
| `best_current_streak()` | Maior sequência atual (dashboard) |
| `check_in(id, day)` / `undo_check_in(id, day)` | Marcar/desmarcar |

## Próximos passos possíveis

Hábitos semanais (meta de N vezes por semana) entram como um campo `frequency` em `Habit` e uma regra
nova em `streaks.py`, sem mudar o resto.
