import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, flash, request, current_app
from flask_login import login_required, current_user
from app.extensions import db, limiter
from app.models import Challenge, Category, Submission, Solve, EventSettings, Hint, HintUnlock, ChallengeView
from app.forms.challenge import FlagSubmissionForm

challenges_bp = Blueprint('challenges', __name__, url_prefix='/challenges')

@challenges_bp.route('/')
@login_required
def index():
    # Check maintenance and competition status
    settings = EventSettings.query.first()
    
    categories = Category.query.all()
    # Eager load saves DB hits in template
    challenges = Challenge.query.filter_by(is_visible=True).all()
    
    # Get user's team solves if applicable
    solved_challenge_ids = []
    if current_user.team:
        solves = Solve.query.filter_by(team_id=current_user.team.id).all()
        solved_challenge_ids = [s.challenge_id for s in solves]
    else:
        # Solo player mode support
        solves = Solve.query.filter_by(user_id=current_user.id).all()
        solved_challenge_ids = [s.challenge_id for s in solves]
        
    return render_template('challenges/index.html', 
                           categories=categories, 
                           challenges=challenges,
                           solved_ids=solved_challenge_ids,
                           settings=settings)

@challenges_bp.route('/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per minute")
def view(challenge_id):
    challenge = Challenge.query.filter_by(id=challenge_id, is_visible=True).first_or_404()
    form = FlagSubmissionForm()
    
    # Check if competition is live
    settings = EventSettings.query.first()
    if settings and not settings.is_live:
        flash('Competition is currently paused or not started.', 'warning')

    # Track first view time for impossible-solve detection
    existing_view = ChallengeView.query.filter_by(user_id=current_user.id, challenge_id=challenge.id).first()
    if not existing_view:
        view_log = ChallengeView(user_id=current_user.id, challenge_id=challenge.id)
        db.session.add(view_log)
        db.session.commit()
        
    if form.validate_on_submit() and settings and settings.is_live:
        # Check team requirement
        if not current_user.team:
            flash('You must be in a team to submit flags.', 'error')
            return redirect(f'/challenges/{challenge_id}')

        # Prevent duplicate solve
        existing_solve = Solve.query.filter_by(team_id=current_user.team.id, challenge_id=challenge.id).first()
        if existing_solve:
            flash('Your team has already solved this challenge.', 'warning')
            return redirect(f'/challenges/{challenge_id}')
        
        # --- Rate Limiting ---
        # Count wrong submissions by this team on this challenge in the last 60 seconds
        from sqlalchemy import and_
        RATE_LIMIT_WINDOW = 60   # seconds
        RATE_LIMIT_MAX    = 5    # max wrong guesses per window
        cutoff = datetime.utcnow() - timedelta(seconds=RATE_LIMIT_WINDOW)
        
        recent_wrong = Submission.query.filter(
            and_(
                Submission.team_id    == current_user.team.id,
                Submission.challenge_id == challenge.id,
                Submission.is_correct  == False,
                Submission.submitted_at >= cutoff
            )
        ).count()
        
        if recent_wrong >= RATE_LIMIT_MAX:
            flash(f'⚠️ Too many wrong submissions. Slow down — try again in {RATE_LIMIT_WINDOW}s.', 'error')
            return redirect(f'/challenges/{challenge_id}')
        
        submitted_flag = form.flag.data.strip()
        is_correct = challenge.verify_flag(submitted_flag)

        
        # Log Submission
        sub = Submission(
            user_id=current_user.id,
            team_id=current_user.team.id,
            challenge_id=challenge.id,
            submitted_flag=submitted_flag, # In prod, consider not storing incorrect plain flags for security
            is_correct=is_correct,
            ip_address=request.remote_addr
        )
        db.session.add(sub)
        
        if is_correct:
            # Check for first blood
            first_blood = Solve.query.filter_by(challenge_id=challenge.id).first() is None
            
            solve = Solve(
                user_id=current_user.id,
                team_id=current_user.team.id,
                challenge_id=challenge.id,
                points_awarded=0,          # calculated below
                is_first_blood=first_blood
            )
            db.session.add(solve)
            db.session.flush()  # give the new solve an id so count() includes it

            # Recalculate dynamic points
            new_points = challenge.get_current_points()
            challenge.points = new_points

            # Retroactively update every solve for this challenge
            for s in challenge.solves:
                s.points_awarded = new_points

            db.session.commit()
            flash(f'Correct Flag! +{new_points} pts 🎉', 'success')
        else:
            db.session.commit()
            flash('Incorrect Flag.', 'error')
            
        return redirect(f'/challenges/{challenge_id}')

    # Get unlocked hints
    unlocked_hint_ids = []
    wrong_attempts = 0
    RATE_LIMIT_MAX = 5
    if current_user.team:
        unlocked = HintUnlock.query.filter_by(team_id=current_user.team.id).all()
        unlocked_hint_ids = [u.hint_id for u in unlocked]
        
        from sqlalchemy import and_
        cutoff = datetime.utcnow() - timedelta(seconds=60)
        wrong_attempts = Submission.query.filter(
            and_(
                Submission.team_id    == current_user.team.id,
                Submission.challenge_id == challenge.id,
                Submission.is_correct  == False,
                Submission.submitted_at >= cutoff
            )
        ).count()
        
    return render_template('challenges/view.html', challenge=challenge, form=form,
                           unlocked_hint_ids=unlocked_hint_ids,
                           wrong_attempts=wrong_attempts,
                           rate_limit_max=RATE_LIMIT_MAX)

@challenges_bp.route('/<int:challenge_id>/hints/<int:hint_id>/unlock', methods=['POST'])
@login_required
def unlock_hint(challenge_id, hint_id):
    if not current_user.team:
        flash('You must be in a team to unlock hints.', 'error')
        return redirect(f'/challenges/{challenge_id}')
        
    hint = Hint.query.filter_by(id=hint_id, challenge_id=challenge_id).first_or_404()
    
    # Check if already unlocked
    existing = HintUnlock.query.filter_by(hint_id=hint.id, team_id=current_user.team.id).first()
    if existing:
        flash('You already unlocked this hint.', 'info')
        return redirect(f'/challenges/{challenge_id}')
        
    unlock = HintUnlock(hint_id=hint.id, team_id=current_user.team.id, user_id=current_user.id)
    db.session.add(unlock)
    db.session.commit()
    
    flash(f'Hint unlocked! (-{hint.cost} points)', 'success')
    return redirect(f'/challenges/{challenge_id}')



