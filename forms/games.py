from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, StringField, TextAreaField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired


class GamesForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    submit = SubmitField('Применить')
    immage = FileField('Изображение', validators=[FileAllowed(['png'], 'Только изображение'),
                                                FileRequired('Файл пустой!')])
    torrent = FileField('Торрент', validators=[FileAllowed(['torrent'], 'Только торрент'),
                                                FileRequired('Файл пустой!')])
