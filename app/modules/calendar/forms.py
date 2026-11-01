from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, SelectField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Length, Optional

from app.modules.quests import services as quests

from .services import KINDS, EventInput


def _int_or_none(value):
    return int(value) if value not in (None, "", "0", 0) else None


class EventForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(), Length(max=200)])
    kind = SelectField("Tipo", choices=list(KINDS.items()), default="personal")
    start_date = DateField("Data", validators=[DataRequired()])
    start_time = TimeField("Início", validators=[Optional()])
    end_date = DateField("Data final (opcional)", validators=[Optional()])
    end_time = TimeField("Fim", validators=[Optional()])
    all_day = BooleanField("Dia inteiro")
    location = StringField("Local", validators=[Optional(), Length(max=200)])
    quest_id = SelectField("Quest vinculada", coerce=_int_or_none, validate_choice=False)
    description = TextAreaField("Descrição", validators=[Optional(), Length(max=2000)])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quest_id.choices = [(0, "Nenhuma")] + quests.quest_choices()

    def validate(self, extra_validators=None) -> bool:
        if not super().validate(extra_validators):
            return False
        if not self.all_day.data and self.start_time.data is None:
            self.start_time.errors.append("Informe o horário ou marque Dia inteiro.")
            return False
        return True

    def to_input(self) -> EventInput:
        start = datetime.combine(self.start_date.data, self.start_time.data or datetime.min.time())
        end = None
        if self.end_time.data or self.end_date.data:
            end = datetime.combine(self.end_date.data or self.start_date.data,
                                   self.end_time.data or self.start_time.data or datetime.min.time())
        return EventInput(
            title=self.title.data,
            start_at=start,
            end_at=end,
            all_day=self.all_day.data,
            kind=self.kind.data,
            description=self.description.data or "",
            location=self.location.data or "",
            quest_id=self.quest_id.data,
        )

    def fill_from(self, event) -> None:
        self.start_date.data = event.start_at.date()
        self.start_time.data = None if event.all_day else event.start_at.time()
        self.end_date.data = event.end_at.date()
        self.end_time.data = None if event.all_day else event.end_at.time()
        self.quest_id.data = event.quest_id or 0
