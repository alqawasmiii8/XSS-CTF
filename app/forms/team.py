from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import Team

class TeamCreateForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired(), Length(min=3, max=100)])
    submit = SubmitField('Create Team')

    def validate_name(self, name):
        team = Team.query.filter_by(name=name.data).first()
        if team:
            raise ValidationError('Team name already taken.')

class TeamJoinForm(FlaskForm):
    invite_code = StringField('Invite Code', validators=[DataRequired(), Length(min=36, max=36, message="Invalid invite code format.")])
    submit = SubmitField('Join Team')
    
    def validate_invite_code(self, invite_code):
        team = Team.query.filter_by(invite_code=invite_code.data).first()
        if not team:
            raise ValidationError('Invalid invite code.')
