import os
from flask import Flask, render_template
from .config import config
from .extensions import db, migrate, login_manager, csrf, limiter

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Determine config to use
    env_config_name = os.environ.get('FLASK_ENV', config_name)
    app.config.from_object(config.get(env_config_name, config['default']))
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Test DB Connection on Startup
    with app.app_context():
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    
    # Import and register blueprints
    from .blueprints.public import public_bp
    from .blueprints.auth import auth_bp
    from .blueprints.teams import teams_bp
    from .blueprints.challenges import challenges_bp
    from .blueprints.scoreboard import scoreboard_bp
    from .blueprints.admin import admin_bp
    
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(scoreboard_bp)
    app.register_blueprint(admin_bp)
    
    # Register error handlers
    register_error_handlers(app)
    # Single Session Enforcement
    @app.before_request
    def check_single_session():
        from flask_login import current_user
        from flask import session, flash, redirect, request
        
        # Don't check static files to avoid overhead
        if request.endpoint and request.endpoint.startswith('static'):
            return
            
        if current_user.is_authenticated:
            session_token = session.get('session_token')
            if session_token and current_user.session_token and session_token != current_user.session_token:
                from flask_login import logout_user
                logout_user()
                session.clear()
                flash('You have been logged out because your account was accessed from another location.', 'error')
                return redirect('/auth/login')

    return app

def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
