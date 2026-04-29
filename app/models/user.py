from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    bio = db.Column(db.String(255))
    avatar = db.Column(db.String(255))
    country = db.Column(db.String(64))
    
    role = db.Column(db.String(20), default='user') # 'user' or 'admin'
    
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    team_memberships = db.relationship('TeamMember', back_populates='user', lazy='dynamic')
    submissions = db.relationship('Submission', back_populates='user', lazy='dynamic')
    solves = db.relationship('Solve', back_populates='user', lazy='dynamic')
    
    @property
    def team(self):
        # Return the team the user belongs to (assuming 1 team per user for the competition)
        membership = self.team_memberships.first()
        if membership:
            return membership.team
        return None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'
