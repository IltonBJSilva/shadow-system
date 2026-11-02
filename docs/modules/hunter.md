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

## Títulos

O título exibido no perfil não é mais um texto livre: você escolhe entre os títulos **conquistados**
(Hunter > *Editar perfil* > *Título exibido*, ou a página **Títulos** em `/hunter/titles`).

| Tipo | Como se ganha |
|---|---|
| Conquista | Meta atingida numa métrica: `level`, `total_xp`, `quests_completed`, `habit_best_streak`, `workouts_completed` |
| Criado por você | Já nasce desbloqueado; só esses podem ser apagados |

Títulos padrão (`defaults.DEFAULT_TITLES`, nomes originais): Recém-desperto (início), Primeiro Passo,
Cumpridor de Missões (10 quests), Veterano das Missões (50), Incansável (200), Chama Constante
(7 dias seguidos num hábito), Inquebrável (30), Disciplina de Ferro (100), Primeiro Treino, Corpo em
Forja (20 treinos), Corpo de Aço (100), Ascendente (nível 10), Caçador Experiente (25), Elite (50),
Lenda Viva (100) e Colecionador de XP (10.000 XP).

Como funciona:

- `check_titles()` roda dentro de `award_xp` (todo ganho de XP) e ao abrir o perfil. O desbloqueio vira
  a mensagem *"[SYSTEM] Título desbloqueado: ..."*.
- A página **Títulos** mostra o progresso dos bloqueados (`3 / 10 quests concluídas`).
- Títulos padrão novos aparecem sozinhos em bancos antigos (`_seed_titles`). Um título escrito à mão na
  versão antiga vira um título seu, para não sumir.

Métricas de outros módulos são registradas sem o Hunter importar esses módulos:

```python
# app/modules/quests/__init__.py
from app.modules.hunter import services as hunter
hunter.register_metric("quests_completed", services.completed_count)
```

Para um título novo de outra métrica: registre a métrica no módulo dono do dado, acrescente a linha em
`DEFAULT_TITLES` e o rótulo em `RULE_LABELS`.
