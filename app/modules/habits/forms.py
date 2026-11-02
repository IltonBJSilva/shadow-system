from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectMultipleField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.modules.hunter import services as hunter


class HabitForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Descrição", validators=[Optional(), Length(max=1000)])
    xp_per_check = IntegerField("XP por dia feito", default=10, validators=[DataRequired(), NumberRange(min=0, max=1000)])
    attribute_ids = SelectMultipleField("Atributos que este hábito desenvolve", coerce=int)
    weekdays = SelectMultipleField(
        "Dias em que conta", coerce=int,
        choices=[(0, "Seg"), (1, "Ter"), (2, "Qua"), (3, "Qui"), (4, "Sex"), (5, "Sáb"), (6, "Dom")],
        description="Nenhum marcado = todos os dias. Dias fora da agenda (descanso) não quebram a sequência.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attribute_ids.choices = hunter.attribute_choices()
