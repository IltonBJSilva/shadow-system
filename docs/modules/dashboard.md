# Dashboard

Janela de status inspirada no *System* de Solo Leveling, montada com dados reais dos outros módulos.

| | |
|---|---|
| Pasta | `app/modules/dashboard/` |
| URL | `/` e `/dashboard/settings` |
| Tabelas | nenhuma (a escolha de widgets fica em `app_settings`, chave `dashboard.widgets`) |
| Depende de | `hunter`, `quests`, `habits`, `calendar`, `integrations.buffer` |

## Widgets

| Chave | Mostra | Fonte |
|---|---|---|
| `status` | Rank, nível, XP, atributos, quests concluídas/ativas, maior streak | `hunter.get_status`, `quests.stats`, `habits.best_current_streak` |
| `notifications` | Quests vencidas, Penalty Zone, falhas sem motivo, hábitos pendentes hoje, eventos de hoje | calculado na hora |
| `progress` | Dias seguidos evoluindo, XP e missões desta semana x o mesmo trecho da anterior, concluídas hoje | `hunter.evolution_streak`, `hunter.xp_between`, `quests.completed_between`, `quests.completed_on` |
| `today_quests` | Quests até hoje + Daily Quests sem data (com botão concluir) | `quests.quests_for_today` |
| `habits` | Hábitos com botão de check | `habits.list_habits` |
| `priority_quests` | Alta/crítica, Main e Emergency | `quests.priority_quests` |
| `upcoming_events` | Próximos 7 dias | `calendar.upcoming_events` |
| `weekly_xp` | XP por dia nos últimos 7 dias | `hunter.xp_by_day` |
| `recent_activity` | Últimos ganhos de XP | `hunter.recent_events` |
| `emails` | Não lidos do Gmail | `gmail.unread_safe` |
| `scheduled_content` | Posts agendados no seu Buffer | `buffer.scheduled_posts_safe` |

Widgets desligados não fazem consulta. Ao abrir o dashboard, `quests.roll_over_recurring()` roda
para que as Daily Quests do dia já apareçam.

**Widgets novos aparecem ligados** mesmo para quem já tinha salvo a escolha: `dashboard.widgets_known`
guarda os widgets que existiam no último salvamento, e um widget fora dessa lista entra ligado até você
salvar de novo.

Resumo financeiro e progresso acadêmico entram como widgets quando os módulos Finance e University
existirem; não são exibidos antes disso.

## Personalizar (`/dashboard/settings`)

Além dos widgets, escolhe o modo da **inicialização do System** (`ui.boot_mode` em `app_settings`, lido
por `app/core/experience.py`): uma vez por sessão do navegador (padrão), sempre que abrir o Dashboard, ou
desligada. A animação (`static/js/boot.js`) dura cerca de 3,5 s, pula com clique ou qualquer tecla,
respeita "reduzir movimento" e nunca aparece na tela de login.

## Adicionar um widget

1. Em `services.py`: chave e rótulo em `WIDGETS` e a função em `_LOADERS`.
2. Template `app/templates/dashboard/widgets/<chave>.html` (os dados chegam numa variável com o nome da chave).
3. Teste em `tests/test_dashboard.py`.
