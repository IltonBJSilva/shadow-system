from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, SelectMultipleField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp

from app.modules.hunter import progression
from app.modules.hunter import services as hunter

from . import constants, services
from .services import QuestInput


def _int_or_none(value):
    return int(value) if value not in (None, "", "0", 0) else None


class QuestForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Descrição", validators=[Optional(), Length(max=2000)])
    quest_type = SelectField("Tipo", choices=list(constants.QUEST_TYPES.items()), default="custom")
    category_id = SelectField("Categoria", coerce=_int_or_none, validate_choice=False)
    priority = SelectField("Prioridade", choices=list(constants.PRIORITIES.items()), default="medium")
    difficulty = SelectField("Dificuldade", coerce=int, default=3,
                             choices=[(k, f"{v} ({progression.DIFFICULTY_XP[k]} XP)")
                                      for k, v in progression.DIFFICULTY_LABELS.items()])
    xp_reward = IntegerField("XP (vazio = padrão: dificuldade x prioridade)",
                             validators=[Optional(), NumberRange(min=0, max=100000)])
    due_date = DateField("Prazo", validators=[Optional()])
    recurrence = SelectField("Repetição", choices=list(constants.RECURRENCES.items()), default="none")
    completion_criteria = TextAreaField("Critérios de conclusão", validators=[Optional(), Length(max=1000)])
    reward = StringField("Recompensa pessoal (opcional)", validators=[Optional(), Length(max=200)])
    attribute_ids = SelectMultipleField("Atributos (vazio = os da categoria)", coerce=int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_id.choices = [(0, "Sem categoria")] + services.category_choices()
        self.attribute_ids.choices = hunter.attribute_choices()

    def to_input(self) -> QuestInput:
        return QuestInput(
            title=self.title.data,
            description=self.description.data or "",
            quest_type=self.quest_type.data,
            category_id=self.category_id.data,
            priority=self.priority.data,
            difficulty=self.difficulty.data,
            xp_reward=self.xp_reward.data,
            due_date=self.due_date.data,
            recurrence=self.recurrence.data,
            completion_criteria=self.completion_criteria.data or "",
            reward=self.reward.data or "",
            attribute_ids=list(self.attribute_ids.data or []),
        )


class CategoryForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=60)])
    color = StringField("Cor", default="#8b5cf6",
                        validators=[DataRequired(), Regexp(r"^#[0-9a-fA-F]{6}$", message="Use #RRGGBB.")])
    attribute_ids = SelectMultipleField("Atributos que esta categoria desenvolve", coerce=int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attribute_ids.choices = hunter.attribute_choices()
