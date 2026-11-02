from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import BooleanField, DateField, DecimalField, IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp


class PlanForm(FlaskForm):
    name = StringField("Nome do plano", validators=[Optional(), Length(max=120)])
    text = TextAreaField("Rotina", validators=[DataRequired(), Length(max=20000)])
    description = StringField("Objetivo (opcional)", validators=[Optional(), Length(max=500)])
    start_date = DateField("Começar em", validators=[Optional()])
    session_time = StringField("Horário do treino", default="18:00",
                               validators=[DataRequired(), Regexp(r"^\d{1,2}:\d{2}$", message="Use HH:MM.")])
    session_minutes = IntegerField("Duração (min)", default=60, validators=[DataRequired(), NumberRange(5, 600)])
    load_increment_kg = DecimalField("Aumento de carga por semana completa (kg)", default=2.5, places=1,
                                     validators=[Optional(), NumberRange(0, 50)])
    make_quests = BooleanField("Criar uma quest semanal por dia de treino", default=True)
    make_events = BooleanField("Colocar os treinos no calendário", default=True)
    make_habit = BooleanField("Criar o hábito \"Treinar\" (folga não quebra a sequência)", default=True)
    progression = BooleanField("Sugerir progressão de carga a cada semana completa", default=True)


class UploadForm(FlaskForm):
    document = FileField("Documento (.txt, .md, .docx ou .pdf, até 5 MB)")
