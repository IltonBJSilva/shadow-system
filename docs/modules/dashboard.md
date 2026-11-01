# Dashboard

Janela de status inspirada no *System* de Solo Leveling, montada com dados reais dos outros módulos.

| | |
|---|---|
| Pasta | `app/modules/dashboard/` |
| URL | `/` e `/dashboard/settings` |
| Tabelas | nenhuma (a escolha de widgets fica em `app_settings`, chave `dashboard.widgets`) |
| Depende de | `hunter`, `quests`, `habits`, `calendar`, `integrations.kausa_scheduler` |

## Widgets

| Chave | Mostra | Fonte |
|---|---|---|
| `status` | Rank, nível, XP, atributos, quests concluídas/ativas, maior streak | `hunter.get_status`, `quests.stats`, `habits.best_current_streak` |
| `notifications` | Quests vencidas, hábitos pendentes hoje, eventos de hoje | calculado na hora |
| `today_quests` | Quests até hoje + Daily Quests sem data (com botão concluir) | `quests.quests_for_today` |
| `habits` | Hábitos com botão de check | `habits.list_habits` |
| `priority_quests` | Alta/crítica, Main e Emergency | `quests.priority_quests` |
| `upcoming_events` | Próximos 7 dias | `calendar.upcoming_events` |
| `weekly_xp` | XP por dia nos últimos 7 dias | `hunter.xp_by_day` |
| `recent_activity` | Últimos ganhos de XP | `hunter.recent_events` |
| `scheduled_content` | Posts agendados no Buffer (via Kausa) | `kausa_scheduler.scheduled_posts_safe` |

Widgets desligados não fazem consulta. Ao abrir o dashboard, `quests.roll_over_recurring()` roda
para que as Daily Quests do dia já apareçam.

Treinos, resumo financeiro e progresso acadêmico entram como widgets quando os módulos Fitness,
Finance e University existirem; não são exibidos antes disso.

## Adicionar um widget

1. Em `services.py`: chave e rótulo em `WIDGETS` e a função em `_LOADERS`.
2. Template `app/templates/dashboard/widgets/<chave>.html` (os dados chegam numa variável com o nome da chave).
3. Teste em `tests/test_dashboard.py`.
