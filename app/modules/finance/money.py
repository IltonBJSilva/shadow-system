"""Dinheiro em centavos: ler o que a pessoa digita ("1.234,56", "R$ 10", "9.9") e formatar em reais."""
import re

from app.core.errors import DomainError

MAX_CENTS = 100_000_000_00  # R$ 100 milhões: protege contra valores digitados errado


def parse(text: str | int | float | None, *, allow_zero: bool = False) -> int:
    if isinstance(text, int):
        cents = text
    else:
        raw = re.sub(r"[^\d,.\-]", "", str(text or "")).strip()
        if not raw:
            raise DomainError("Informe um valor.")
        if "," in raw:  # padrão brasileiro: ponto separa milhar, vírgula separa centavos
            raw = raw.replace(".", "").replace(",", ".")
        elif raw.count(".") > 1:
            raw = raw.replace(".", "")
        try:
            cents = round(float(raw) * 100)
        except ValueError as exc:
            raise DomainError("Valor inválido.") from exc
    if cents < 0 or (cents == 0 and not allow_zero):
        raise DomainError("O valor precisa ser maior que zero.")
    if cents > MAX_CENTS:
        raise DomainError("Valor alto demais.")
    return cents


def brl(cents: int | None) -> str:
    cents = int(cents or 0)
    sign = "-" if cents < 0 else ""
    reais, cent = divmod(abs(cents), 100)
    return f"{sign}R$ {reais:,}".replace(",", ".") + f",{cent:02d}"
