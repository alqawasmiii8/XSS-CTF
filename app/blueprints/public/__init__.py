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

