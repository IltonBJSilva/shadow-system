"""Sincroniza uploads de vídeos e posts da fila do banco local para o Render (produção)."""
import time
import httpx
from app import create_app
from app.core.models import BufferQueuePost, BufferUpload

RENDER_URL = "https://shadow-system-5v0w.onrender.com"
SYNC_KEY = "shadow-system-sync-2026-sec"


def run():
    app = create_app()
    with app.app_context():
        # 1. Enviar os 11 arquivos de vídeo para buffer_uploads no Render
        uploads = BufferUpload.query.all()
        print(f"=== Sincronizando {len(uploads)} uploads de vídeo para o Render ===")
        with httpx.Client(timeout=120.0) as client:
            for idx, u in enumerate(uploads):
                print(f"[{idx+1}/{len(uploads)}] Enviando {u.filename} ({u.size / 1024 / 1024:.2f} MB)...")
                try:
                    res = client.post(
                        f"{RENDER_URL}/integrations/buffer/api/sync-upload",
                        headers={"X-Sync-Key": SYNC_KEY},
                        data={
                            "token": u.token,
                            "filename": u.filename,
                            "mimetype": u.mimetype or "video/mp4",
                        },
                        files={"file": (u.filename, u.data, u.mimetype or "video/mp4")},
                    )
                    if res.status_code == 200:
                        print(f"       ✓ Upload sincronizado com sucesso!")
                    else:
                        print(f"       ✖ Erro ({res.status_code}): {res.text[:100]}")
                except Exception as e:
                    print(f"       ✖ Falha: {e}")

        # 2. Enviar os posts de vídeo da fila para buffer_queue_posts no Render
        all_posts = BufferQueuePost.query.all()
        video_posts = [p for p in all_posts if p.is_video]
        print(f"\n=== Sincronizando {len(video_posts)} posts de vídeo da fila para o Render ===")
        payload = [
            {
                "channel_id": p.channel_id,
                "channel_name": p.channel_name,
                "service": p.service,
                "text": p.text,
                "thumbnail": p.thumbnail,
                "target_date": p.target_date.isoformat() if p.target_date else None,
                "target_time": p.target_time,
                "status": p.status,
            }
            for p in video_posts
        ]

        with httpx.Client(timeout=60.0) as client:
            try:
                res = client.post(
                    f"{RENDER_URL}/integrations/buffer/api/sync-queue",
                    headers={"X-Sync-Key": SYNC_KEY},
                    json={"posts": payload},
                )
                if res.status_code == 200:
                    data = res.json()
                    print(f"✓ Fila sincronizada com sucesso! Novos posts adicionados: {data.get('added')}")
                else:
                    print(f"✖ Erro ao sincronizar fila ({res.status_code}): {res.text}")
            except Exception as e:
                print(f"✖ Falha: {e}")

        # 3. Verificação final
        print("\n=== Verificando URLs públicas no Render ===")
        with httpx.Client(timeout=30.0) as client:
            for u in uploads[:3]:
                url = f"{RENDER_URL}/integrations/buffer/uploads/{u.token}/{u.filename}"
                check = client.head(url)
                print(f"Status {check.status_code} -> {u.filename}")

        print("\n=== Sincronização concluída com sucesso! ===")


if __name__ == "__main__":
    run()

