# Calendário interno

Eventos com visão mensal, quests com prazo no mesmo calendário e aviso de conflito de horário.

| | |
|---|---|
| Pasta | `app/modules/calendar/` |
| URL | `/calendar/` (`?month=2026-11` para outro mês) |
| API pública | `app/modules/calendar/services.py` |
| Tabela | `calendar_events` |
| Depende de | `quests.services` |

## Por que um calendário interno, se existe o Google Calendar?

O calendário interno é a fonte de verdade do Shadow System: funciona sem internet, sem credenciais
e é o que os outros módulos consultam. O Google Calendar é uma integração **opcional** que importa
eventos para cá e envia eventos daqui para lá (ver [integrations.md](../integrations.md)).

## Regras

- Evento sem horário de fim dura **1 hora**. Evento de **dia inteiro** vai de 00:00 a 23:59.
- `end_at >= start_at` é garantido no serviço e no banco (constraint `end_after_start`).
- **Conflitos**: ao salvar, eventos com horário sobreposto aparecem como aviso. Não bloqueia (às vezes é
  intencional). Eventos de dia inteiro não contam como conflito.
- Um evento pode ser **vinculado a uma quest** (ex.: "Treino 18h" ligado à Daily Quest "Treinar").
- Quests com prazo aparecem no calendário automaticamente (não são copiadas para `calendar_events`).
- `source` diz a origem (`local` ou `google`) e `google_event_id` (único) evita duplicar eventos
  na sincronização.

## Para outros módulos

| Função | Uso |
|---|---|
| `save_event(EventInput)` | Criar/editar; retorna `(evento, conflitos)` |
| `events_between(start, end)` | Eventos que se sobrepõem ao intervalo |
| `upcoming_events(days, limit)` | Dashboard |
| `find_conflicts(start, end)` | Checar agenda antes de marcar algo (ex.: IA no futuro) |
| `month_grid(year, month)` | Tela mensal |
| `upsert_google_event`, `mark_pushed`, `local_events_to_push`, `delete_google_events_not_in` | Usadas pela integração com o Google |
