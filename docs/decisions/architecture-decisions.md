# Decisões de arquitetura

Registro curto do que foi decidido e por quê. Nova decisão = nova seção, sem apagar as antigas.

## ADR-001: Monólito modular em Flask (01/11/2026)

**Decisão:** uma aplicação Flask com módulos (`app/modules/*`) que conversam só pela API pública
(`services.py`).
**Motivo:** sistema pessoal, um usuário, um servidor. Microserviços trariam rede, deploy e consistência
distribuída sem ganho. A disciplina de fronteiras dá a modularidade que importa.

## ADR-002: Sem camada de repositório (01/11/2026)

**Decisão:** consultas SQLAlchemy dentro dos serviços.
**Motivo:** com SQLAlchemy 2 as consultas já são legíveis; repositórios só repetiriam métodos. Se um
módulo crescer, extrair `queries.py` não muda a API pública.

## ADR-003: Datas sem fuso, no horário local (01/11/2026)

**Decisão:** `DateTime` naive no fuso de `TIMEZONE`; conversão só nas integrações.
**Motivo:** um usuário em um fuso. Evita converter em toda consulta e tela. Se um dia houver vários
fusos, migrar para UTC + conversão na apresentação.

## ADR-004: Calendário interno como fonte de verdade (01/11/2026)

**Decisão:** eventos ficam em `calendar_events`; o Google Calendar é sincronizado de/para lá.
**Motivo:** o app funciona sem internet e sem credenciais, e os módulos consultam um lugar só.
Duplicação evitada por `google_event_id` único e pela marca `shadowEventId` no Google.

## ADR-005: Buffer só através do Kausa Social Scheduler (01/11/2026) — substituída pela ADR-009

**Decisão:** o Shadow System não chama o Buffer; lê o Kausa por HTTP.
**Motivo:** o Kausa já tem a chave, o upload de imagens (Supabase) e as regras de cada rede. Duplicar
seria manter dois clientes e duas chaves. Os repositórios continuam independentes.

## ADR-006: Gamificação sem punição (01/11/2026) — revista pela ADR-010

**Decisão:** XP nunca é retirado por inatividade; ocorrências recorrentes perdidas viram "Não
realizada"; estornos só desfazem ações do próprio usuário e nunca deixam o XP negativo.
**Motivo:** o objetivo é incentivar constância. Punição excessiva faz abandonar o sistema.

## ADR-007: Curva de XP linear (01/11/2026)

**Decisão:** `100 + 50 × (nível − 1)` XP por nível.
**Motivo:** cresce de forma perceptível sem ficar inalcançável. Fica isolada em `progression.py` para
ser trocada sem impacto.

## ADR-008: Frontend sem framework e sem CDN (01/11/2026)

**Decisão:** Jinja2 + CSS/JS próprios, CSP restritiva.
**Motivo:** menos dependências, funciona offline, fácil de entender. Interatividade pontual em `shadow.js`.

## ADR-009: Buffer pessoal direto, sem o Kausa (01/11/2026)

**Substitui a ADR-005.**
**Decisão:** o Shadow System fala direto com o Buffer da conta pessoal do usuário, com token cadastrado
pela tela. A integração de leitura do Kausa Social Scheduler foi removida.
**Motivo:** o Kausa é da empresa (Kausa); as postagens do Shadow System são do perfil pessoal, em outra
conta do Buffer. As regras por rede já validadas no Kausa foram reaproveitadas no código (sem depender
dele), e os dois projetos seguem independentes.

## ADR-010: Punições justas e redimíveis (01/11/2026)

**Revê a ADR-006**, a pedido do usuário (quer punições, como no Solo Leveling).
**Decisão:** quest recorrente não feita tira uma porcentagem pequena do XP (padrão 10%), limitada ao XP
do nível atual (nunca cai de nível), e gera uma Penalty Quest que devolve o XP se cumprida no dia.
Tudo configurável e desligável em `/gamification/`. Bônus para primeira quest, prazo adiantado, combo
diário e sequências de hábito.
**Motivo:** a pressão do "Penalty Zone" motiva, mas sem espiral de perda: sempre há como recuperar.

## ADR-011: Eventos em processo para regras transversais (01/11/2026)

**Decisão:** `app/core/events.py` (publish/subscribe síncrono). A gamificação reage a quests e hábitos.
**Motivo:** `gamification` depende de `quests`; se `quests` chamasse `gamification` haveria ciclo. Eventos
deixam a regra de jogo num lugar só sem acoplar os módulos. Síncrono e na mesma transação: simples e consistente.

## ADR-012: Sons sintetizados e arte original (01/11/2026)

**Decisão:** efeitos sonoros gerados com Web Audio e emblema SVG próprio; avatar por link público escolhido
pelo usuário.
**Motivo:** áudios e imagens do anime são protegidos por direitos autorais. Sons sintetizados não pesam no
repositório e funcionam offline.
