from datetime import datetime
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    challenges = db.relationship('Challenge', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

class Challenge(db.Model):
    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    difficulty = db.Column(db.String(20), default='Easy') # Easy, Medium, Hard, Insane
    
    # Dynamic scoring columns
    initial_points = db.Column(db.Integer, nullable=False, default=500)
    minimum_points = db.Column(db.Integer, nullable=False, default=50)
    decay_limit    = db.Column(db.Integer, nullable=False, default=10)  # solves to reach minimum
    points         = db.Column(db.Integer, nullable=False, default=500) # current live value (cached)
    
    description = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=True, default='Unknown')  # Challenge author display name
    
    # Store exact flag hash or a string used for verification
    flag_hash = db.Column(db.String(256), nullable=False) 
    
    is_visible = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('Category', back_populates='challenges')
    files = db.relationship('ChallengeFile', back_populates='challenge', cascade="all, delete-orphan")
    hints = db.relationship('Hint', back_populates='challenge', cascade="all, delete-orphan")
    submissions = db.relationship('Submission', back_populates='challenge', lazy='dynamic', cascade="all, delete-orphan")
    solves = db.relationship('Solve', back_populates='challenge', lazy='dynamic', cascade="all, delete-orphan")
    challenge_views = db.relationship('ChallengeView', back_populates='challenge', cascade="all, delete-orphan")

    def get_current_points(self, solve_count: int | None = None) -> int:
        """Quadratic decay: points fall from initial to minimum over decay_limit solves."""
        if solve_count is None:
            solve_count = self.solves.count()
        if self.decay_limit <= 0:
            return self.initial_points
        value = (
            ((self.minimum_points - self.initial_points) / (self.decay_limit ** 2))
            * (solve_count ** 2)
            + self.initial_points
        )
        return max(self.minimum_points, int(round(value)))

    def set_flag(self, flag_string):
        """Hashes the flag for secure exact-match."""
        self.flag_hash = generate_password_hash(flag_string)

    def verify_flag(self, flag_string):
        return check_password_hash(self.flag_hash, flag_string)

    def __repr__(self):
        return f'<Challenge {self.title}>'

class ChallengeFile(db.Model):
    __tablename__ = 'challenge_files'

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False) # Display name for the file
    url = db.Column(db.String(512), nullable=False)       # External download URL (Google Drive, Dropbox, etc.)
    
    challenge = db.relationship('Challenge', back_populates='files')

class Hint(db.Model):
    __tablename__ = 'hints'

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)

    challenge = db.relationship('Challenge', back_populates='hints')
    unlocks = db.relationship('HintUnlock', back_populates='hint', cascade="all, delete-orphan", lazy='dynamic')

class HintUnlock(db.Model):
    __tablename__ = 'hint_unlocks'
    
    id = db.Column(db.Integer, primary_key=True)
    hint_id = db.Column(db.Integer, db.ForeignKey('hints.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True) # Assuming team mode
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # For solo players if needed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    hint = db.relationship('Hint', back_populates='unlocks')
