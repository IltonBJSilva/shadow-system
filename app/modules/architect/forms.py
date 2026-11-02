from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from . import ai


class GoalForm(FlaskForm):
    title = StringField("Meta", validators=[DataRequired(), Length(max=160)])
    area = SelectField("Área (categoria)", validators=[Optional()])
    why = TextAreaField("Por que importa para você (opcional)", validators=[Optional(), Length(max=1000)])
    deadline = DateField("Prazo (opcional)", validators=[Optional()])


class KeyForm(FlaskForm):
    api_key = StringField("Chave da API da Anthropic", validators=[DataRequired(), Length(max=300)])
    model = SelectField("Modelo", choices=list(ai.MODELS.items()), default=ai.DEFAULT_MODEL)


class AskForm(FlaskForm):
    question = TextAreaField("Pergunte ao Arquiteto", validators=[DataRequired(), Length(max=4000)])


class PlanForm(FlaskForm):
    focus = StringField("Foco (opcional)", validators=[Optional(), Length(max=500)])
