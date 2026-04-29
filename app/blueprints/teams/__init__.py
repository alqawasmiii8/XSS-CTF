from flask import Blueprint, render_template, redirect, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Team, TeamMember
from app.forms.team import TeamCreateForm, TeamJoinForm

teams_bp = Blueprint('teams', __name__, url_prefix='/team')

@teams_bp.route('/', methods=['GET'])
@login_required
def index():
    if current_user.team:
        return redirect(f'/team/{current_user.team.id}')
    
    create_form = TeamCreateForm()
    join_form = TeamJoinForm()
    return render_template('teams/index.html', create_form=create_form, join_form=join_form)

@teams_bp.route('/create', methods=['POST'])
@login_required
def create():
    if current_user.team:
        flash('You are already in a team.', 'warning')
        return redirect('/team/')
        
    form = TeamCreateForm()
    if form.validate_on_submit():
        team = Team(name=form.name.data, captain_id=current_user.id)
        db.session.add(team)
        db.session.flush() # get team.id
        
        member = TeamMember(user_id=current_user.id, team_id=team.id)
        db.session.add(member)
        db.session.commit()
        
        flash('Team created successfully!', 'success')
        return redirect(f'/team/{team.id}')
    
    flash('Error creating team.', 'error')
    return redirect('/team/')

@teams_bp.route('/join', methods=['POST'])
@login_required
def join():
    if current_user.team:
        flash('You are already in a team.', 'warning')
        return redirect('/team/')
        
    form = TeamJoinForm()
    if form.validate_on_submit():
        team = Team.query.filter_by(invite_code=form.invite_code.data).first()
        if not team:
            flash('Invalid invite code.', 'error')
            return redirect('/team/')
            
        member = TeamMember(user_id=current_user.id, team_id=team.id)
        db.session.add(member)
        db.session.commit()
        
        flash(f'Successfully joined team {team.name}!', 'success')
        return redirect(f'/team/{team.id}')
        
    flash('Error joining team. Check your code.', 'error')
    return redirect('/team/')

@teams_bp.route('/<int:team_id>', methods=['GET'])
def view(team_id):
    from app.models import Solve, Category
    team = Team.query.get_or_404(team_id)
    solves = Solve.query.filter_by(team_id=team.id).order_by(Solve.solved_at.desc()).all()
    
    # Build category breakdown for radar chart
    categories = Category.query.all()
    category_scores = {}
    for cat in categories:
        cat_solves = [s for s in solves if s.challenge and s.challenge.category_id == cat.id]
        category_scores[cat.name] = sum(s.points_awarded or 0 for s in cat_solves)
    
    return render_template('teams/view.html', team=team, solves=solves, category_scores=category_scores)
