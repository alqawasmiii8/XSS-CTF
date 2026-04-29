from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, URL, Optional

class ProfileEditForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=255)])
    avatar = StringField('Avatar URL', validators=[Optional(), URL(), Length(max=255)])
    country = StringField('Country', validators=[Optional(), Length(max=64)])
    submit = SubmitField('Update Profile')
