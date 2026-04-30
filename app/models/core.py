from datetime import datetime
from app.extensions import db

class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

class EventSettings(db.Model):
    """
    Singleton-style table to hold global settings.
    """
    __tablename__ = 'event_settings'

    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100), default='XSSPloit CTF')
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    is_live = db.Column(db.Boolean, default=False)
    scoreboard_frozen = db.Column(db.Boolean, default=False)
    registration_open = db.Column(db.Boolean, default=True)
    challenges_maintenance = db.Column(db.Boolean, default=False)
    registration_maintenance = db.Column(db.Boolean, default=False)
    flag_format = db.Column(db.String(100), default='XSS{.*}')
    
    # Anticheat Settings
    anticheat_flag_spam_action = db.Column(db.String(20), default='notify') # 'ignore', 'notify', 'ban'
    anticheat_flag_spam_threshold = db.Column(db.Integer, default=50)

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin = db.relationship('User', foreign_keys=[admin_id])

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(256), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class Page(db.Model):
    __tablename__ = 'pages'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # e.g. 'rules', 'faq'
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
