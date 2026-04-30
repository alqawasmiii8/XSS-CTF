import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(os.path.dirname(basedir), '.env')
load_dotenv(env_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @classmethod
    def init_app(cls, app):
        pass
    
    # Session / Cookie settings for security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

class DevelopmentConfig(Config):
    DEBUG = True
    # Default to sqlite relative to instance folder or project root
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
        elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+pg8000://"):
            db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
            
        # Remove pgbouncer=true if present as it can cause issues with some drivers
        if "?" in db_url:
            base_url, query = db_url.split("?", 1)
            params = [p for p in query.split("&") if not p.startswith("pgbouncer=")]
            db_url = f"{base_url}?{'&'.join(params)}" if params else base_url
            
    SQLALCHEMY_DATABASE_URI = db_url or \
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'ctf.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError('SECRET_KEY environment variable must be set in production!')
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
        elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+pg8000://"):
            db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
        
        # Supabase often requires sslmode=require for external connections
        if "?" in db_url:
            if "sslmode=" not in db_url:
                db_url += "&sslmode=require"
            # Remove pgbouncer if it causes issues, but Supabase usually handles it
        else:
            db_url += "?sslmode=require"
            
    SQLALCHEMY_DATABASE_URI = db_url
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
