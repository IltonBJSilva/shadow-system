# Módulo Hunter

Perfil do usuário, com nível, rank, atributos e histórico de XP.

| | |
|---|---|
| Pasta | `app/modules/hunter/` |
| URL | `/hunter/` |
| API pública | `app/modules/hunter/services.py` |
| Tabelas | `hunters`, `ranks`, `attributes`, `xp_events`, `attribute_gains` |

## Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `progression.py` | Regras puras: curva de XP, nível a partir do XP, rank por nível, XP por dificuldade. Sem banco. |
| `models.py` | Tabelas. |
| `defaults.py` | Ranks e atributos criados na primeira execução. |
| `services.py` | API pública: `get_status`, `award_xp`, `list_attributes`, `attribute_choices`, ranks, histórico. |
| `forms.py` / `routes.py` | Telas do perfil, atributos e ranks. |
| `cli.py` | `flask hunter seed`: cria os dados iniciais (também acontece sozinho no primeiro acesso). |

## Regras

**Curva de nível** (`progression.py`): para sair do nível N são necessários `100 + 50 × (N − 1)` XP.
É linear de propósito: sempre cresce, mas nunca fica impossível. Para mudar a curva, altere
`XP_BASE`/`XP_STEP` ou a função `xp_to_next_level`; os testes em `tests/test_hunter.py` mostram o
comportamento esperado.

**XP por dificuldade**: Trivial 10, Fácil 25, Normal 50, Difícil 100, Extrema 200
(`DIFFICULTY_XP`). Uma quest pode definir outro valor.

**Pontos de atributo**: cada atividade concluída dá pontos (1 a 5, igual à dificuldade) aos
atributos ligados a ela. Quais atividades contam para cada atributo é configurado nas quests,
categorias e hábitos.

**Ranks**: configuráveis em `/hunter/ranks`. O rank atual é o de maior nível mínimo já alcançado.
O rank de nível 1 não pode ser removido (sempre precisa existir um rank inicial).

**Sem punição excessiva**: `award_xp` com valor negativo (estorno, ex.: desmarcar um hábito)
nunca deixa o XP abaixo de zero. Dias sem atividade não tiram XP.

**Histórico**: todo ganho ou estorno vira um `XpEvent` com origem (`source`: `quest`, `habit`,
`manual`) e os pontos de atributo (`AttributeGain`). `hunters.total_xp` guarda a soma, para não
somar o histórico a cada página.

## Como outro módulo concede XP

```python
from app.modules.hunter import services as hunter

result = hunter.award_xp(
    50,
    source="quest",
    source_id=quest.id,
    description=f"Quest concluída: {quest.title}",
    attribute_ids=[1, 3],
    attribute_points=3,
)
db.session.commit()  # award_xp não faz commit: salve junto com a sua alteração
for message, category in hunter.award_messages(result):
    flash(message, category)
```
