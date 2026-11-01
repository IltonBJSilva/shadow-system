# Guia de desenvolvimento

## Rodar

```powershell
.\run.ps1 --dev          # recarrega ao salvar, erros detalhados, http://localhost:5050
.\.venv\Scripts\python -m pytest
```

Comandos `flask` sempre com `--app wsgi` (ou ative o venv e defina `FLASK_APP=wsgi.py`, que já está
no `.env.example`).

## Adicionar um módulo

Exemplo: `fitness`.

1. Crie `app/modules/fitness/` com:

   ```python
   # __init__.py
   """Fitness: treinos, exercícios e evolução de cargas."""
   from flask import Blueprint

   bp = Blueprint("fitness", __name__, url_prefix="/fitness")

   from . import models, routes  # noqa: E402,F401
   ```

2. Registre em `app/modules/__init__.py` (lista `blueprints`).
3. Para aparecer no menu, adicione em `NAV_ITEMS` (`app/core/template_helpers.py`):
   `("Fitness", "fitness.index", "♜")`.
4. Templates em `app/templates/fitness/`.
5. Migration, testes (`tests/test_fitness.py`) e `docs/modules/fitness.md`.

## Criar um modelo

```python
# app/modules/fitness/models.py
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TimestampMixin
from app.extensions import db


class WorkoutSession(TimestampMixin, db.Model):
    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    split: Mapped[str] = mapped_column(String(20), nullable=False)  # "A", "B", "Full Body"...
```

Depois: `flask --app wsgi db migrate -m "add workout sessions"`, revise o arquivo e `db upgrade`.

## Criar um serviço

Regras de negócio ficam aqui. Valide, altere, faça um commit, retorne algo útil.

```python
# app/modules/fitness/services.py
from app.core.errors import DomainError
from app.extensions import db
from app.modules.hunter import services as hunter

from .models import WorkoutSession


def log_workout(day, split: str) -> hunter.AwardResult:
    if not split.strip():
        raise DomainError("Informe a divisão do treino.")
    db.session.add(WorkoutSession(day=day, split=split.strip()))
    strength = [a.id for a in hunter.list_attributes() if a.key == "strength"]
    result = hunter.award_xp(40, source="workout", description=f"Treino {split}",
                             attribute_ids=strength, attribute_points=3)
    db.session.commit()  # treino e XP salvos juntos
    return result
```

Regras:
- `DomainError` com mensagem para o usuário quando uma regra é violada (a rota não precisa tratar).
- Só importe o `services.py` de outro módulo.
- Funções para outros módulos retornam dataclasses quando o modelo não deve vazar.

## Criar uma rota

```python
# app/modules/fitness/routes.py
from flask import flash, redirect, render_template, url_for

from app.modules.hunter import services as hunter

from . import bp, services
from .forms import WorkoutForm


@bp.get("/")
def index():
    return render_template("fitness/index.html", form=WorkoutForm())


@bp.post("/")
def create():
    form = WorkoutForm()
    if form.validate_on_submit():
        result = services.log_workout(form.day.data, form.split.data)
        for message, category in hunter.award_messages(result):
            flash(message, category)
    return redirect(url_for("fitness.index"))
```

- Ações que alteram dados: sempre `POST`. Formulários levam `{{ form.csrf_token }}` (ou o macro
  `ui.post_button`, que já inclui o token).
- Para voltar para a página de origem, envie `next` e use `app.core.http.redirect_back`.

## Formulários

Flask-WTF em `forms.py`. Um método `to_input()` que converte para o tipo de entrada do serviço
(ex.: `QuestForm.to_input() -> QuestInput`) mantém a rota curta.

## Interface

- Layout: `templates/base.html`. Macros: `templates/partials/_macros.html` (`field`, `progress`,
  `post_button`, `empty`).
- Componentes CSS prontos: `.panel`, `.system-window` (cantos holográficos), `.list`/`.list-item`, `.tag`,
  `.btn` (`-primary`, `-success`, `-danger`, `-ghost`, `-sm`), `.kpis`, `.progress`, `.form-grid`.
- Cores no topo de `static/css/shadow.css` (`--purple`, `--blue`, ...). Mudar ali muda tudo.
- **Sem JavaScript inline** (a CSP bloqueia). Use atributos e trate em `static/js/shadow.js`:
  `data-toggle="id"` abre/fecha um painel, `data-autosubmit` envia o formulário ao mudar.
- **Sons**: mensagens com categoria `success`, `bonus`, `levelup`, `penalty`, `error` ou `info` tocam um som
  (`static/js/sounds.js`). Para tocar em outro momento: `ShadowSound.play("notify")`.
- Widget novo no dashboard: chave em `WIDGETS` e loader em `_LOADERS`
  (`app/modules/dashboard/services.py`) + `templates/dashboard/widgets/<chave>.html`.

## Adicionar uma integração

Ver [integrations.md](integrations.md#como-adicionar-uma-integração).

## Atualizar a documentação

Toda feature atualiza, no mesmo commit:
- `docs/modules/<modulo>.md` (regras e API pública);
- `README.md` (lista de funcionalidades, estrutura, configuração, se mudaram);
- `ROADMAP.md` (marcar o que foi concluído);
- `.env.example`, se surgiu variável nova.

## Commits

Conventional Commits em inglês, um por feature concluída:

```
feat: add workout logging
fix: prevent duplicate habit check-in
docs: document fitness module
test: cover grade calculation rules
refactor: extract recurrence rules
chore: bump dependencies
```

Antes de commitar: testes passando, `git diff` revisado, só os arquivos da feature no stage
(`git add <arquivos>`, não `git add .`), nenhum arquivo sensível.
