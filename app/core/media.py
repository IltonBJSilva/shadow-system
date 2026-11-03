"""Mídias do System: cada "slot" é um momento da experiência (entrada, música, level up...).

O dono envia os arquivos em Configurações > Mídias do System (ou `flask media import <pasta>`), e todos
os usuários ouvem/veem os mesmos. Sem arquivo num slot, o sistema usa o som sintetizado (sounds.js) ou
só o visual em CSS: nada quebra. Para adicionar um momento novo, inclua o slot em SLOTS e use
`ShadowAudio.play("<slot>")` no front-end.
"""
import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import defer

from app.extensions import db

from .errors import DomainError
from .models import MediaAsset


@dataclass(frozen=True)
class Slot:
    key: str
    label: str
    kind: str  # audio | image
    hint: str


SLOTS: dict[str, Slot] = {s.key: s for s in [
    Slot("entrance", "Áudio de entrada", "audio", "Toca uma vez ao entrar no System (voz curta)."),
    Slot("music", "Música de fundo", "audio", "Trilha ambiente em loop, opcional para cada usuário."),
    Slot("levelup", "Subida de nível", "audio", "Voz curta na janela de LEVEL UP."),
    Slot("achievement", "Conquista / recompensa", "audio", "Voz curta ao desbloquear conquista ou fragmento."),
    Slot("penalty", "Zona de Falha", "audio", "Voz curta quando uma punição é aplicada."),
    Slot("boot", "Imagem da inicialização", "image", "Fundo da tela de abertura do System (retrato)."),
    Slot("background", "Imagem do painel", "image", "Arte discreta atrás da janela de status do Hunter."),
    Slot("login", "Imagem do acesso", "image", "Arte da tela de login e do convite (pública)."),
]}
# A tela de login é pública: só a imagem dela pode ser lida sem estar logado.
PUBLIC_SLOTS = {"login"}
MAX_BYTES = {"audio": 12 * 1024 * 1024, "image": 3 * 1024 * 1024}
ALLOWED = {
    "audio": {"audio/mpeg", "audio/mp4", "audio/aac", "audio/ogg", "audio/webm", "audio/wav", "audio/x-wav"},
    "image": {"image/webp", "image/jpeg", "image/png", "image/avif"},
}


def get(slot: str) -> MediaAsset | None:
    return db.session.get(MediaAsset, slot) if slot in SLOTS else None


def versions() -> dict[str, str]:
    """slot -> versão curta (para o front-end montar URLs que mudam quando o arquivo muda)."""
    rows = db.session.execute(select(MediaAsset.slot, MediaAsset.etag)).all()
    return {slot: etag[:10] for slot, etag in rows if slot in SLOTS}


def listing() -> list[tuple[Slot, MediaAsset | None]]:
    present = {row.slot: row for row in db.session.scalars(select(MediaAsset).options(defer(MediaAsset.data)))}
    return [(slot, present.get(key)) for key, slot in SLOTS.items()]


def save(slot: str, filename: str, content: bytes, mimetype: str | None = None) -> MediaAsset:
    spec = SLOTS.get(slot)
    if spec is None:
        raise DomainError("Momento de mídia desconhecido.")
    mimetype = (mimetype or mimetypes.guess_type(filename)[0] or "").split(";")[0].strip().lower()
    if mimetype == "audio/mp3":
        mimetype = "audio/mpeg"
    if mimetype not in ALLOWED[spec.kind]:
        kind = "um áudio (mp3, m4a, ogg, webm)" if spec.kind == "audio" else "uma imagem (webp, jpg, png)"
        raise DomainError(f"Envie {kind} para “{spec.label}”.")
    if not content:
        raise DomainError("Arquivo vazio.")
    if len(content) > MAX_BYTES[spec.kind]:
        raise DomainError(f"Arquivo grande demais (máximo {MAX_BYTES[spec.kind] // (1024 * 1024)} MB).")
    row = db.session.get(MediaAsset, slot) or MediaAsset(slot=slot)
    row.filename = Path(filename).name[:200]
    row.mimetype = mimetype
    row.size = len(content)
    row.etag = hashlib.sha1(content).hexdigest()
    row.data = content
    db.session.add(row)
    db.session.commit()
    return row


def delete(slot: str) -> None:
    row = db.session.get(MediaAsset, slot)
    if row is not None:
        db.session.delete(row)
        db.session.commit()


def import_folder(folder: Path) -> list[str]:
    """Importa arquivos chamados <slot>.<extensão> (ex.: music.mp3, boot.webp). Devolve os slots salvos."""
    saved = []
    for path in sorted(Path(folder).iterdir()):
        if path.is_file() and path.stem in SLOTS:
            save(path.stem, path.name, path.read_bytes())
            saved.append(path.stem)
    return saved
