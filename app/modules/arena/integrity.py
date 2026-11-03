"""Indicador de integridade do ranking: sinais de atividade fora do normal, nunca uma acusação.

Função pura (sem banco), alimentada pelo ActivityReport dos últimos 7 dias. Cada sinal tira pontos de
100 e vem com uma explicação neutra. Um dia de 24 h, por exemplo, só pesa junto de outros sinais: pode
ser erro de registro ou um dia excepcional. O resultado aparece no ranking como "Íntegro", "Atenção"
ou "Em análise" e o próprio jogador vê os motivos.
"""
from dataclasses import dataclass, field

from app.modules.quests.services import ActivityReport

LEVELS = (
    (80, "ok", "Íntegro"),
    (50, "watch", "Atenção"),
    (0, "review", "Em análise"),
)


@dataclass
class Integrity:
    score: int = 100
    reasons: list[str] = field(default_factory=list)

    @property
    def level(self) -> str:
        return next(key for limit, key, _ in LEVELS if self.score >= limit)

    @property
    def label(self) -> str:
        return next(label for limit, _, label in LEVELS if self.score >= limit)

    def flag(self, points: int, reason: str) -> None:
        self.score = max(0, self.score - points)
        self.reasons.append(reason)


def evaluate(report: ActivityReport, xp_week: int) -> Integrity:
    result = Integrity()
    long_days = [m for m in report.minutes_by_day.values() if m >= 20 * 60]
    busy_days = [m for m in report.minutes_by_day.values() if 16 * 60 <= m < 20 * 60]
    if long_days:
        result.flag(15 + 5 * (len(long_days) - 1), f"{len(long_days)} dia(s) com 20 h ou mais de atividade registrada")
    if busy_days:
        result.flag(5 * len(busy_days), f"{len(busy_days)} dia(s) com 16 h ou mais de atividade")

    raw, merged = sum(report.raw_minutes_by_day.values()), report.minutes
    if raw - merged > 120 and raw > merged * 1.3:
        result.flag(10, f"{(raw - merged) // 60} h de missões registradas no mesmo horário (contadas uma vez)")

    most_short = max(report.short_by_day.values(), default=0)
    if most_short >= 30:
        result.flag(20, f"{most_short} missões de até 10 min num só dia")
    elif most_short >= 15:
        result.flag(8, f"{most_short} missões de até 10 min num só dia")

    most_repeat = max(report.max_repeat_by_day.values(), default=0)
    if most_repeat >= 6:
        result.flag(10, f"A mesma missão concluída {most_repeat} vezes num dia")

    if report.bursts >= 10:
        result.flag(20, f"{report.bursts} conclusões com menos de 15 s de intervalo (padrão de automação)")
    elif report.bursts >= 4:
        result.flag(8, f"{report.bursts} conclusões com menos de 15 s de intervalo")

    if report.edits_after_xp >= 5:
        result.flag(10, f"{report.edits_after_xp} edições em missões depois de receber XP")
    elif report.edits_after_xp:
        result.flag(3, f"{report.edits_after_xp} edição(ões) em missões já concluídas")

    hours = report.minutes / 60
    if xp_week > 300 and hours and xp_week / hours > 150:
        result.flag(10, f"{round(xp_week / hours)} XP por hora de atividade (acima do esperado)")
    elif xp_week > 300 and not hours:
        result.flag(10, "XP na semana sem tempo de atividade registrado")
    return result
