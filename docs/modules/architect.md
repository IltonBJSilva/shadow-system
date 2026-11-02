# O Arquiteto

O mentor do Shadow System. Lê os dados reais, tira conclusões, indica prioridades e sugere missões. O
jogador decide: nenhuma sugestão vira quest sem ser aceita.

| | |
|---|---|
| Pasta | `app/modules/architect/` |
| URL | `/architect/` (configuração da IA em `/architect/settings`) |
| API pública | `app/modules/architect/services.py` |
| Tabelas | `architect_goals`, `architect_suggestions`, `architect_messages` |
| Depende de | `hunter`, `quests`, `habits`, `gamification`, `training` (só leitura) e `quests` (criar a missão aceita) |

## Fluxo

```
dados reais ──▶ context.build() ──▶ Snapshot ──┬──▶ analysis.analyze() ──▶ Report (regras, sem custo)
(services.py de                                │        insights · priorities · drafts
 cada módulo)                                  │
                                               └──▶ ai.chat() / ai.plan()  (Claude, opcional)
                                                        resposta · plano estruturado

drafts / plano ──▶ architect_suggestions (pendentes) ──▶ Aceitar ──▶ quests.create_quest()
                                                   └──▶ Descartar (a regra não volta por 14 dias)
```

## O retrato (`context.py`)

Um `Snapshot` com: nome, nível, rank, XP do nível, sequência de evolução, atributos (atuais e ganhos em 4
semanas), quais categorias desenvolvem cada atributo, contadores de quests, até 40 missões ativas
(título, tipo, categoria, prioridade, dificuldade, prazo, atraso, recorrência, XP), desempenho por
categoria em 30 dias (concluídas x não realizadas, dificuldade média, taxa), falhas por motivo em 60 dias,
hábitos (sequência, recorde, feito hoje, esperado hoje), treinos ativos (feitos x previstos na semana),
metas ativas e XP desta semana x o mesmo trecho da anterior.

É a única entrada das regras e da IA. Não inclui tokens, e-mails, senhas nem conteúdo de integrações.

## Regras (`analysis.py`)

Funções puras sobre o `Snapshot`. Cada uma só fala quando há dado suficiente e sempre cita o número.

| Regra | Quando | Saída |
|---|---|---|
| Sequência / ritmo | ≥ 3 dias com XP; semana < 60% ou > a anterior | insight |
| Level up perto | faltam ≤ 60 XP | insight |
| Atrasadas acumulando | ≥ 3 missões atrasadas | insight + "Revisar missões atrasadas (15 min)" |
| Sequência em risco | hábito esperado hoje, não feito, sequência ≥ 3 | insight |
| Desafio acima do momento | categoria com ≥ 4 casos e < 50% concluídas | insight + versão curta com dificuldade −1 |
| Pronto para subir | ≥ 90% concluídas e dificuldade média ≤ 2,5 | insight + desafio com dificuldade +2 |
| Padrão nas falhas | ≥ 3 falhas com motivo | insight; planejamento → "Planejar a semana" semanal; procrastinação → "Primeiros 15 minutos" |
| Falhas sem motivo | alguma sem motivo | insight (lembra que imprevisto devolve XP) |
| Atributo parado | os 2 com menos pontos em 4 semanas (com ≥ 10 pontos no total) | insight + sessão de 25 min numa categoria que o desenvolve |
| Treino da semana | sexta em diante, semana incompleta | insight |
| Meta sem missão | nenhuma missão ativa da área da meta nem que cite a meta | insight + "Próximo passo" e "Sessão semanal" |
| Dia sem missões | nada com prazo até hoje | insight |

**Faça primeiro:** até 3 missões ativas, ordenadas por atrasada → prazo hoje → prioridade → XP.

**Sugestões das regras** são guardadas com uma `rule_key`. A mesma regra não sugere de novo enquanto há
uma pendente nem por 14 dias depois de aceita ou descartada, e há no máximo 8 sugestões de regra pendentes.

## IA (`ai.py`)

- SDK oficial `anthropic` (fixado no `requirements.txt`), chamado só no servidor.
- Chave cadastrada pela tela, conferida com `models.retrieve` (sem gastar tokens) e guardada em
  `stored_secrets` (`credentials:architect`). Só o final aparece na tela.
- Modelo padrão `claude-opus-5-5`; opções Sonnet 5.5 e Haiku 5.5.
- `fallbacks: "default"` com o beta `server-side-fallback-2026-07-01` (Opus e Sonnet): se o classificador
  de segurança recusar, a API repete num modelo alternativo. O Haiku 5.5 não tem fallback e vai sem o
  parâmetro. Uma recusa final (`stop_reason == "refusal"`) vira mensagem de erro, nunca resposta.
- **Conversa:** `effort: "low"`; manda as últimas 20 falas (só o texto da pergunta e da resposta) e, na
  pergunta nova, o `Snapshot` dentro de `<dados_do_sistema>`.
- **Plano:** `effort: "medium"` e saída estruturada (`output_config.format` com JSON Schema). O servidor
  ainda saneia cada missão (dificuldade 1 a 5, prazo 0 a 30 dias, prioridade e recorrência válidas, meta
  existente).
- Erros da API (chave recusada, limite de uso, rede, 5xx) viram mensagens em português na tela.
- O prompt de sistema (`SYSTEM_PROMPT`) define o papel: usar só os dados, citar números, missões
  concretas, adaptar o desafio, não culpar falhas por imprevisto, respeitar descanso e espiritualidade.

Sem chave, a página mostra a análise por regras e explica como ligar a IA. Nenhuma resposta é simulada.

## Para outros módulos

| Função | Uso |
|---|---|
| `report()` | `(Snapshot, Report)` e guarda as sugestões novas das regras |
| `pending_suggestions()` / `accept_suggestion(id)` / `dismiss_suggestion(id)` | Sugestões |
| `save_goal(...)` / `list_goals()` / `set_goal_status(id, status)` | Metas |
| `ask(pergunta)` / `plan_with_ai(foco)` | IA (levantam `ArchitectAIError` com mensagem para a tela) |

## Testes

`tests/test_architect.py` usa um cliente falso no lugar do SDK: nenhum teste chama a Anthropic. Os testes
conferem o retrato, as regras, a não duplicação de sugestões, a validação da chave, o envio dos dados
reais com fallback, a memória da conversa, o tratamento de recusa e o saneamento do plano.

## Próximos passos possíveis

- Sugestões semanais automáticas (agendador) e relatório semanal.
- Comando de voz e transformar uma frase livre ("estudar cálculo amanhã à noite") em missão.
