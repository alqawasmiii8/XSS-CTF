from datetime import datetime
from app.extensions import db

class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True) # Optional in some CTFs, required in team CTFs
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    
    submitted_flag = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    ip_address = db.Column(db.String(64))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='submissions')
    team = db.relationship('Team', back_populates='submissions')
    challenge = db.relationship('Challenge', back_populates='submissions')

    def __repr__(self):
        return f'<Submission {self.id} correct={self.is_correct}>'

class Solve(db.Model):
    """
    Records an actual solve. Avoids recalculating from thousands of submissions.
    """
    __tablename__ = 'solves'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    
    points_awarded = db.Column(db.Integer, nullable=False, default=0)
    solved_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_first_blood = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='solves')
    team = db.relationship('Team', back_populates='solves')
    challenge = db.relationship('Challenge', back_populates='solves')

    # Ensure a team (or user) only solves a challenge once
    __table_args__ = (
        db.UniqueConstraint('team_id', 'challenge_id', name='_team_challenge_solve_uc'),
        db.UniqueConstraint('user_id', 'challenge_id', name='_user_challenge_solve_uc'),
    )

class ChallengeView(db.Model):
    """
    Records the first time a user opens a challenge page.
    Used for impossible solve time detection.
    """
    __tablename__ = 'challenge_views'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    first_viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')
    challenge = db.relationship('Challenge')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'challenge_id', name='_user_challenge_view_uc'),
    )
