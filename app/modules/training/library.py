"""Rotinas prontas, escritas no mesmo formato de texto que a pessoa cola (ver parser.py).

São modelos gerais para começar e ajustar: cargas ficam em branco para você preencher depois do
primeiro treino. Não substituem a orientação de um profissional de educação física.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    key: str
    name: str
    summary: str
    level: str
    text: str


TEMPLATES: list[Template] = [
    Template(
        key="abc", name="ABC (3x por semana)", level="Intermediário",
        summary="Peito/ombro/tríceps, costas/bíceps e pernas em dias separados.",
        text="""Plano: ABC
Segunda: Treino A - Peito, ombro e tríceps
- Supino reto 4x8-12 descanso 90s
- Supino inclinado com halteres 3x10-12 descanso 90s
- Desenvolvimento com halteres 3x10-12 descanso 90s
- Elevação lateral 3x12-15 descanso 60s
- Tríceps na polia 3x12 descanso 60s
Quarta: Treino B - Costas e bíceps
- Puxada frontal 4x8-12 descanso 90s
- Remada curvada 4x8-12 descanso 90s
- Remada baixa 3x10-12 descanso 90s
- Rosca direta 3x10-12 descanso 60s
- Rosca martelo 3x12 descanso 60s
Sexta: Treino C - Pernas e core
- Agachamento livre 4x8-10 descanso 120s
- Leg press 3x10-12 descanso 90s
- Cadeira extensora 3x12-15 descanso 60s
- Mesa flexora 3x12-15 descanso 60s
- Panturrilha em pé 4x15 descanso 45s
- Prancha 3x45s descanso 45s
"""),
    Template(
        key="fullbody", name="Full body (3x por semana)", level="Iniciante",
        summary="O corpo todo em cada treino. Bom para começar ou voltar a treinar.",
        text="""Plano: Full body
Segunda: Full body A
- Agachamento goblet 3x10-12 descanso 90s
- Supino com halteres 3x10-12 descanso 90s
- Remada com halter 3x10-12 descanso 90s
- Desenvolvimento com halteres 2x12 descanso 60s
- Prancha 3x30s descanso 45s
Quarta: Full body B
- Levantamento terra romeno 3x10 descanso 90s
- Flexão de braço 3x8-12 descanso 60s
- Puxada frontal 3x10-12 descanso 90s
- Afundo 2x10 (cada perna) descanso 60s
- Abdominal infra 3x12 descanso 45s
Sexta: Full body C
- Leg press 3x12 descanso 90s
- Supino inclinado com halteres 3x10 descanso 90s
- Remada baixa 3x12 descanso 90s
- Elevação lateral 2x15 descanso 45s
- Ponte de glúteo 3x12 descanso 45s
"""),
    Template(
        key="upperlower", name="Superior / Inferior (4x por semana)", level="Intermediário",
        summary="Dois treinos de parte superior e dois de pernas.",
        text="""Plano: Superior / Inferior
Segunda: Superior 1
- Supino reto 4x6-8 descanso 120s
- Remada curvada 4x6-8 descanso 120s
- Desenvolvimento militar 3x8-10 descanso 90s
- Puxada frontal 3x10 descanso 90s
- Tríceps testa 2x12 descanso 60s
- Rosca direta 2x12 descanso 60s
Terça: Inferior 1
- Agachamento livre 4x6-8 descanso 150s
- Stiff 3x8-10 descanso 120s
- Cadeira extensora 3x12 descanso 60s
- Panturrilha sentado 4x15 descanso 45s
Quinta: Superior 2
- Supino inclinado com halteres 4x8-10 descanso 90s
- Barra fixa 4xmax descanso 120s
- Elevação lateral 3x12-15 descanso 60s
- Remada baixa 3x10-12 descanso 90s
- Tríceps na polia 2x12 descanso 60s
- Rosca martelo 2x12 descanso 60s
Sexta: Inferior 2
- Levantamento terra 3x5 descanso 180s
- Leg press 3x10-12 descanso 90s
- Mesa flexora 3x12 descanso 60s
- Afundo 2x10 (cada perna) descanso 60s
- Prancha 3x45s descanso 45s
"""),
    Template(
        key="ppl", name="Push / Pull / Legs (3x por semana)", level="Intermediário",
        summary="Empurrar, puxar e pernas. Dá para repetir o ciclo e fazer 6x.",
        text="""Plano: Push / Pull / Legs
Segunda: Push - Peito, ombro e tríceps
- Supino reto 4x6-10 descanso 120s
- Desenvolvimento com halteres 3x8-12 descanso 90s
- Crucifixo 3x12 descanso 60s
- Elevação lateral 3x15 descanso 45s
- Tríceps corda 3x12 descanso 60s
Quarta: Pull - Costas e bíceps
- Barra fixa 4xmax descanso 120s
- Remada curvada 4x8-10 descanso 90s
- Face pull 3x15 descanso 60s
- Rosca direta 3x10 descanso 60s
- Rosca concentrada 2x12 descanso 45s
Sexta: Legs - Pernas
- Agachamento livre 4x6-10 descanso 150s
- Stiff 3x8-10 descanso 120s
- Leg press 3x12 descanso 90s
- Cadeira flexora 3x12 descanso 60s
- Panturrilha em pé 4x15 descanso 45s
"""),
    Template(
        key="casa", name="Em casa, sem equipamento (3x)", level="Iniciante",
        summary="Peso do corpo, em circuito. Só precisa de espaço no chão.",
        text="""Plano: Treino em casa
Segunda: Circuito A
- Agachamento livre 3x15 descanso 45s
- Flexão de braço 3x8-12 descanso 45s
- Afundo 3x10 (cada perna) descanso 45s
- Prancha 3x30s descanso 30s
- Polichinelo 3x40s descanso 30s
Quarta: Circuito B
- Ponte de glúteo 3x15 descanso 45s
- Flexão diamante 3x6-10 descanso 45s
- Agachamento sumô 3x15 descanso 45s
- Abdominal bicicleta 3x20 descanso 30s
- Burpee 3x10 descanso 45s
Sexta: Circuito C
- Agachamento búlgaro 3x10 (cada perna) descanso 45s
- Mergulho no banco 3x10-12 descanso 45s
- Superman 3x12 descanso 30s
- Prancha lateral 3x30s (cada lado) descanso 30s
- Mountain climber 3x30s descanso 30s
"""),
    Template(
        key="corrida", name="Corrida para iniciantes (3x)", level="Iniciante",
        summary="Alterna caminhada e corrida e aumenta o tempo correndo aos poucos.",
        text="""Plano: Corrida iniciante
Terça: Intervalado leve
- Caminhada de aquecimento 5min
- Corrida leve 6x1min (intercalar com 2min de caminhada)
- Caminhada de volta à calma 5min
Quinta: Intervalado médio
- Caminhada de aquecimento 5min
- Corrida leve 5x2min (intercalar com 2min de caminhada)
- Alongamento 5min
Sábado: Rodagem
- Caminhada de aquecimento 5min
- Corrida contínua leve 15min
- Alongamento 5min
"""),
]


def get_template(key: str) -> Template | None:
    return next((t for t in TEMPLATES if t.key == key), None)
