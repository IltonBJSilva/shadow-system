"""Cria uma playlist no YouTube e adiciona os 11 Shorts agendados."""
from app import create_app
from app.integrations import youtube

PLAYLIST_TITLE = "Inteligência Artificial & Tokens 🤖"
PLAYLIST_DESC = (
    "Aprenda tudo sobre tokens em IA, como economizar dinheiro e limites de contexto "
    "no ChatGPT, Claude e LLMs. Série completa em Shorts explicativos direto ao ponto."
)

VIDEO_IDS = [
    ("F8NyEj7RyoQ", "Você Não Paga a IA por Palavras"),
    ("V9SDbkR8Pa0", "Escrever em Português Gasta Mais Tokens?"),
    ("TRmwtqeNeEE", "O Segredo dos IDs de Tokens que Ninguém Te Conta"),
    ("Ooh9rQq7rfY", "Pare de Usar o Modelo de IA Mais Caro!"),
    ("nR2w2g-vOIw", "Nem Todo Problema Precisa da IA Mais Inteligente"),
    ("-hZR68CNUIU", "A Memória da IA Tem Limite"),
    ("8k3StXZb558", "A IA Relê Sua Conversa INTEIRA a Cada Mensagem"),
    ("UEEEdtxp0O0", "2 Comandos do Claude Code que Vão Te Salvar"),
    ("p3V3kXHmJws", "Pare de Mandar Seu Código INTEIRO para a IA"),
    ("3t9NqDVlVjI", "O Erro que Faz Você Gastar Tokens à Toa"),
    ("KwMg1Hu4_sI", "6 Hábitos para Gastar Menos Tokens na IA"),
]


def run():
    app = create_app()
    with app.app_context():
        if not youtube.is_authorized():
            print("[ERRO] YouTube não está autorizado.")
            return

        print("=== Criando Playlist no YouTube ===")
        print(f"Título: {PLAYLIST_TITLE}")
        try:
            pl_id = youtube.create_playlist(
                title=PLAYLIST_TITLE,
                description=PLAYLIST_DESC,
                privacy_status="public",
            )
            print(f"✓ Playlist criada com sucesso! ID: {pl_id}")
            print(f"🔗 Link da Playlist: https://www.youtube.com/playlist?list={pl_id}\n")
        except Exception as e:
            print(f"✖ Erro ao criar playlist: {e}")
            return

        print("=== Adicionando os 11 vídeos à Playlist ===")
        for idx, (vid_id, title) in enumerate(VIDEO_IDS):
            try:
                youtube.add_video_to_playlist(pl_id, vid_id)
                print(f"[{idx+1}/11] ✓ Adicionado: {title} ({vid_id})")
            except Exception as e:
                print(f"[{idx+1}/11] ✖ Erro ao adicionar {title}: {e}")

        print("\n=== Todos os vídeos foram adicionados à playlist com sucesso! ===")


if __name__ == "__main__":
    run()
