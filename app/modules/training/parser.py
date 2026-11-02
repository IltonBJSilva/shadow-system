"""Lê uma rotina de treino escrita em texto simples (funções puras, sem banco).

Formato (o mesmo que a tela mostra como exemplo e que as rotinas prontas usam):

    Plano: Hipertrofia ABC                  <- opcional: nome do plano
    Segunda: Treino A - Peito e tríceps     <- dia da semana + nome do treino
    - Supino reto 4x8-12 40kg descanso 90s  <- exercício: séries x repetições, carga e descanso opcionais
    - Tríceps na polia 3x12 (pegada neutra) <- texto entre parênteses vira observação
    Quarta: Treino B - Costas
    - Corrida leve 20min                    <- sem "x": uma série com a duração/distância

Também aceita "Treino A: ..." ou "Dia 1: ..." sem dia da semana; nesse caso os dias são distribuídos
sozinhos na semana (ver `assign_weekdays`). Linhas que não são dia nem exercício são ignoradas e
listadas em `warnings`, para a pessoa conferir.
"""
import re
import unicodedata
from dataclasses import dataclass, field

WEEKDAY_LABELS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

_WEEKDAYS = {
    "segunda": 0, "seg": 0, "segunda-feira": 0, "monday": 0, "mon": 0,
    "terca": 1, "ter": 1, "terca-feira": 1, "tuesday": 1, "tue": 1,
    "quarta": 2, "qua": 2, "quarta-feira": 2, "wednesday": 2, "wed": 2,
    "quinta": 3, "qui": 3, "quinta-feira": 3, "thursday": 3, "thu": 3,
    "sexta": 4, "sex": 4, "sexta-feira": 4, "friday": 4, "fri": 4,
    "sabado": 5, "sab": 5, "saturday": 5, "sat": 5,
    "domingo": 6, "dom": 6, "sunday": 6, "sun": 6,
}

# Distribuição padrão quando o texto não diz os dias (n treinos -> dias da semana).
_SPREAD = {1: [0], 2: [0, 3], 3: [0, 2, 4], 4: [0, 1, 3, 4], 5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4, 5],
           7: [0, 1, 2, 3, 4, 5, 6]}

_BULLET = re.compile(r"^\s*(?:[-*•·]|\d+[.)])\s*")
_HEADER = re.compile(r"^(?P<day>[A-Za-zÀ-ÿ-]+)\s*(?:[:\-–]\s*(?P<name>.*))?$")
_GENERIC_HEADER = re.compile(r"^(?P<name>(?:treino|dia|day|workout)\s+[\wÀ-ÿ]+.*?)\s*:?\s*$", re.IGNORECASE)
_PLAN = re.compile(r"^\s*(?:plano|rotina|plan)\s*:\s*(?P<name>.+)$", re.IGNORECASE)
_SETS = re.compile(r"(?P<sets>\d{1,2})\s*[x×X]\s*(?P<reps>\d+(?:\s*[-–/a]\s*\d+)?\s*(?:s|seg|min|km|m|reps?)?\b|max|falha)",
                   re.IGNORECASE)
_LOAD = re.compile(r"(?:@\s*)?(?P<load>\d+(?:[.,]\d+)?)\s*kg\b", re.IGNORECASE)
_REST = re.compile(r"(?:descanso|desc\.?|rest|intervalo)\s*:?\s*(?P<rest>\d+)\s*(?P<unit>s|seg|min|m)?\b", re.IGNORECASE)
_DURATION = re.compile(r"(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>min|km|s|seg|m)\b", re.IGNORECASE)
_NOTE = re.compile(r"\((?P<note>[^)]*)\)")

MAX_DAYS = 7
MAX_EXERCISES_PER_DAY = 30


@dataclass
class ParsedExercise:
    name: str
    sets: int = 1
    reps: str = ""
    load_kg: float | None = None
    rest_seconds: int | None = None
    notes: str = ""

    def describe(self) -> str:
        """Ex.: "Supino reto: 4x8-12 · 40 kg · descanso 90s"."""
        parts = [f"{self.sets}x{self.reps}" if self.reps and self.sets > 1 else (self.reps or f"{self.sets} série(s)")]
        if self.load_kg is not None:
            parts.append(f"{format_kg(self.load_kg)} kg")
        if self.rest_seconds:
            parts.append(f"descanso {self.rest_seconds}s")
        text = f"{self.name}: " + " · ".join(parts)
        return f"{text} ({self.notes})" if self.notes else text


@dataclass
class ParsedDay:
    name: str
    weekday: int | None = None
    exercises: list[ParsedExercise] = field(default_factory=list)


@dataclass
class ParsedPlan:
    name: str = ""
    days: list[ParsedDay] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def exercise_count(self) -> int:
        return sum(len(day.exercises) for day in self.days)


def format_kg(value: float) -> str:
    return f"{value:g}".replace(".", ",")


def _fold(text: str) -> str:
    """Minúsculas e sem acento: "Terça" -> "terca"."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower().strip()


def _weekday(word: str) -> int | None:
    return _WEEKDAYS.get(_fold(word).rstrip(".:"))


def parse(text: str) -> ParsedPlan:
    plan = ParsedPlan()
    current: ParsedDay | None = None
    for number, raw in enumerate((text or "").splitlines(), start=1):
        line = raw.strip().strip("#").strip()
        if not line:
            continue
        plan_match = _PLAN.match(line)
        if plan_match and not plan.days:
            plan.name = plan_match.group("name").strip()[:120]
            continue
        is_bullet = bool(_BULLET.match(raw))
        header = None if is_bullet else _header(line)
        if header:
            if len(plan.days) >= MAX_DAYS:
                plan.warnings.append(f"Linha {number}: mais de {MAX_DAYS} dias; o resto foi ignorado.")
                break
            current = header
            plan.days.append(current)
            continue
        exercise = _exercise(_BULLET.sub("", raw).strip())
        if exercise is None:
            plan.warnings.append(f"Linha {number} ignorada: \"{line[:60]}\"")
            continue
        if current is None:
            current = ParsedDay(name="Treino")
            plan.days.append(current)
        if len(current.exercises) >= MAX_EXERCISES_PER_DAY:
            plan.warnings.append(f"Linha {number}: limite de {MAX_EXERCISES_PER_DAY} exercícios no dia.")
            continue
        current.exercises.append(exercise)
    plan.days = [day for day in plan.days if day.exercises]
    assign_weekdays(plan)
    return plan


def assign_weekdays(plan: ParsedPlan) -> None:
    """Dá um dia da semana a quem não tem, sem repetir os já usados."""
    missing = [day for day in plan.days if day.weekday is None]
    if not missing:
        return
    used = {day.weekday for day in plan.days if day.weekday is not None}
    preferred = [d for d in _SPREAD.get(len(plan.days), list(range(7))) if d not in used]
    free = preferred + [d for d in range(7) if d not in used and d not in preferred]
    for day, weekday in zip(missing, free):
        day.weekday = weekday


def _header(line: str) -> ParsedDay | None:
    match = _HEADER.match(line)
    if match:
        weekday = _weekday(match.group("day"))
        if weekday is not None:
            name = (match.group("name") or "").strip() or f"Treino de {WEEKDAY_LABELS[weekday].lower()}"
            return ParsedDay(name=name[:120], weekday=weekday)
    generic = _GENERIC_HEADER.match(line)
    if generic and not _SETS.search(line):
        return ParsedDay(name=generic.group("name").strip().rstrip(":")[:120])
    return None


def _exercise(line: str) -> ParsedExercise | None:
    if not line or len(line) > 200:
        return None
    notes = "; ".join(m.group("note").strip() for m in _NOTE.finditer(line) if m.group("note").strip())
    rest_text = _NOTE.sub(" ", line)

    rest_seconds = None
    rest = _REST.search(rest_text)
    if rest:
        rest_seconds = int(rest.group("rest")) * (60 if (rest.group("unit") or "s").lower() in ("min", "m") else 1)
        rest_text = rest_text[:rest.start()] + " " + rest_text[rest.end():]

    load_kg = None
    load = _LOAD.search(rest_text)
    if load:
        load_kg = float(load.group("load").replace(",", "."))
        rest_text = rest_text[:load.start()] + " " + rest_text[load.end():]

    sets, reps = 1, ""
    sets_match = _SETS.search(rest_text)
    if sets_match:
        sets, reps = int(sets_match.group("sets")), re.sub(r"\s+", "", sets_match.group("reps"))
        name = rest_text[:sets_match.start()]
    else:
        duration = _DURATION.search(rest_text)
        if not duration:
            return None  # sem séries nem duração: não dá para saber que é exercício
        reps = re.sub(r"\s+", "", duration.group(0))
        name = rest_text[:duration.start()] + rest_text[duration.end():]
    name = re.sub(r"\s+", " ", name).strip(" -–:,;@")
    if not name or not any(ch.isalpha() for ch in name):
        return None
    return ParsedExercise(name=name[:120], sets=max(1, min(sets, 20)), reps=reps[:20], load_kg=load_kg,
                          rest_seconds=rest_seconds, notes=notes[:200])


def to_text(plan_name: str, days: list[ParsedDay]) -> str:
    """O caminho de volta: plano -> texto no mesmo formato (para editar)."""
    lines = [f"Plano: {plan_name}"] if plan_name else []
    for day in days:
        label = WEEKDAY_LABELS[day.weekday] if day.weekday is not None else "Treino"
        lines.append(f"{label}: {day.name}")
        for ex in day.exercises:
            parts = [f"- {ex.name}", f"{ex.sets}x{ex.reps}" if ex.sets > 1 or not _DURATION.fullmatch(ex.reps or "")
                     else ex.reps]
            if ex.load_kg is not None:
                parts.append(f"{format_kg(ex.load_kg)}kg")
            if ex.rest_seconds:
                parts.append(f"descanso {ex.rest_seconds}s")
            line = " ".join(p for p in parts if p)
            lines.append(f"{line} ({ex.notes})" if ex.notes else line)
    return "\n".join(lines)
