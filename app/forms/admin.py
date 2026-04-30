from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional

class CategoryForm(FlaskForm):
    name        = StringField('Category Name', validators=[DataRequired()])
    description = TextAreaField('Description (optional)', validators=[Optional()])
    submit      = SubmitField('Add Category')

class ChallengeCreateForm(FlaskForm):
    title          = StringField('Title', validators=[DataRequired()])
    slug           = StringField('Slug', validators=[DataRequired()])
    author         = StringField('Author', validators=[Optional()])
    category_id    = SelectField('Category', coerce=int, validators=[DataRequired()])
    difficulty     = SelectField('Difficulty', choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ('Insane', 'Insane')])
    initial_points = IntegerField('Initial Points (max)', validators=[DataRequired()])
    minimum_points = IntegerField('Minimum Points (floor)', validators=[DataRequired()])
    decay_limit    = IntegerField('Decay Limit (# solves to reach min)', validators=[DataRequired()])
    description    = TextAreaField('Description', validators=[DataRequired()])
    flag           = StringField('Flag (Exact Match)', validators=[DataRequired()])
    is_visible     = BooleanField('Visible to Players')
    submit         = SubmitField('Save Challenge')

class ChallengeEditForm(FlaskForm):
    title          = StringField('Title', validators=[DataRequired()])
    slug           = StringField('Slug', validators=[DataRequired()])
    author         = StringField('Author', validators=[Optional()])
    category_id    = SelectField('Category', coerce=int, validators=[DataRequired()])
    difficulty     = SelectField('Difficulty', choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ('Insane', 'Insane')])
    initial_points = IntegerField('Initial Points (max)', validators=[DataRequired()])
    minimum_points = IntegerField('Minimum Points (floor)', validators=[DataRequired()])
    decay_limit    = IntegerField('Decay Limit (# solves to reach min)', validators=[DataRequired()])
    description    = TextAreaField('Description', validators=[DataRequired()])
    flag           = StringField('Flag (Leave blank to keep current)', validators=[Optional()])
    is_visible     = BooleanField('Visible to Players')
    submit         = SubmitField('Update Challenge')

class EventSettingsForm(FlaskForm):
    event_name = StringField('Event Name', validators=[DataRequired()])
    is_live = BooleanField('Competition is Live')
    scoreboard_frozen = BooleanField('Freeze Scoreboard')
    registration_open = BooleanField('Registration Open')
    challenges_maintenance = BooleanField('Challenges Under Maintenance')
    registration_maintenance = BooleanField('Registration Under Maintenance')
    flag_format = StringField('Global Flag Format (regex or template)')
    anticheat_flag_spam_action = SelectField('Flag Spam Action', choices=[('ignore', 'Ignore (Rate Limit Only)'), ('notify', 'Notify Admin (Log)'), ('ban', 'Auto-Ban User')])
    anticheat_flag_spam_threshold = IntegerField('Flag Spam Threshold (Failed Attempts)', default=50)
    submit = SubmitField('Update Settings')

class TeamCreateAdminForm(FlaskForm):
    name       = StringField('Team Name', validators=[DataRequired()])
    captain_username = StringField('Captain Username', validators=[DataRequired()])
    submit     = SubmitField('Create Team')

class NotificationAdminForm(FlaskForm):
    user_id = SelectField('User (Leave blank for All Users)', coerce=int, validators=[Optional()])
    title = StringField('Title', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Notification')

class HintAdminForm(FlaskForm):
    content = TextAreaField('Hint Content', validators=[DataRequired()])
    cost = IntegerField('Cost (Optional)', default=0)
    is_visible = BooleanField('Visible immediately', default=True)
    submit = SubmitField('Add Hint')

class PageEditForm(FlaskForm):
    title = StringField('Page Title', validators=[DataRequired()])
    content = TextAreaField('Content (HTML)', validators=[DataRequired()])
    submit = SubmitField('Save Page')
