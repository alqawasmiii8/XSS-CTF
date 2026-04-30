from flask import Blueprint, render_template
from app.models import Challenge, Team, User, Notification, Page, EventSettings
from flask_login import login_required, current_user
from flask import request, redirect
from app.extensions import db

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    settings = EventSettings.query.first()
    return render_template('public/index.html', settings=settings)

@public_bp.route('/rules')
def rules():
    page = Page.query.filter_by(slug='rules').first()
    return render_template('public/dynamic_page.html', page=page)

@public_bp.route('/faq')
def faq():
    page = Page.query.filter_by(slug='faq').first()
    return render_template('public/dynamic_page.html', page=page)

@public_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    if request.method == 'POST':
        # Mark all as read
        notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
        for n in notifs:
            n.is_read = True
        db.session.commit()
        return redirect('/notifications')
        
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('public/notifications.html', notifications=notifs)

@public_bp.route('/dashboard')
@login_required
def dashboard():
    from app.models import Solve, Submission, Team, HintUnlock, Hint
    from sqlalchemy import func
    
    # Calculate user's total points (via their team)
    total_points = 0
    solves_count = 0
    rank = "N/A"
    
    if current_user.team:
        # Base scores from solves for the team
        team_id = current_user.team.id
        
        solve_points = db.session.query(func.sum(Solve.points_awarded)).filter_by(team_id=team_id).scalar() or 0
        
        # Deductions from hint unlocks
        hint_deductions = db.session.query(func.sum(Hint.cost)).join(HintUnlock).filter(HintUnlock.team_id == team_id).scalar() or 0
        
        total_points = solve_points - hint_deductions
        solves_count = Solve.query.filter_by(team_id=team_id).count()
        
        # Calculate Rank
        # This is a bit expensive but okay for a dashboard
        all_team_scores = db.session.query(
            Solve.team_id,
            (func.sum(Solve.points_awarded) - 
             func.coalesce(db.session.query(func.sum(Hint.cost)).join(HintUnlock).filter(HintUnlock.team_id == Solve.team_id).correlate(Solve).as_scalar(), 0)).label('total')
        ).group_by(Solve.team_id).order_by(db.text('total DESC')).all()
        
        for i, (tid, score) in enumerate(all_team_scores):
            if tid == team_id:
                rank = i + 1
                break
    else:
        # Solo stats if no team
        solve_points = db.session.query(func.sum(Solve.points_awarded)).filter_by(user_id=current_user.id).scalar() or 0
        total_points = solve_points
        solves_count = Solve.query.filter_by(user_id=current_user.id).count()

    # Recent solves for this user/team
    recent_solves = Solve.query.filter(
        (Solve.team_id == current_user.team.id) if current_user.team else (Solve.user_id == current_user.id)
    ).order_by(Solve.solved_at.desc()).limit(5).all()

    return render_template('public/dashboard.html', 
                           total_points=total_points, 
                           solves_count=solves_count, 
                           rank=rank,
                           recent_solves=recent_solves)

@public_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    from app.forms.user import ProfileEditForm
    form = ProfileEditForm(obj=current_user)
    if form.validate_on_submit():
        # Check if email is being changed and is unique
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email is already in use by another account.', 'error')
                return render_template('public/profile_edit.html', form=form)
            current_user.email = form.email.data
            
        current_user.bio = form.bio.data
        current_user.avatar = form.avatar.data
        current_user.country = form.country.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect('/dashboard')
    
    return render_template('public/profile_edit.html', form=form)

@public_bp.route('/users/<int:user_id>')
def user_profile(user_id):
    from app.models import User, Solve
    user = User.query.get_or_404(user_id)
    
    # Calculate user's individual solves (even if in a team, these are the flags THEY submitted)
    solves = Solve.query.filter_by(user_id=user.id).order_by(Solve.solved_at.desc()).all()
    total_points = sum(s.points_awarded for s in solves)
    
    return render_template('public/user_profile.html', user=user, solves=solves, total_points=total_points)

@public_bp.route('/anticheat')
def anticheat_rules():
    return render_template('public/anticheat_rules.html')

