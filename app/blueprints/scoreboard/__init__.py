from flask import Blueprint, render_template, jsonify
from sqlalchemy import func
from app.extensions import db
from app.models import Team, Solve, EventSettings, HintUnlock, Hint

scoreboard_bp = Blueprint('scoreboard', __name__, url_prefix='/scoreboard')

@scoreboard_bp.route('/')
def index():
    # Base scores from solves
    scores = db.session.query(
        Solve.team_id,
        func.sum(Solve.points_awarded).label('score'),
        func.max(Solve.solved_at).label('last_solve')
    ).group_by(Solve.team_id).all()
    
    # Calculate deductions from hint unlocks
    unlock_costs = db.session.query(
        HintUnlock.team_id,
        func.sum(Hint.cost).label('total_cost')
    ).join(Hint).group_by(HintUnlock.team_id).all()
    
    cost_map = {u.team_id: u.total_cost or 0 for u in unlock_costs if u.team_id}
    
    # Get team details
    team_ids = [s.team_id for s in scores if s.team_id]
    teams = {t.id: t for t in Team.query.filter(Team.id.in_(team_ids)).all()}
    
    raw_data = []
    for s in scores:
        if s.team_id and s.team_id in teams:
            team_score = (s.score or 0) - cost_map.get(s.team_id, 0)
            raw_data.append({
                'team': teams[s.team_id],
                'score': team_score,
                'last_solve': s.last_solve
            })
            
    raw_data.sort(key=lambda x: (-x['score'], x['last_solve']))
    
    scoreboard_data = []
    rank = 1
    for data in raw_data:
        data['rank'] = rank
        scoreboard_data.append(data)
        rank += 1
            
    return render_template('scoreboard/index.html', scoreboard=scoreboard_data)

@scoreboard_bp.route('/api/timeline')
def timeline_api():
    """
    Returns a JSON structure suitable for a Chart.js multi-line graph.
    Shows cumulative points over time for the top 10 teams.
    """
    # Get top 10 team ids by current score
    score_rows = db.session.query(
        Solve.team_id,
        func.sum(Solve.points_awarded).label('score')
    ).group_by(Solve.team_id).order_by(db.text('score DESC')).limit(10).all()
    
    top_team_ids = [r.team_id for r in score_rows if r.team_id]
    teams = {t.id: t for t in Team.query.filter(Team.id.in_(top_team_ids)).all()}
    
    # Fetch all solves for top teams in chronological order
    solves = Solve.query.filter(
        Solve.team_id.in_(top_team_ids)
    ).order_by(Solve.solved_at).all()
    
    # Fetch hint unlocks for top teams
    hint_unlocks = HintUnlock.query.filter(
        HintUnlock.team_id.in_(top_team_ids)
    ).join(Hint).all()
    
    # Build timeline events: (timestamp, team_id, delta)
    events = []
    for s in solves:
        if s.solved_at:
            events.append((s.solved_at, s.team_id, s.points_awarded or 0))
    for u in hint_unlocks:
        if u.created_at and u.hint:
            events.append((u.created_at, u.team_id, -(u.hint.cost or 0)))
    events.sort(key=lambda x: x[0])
    
    # Build cumulative series per team
    NEON_COLORS = [
        'rgba(0, 240, 255, 1)',   # cyan
        'rgba(255, 0, 128, 1)',   # pink
        'rgba(0, 255, 128, 1)',   # green
        'rgba(255, 200, 0, 1)',   # yellow
        'rgba(200, 100, 255, 1)', # purple
        'rgba(255, 80, 0, 1)',    # orange
        'rgba(0, 180, 255, 1)',   # blue
        'rgba(255, 255, 0, 1)',   # bright yellow
        'rgba(0, 255, 200, 1)',   # teal
        'rgba(255, 50, 50, 1)',   # red
    ]
    
    cumulative = {tid: 0 for tid in top_team_ids}
    
    # Collect all unique timestamps
    all_timestamps = sorted(set(e[0].isoformat() for e in events))
    
    # Build dataset per team
    datasets = []
    for i, tid in enumerate(top_team_ids):
        if tid not in teams:
            continue
        team = teams[tid]
        cumulative_score = 0
        data_points = []
        # Iterate events for this team
        team_events = [(ts, delta) for ts, t_id, delta in events if t_id == tid]
        for ts, delta in team_events:
            cumulative_score += delta
            data_points.append({'x': ts.isoformat(), 'y': cumulative_score})
        
        color = NEON_COLORS[i % len(NEON_COLORS)]
        datasets.append({
            'label': team.name,
            'data': data_points,
            'borderColor': color,
            'backgroundColor': color.replace('1)', '0.1)'),
            'borderWidth': 2,
            'pointRadius': 4,
            'pointHoverRadius': 6,
            'tension': 0.3,
            'fill': False,
        })
    
    return jsonify({'datasets': datasets})

