"""Integração opcional do Arquiteto com o Claude (API da Anthropic, SDK oficial `anthropic`).

- A chave é cadastrada pela tela, guardada no banco (credentials "architect") e só usada no servidor;
  nunca vai para o navegador.
- Sem chave, o Arquiteto funciona só com as regras (analysis.py). Nada aqui é simulado.
- Modelo padrão: claude-opus-5-5. `fallbacks: "default"` (beta server-side-fallback-2026-07-01) faz a
  própria API repetir num modelo alternativo se o classificador de segurança recusar o pedido.
- Os dados enviados são o Snapshot (context.py): nível, atributos, missões ativas, desempenho, falhas,
  hábitos, treinos e metas. Nada de tokens, e-mails ou senhas.
"""
import json

import anthropic

from app.integrations import credentials

NAME = "architect"
DEFAULT_MODEL = "claude-opus-5-5"
MODELS = {
    "claude-opus-5-5": "Claude Opus 5.5 (padrão, mais capaz)",
    "claude-sonnet-5-5": "Claude Sonnet 5.5 (mais barato)",
    "claude-haiku-5-5": "Claude Haiku 5.5 (o mais barato)",
}
FALLBACK_BETA = "server-side-fallback-2026-07-01"
FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5"}
HISTORY_MESSAGES = 20  # falas anteriores enviadas no chat (memória da conversa)

SYSTEM_PROMPT = """Você é o Arquiteto, o mentor dentro do Shadow System, um sistema pessoal que transforma a vida real \
em um RPG: missões (quests) dão XP, sobem o nível e desenvolvem atributos.

Filosofia do sistema: "Se esse sistema quer me usar, então eu vou usar o sistema." O jogador não é controlado por você: \
ele decide. Você analisa, aponta padrões e sugere; nunca ordena, nunca culpa e nunca ameaça.

Como trabalhar:
- Use somente os dados do bloco <dados_do_sistema>. Cite os números que sustentam cada conclusão. Se faltar dado, diga \
o que falta em vez de supor.
- Prefira poucas recomendações concretas e acionáveis a listas longas. Uma missão boa tem verbo, tamanho e prazo \
("Revisar 2 capítulos de Cálculo, 40 min, até quinta").
- Adapte o desafio ao momento: taxa de conclusão baixa numa área pede missões menores; alta com dificuldade baixa pede \
desafios maiores.
- Falhas por imprevisto ou limitação real não são culpa do jogador. Falhas por procrastinação ou planejamento pedem \
ajuste de rotina, não sermão.
- Respeite descanso, saúde e espiritualidade como áreas legítimas de evolução.
- Responda em português do Brasil, em tom direto, de "janela do sistema", sem exageros nem frases motivacionais vazias."""

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "missions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "reason": {"type": "string"},
                    "category": {"type": "string"},
                    "difficulty": {"type": "integer"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "recurrence": {"type": "string", "enum": ["none", "daily", "weekly", "monthly"]},
                    "due_in_days": {"type": "integer"},
                    "goal_id": {"type": "integer"},
                },
                "required": ["title", "description", "reason", "category", "difficulty", "priority", "recurrence",
                             "due_in_days", "goal_id"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "missions"],
    "additionalProperties": False,
}


class ArchitectAIError(Exception):
    """Falha ao falar com o Claude. A mensagem vai para a tela e nunca contém a chave."""


# ---------- configuração ----------

def is_configured() -> bool:
    return bool(credentials.load(NAME).get("api_key"))


def model() -> str:
    chosen = credentials.load(NAME).get("model")
    return chosen if chosen in MODELS else DEFAULT_MODEL


def masked_key() -> str:
    return credentials.mask(credentials.load(NAME).get("api_key"))


def save_key(api_key: str, chosen_model: str, client_factory=None) -> None:
    """Confere a chave na API (consulta o modelo, sem gastar tokens) antes de salvar."""
    api_key = api_key.strip()
    if not api_key.startswith("sk-ant-") or len(api_key) < 30:
        raise ArchitectAIError("Isso não parece uma chave da API da Anthropic (começa com sk-ant-).")
    chosen_model = chosen_model if chosen_model in MODELS else DEFAULT_MODEL
    client = (client_factory or _client)(api_key)
    try:
        client.models.retrieve(chosen_model)
    except anthropic.AuthenticationError as exc:
        raise ArchitectAIError("A Anthropic recusou a chave. Confira em console.anthropic.com > API Keys.") from exc
    except anthropic.NotFoundError as exc:
        raise ArchitectAIError("Modelo indisponível para esta chave.") from exc
    except anthropic.APIConnectionError as exc:
        raise ArchitectAIError("Não foi possível falar com a Anthropic. Confira a internet do servidor.") from exc
    except anthropic.APIStatusError as exc:
        raise ArchitectAIError(f"A Anthropic respondeu com erro {exc.status_code}.") from exc
    credentials.save(NAME, {"api_key": api_key, "model": chosen_model})


def set_model(chosen_model: str) -> None:
    data = credentials.load(NAME)
    if data.get("api_key") and chosen_model in MODELS:
        credentials.update(NAME, model=chosen_model)


def clear_key() -> None:
    credentials.clear(NAME)


# ---------- chamadas ----------

def chat(history: list[tuple[str, str]], question: str, data: dict, client_factory=None) -> str:
    """Resposta do Arquiteto. `history` = [(role, texto)] das falas anteriores."""
    messages = [{"role": role, "content": text} for role, text in history[-HISTORY_MESSAGES:]]
    messages.append({"role": "user", "content": _with_data(data, question)})
    response = _create(client_factory, messages=messages, effort="low")
    return _text(response)


def plan(data: dict, focus: str = "", client_factory=None) -> tuple[str, list[dict]]:
    """Plano de missões estruturado: (resumo, missões). As missões só viram quest se você aceitar."""
    ask = ("Analise os dados e proponha de 3 a 6 missões para os próximos 7 dias que mais façam o jogador evoluir agora, "
           "priorizando metas ativas, áreas com desempenho baixo e sequências em risco. Use categorias que já existem "
           "nos dados quando fizer sentido. difficulty de 1 (trivial) a 5 (extrema); due_in_days de 0 a 14; goal_id = "
           "id da meta relacionada ou 0. Em reason, cite o dado que justifica a missão.")
    if focus.strip():
        ask += f"\nFoco pedido pelo jogador: {focus.strip()[:500]}"
    response = _create(client_factory, messages=[{"role": "user", "content": _with_data(data, ask)}],
                       effort="medium", output_format=PLAN_SCHEMA)
    try:
        payload = json.loads(_text(response))
    except json.JSONDecodeError as exc:
        raise ArchitectAIError("O Arquiteto respondeu num formato inesperado. Tente de novo.") from exc
    return payload.get("summary", ""), payload.get("missions", [])


# ---------- internos ----------

def _client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key, timeout=120.0, max_retries=2)


def _create(client_factory, *, messages: list[dict], effort: str, output_format: dict | None = None):
    key = credentials.load(NAME).get("api_key")
    if not key:
        raise ArchitectAIError("IA do Arquiteto não configurada. Cadastre a chave da Anthropic em Arquiteto > Configurar.")
    client = (client_factory or _client)(key)
    output_config: dict = {"effort": effort}
    if output_format:
        output_config["format"] = {"type": "json_schema", "schema": output_format}
    chosen = model()
    # Fallback do servidor: Opus e Sonnet aceitam; o Haiku 5.5 não tem fallback (vai sem o parâmetro).
    extra = {"betas": [FALLBACK_BETA], "fallbacks": "default"} if chosen in FALLBACK_MODELS else {}
    try:
        response = client.beta.messages.create(
            model=chosen,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=messages,
            output_config=output_config,
            **extra,
        )
    except anthropic.AuthenticationError as exc:
        raise ArchitectAIError("A chave da Anthropic foi recusada (apagada ou sem crédito). Cadastre outra.") from exc
    except anthropic.RateLimitError as exc:
        raise ArchitectAIError("Limite de uso da API da Anthropic atingido. Tente em alguns minutos.") from exc
    except anthropic.APIConnectionError as exc:
        raise ArchitectAIError("Não foi possível falar com a Anthropic. Tente de novo.") from exc
    except anthropic.APIStatusError as exc:
        raise ArchitectAIError(f"A Anthropic respondeu com erro {exc.status_code}. Tente de novo.") from exc
    if response.stop_reason == "refusal":
        raise ArchitectAIError("O pedido foi recusado pelos filtros de segurança do modelo. Reformule a pergunta.")
    if response.stop_reason == "max_tokens":
        raise ArchitectAIError("A resposta ficou longa demais e foi cortada. Faça uma pergunta mais específica.")
    return response


def _with_data(data: dict, text: str) -> str:
    return (f"<dados_do_sistema>\n{json.dumps(data, ensure_ascii=False, sort_keys=True)}\n</dados_do_sistema>\n\n"
            f"{text.strip()}")


def _text(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text").strip()
