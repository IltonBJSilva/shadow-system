"""WhatsApp: enviar para o SEU número o resumo do dia do Shadow System.

As mensagens só vão para o número cadastrado como seu (nunca para outros contatos) e só quando você
clica em enviar. Token, Phone number ID e seu número ficam em instance/credentials/whatsapp.json.
"""
from app.core import time
from app.modules.calendar import services as calendar
from app.modules.habits import services as habits
from app.modules.hunter import services as hunter
from app.modules.quests import services as quests

from .. import credentials
from ..registry import IntegrationStatus
from .client import WhatsAppClient, WhatsAppError, normalize_number

NAME = "whatsapp"

# Testes trocam por um httpx.MockTransport.
_transport = None


def settings() -> dict:
    return credentials.load(NAME)


def is_configured() -> bool:
    data = settings()
    return bool(data.get("token") and data.get("phone_number_id") and data.get("my_number"))


def get_client(token: str | None = None, phone_number_id: str | None = None) -> WhatsAppClient:
    data = settings()
    return WhatsAppClient(token or data.get("token", ""), phone_number_id or data.get("phone_number_id", ""),
                          transport=_transport)


def save(token: str, phone_number_id: str, my_number: str) -> str:
    """Confere token e número na API antes de salvar. Retorna o número da empresa (remetente)."""
    token, phone_number_id = token.strip(), phone_number_id.strip()
    if not token:  # trocar só os números mantendo o token atual
        token = settings().get("token", "")
    my_number = normalize_number(my_number)
    info = get_client(token, phone_number_id).phone_info()
    sender = info.get("display_phone_number") or phone_number_id
    credentials.save(NAME, {"token": token, "phone_number_id": phone_number_id, "my_number": my_number,
                            "sender": sender, "verified_name": info.get("verified_name", "")})
    return sender


def status() -> IntegrationStatus:
    base = dict(key="whatsapp", name="WhatsApp", description="Resumo do dia e lembretes no seu WhatsApp.",
                url="/integrations/whatsapp/")
    if not is_configured():
        return IntegrationStatus(**base, state="not_configured", detail="Cadastre o token quando gerar.")
    data = settings()
    return IntegrationStatus(**base, state="connected",
                             detail=f"De {data.get('sender')} para ••••{data['my_number'][-4:]}")


def daily_summary() -> str:
    """Texto do resumo do dia, só com dados registrados no Shadow System."""
    status_ = hunter.get_status()
    today = time.today()
    lines = [f"*[SYSTEM] Resumo de {today:%d/%m}*",
             f"{status_.name} · Nível {status_.progress.level} · Rank {status_.rank.code if status_.rank else '-'} · "
             f"{status_.progress.xp_into_level}/{status_.progress.xp_for_next} XP", ""]
    today_quests = quests.quests_for_today(today)
    lines.append(f"*Quests de hoje ({len(today_quests)})*")
    lines += [f"{'⚠️' if q.is_overdue else '⚔️'} {q.title} (+{q.xp_reward} XP)" for q in today_quests[:10]] or ["Nenhuma."]
    pending = [h for h in habits.list_habits() if not h.done_today]
    lines += ["", f"*Hábitos pendentes ({len(pending)})*"]
    lines += [f"✦ {h.name} · 🔥 {h.current_streak}" for h in pending[:10]] or ["Todos feitos hoje."]
    events = [e for e in calendar.upcoming_events(days=1, limit=20) if e.start_at.date() == today]
    if events:
        lines += ["", "*Agenda de hoje*"] + [f"▦ {e.start_at:%H:%M} {e.title}" for e in events[:10]]
    return "\n".join(lines)


def send_to_me(text: str) -> str:
    if not is_configured():
        raise WhatsAppError("WhatsApp não configurado.")
    return get_client().send_text(settings()["my_number"], text)


def send_test_template() -> str:
    if not is_configured():
        raise WhatsAppError("WhatsApp não configurado.")
    return get_client().send_template(settings()["my_number"])


__all__ = ["WhatsAppError", "daily_summary", "is_configured", "save", "send_test_template", "send_to_me", "status"]
