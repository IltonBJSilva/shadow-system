"""Script para agendar em lote os 11 Shorts no YouTube (YouTube Data API v3).

Datas: 1 vídeo por dia, às 18:30 (horário de Brasília).
Requer: Canal do YouTube autorizado em /integrations/youtube/.
"""
from datetime import datetime, timezone
from pathlib import Path

from app import create_app
from app.integrations import youtube

RENDERS_DIR = Path(r"C:\Users\ilton\Videos\IA\renders")

YOUTUBE_VIDEOS = [
    {
        "filename": "Você Não Paga a IA por Palavras.mp4",
        "title": "Você Não Paga a IA por Palavras 🤯 #Shorts",
        "date_utc": datetime(2026, 11, 11, 21, 30, tzinfo=timezone.utc),  # 18:30 BRT
        "description": (
            "Quando você usa o ChatGPT, o Claude ou qualquer outra IA, a cobrança não é por palavra: é por TOKEN. "
            "E entender isso muda o jeito como você escreve seus prompts.\n\n"
            "Neste short eu explico o que é um token e por que ele é a 'moeda' das inteligências artificiais.\n\n"
            "👉 Siga o canal para mais dicas de como usar IA gastando menos.\n\n"
            "#shorts #ia #inteligenciaartificial #tokens #chatgpt #claude #prompt #tecnologia"
        ),
        "tags": ["shorts", "ia", "inteligenciaartificial", "tokens", "chatgpt", "claude", "prompt", "tecnologia"],
    },
    {
        "filename": "Escrever em Português Gasta Mais Tokens.mp4",
        "title": "Escrever em Português Gasta Mais Tokens? 🇧🇷 #Shorts",
        "date_utc": datetime(2026, 11, 12, 21, 30, tzinfo=timezone.utc),
        "description": (
            "Você sabia que o mesmo texto pode custar mais tokens em português do que em inglês? "
            "Os modelos de IA quebram as palavras de um jeito diferente em cada idioma, e isso pesa no bolso e no limite de uso.\n\n"
            "Veja por que isso acontece e o que você pode fazer a respeito.\n\n"
            "👉 Siga o canal para mais dicas sobre IA.\n\n"
            "#shorts #ia #tokens #portugues #chatgpt #claude #inteligenciaartificial #dicasdeia"
        ),
        "tags": ["shorts", "ia", "tokens", "portugues", "chatgpt", "claude", "inteligenciaartificial", "dicasdeia"],
    },
    {
        "filename": "O Segredo dos IDs de Tokens que Ninguém Te Conta.mp4",
        "title": "O Segredo dos IDs de Tokens que Ninguém Te Conta 🔢 #Shorts",
        "date_utc": datetime(2026, 11, 13, 21, 30, tzinfo=timezone.utc),
        "description": (
            "A IA não lê palavras: ela lê NÚMEROS. Cada pedaço de texto vira um ID de token antes de chegar ao modelo.\n\n"
            "Neste short eu mostro como funciona essa tradução de texto para números por trás de toda conversa com uma IA.\n\n"
            "👉 Siga o canal para entender a IA por dentro.\n\n"
            "#shorts #ia #tokens #llm #inteligenciaartificial #machinelearning #tecnologia #curiosidades"
        ),
        "tags": ["shorts", "ia", "tokens", "llm", "inteligenciaartificial", "machinelearning", "tecnologia"],
    },
    {
        "filename": "Pare de Usar o Modelo de IA Mais Caro.mp4",
        "title": "Pare de Usar o Modelo de IA Mais Caro! 💸 #Shorts",
        "date_utc": datetime(2026, 11, 14, 21, 30, tzinfo=timezone.utc),
        "description": (
            "Usar sempre o modelo mais poderoso parece a escolha certa, mas na maioria das vezes é só desperdício. "
            "Muitas tarefas são resolvidas perfeitamente por modelos menores, mais rápidos e mais baratos.\n\n"
            "Aprenda a escolher o modelo certo para cada tarefa.\n\n"
            "👉 Siga o canal para usar IA de forma mais inteligente.\n\n"
            "#shorts #ia #claude #chatgpt #economia #produtividade #inteligenciaartificial #dicasdeia"
        ),
        "tags": ["shorts", "ia", "claude", "chatgpt", "economia", "produtividade", "inteligenciaartificial"],
    },
    {
        "filename": "Nem Todo Problema Precisa da IA Mais Inteligente.mp4",
        "title": "Nem Todo Problema Precisa da IA Mais Inteligente 🧠 #Shorts",
        "date_utc": datetime(2026, 11, 15, 21, 30, tzinfo=timezone.utc),
        "description": (
            "Você não chama um cirurgião para colocar um curativo. Com a IA é a mesma coisa: nem todo problema precisa do modelo 'especialista'.\n\n"
            "Neste short eu mostro como pensar antes de escolher qual IA usar e economizar tempo e dinheiro.\n\n"
            "👉 Siga o canal para mais dicas práticas de IA.\n\n"
            "#shorts #ia #inteligenciaartificial #claude #chatgpt #produtividade #tokens #dicasdeia"
        ),
        "tags": ["shorts", "ia", "inteligenciaartificial", "claude", "chatgpt", "produtividade", "tokens"],
    },
    {
        "filename": "A Memória da IA Tem Limite.mp4",
        "title": "A Memória da IA Tem Limite (e Você Precisa Saber Disso) ⚠️ #Shorts",
        "date_utc": datetime(2026, 11, 16, 21, 30, tzinfo=timezone.utc),
        "description": (
            "A IA não lembra de tudo para sempre. Toda conversa tem uma 'janela de contexto', "
            "e quando ela enche, informações importantes começam a ser esquecidas.\n\n"
            "Entenda o que é a janela de contexto e por que ela afeta a qualidade das respostas.\n\n"
            "👉 Siga o canal para dominar a IA.\n\n"
            "#shorts #ia #janeladecontexto #tokens #llm #claude #chatgpt #inteligenciaartificial"
        ),
        "tags": ["shorts", "ia", "janeladecontexto", "tokens", "llm", "claude", "chatgpt"],
    },
    {
        "filename": "A IA Relê Sua Conversa INTEIRA a Cada Mensagem.mp4",
        "title": "A IA Relê Sua Conversa INTEIRA a Cada Mensagem 😱 #Shorts",
        "date_utc": datetime(2026, 11, 17, 21, 30, tzinfo=timezone.utc),
        "description": (
            "Cada vez que você manda uma mensagem, a IA relê toda a conversa desde o começo. "
            "Por isso conversas longas ficam mais lentas, mais caras e consomem seu limite mais rápido.\n\n"
            "Veja como isso funciona e quando vale a pena começar um chat novo.\n\n"
            "👉 Siga o canal para mais dicas de IA.\n\n"
            "#shorts #ia #tokens #chatgpt #claude #inteligenciaartificial #tecnologia #dicasdeia"
        ),
        "tags": ["shorts", "ia", "tokens", "chatgpt", "claude", "inteligenciaartificial", "tecnologia"],
    },
    {
        "filename": "2 Comandos do Claude Code que Vão Te Salvar.mp4",
        "title": "2 Comandos do Claude Code que Vão Te Salvar ⚡ #Shorts",
        "date_utc": datetime(2026, 11, 18, 21, 30, tzinfo=timezone.utc),
        "description": (
            "Se você usa o Claude Code para programar, precisa conhecer esses dois comandos. "
            "Eles ajudam a controlar o contexto da conversa e evitam desperdício de tokens.\n\n"
            "Simples, rápidos e fazem muita diferença no dia a dia.\n\n"
            "👉 Siga o canal para mais dicas de Claude Code e IA para programação.\n\n"
            "#shorts #claudecode #claude #programacao #ia #devs #tokens #produtividade"
        ),
        "tags": ["shorts", "claudecode", "claude", "programacao", "ia", "devs", "tokens"],
    },
    {
        "filename": "Pare de Mandar Seu Código INTEIRO para a IA.mp4",
        "title": "Pare de Mandar Seu Código INTEIRO para a IA 🛑 #Shorts",
        "date_utc": datetime(2026, 11, 19, 21, 30, tzinfo=timezone.utc),
        "description": (
            "Jogar o projeto inteiro na IA parece ajudar, mas só gasta tokens e deixa as respostas piores. "
            "A IA funciona melhor quando recebe apenas o contexto que realmente importa.\n\n"
            "Aprenda a enviar só o necessário e a ter respostas melhores gastando menos.\n\n"
            "👉 Siga o canal para programar melhor com IA.\n\n"
            "#shorts #programacao #ia #claudecode #chatgpt #devs #tokens #codigo"
        ),
        "tags": ["shorts", "programacao", "ia", "claudecode", "chatgpt", "devs", "tokens"],
    },
    {
        "filename": "O Erro que Faz Você Gastar Tokens à Toa.mp4",
        "title": "O Erro que Faz Você Gastar Tokens à Toa 🔥 #Shorts",
        "date_utc": datetime(2026, 11, 20, 21, 30, tzinfo=timezone.utc),
        "description": (
            "Tem um erro muito comum que faz você queimar tokens sem perceber, e quase todo mundo comete.\n\n"
            "Neste short eu mostro qual é esse erro e como evitar, para sua IA render muito mais.\n\n"
            "👉 Siga o canal para mais dicas de economia com IA.\n\n"
            "#shorts #ia #tokens #claude #chatgpt #economia #inteligenciaartificial #dicasdeia"
        ),
        "tags": ["shorts", "ia", "tokens", "claude", "chatgpt", "economia", "inteligenciaartificial"],
    },
    {
        "filename": "6 Hábitos para Gastar Menos Tokens na IA.mp4",
        "title": "6 Hábitos para Gastar Menos Tokens na IA ✅ #Shorts",
        "date_utc": datetime(2026, 11, 21, 21, 30, tzinfo=timezone.utc),
        "description": (
            "Quer usar a IA o dia inteiro sem estourar o limite? "
            "Esses 6 hábitos simples vão fazer você gastar muito menos tokens e ainda ter respostas melhores.\n\n"
            "Salve este vídeo para consultar depois!\n\n"
            "👉 Siga o canal para mais dicas práticas de IA.\n\n"
            "#shorts #ia #tokens #produtividade #claude #chatgpt #inteligenciaartificial #dicasdeia"
        ),
        "tags": ["shorts", "ia", "tokens", "produtividade", "claude", "chatgpt", "inteligenciaartificial"],
    },
]


def run():
    app = create_app()
    with app.app_context():
        if not youtube.is_authorized():
            print("[ERRO] YouTube não está autorizado.")
            print("Por favor, acesse http://127.0.0.1:5050/integrations/youtube/ e clique em 'Autorizar Canal do YouTube'.")
            return

        print("=== Iniciando Agendamento em Lote no YouTube ===")
        ch = youtube.channel_info()
        print(f"Canal: {ch.title} ({ch.subscriber_count} inscritos, {ch.video_count} vídeos)\n")

        for idx, item in enumerate(YOUTUBE_VIDEOS):
            v_path = RENDERS_DIR / item["filename"]
            if not v_path.is_file():
                print(f"[ERRO] Arquivo não encontrado: {v_path}")
                continue

            print(f"[{idx+1}/11] Enviando e Agendando: {item['title']}")
            print(f"       Data de Lançamento (UTC): {item['date_utc'].strftime('%d/%m/%Y às %H:%M UTC')}")
            try:
                vid = youtube.upload_video(
                    media_source=v_path,
                    title=item["title"],
                    description=item["description"],
                    tags=item["tags"],
                    privacy_status="private",
                    publish_at_utc=item["date_utc"],
                    is_short=True,
                )
                print(f"       ✓ Agendado com sucesso! Link: {vid.url}\n")
            except Exception as e:
                print(f"       ✖ Falha no agendamento: {e}\n")

        print("=== Todos os 11 vídeos foram processados no YouTube! ===")


if __name__ == "__main__":
    run()
