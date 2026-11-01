"""Eventos de domínio dentro do processo (publish/subscribe simples).

Permite que um módulo reaja ao que acontece em outro sem que o outro o conheça. Exemplo:
`quests` publica "quest.completed"; `gamification` assina e concede bônus. Assim `quests` não
importa `gamification` (o que criaria dependência circular).

Os handlers rodam na hora, na mesma transação de quem publicou, e podem devolver mensagens
(texto, categoria do flash) para mostrar ao usuário.

Eventos publicados hoje:
    quest.completed   quest: QuestView, completed_at: datetime
    quest.missed      quest: QuestView, today: date
    habit.checked     habit_id, habit_name, log_id, streak, base_xp
    habit.unchecked   habit_id, log_id
"""
import logging
from collections import defaultdict
from typing import Any, Callable, Iterable

log = logging.getLogger(__name__)

Message = tuple[str, str]
Handler = Callable[..., Iterable[Message] | None]

_handlers: dict[str, list[Handler]] = defaultdict(list)


def subscribe(event: str) -> Callable[[Handler], Handler]:
    """Decorator: @subscribe("quest.completed")."""
    def register(handler: Handler) -> Handler:
        if handler not in _handlers[event]:
            _handlers[event].append(handler)
        return handler
    return register


def publish(event: str, **payload: Any) -> list[Message]:
    """Chama todos os handlers do evento e junta as mensagens que eles devolverem."""
    messages: list[Message] = []
    for handler in _handlers.get(event, []):
        result = handler(**payload)
        if result:
            messages.extend(result)
    return messages
