import uuid
from datetime import datetime
from app.extensions import db

class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, index=True, nullable=False)
    invite_code = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    captain_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    captain = db.relationship('User', foreign_keys=[captain_id])
    members = db.relationship('TeamMember', back_populates='team', cascade="all, delete-orphan", lazy='dynamic')
    submissions = db.relationship('Submission', back_populates='team', lazy='dynamic')
    solves = db.relationship('Solve', back_populates='team', lazy='dynamic')

    def __repr__(self):
        return f'<Team {self.name}>'

class TeamMember(db.Model):
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Prevent a user from being in multiple teams
    __table_args__ = (db.UniqueConstraint('user_id', name='_user_team_uc'),)

    user = db.relationship('User', back_populates='team_memberships')
    team = db.relationship('Team', back_populates='members')

    def __repr__(self):
        return f'<TeamMember user_id={self.user_id} team_id={self.team_id}>'
