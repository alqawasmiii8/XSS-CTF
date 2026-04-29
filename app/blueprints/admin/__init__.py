import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, flash, request, current_app
from app.extensions import db
from app.models import Challenge, Category, User, Team, TeamMember, Solve, EventSettings, Notification, Hint, ChallengeFile, Page
from app.forms.admin import ChallengeCreateForm, ChallengeEditForm, EventSettingsForm, CategoryForm, TeamCreateAdminForm, NotificationAdminForm, HintAdminForm, PageEditForm
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@admin_required
def require_admin():
    pass

@admin_bp.route('/')
def dashboard():
    users_count = User.query.count()
    teams_count = Team.query.count()
    challenges_count = Challenge.query.count()
    solves_count = Solve.query.count()
    return render_template('admin/index.html', 
                           users=users_count, 
                           teams=teams_count, 
                           challenges=challenges_count, 
                           solves=solves_count)

@admin_bp.route('/challenges', methods=['GET', 'POST'])
def manage_challenges():
    form = ChallengeCreateForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        chal = Challenge(
            title=form.title.data,
            slug=form.slug.data,
            category_id=form.category_id.data,
            difficulty=form.difficulty.data,
            initial_points=form.initial_points.data,
            minimum_points=form.minimum_points.data,
            decay_limit=form.decay_limit.data,
            points=form.initial_points.data,   # starts at max
            description=form.description.data,
            is_visible=form.is_visible.data
        )
        chal.set_flag(form.flag.data)
        db.session.add(chal)
        db.session.commit()
        flash('Challenge created successfully.', 'success')
        return redirect('/admin/challenges')
        
    challenges = Challenge.query.order_by(Challenge.category_id).all()
    return render_template('admin/challenges.html', challenges=challenges, form=form)

@admin_bp.route('/challenges/toggle/<int:id>', methods=['POST'])
def toggle_challenge(id):
    chal = Challenge.query.get_or_404(id)
    chal.is_visible = not chal.is_visible
    db.session.commit()
    flash(f"Challenge {'published' if chal.is_visible else 'hidden'}.", 'success')
    return redirect('/admin/challenges')

@admin_bp.route('/challenges/edit/<int:id>', methods=['GET', 'POST'])
def edit_challenge(id):
    chal = Challenge.query.get_or_404(id)
    form = ChallengeEditForm(obj=chal)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    hint_form = HintAdminForm()
    
    if form.validate_on_submit():
        chal.title = form.title.data
        chal.slug = form.slug.data
        chal.category_id = form.category_id.data
        chal.difficulty = form.difficulty.data
        chal.initial_points = form.initial_points.data
        chal.minimum_points = form.minimum_points.data
        chal.decay_limit = form.decay_limit.data
        chal.description = form.description.data
        chal.is_visible = form.is_visible.data
        
        # Only update flag if provided
        if form.flag.data and form.flag.data.strip():
            chal.set_flag(form.flag.data.strip())
            
        # Handle file uploads
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file.filename:
                    original_filename = secure_filename(file.filename)
                    # Generate unique name for disk
                    unique_name = str(uuid.uuid4()) + "_" + original_filename
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
                    
                    file.save(save_path)
                    
                    chal_file = ChallengeFile(
                        challenge_id=chal.id,
                        filename=original_filename,
                        stored_path=unique_name
                    )
                    db.session.add(chal_file)
            
        db.session.commit()
        flash(f"Challenge '{chal.title}' updated successfully.", 'success')
        return redirect('/admin/challenges')
    
    return render_template('admin/edit_challenge.html', form=form, hint_form=hint_form, challenge=chal)

@admin_bp.route('/challenges/delete/<int:id>', methods=['POST'])
def delete_challenge(id):
    chal = Challenge.query.get_or_404(id)
    db.session.delete(chal)
    db.session.commit()
    flash(f"Challenge '{chal.title}' has been deleted.", 'success')
    return redirect('/admin/challenges')

@admin_bp.route('/challenges/files/delete/<int:file_id>', methods=['POST'])
def delete_challenge_file(file_id):
    chal_file = ChallengeFile.query.get_or_404(file_id)
    chal_id = chal_file.challenge_id
    
    # Remove from disk
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], chal_file.stored_path)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(chal_file)
    db.session.commit()
    
    flash('File deleted.', 'success')
    return redirect(f'/admin/challenges/edit/{chal_id}')

@admin_bp.route('/challenges/<int:id>/hints/add', methods=['POST'])
def add_hint(id):
    chal = Challenge.query.get_or_404(id)
    hint_form = HintAdminForm()
    if hint_form.validate_on_submit():
        hint = Hint(
            challenge_id=chal.id,
            content=hint_form.content.data,
            cost=hint_form.cost.data,
            is_visible=hint_form.is_visible.data
        )
        db.session.add(hint)
        
        # Send notification to all users
        users = User.query.all()
        for u in users:
            notif = Notification(user_id=u.id, title=f"New Hint: {chal.title}", message=f"A new hint was added for challenge '{chal.title}'.")
            db.session.add(notif)
            
        db.session.commit()
        flash('Hint added successfully and all users notified.', 'success')
    return redirect(f'/admin/challenges/edit/{chal.id}')

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    from datetime import datetime as dt
    settings_obj = EventSettings.query.first()
    if not settings_obj:
        settings_obj = EventSettings()
        db.session.add(settings_obj)
        db.session.commit()
        
    form = EventSettingsForm(obj=settings_obj)
    if form.validate_on_submit():
        form.populate_obj(settings_obj)
        
        # Handle manual datetime-local fields for start/end times
        start_str = request.form.get('start_time', '').strip()
        end_str   = request.form.get('end_time', '').strip()
        if start_str:
            try:
                settings_obj.start_time = dt.strptime(start_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
        else:
            settings_obj.start_time = None
        if end_str:
            try:
                settings_obj.end_time = dt.strptime(end_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
        else:
            settings_obj.end_time = None
        
        db.session.commit()
        flash('Settings updated globally.', 'success')
        return redirect('/admin/settings')
        
    return render_template('admin/settings.html', form=form, settings=settings_obj)

@admin_bp.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        existing = Category.query.filter_by(name=form.name.data.strip()).first()
        if existing:
            flash(f'Category "{form.name.data}" already exists.', 'error')
        else:
            cat = Category(name=form.name.data.strip(), description=form.description.data.strip())
            db.session.add(cat)
            db.session.commit()
            flash(f'Category "{cat.name}" added.', 'success')
        return redirect('/admin/categories')

    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories, form=form)

@admin_bp.route('/categories/delete/<int:id>', methods=['POST'])
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.challenges.count() > 0:
        flash(f'Cannot delete "{cat.name}" — it still has challenges assigned to it.', 'error')
        return redirect('/admin/categories')
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{cat.name}" deleted.', 'success')
    return redirect('/admin/categories')

@admin_bp.route('/teams', methods=['GET', 'POST'])
def manage_teams():
    from sqlalchemy import func
    form = TeamCreateAdminForm()

    if form.validate_on_submit():
        captain = User.query.filter_by(username=form.captain_username.data.strip()).first()
        if not captain:
            flash(f'User "{form.captain_username.data}" not found.', 'error')
        elif Team.query.filter_by(name=form.name.data.strip()).first():
            flash(f'Team name "{form.name.data}" is already taken.', 'error')
        elif captain.team:
            flash(f'{captain.username} is already in a team.', 'error')
        else:
            team = Team(name=form.name.data.strip(), captain_id=captain.id)
            db.session.add(team)
            db.session.flush()
            member = TeamMember(user_id=captain.id, team_id=team.id)
            db.session.add(member)
            db.session.commit()
            flash(f'Team "{team.name}" created with {captain.username} as captain!', 'success')
        return redirect('/admin/teams')

    teams = Team.query.order_by(Team.name).all()

    # Build score map: team_id -> total points
    scores_raw = db.session.query(
        Solve.team_id,
        func.sum(Solve.points_awarded).label('score')
    ).group_by(Solve.team_id).all()
    
    # Calculate deductions from hint unlocks
    from app.models import HintUnlock, Hint
    unlock_costs = db.session.query(
        HintUnlock.team_id,
        func.sum(Hint.cost).label('total_cost')
    ).join(Hint).group_by(HintUnlock.team_id).all()
    
    cost_map = {u.team_id: u.total_cost or 0 for u in unlock_costs if u.team_id}

    scores = {s.team_id: (s.score or 0) - cost_map.get(s.team_id, 0) for s in scores_raw}

    teams_data = []
    for t in teams:
        teams_data.append({
            'team': t,
            'members': t.members.all(),
            'score': scores.get(t.id, 0),
            'solves': t.solves.count(),
        })

    return render_template('admin/teams.html', teams_data=teams_data, form=form)

@admin_bp.route('/teams/delete/<int:id>', methods=['POST'])
def delete_team(id):
    team = Team.query.get_or_404(id)
    name = team.name
    db.session.delete(team)
    db.session.commit()
    flash(f'Team "{name}" and all its members have been removed.', 'success')
    return redirect('/admin/teams')

@admin_bp.route('/teams/kick/<int:member_id>', methods=['POST'])
def kick_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    team_id = member.team_id
    db.session.delete(member)
    db.session.commit()
    flash('Member removed from team.', 'success')
    return redirect('/admin/teams')

@admin_bp.route('/notifications', methods=['GET', 'POST'])
def manage_notifications():
    form = NotificationAdminForm()
    choices = [(0, '--- All Users ---')] + [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    form.user_id.choices = choices
    
    if form.validate_on_submit():
        if form.user_id.data and form.user_id.data != 0:
            notif = Notification(user_id=form.user_id.data, title=form.title.data, message=form.message.data)
            db.session.add(notif)
            db.session.commit()
            flash('Notification sent to user.', 'success')
        else:
            users = User.query.all()
            for u in users:
                notif = Notification(user_id=u.id, title=form.title.data, message=form.message.data)
                db.session.add(notif)
            db.session.commit()
            flash('Notification sent to ALL users.', 'success')
        return redirect('/admin/notifications')
        
    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    return render_template('admin/notifications.html', form=form, notifications=recent_notifications)

@admin_bp.route('/pages', methods=['GET'])
def manage_pages():
    pages = Page.query.all()
    return render_template('admin/pages.html', pages=pages)

@admin_bp.route('/pages/edit/<slug>', methods=['GET', 'POST'])
def edit_page(slug):
    page = Page.query.filter_by(slug=slug).first_or_404()
    form = PageEditForm(obj=page)
    if form.validate_on_submit():
        page.title = form.title.data
        page.content = form.content.data
        db.session.commit()
        flash(f"Page '{page.title}' updated successfully.", 'success')
        return redirect('/admin/pages')
    return render_template('admin/edit_page.html', form=form, page=page)
