# Módulo Treinos

Rotinas de treino que viram quests, calendário, hábito e progressão de carga. Sem IA: a rotina vem de
um modelo pronto, de um texto colado ou de um documento enviado, sempre num formato simples que o
System lê e mostra numa prévia antes de salvar.

Código: `app/modules/training/`. Telas em `/training/`. Depende de `quests`, `habits`, `calendar` e
`hunter`, sempre pela API pública (`services.py`).

## Três formas de criar

| Forma | Onde | Como funciona |
|---|---|---|
| Rotina pronta | `/training/new` > *Usar esta* | ABC, Full body, Superior/Inferior, Push/Pull/Legs, Em casa e Corrida iniciante (`library.py`). Abre o texto para ajustar |
| Colar texto | `/training/new` > campo *Rotina* | Escreva ou cole no formato abaixo |
| Enviar documento | `/training/new` > *Ler documento* | `.txt`, `.md`, `.docx` ou `.pdf` até 5 MB (`documents.py`). O texto extraído aparece para conferir; PDF escaneado (imagem) não tem texto |

## Formato do texto (`parser.py`)

```
Plano: Hipertrofia ABC
Segunda: Treino A - Peito e tríceps
- Supino reto 4x8-12 40kg descanso 90s
- Tríceps na polia 3x12 (pegada neutra)
Quarta: Treino B - Costas
1. Puxada frontal 4 x 10 @ 35,5 kg desc 2min
- Corrida leve 20min
```

- **Dia:** nome do dia da semana (`Segunda`, `seg`, `Terça-feira`...) seguido de `:` ou `-` e o nome do
  treino. Sem dia (`Treino A:` ou `Dia 1:`), os dias são distribuídos sozinhos: 3 treinos vão para
  segunda, quarta e sexta; 4 vão para segunda, terça, quinta e sexta.
- **Exercício:** `séries x repetições` (`4x10`, `3x8-12`, `3x45s`, `4xmax`). Opcionais: carga (`40kg`,
  `@ 35,5 kg`), descanso (`descanso 90s`, `desc 2min`) e observação entre parênteses.
- Sem séries, uma duração ou distância vira uma série só (`Corrida leve 20min`).
- Linhas que não são dia nem exercício são ignoradas e listadas na prévia.
- Dois treinos no mesmo dia da semana não são aceitos (junte os dois ou mude um de dia).

## O que acontece ao ativar (`services.activate_plan`)

Cada automação pode ser desligada no formulário.

1. **Quests:** uma Daily Quest semanal recorrente por dia de treino (`Treino: Treino A - Peito`), com os
   exercícios na descrição e os atributos Strength e Vitality. O dia guarda o `quest_series_id`, então
   toda ocorrência futura continua ligada ao plano.
2. **Calendário:** eventos do tipo *Treino* nas próximas 4 semanas, no horário e na duração do plano.
   Cada treino concluído renova as 4 semanas à frente, sem duplicar. Para mandar ao Google, use
   *Enviar ao Google* na tela do Google Calendar.
3. **Hábito:** `Treinar (nome do plano)`, agendado só nos dias do plano. Folga não quebra a sequência
   (ver [habits.md](habits.md)). É marcado sozinho quando o treino é concluído.
4. **Progressão:** quando todos os treinos da semana são feitos, o plano mostra a sugestão para a
   semana seguinte. Nada muda sozinho: você aplica ou ignora.

Dois planos ativos não podem usar o mesmo dia da semana.

## Registrar um treino

Conclua a quest do dia (em Quests ou no Dashboard). O módulo assina o evento `quest.completed`
(`handlers.py`) e, se a quest for de um dia de treino, grava uma `WorkoutSession`, marca o hábito,
confere os títulos (*Primeiro Treino*, *Corpo em Forja*, *Corpo de Aço*) e verifica se a semana fechou.

## Regras de progressão (`progression.py`)

| Exercício | Sugestão |
|---|---|
| Com carga (`40kg`) | + o aumento do plano (padrão 2,5 kg) |
| Repetições fixas (`12`) | +1 repetição, até 30 |
| Faixa (`8-12`) | +1 nas duas pontas, até 30 |
| Tempo (`45s`, `20min`) | +5 s ou +1 min |
| `max`, `falha`, distância | sem mudança |

Ao aplicar, os exercícios e a descrição das quests pendentes são atualizados; as próximas ocorrências
herdam o texto novo.

## Editar, pausar e remover

- **Editar** abre o plano no mesmo formato de texto. Num plano ativo, as quests pendentes e os eventos
  futuros são refeitos com o conteúdo novo.
- **Pausar** cancela as quests pendentes (sem perder XP), apaga os eventos futuros e arquiva o hábito.
  **Ativar** de novo reaproveita o mesmo hábito, com a sequência guardada.
- **Remover** apaga o plano e os treinos registrados. O XP ganho continua no histórico.

## Tabelas

| Tabela | O que guarda |
|---|---|
| `workout_plans` | Plano, horário, duração, automações ligadas, aumento de carga, hábito e semana de progressão pendente |
| `workout_days` | Um dia de treino (dia da semana, nome, série de quests) |
| `workout_exercises` | Exercícios do dia (séries, repetições, carga, descanso, observação) |
| `workout_sessions` | Cada treino feito (data, dia, quest) |

## Limitações

- Sem IA: textos muito livres (parágrafos corridos) precisam ser ajustados para o formato antes de
  salvar. A prévia mostra o que foi entendido.
- Um treino por dia da semana em cada plano.
- A carga é por exercício, não por série.
- As rotinas prontas são modelos gerais e não substituem um profissional de educação física.
