from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp


class ProfileForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=80)])
    avatar_url = StringField("Avatar: link público de uma imagem (https://...)",
                             validators=[Optional(), Length(max=500)])


class RankForm(FlaskForm):
    code = StringField("Código", validators=[DataRequired(), Length(max=4)])
    name = StringField("Nome", validators=[DataRequired(), Length(max=60)])
    min_level = IntegerField("Nível mínimo", validators=[DataRequired(), NumberRange(min=1, max=9999)])
    color = StringField("Cor", default="#8b5cf6",
                        validators=[DataRequired(), Regexp(r"^#[0-9a-fA-F]{6}$", message="Use #RRGGBB.")])


class AttributeForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=60)])
    description = TextAreaField("O que conta para este atributo", validators=[Optional(), Length(max=500)])


class TitleForm(FlaskForm):
    name = StringField("Nome do título", validators=[DataRequired(), Length(max=80)])
    description = StringField("Descrição (opcional)", validators=[Optional(), Length(max=500)])
