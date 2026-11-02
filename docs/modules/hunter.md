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

## Conquistas e títulos

Cada **conquista** desbloqueia um **título** com o mesmo nome e paga, uma vez, uma recompensa em XP. O
título exibido no perfil é escolhido entre os conquistados (Hunter > *Editar perfil* > *Título exibido*,
ou a página **Conquistas** em `/hunter/titles`). Títulos criados por você nascem desbloqueados e são os
únicos que podem ser apagados.

| Ícone | Conquista (título) | Condição | XP |
|---|---|---|---|
| 🌑 | Recém-desperto | início | 0 |
| 👣 | Primeiro Passo | 1 missão concluída | 10 |
| ⬆️ | Despertar | nível 2 (primeiro level up) | 15 |
| 📆 | Semana Consistente | 7 dias seguidos com XP | 50 |
| ⚔️ | Cumpridor de Missões | 10 missões | 25 |
| 🏁 | Projeto Finalizado | 1 Main Quest concluída | 50 |
| 🔥 | Chama Constante | 7 dias seguidos num hábito | 30 |
| 🏋️ | Primeiro Treino | 1 treino | 15 |
| 🛡️ | Ascendente | nível 10 (Rank D) | 100 |
| 🌗 | 30 Dias de Evolução | 30 dias seguidos com XP | 150 |
| 💎 | Inquebrável | 30 dias seguidos num hábito | 100 |
| ⚒️ | Corpo em Forja | 20 treinos | 60 |
| 🎖️ | Veterano das Missões | 50 missões | 80 |
| 💯 | Centurião | 100 missões | 150 |
| 🗡️ | Caçador Experiente | nível 25 | 200 |
| ♾️ | Incansável | 200 missões | 250 |
| 🦾 | Corpo de Aço | 100 treinos | 250 |
| 🧱 | Disciplina de Ferro | 100 dias seguidos num hábito | 300 |
| 💠 | Colecionador de XP | 10.000 XP | 0 |
| 👑 | Elite | nível 50 | 500 |
| 🌌 | Lenda Viva | nível 100 | 1000 |

Métricas: `level`, `total_xp` e `evolution_days` (maior sequência de dias com XP líquido positivo) são do
próprio Hunter; `quests_completed`, `main_quests_completed`, `habit_best_streak` e `workouts_completed`
vêm de outros módulos (`register_metric`, abaixo).

Como funciona:

- `check_titles()` roda dentro de `award_xp` (todo ganho de XP), ao abrir o perfil e ao registrar um treino.
  O desbloqueio vira a notificação dourada *"[SYSTEM] CONQUISTA · Conquista desbloqueada: ... (+N XP)"*,
  com som próprio.
- A recompensa entra no histórico como `source="achievement"`, direto (sem passar por `award_xp`, para
  não verificar conquistas em laço). Desligável em Gamificação (`hunter.achievement_rewards`).
- Bancos da versão anterior: os títulos ganham ícone e ordem, e a recompensa vale só para o que ainda
  não foi desbloqueado (não paga retroativo).
- A página **Títulos** mostra o progresso dos bloqueados (`3 / 10 quests concluídas`).
- Títulos padrão novos aparecem sozinhos em bancos antigos (`_seed_titles`). Um título escrito à mão na
  versão antiga vira um título seu, para não sumir.

Métricas de outros módulos são registradas sem o Hunter importar esses módulos:

```python
# app/modules/quests/__init__.py
from app.modules.hunter import services as hunter
hunter.register_metric("quests_completed", services.completed_count)
```

Para uma conquista nova: registre a métrica no módulo dono do dado (se for nova), acrescente a linha em
`DEFAULT_TITLES` (key, nome, descrição, regra, limite, ícone, XP) e o rótulo em `RULE_LABELS`.

## XP padrão de uma missão

`progression.xp_for_difficulty(dificuldade, prioridade)`: XP base da dificuldade (10/25/50/100/200) ×
importância (baixa 0,8 · média 1,0 · alta 1,2 · crítica 1,4), arredondado para múltiplo de 5, mínimo 5.
Tabela completa no [README](../../README.md#xp-de-uma-missão).

## Atributos

Dez atributos padrão: Strength, Vitality, Intelligence, Discipline, Focus, Creativity, Financial
Intelligence, Spirituality, **Wisdom** (Sabedoria) e **Charisma** (Carisma). Bancos antigos ganham os dois
novos sozinhos (`_seed_missing_attributes`, pela chave; nomes que você mudou continuam).

`attribute_history(weeks=8)` devolve os pontos ganhos por atributo em cada semana (segunda a domingo), a
partir do histórico real (`AttributeGain`). É o gráfico *Evolução dos atributos* do perfil.

## Sequência de evolução

`evolution_streak()` = dias seguidos com XP líquido positivo até hoje (ou até ontem, se hoje ainda está
zerado). Um dia em que a punição anulou o ganho não conta. `best_evolution_streak()` é o recorde.
`xp_between(início, fim)` soma o XP líquido de um período (usado no widget Progresso e no Arquiteto).
