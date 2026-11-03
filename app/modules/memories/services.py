"""Regras das Memórias: upload otimizado, limites de armazenamento, privacidade, busca e filtros."""
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, or_, select

from app.core import images, time
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.hunter import services as hunter
from app.modules.quests import constants as quest_constants
from app.modules.quests import services as quests

from .models import Memory

KINDS: dict[str, str] = {
    "workout": "Treino", "project": "Projeto", "college": "Faculdade", "book": "Livro / estudo",
    "goal": "Meta alcançada", "spiritual": "Espiritual", "achievement": "Conquista pessoal", "other": "Outro",
}
IMAGE_SIDE = 1600
THUMB_SIDE = 480
MAX_PER_USER_BYTES = 60 * 1024 * 1024   # ~60 MB por conta (cabe no plano gratuito do banco)
MAX_PER_DAY = 20


@dataclass
class MemoryInput:
    title: str
    description: str = ""
    note: str = ""
    kind: str = "other"
    quest_id: int | None = None
    achievement: str = ""
    public: bool = False
    share_in_feed: bool = False
    day: date | None = None


def create(data: MemoryInput, photo: bytes) -> Memory:
    if not data.title.strip():
        raise DomainError("Dê um título para a memória.")
    if data.kind not in KINDS:
        raise DomainError("Tipo de atividade inválido.")
    if count_today() >= MAX_PER_DAY:
        raise DomainError(f"Limite de {MAX_PER_DAY} memórias por dia.")
    image = images.open_image(photo)
    full = images.to_webp(image, IMAGE_SIDE, 80)
    small = images.to_webp(image, THUMB_SIDE, 70)
    if used_bytes() + len(full.data) + len(small.data) > MAX_PER_USER_BYTES:
        raise DomainError("Espaço das memórias cheio. Apague algumas antigas para registrar novas.")
    quest_title, specialty = "", "other"
    if data.quest_id:
        quest = quests.get_quest(data.quest_id)  # já filtra pelo usuário: não liga memória à missão de outro
        quest_title = quest.title
        specialty = quest.category.specialty if quest.category else "other"
    status = hunter.get_status()
    memory = Memory(
        title=data.title.strip()[:120], description=data.description.strip()[:2000], note=data.note.strip()[:2000],
        kind=data.kind, quest_id=data.quest_id or None, quest_title=quest_title[:160], specialty=specialty,
        achievement=data.achievement.strip()[:80], rank_code=status.rank.code if status.rank else "",
        visibility="public" if data.public else "private", day=data.day or time.today(),
        width=full.width, height=full.height, size=len(full.data) + len(small.data), image=full.data, thumb=small.data,
    )
    db.session.add(memory)
    db.session.flush()
    if data.public and data.share_in_feed:
        _post(memory)
    db.session.commit()
    return memory


def get(memory_id: int) -> Memory:
    memory = db.session.get(Memory, memory_id)
    if memory is None:
        raise NotFoundError("Memória não encontrada.")
    return memory


def public(memory_id: int) -> Memory:
    """Memória de qualquer Hunter, desde que pública (a do próprio usuário vale sempre)."""
    memory = db.session.get(Memory, memory_id, execution_options={"all_users": True})
    from app.core.tenancy import current_user_id

    if memory is None or (memory.visibility != "public" and memory.user_id != current_user_id()):
        raise NotFoundError("Memória não encontrada.")
    return memory


def set_visibility(memory_id: int, public_: bool) -> Memory:
    memory = get(memory_id)
    memory.visibility = "public" if public_ else "private"
    db.session.commit()
    return memory


def delete(memory_id: int) -> None:
    memory = get(memory_id)
    from app.modules.arena.models import ActivityPost

    db.session.query(ActivityPost).filter(ActivityPost.memory_id == memory.id).delete()
    db.session.delete(memory)
    db.session.commit()


def gallery(search: str = "", kind: str = "", specialty: str = "", rank: str = "", month: str = "",
            visibility: str = "") -> list[Memory]:
    query = select(Memory).order_by(Memory.day.desc(), Memory.id.desc())
    if search.strip():
        like = f"%{search.strip().lower()}%"
        query = query.where(or_(func.lower(Memory.title).like(like), func.lower(Memory.quest_title).like(like),
                                func.lower(Memory.description).like(like), func.lower(Memory.achievement).like(like)))
    if kind in KINDS:
        query = query.where(Memory.kind == kind)
    if specialty in quest_constants.SPECIALTIES:
        query = query.where(Memory.specialty == specialty)
    if rank:
        query = query.where(Memory.rank_code == rank)
    if len(month) == 7 and month[4] == "-":
        year, mon = int(month[:4]), int(month[5:])
        start = date(year, mon, 1)
        end = date(year + (mon == 12), mon % 12 + 1, 1)
        query = query.where(Memory.day >= start, Memory.day < end)
    if visibility in ("public", "private"):
        query = query.where(Memory.visibility == visibility)
    return list(db.session.scalars(query.limit(200)))


def for_quest(quest_id: int) -> list[Memory]:
    return list(db.session.scalars(select(Memory).where(Memory.quest_id == quest_id).order_by(Memory.id)))


def used_bytes() -> int:
    return int(db.session.scalar(select(func.coalesce(func.sum(Memory.size), 0))) or 0)


def count_today() -> int:
    return db.session.scalar(select(func.count(Memory.id)).where(Memory.day == time.today())) or 0


def ranks_used() -> list[str]:
    return sorted({code for code in db.session.scalars(select(Memory.rank_code).distinct()) if code})


def _post(memory: Memory) -> None:
    from app.modules.arena import feed

    feed.post("memory", f"registrou a memória “{memory.title}”", icon="📸", specialty=memory.specialty,
              memory_id=memory.id)
