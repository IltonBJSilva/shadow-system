"""Regras da Loja das Sombras: requisitos, recrutamento e bônus (XP e atributos)."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core import events
from app.core.errors import DomainError, NotFoundError
from app.extensions import db
from app.modules.character import catalog as items
from app.modules.character import services as character
from app.modules.hunter import services as hunter

from . import catalog
from .models import PlayerShadow


@dataclass(frozen=True)
class ShadowState:
    shadow: catalog.Shadow
    recruited_at: datetime | None
    rank_ok: bool
    progress: list[tuple[str, int, int]]  # (métrica, atual, meta)

    @property
    def recruited(self) -> bool:
        return self.recruited_at is not None

    @property
    def challenges_ok(self) -> bool:
        return all(current >= goal for _, current, goal in self.progress)

    @property
    def available(self) -> bool:
        return not self.recruited and self.rank_ok and self.challenges_ok

    @property
    def rarity_label(self) -> str:
        return items.RARITIES[self.shadow.rarity][0]

    @property
    def rarity_color(self) -> str:
        return items.RARITIES[self.shadow.rarity][1]


def shop() -> list[ShadowState]:
    metrics = character.metrics()
    level = hunter.get_status().progress.level
    recruited = {row.shadow_key: row.recruited_at for row in db.session.scalars(select(PlayerShadow))}
    return [ShadowState(
        shadow=shadow,
        recruited_at=recruited.get(shadow.key),
        rank_ok=level >= character.rank_level(shadow.min_rank),
        progress=[(metric, metrics.get(metric, 0), goal) for metric, goal in shadow.challenges],
    ) for shadow in catalog.SHADOWS.values()]


def recruit(shadow_key: str) -> catalog.Shadow:
    """ARISE: recruta a sombra se rank e desafios estiverem cumpridos (conferido aqui, no servidor)."""
    state = next((s for s in shop() if s.shadow.key == shadow_key), None)
    if state is None:
        raise NotFoundError("Sombra desconhecida.")
    if state.recruited:
        raise DomainError(f"{state.shadow.name} já está no seu exército.")
    if not state.rank_ok:
        raise DomainError(f"{state.shadow.name} só responde a um Hunter Rank {state.shadow.min_rank} ou acima.")
    if not state.challenges_ok:
        raise DomainError("Os desafios desta sombra ainda não foram cumpridos.")
    proof = " · ".join(f"{metric} {current}/{goal}" for metric, current, goal in state.progress)
    db.session.add(PlayerShadow(shadow_key=shadow_key, proof=proof[:300]))
    try:
        db.session.flush()
    except IntegrityError:  # dois cliques ao mesmo tempo: a constraint única segura
        db.session.rollback()
        raise DomainError(f"{state.shadow.name} já está no seu exército.") from None
    events.publish("shadows.recruited", shadow=state.shadow)
    db.session.commit()
    return state.shadow


def recruited() -> list[catalog.Shadow]:
    keys = db.session.scalars(select(PlayerShadow.shadow_key).order_by(PlayerShadow.recruited_at))
    return [catalog.SHADOWS[k] for k in keys if k in catalog.SHADOWS]


def history() -> list[tuple[catalog.Shadow, datetime, str]]:
    rows = db.session.scalars(select(PlayerShadow).order_by(PlayerShadow.recruited_at.desc()))
    return [(catalog.SHADOWS[r.shadow_key], r.recruited_at, r.proof) for r in rows if r.shadow_key in catalog.SHADOWS]


def xp_bonus_lines(context: hunter.BonusContext) -> list[tuple[str, int]]:
    """Bônus das sombras na especialização da missão, com acúmulo controlado (a mais forte inteira,
    as outras pela metade). Os tetos gerais (por missão e por dia) são aplicados por hunter.quote_bonuses."""
    matching = sorted((s for s in recruited() if context.specialty in s.specialties), key=lambda s: s.xp_bonus, reverse=True)
    lines = []
    for index, shadow in enumerate(matching):
        amount = shadow.xp_bonus if index == 0 else int(shadow.xp_bonus * catalog.STACK_FACTOR)
        if amount:
            lines.append((f"Sombra {shadow.name} ({shadow.specialty_label})" + ("" if index == 0 else " ×0,5"), amount))
    return lines


def stat_bonus_lines() -> list[tuple[str, dict[str, int]]]:
    return [(f"{s.icon} Sombra {s.name}", s.stats) for s in recruited()]
