"""Fila do Sistema para agendamento inteligente no Buffer.

Permite gerenciar uma fila local de postagens no Shadow System sem estourar o limite
de 10 posts por canal do plano gratuito do Buffer.

Regras de envio (definidas pelo usuário):
- Obrigatório: cada rede tem sempre pelo menos 10 posts agendados no Buffer (limite do plano
  gratuito), 1 por dia. Assim que abre vaga, a fila repõe.
- Datas sempre projetadas para a frente: se o último post agendado no canal for no dia 20, os
  próximos saem nos dias 21, 22, 23... Sem nada agendado, começa amanhã.
- Bônus do teste grátis (BUFFER_BOOST_UNTIL): até 5 posts a mais por rede em horários de pico, só
  com datas até o fim do teste, para que tudo acima de 10 saia antes do plano gratuito voltar.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, time as dtime, timedelta

from app.core import time
from app.core.models import BufferQueuePost
from app.extensions import db

from . import client as client_mod, posting
from .client import BufferClient, BufferError, Post
from .posting import PostValidationError

log = logging.getLogger(__name__)

# Repõe assim que abrir qualquer vaga: a regra é ter sempre 10 agendados por rede.
DEFAULT_TRIGGER_THRESHOLD = 9
# O plano gratuito permite até 10 posts agendados por canal. Quando houver vagas,
# preenchemos todas elas em vez de exigir duas sincronizações manuais de +5.
DEFAULT_BATCH_SIZE = 10
MAX_SCHEDULED_PER_CHANNEL = 10
DEFAULT_POST_TIME = "18:30"


# Bônus do teste grátis (BUFFER_BOOST_UNTIL): horários de pico por rede, no horário de Brasília,
# para os posts extras. Cada dia recebe no máximo len(horários) posts contando os já agendados.
BOOST_SLOTS = {
    "linkedin": ("08:30", "12:30"),
    "instagram": ("12:00", "19:00"),
    "tiktok": ("12:30", "18:30", "21:30"),
}
BOOST_BONUS = 5  # posts a mais por rede, além dos 10 obrigatórios, enquanto o teste grátis vale
BOOST_MIN_LEAD = timedelta(minutes=30)
BOOST_MIN_GAP = timedelta(hours=1)


def boost_until() -> date | None:
    """Último dia do modo turbo, ou None se estiver desligado ou já tiver passado."""
    from flask import current_app

    raw = (current_app.config.get("BUFFER_BOOST_UNTIL") or "").strip()
    try:
        until = date.fromisoformat(raw) if raw else None
    except ValueError:
        log.warning("BUFFER_BOOST_UNTIL inválido: %r", raw)
        return None
    return until if until and time.today() <= until else None


def boost_slots(service: str, scheduled_dues: list[datetime], until: date,
                now: datetime | None = None) -> list[datetime]:
    """Horários livres de hoje até `until` para a rede, respeitando o que já está agendado.

    Cada dia recebe no máximo len(BOOST_SLOTS[rede]) posts contando os já agendados, e nenhum horário
    novo fica a menos de 1 hora de um post existente.
    """
    now = now or time.now()
    times = BOOST_SLOTS.get(service, (DEFAULT_POST_TIME,))
    out: list[datetime] = []
    day = now.date()
    while day <= until:
        taken = [d for d in scheduled_dues if d.date() == day]
        room = len(times) - len(taken)
        for t in times:
            if room <= 0:
                break
            h, m = [int(x) for x in t.split(":")]
            slot = datetime.combine(day, dtime(h, m))
            if slot <= now + BOOST_MIN_LEAD or any(abs(slot - d) < BOOST_MIN_GAP for d in taken):
                continue
            out.append(slot)
            room -= 1
        day += timedelta(days=1)
    return out


def is_limit_error(message: str) -> bool:
    """O Buffer recusou por falta de vaga (limite de 10 agendados), não por problema no post."""
    msg = (message or "").lower()
    return "scheduled posts limit reached" in msg or "limit of 10" in msg


def enqueue_post(
    *,
    channel_id: str,
    channel_name: str,
    service: str,
    text: str,
    image_urls: list[str],
    target_date: date | None = None,
    target_time: str | None = DEFAULT_POST_TIME,
) -> BufferQueuePost:
    """Insere um novo post na fila do sistema local."""
    cleaned_time = (target_time or DEFAULT_POST_TIME).strip()
    # Valida formato de hora HH:MM
    try:
        parts = [int(p) for p in cleaned_time.split(":")]
        if len(parts) != 2 or not (0 <= parts[0] <= 23 and 0 <= parts[1] <= 59):
            cleaned_time = DEFAULT_POST_TIME
    except Exception:
        cleaned_time = DEFAULT_POST_TIME

    queue_post = BufferQueuePost(
        channel_id=channel_id,
        channel_name=channel_name or service,
        service=service,
        text=text.strip(),
        image_urls=json.dumps(image_urls or []),
        target_date=target_date,
        target_time=cleaned_time,
        status="pending",
    )
    db.session.add(queue_post)
    db.session.commit()
    log.info("Post enfileirado no sistema local: id=%s canal=%s (%s)", queue_post.id, queue_post.channel_name, service)
    return queue_post


def list_queue_posts(status: str | None = None, channel_id: str | None = None) -> list[BufferQueuePost]:
    """Lista as publicações da fila local, ordenadas cronologicamente."""
    stmt = db.select(BufferQueuePost)
    if status:
        stmt = stmt.where(BufferQueuePost.status == status)
    if channel_id:
        stmt = stmt.where(BufferQueuePost.channel_id == channel_id)
    stmt = stmt.order_by(
        BufferQueuePost.status == "pending",  # pendentes primeiro
        BufferQueuePost.target_date.asc().nulls_last(),
        BufferQueuePost.target_time.asc().nulls_last(),
        BufferQueuePost.id.asc(),
    )
    return list(db.session.scalars(stmt).all())


def get_queue_post(post_id: int) -> BufferQueuePost | None:
    return db.session.get(BufferQueuePost, post_id)


def delete_queue_post(post_id: int) -> bool:
    post = get_queue_post(post_id)
    if not post:
        return False
    db.session.delete(post)
    db.session.commit()
    return True


def update_queue_post(
    post_id: int,
    *,
    text: str | None = None,
    target_date: date | None = None,
    target_time: str | None = None,
    status: str | None = None,
    clear_error: bool = False,
) -> BufferQueuePost:
    post = get_queue_post(post_id)
    if not post:
        raise PostValidationError(f"Item #{post_id} da fila não encontrado.")
    if text is not None:
        post.text = text.strip()
    if target_date is not None:
        post.target_date = target_date
    if target_time is not None:
        post.target_time = target_time.strip()
    if status is not None:
        post.status = status
    if clear_error:
        post.error_message = None
        if post.status == "error":
            post.status = "pending"
    db.session.commit()
    return post


def calculate_forward_dates(
    last_due_at: datetime | None,
    count: int,
    default_time: str = DEFAULT_POST_TIME,
    start_date: date | None = None,
) -> list[datetime]:
    """Calcula datas futuras consecutivas para um lote de posts.

    Regra:
    - Se existe um último post agendado no Buffer (last_due_at), o primeiro post do lote
      é agendado no dia SEGUINTE ao último post agendado.
    - Se não existe post agendado no Buffer ou se o último post já ficou no passado,
      começa em max(hoje + 1 dia, start_date ou hoje + 1 dia).
    - Cada post subsequente ganha +1 dia, mantendo o espaçamento sequencial.
    """
    if count <= 0:
        return []

    today = time.today()
    try:
        t_hour, t_minute = [int(p) for p in default_time.split(":")[:2]]
    except Exception:
        t_hour, t_minute = 18, 30

    if last_due_at:
        last_date = last_due_at.date()
        base_date = max(last_date, today)
        cursor_date = base_date + timedelta(days=1)
    else:
        if start_date and start_date > today:
            cursor_date = start_date
        else:
            cursor_date = today + timedelta(days=1)

    results: list[datetime] = []
    for i in range(count):
        post_date = cursor_date + timedelta(days=i)
        results.append(datetime.combine(post_date, dtime(t_hour, t_minute)))
    return results


def dispatch_next_batch(
    channel_id: str,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    trigger_threshold: int = DEFAULT_TRIGGER_THRESHOLD,
    client: BufferClient | None = None,
    organization_id: str | None = None,
    scheduled_posts: list[Post] | None = None,
) -> list[BufferQueuePost]:
    """Verifica e despacha até `batch_size` posts para o canal se o total de agendados <= `trigger_threshold`.

    Retorna a lista dos posts que foram despachados com sucesso.
    """
    from . import get_client, organization_id as get_org_id

    buffer_client = client or get_client()
    org_id = organization_id or get_org_id(buffer_client)

    # 1. Busca posts agendados no Buffer
    all_scheduled = scheduled_posts if scheduled_posts is not None else buffer_client.posts(org_id, statuses=["scheduled"], first=100)
    channel_scheduled = [p for p in all_scheduled if p.channel_id == channel_id]

    # 2. Obrigatório: sempre pelo menos 10 agendados por rede, 1 por dia, a partir do último agendado.
    dispatched: list[BufferQueuePost] = []
    base_room = max(0, MAX_SCHEDULED_PER_CHANNEL - len(channel_scheduled))
    if base_room and len(channel_scheduled) <= trigger_threshold:
        dispatched = _dispatch_daily(channel_id, channel_scheduled, min(batch_size, base_room), buffer_client)

    # 3. Bônus do teste grátis: até BOOST_BONUS posts a mais em horários de pico, só até a data final.
    boost = boost_until()
    if boost:
        bonus_room = MAX_SCHEDULED_PER_CHANNEL + BOOST_BONUS - len(channel_scheduled) - len(dispatched)
        if bonus_room > 0:
            dues = [p.due_at for p in channel_scheduled if p.due_at] + [_queue_due(p) for p in dispatched]
            dispatched += _dispatch_boost(channel_id, dues, boost, bonus_room, buffer_client)
    return dispatched


def _queue_due(post_item: BufferQueuePost) -> datetime:
    h, m = [int(x) for x in (post_item.target_time or DEFAULT_POST_TIME).split(":")[:2]]
    return datetime.combine(post_item.target_date, dtime(h, m))


def _dispatch_daily(channel_id: str, channel_scheduled: list[Post], count: int,
                    buffer_client: BufferClient) -> list[BufferQueuePost]:
    """Ritmo normal: 1 post por dia, a partir do dia seguinte ao último agendado no canal."""
    pending_posts = _pending_for(channel_id, count)
    if not pending_posts:
        return []

    scheduled_due_dates = [p.due_at for p in channel_scheduled if p.due_at]
    latest_due = max(scheduled_due_dates) if scheduled_due_dates else None
    forward_datetimes = calculate_forward_dates(
        last_due_at=latest_due,
        count=len(pending_posts),
        default_time=pending_posts[0].target_time or DEFAULT_POST_TIME,
        start_date=pending_posts[0].target_date,
    )

    def when(post_item: BufferQueuePost, index: int) -> datetime:
        target_dt = forward_datetimes[index]
        # Ajusta horário se o post possuir target_time específico diferente
        if post_item.target_time:
            try:
                h, m = [int(x) for x in post_item.target_time.split(":")[:2]]
                target_dt = target_dt.replace(hour=h, minute=m)
            except Exception:
                pass
        return target_dt

    return _send_items(pending_posts, when, buffer_client)


def _pending_for(channel_id: str, limit: int) -> list[BufferQueuePost]:
    stmt = (
        db.select(BufferQueuePost)
        .where(BufferQueuePost.channel_id == channel_id, BufferQueuePost.status == "pending")
        .order_by(
            BufferQueuePost.target_date.asc().nulls_last(),
            BufferQueuePost.target_time.asc().nulls_last(),
            BufferQueuePost.id.asc(),
        )
        .limit(limit)
    )
    return list(db.session.scalars(stmt).all())


def _dispatch_boost(channel_id: str, dues: list[datetime], until: date, room: int,
                    buffer_client: BufferClient) -> list[BufferQueuePost]:
    """Bônus: preenche horários de pico livres até `until`, no máximo `room` posts."""
    pending_posts = _pending_for(channel_id, room)
    if not pending_posts:
        return []
    slots = boost_slots(pending_posts[0].service, dues, until)[:len(pending_posts)]
    if not slots:
        return []
    return _send_items(pending_posts[:len(slots)], lambda _item, index: slots[index], buffer_client)


def _send_items(pending_posts: list[BufferQueuePost], when, buffer_client: BufferClient) -> list[BufferQueuePost]:
    """Envia os posts em ordem. `when(post, n)` dá o horário do n-ésimo post que entrar no Buffer."""
    dispatched: list[BufferQueuePost] = []
    # O horário só avança quando um post entra: um post com erro não deixa buraco no calendário.
    for post_item in pending_posts:
        target_dt = when(post_item, len(dispatched))

        try:
            due_utc = posting.due_at_utc(target_dt)
            post_input = posting.build_post_input(
                channel_id=post_item.channel_id,
                service=post_item.service,
                text=post_item.text,
                image_urls=post_item.images,
                mode="customScheduled",
                due_at=due_utc,
            )
            created = buffer_client.create_post(post_input)
            post_item.status = "dispatched"
            post_item.buffer_post_id = created.get("id")
            post_item.dispatched_at = time.now()
            post_item.target_date = target_dt.date()
            post_item.target_time = target_dt.strftime("%H:%M")
            post_item.error_message = None
            db.session.commit()
            dispatched.append(post_item)
            log.info(
                "Post #%d despachado para Buffer (Canal %s, data=%s %s)",
                post_item.id, post_item.channel_name, post_item.target_date, post_item.target_time,
            )
        except BufferError as exc:
            if is_limit_error(str(exc)):
                # Sem vaga no canal: o post continua pendente e o lote para aqui.
                log.info("Canal %s sem vagas no Buffer; post #%d segue na fila.", post_item.channel_name, post_item.id)
                break
            # Erro do próprio post: marca e segue para o próximo. Antes o lote parava aqui e o post
            # com erro, sempre o primeiro da fila, travava todos os outros posts daquela rede.
            post_item.status = "error"
            post_item.error_message = str(exc)
            db.session.commit()
            log.warning("Falha ao despachar post #%d para o Buffer: %s", post_item.id, exc)
        except Exception as exc:
            post_item.status = "error"
            post_item.error_message = str(exc)
            db.session.commit()
            log.exception("Erro inesperado ao despachar post #%d: %s", post_item.id, exc)

    return dispatched


def sync_queue(
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    trigger_threshold: int = DEFAULT_TRIGGER_THRESHOLD,
    client: BufferClient | None = None,
    channels_list: list | None = None,
    scheduled_posts: list[Post] | None = None,
) -> dict[str, int]:
    """Varre todos os canais da conta e despacha lotes para os canais elegíveis (<= 5 posts agendados).

    Retorna um dicionário {nome_do_canal: quantidade_despachada}.
    """
    from . import get_client, is_configured, organization_id as get_org_id

    if not is_configured():
        return {}

    buffer_client = client or get_client()
    try:
        org_id = get_org_id(buffer_client)
        raw_chans = channels_list if channels_list is not None else buffer_client.channels(org_id)
        chans = [ch for ch in raw_chans if ch.usable]
    except Exception as exc:
        log.warning("sync_queue: não foi possível listar canais do Buffer: %s", exc)
        return {}

    eligible_chans = []
    for ch in chans:
        pending_count = db.session.scalar(
            db.select(db.func.count(BufferQueuePost.id))
            .where(BufferQueuePost.channel_id == ch.id, BufferQueuePost.status == "pending")
        )
        if pending_count:
            eligible_chans.append(ch)

    if not eligible_chans:
        return {}

    if scheduled_posts is None:
        try:
            scheduled_posts = buffer_client.posts(org_id, statuses=["scheduled"], first=100)
        except Exception as exc:
            log.warning("sync_queue: não foi possível listar posts agendados do Buffer: %s", exc)
            return {}

    results: dict[str, int] = {}
    for ch in eligible_chans:
        dispatched = dispatch_next_batch(
            ch.id,
            batch_size=batch_size,
            trigger_threshold=trigger_threshold,
            client=buffer_client,
            organization_id=org_id,
            scheduled_posts=scheduled_posts,
        )
        if dispatched:
            results[ch.name] = len(dispatched)

    return results


def dispatch_single_post(
    post_id: int,
    *,
    mode: str = "customScheduled",
    due_local: datetime | None = None,
    client: BufferClient | None = None,
) -> BufferQueuePost:
    """Despacha manualmente um post específico da fila para o Buffer.

    Se mode == 'shareNow', publica imediatamente.
    Se mode == 'customScheduled', agenda para a data/hora especificada ou calcula a vaga futura.
    """
    from . import get_client, organization_id as get_org_id

    post_item = get_queue_post(post_id)
    if not post_item:
        raise PostValidationError(f"Item #{post_id} da fila não encontrado.")

    buffer_client = client or get_client()
    org_id = get_org_id(buffer_client)

    if mode == "shareNow":
        due_utc = None
    elif due_local:
        due_utc = posting.due_at_utc(due_local)
    else:
        # Determina o horário alvo
        today = time.today()
        target_d = post_item.target_date or (today + timedelta(days=1))
        if target_d <= today:
            # Busca último post agendado no Buffer para projetar para frente
            all_scheduled = buffer_client.posts(org_id, statuses=["scheduled"], first=100)
            channel_scheduled = [p for p in all_scheduled if p.channel_id == post_item.channel_id and p.due_at]
            latest_due = max([p.due_at for p in channel_scheduled], default=None)
            dates = calculate_forward_dates(latest_due, 1, default_time=post_item.target_time or DEFAULT_POST_TIME)
            target_dt = dates[0]
        else:
            try:
                h, m = [int(x) for x in (post_item.target_time or DEFAULT_POST_TIME).split(":")[:2]]
            except Exception:
                h, m = 18, 30
            target_dt = datetime.combine(target_d, dtime(h, m))
        due_utc = posting.due_at_utc(target_dt)

    post_input = posting.build_post_input(
        channel_id=post_item.channel_id,
        service=post_item.service,
        text=post_item.text,
        image_urls=post_item.images,
        mode=mode,
        due_at=due_utc,
    )
    created = buffer_client.create_post(post_input)
    post_item.status = "dispatched"
    post_item.buffer_post_id = created.get("id")
    post_item.dispatched_at = time.now()
    if mode == "shareNow":
        post_item.target_date = time.today()
        post_item.target_time = time.now().strftime("%H:%M")
    elif 'target_dt' in locals():
        post_item.target_date = target_dt.date()
        post_item.target_time = target_dt.strftime("%H:%M")
    post_item.error_message = None
    db.session.commit()
    return post_item
