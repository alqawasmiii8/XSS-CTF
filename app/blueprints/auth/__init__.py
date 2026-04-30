from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from app.extensions import db, limiter
from app.models.user import User, LoginLog
from app.forms.auth import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from itsdangerous import URLSafeTimedSerializer

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect('/')
    
    from app.models import EventSettings
    settings = EventSettings.query.first()
    
    # Check maintenance mode
    if settings and settings.registration_maintenance:
        return render_template('auth/maintenance.html')
    
    if settings and not settings.registration_open:
        flash('Registration is currently closed.', 'error')
        return redirect('/')

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect('/auth/login')
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        # Check if login is email or username
        user = User.query.filter_by(username=form.login.data).first()
        if user is None:
            user = User.query.filter_by(email=form.login.data).first()
            
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect('/auth/login')
            
        if user.is_banned:
            return redirect('/auth/banned')
        
        login_user(user, remember=form.remember_me.data)
        
        # Update session token
        import uuid
        user.session_token = str(uuid.uuid4())
        db.session.commit()
        session['session_token'] = user.session_token
        
        # Log IP
        login_log = LoginLog(user_id=user.id, ip_address=request.remote_addr)
        db.session.add(login_log)
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = '/'
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@auth_bp.route('/banned')
def banned():
    return render_template('auth/banned.html')

def get_reset_token(user, expires_sec=1800):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps({'user_id': user.id}, salt='password-reset-salt')

def verify_reset_token(token, expires_sec=1800):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='password-reset-salt', max_age=expires_sec)
    except:
        return None
    return User.query.get(data['user_id'])

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def forgot_password():
    if current_user.is_authenticated:
        return redirect('/')
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = get_reset_token(user)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            print(f"--- PASSWORD RESET LINK FOR {user.username} ---")
            print(reset_url)
            print("---------------------------------------------")
        flash('If an account with that email exists, a password reset link has been printed to the server console.', 'info')
        return redirect('/auth/login')
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect('/')
    user = verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect('/auth/forgot-password')
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect('/auth/login')
    return render_template('auth/reset_password.html', form=form)
