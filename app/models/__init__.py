from .user import User
from .team import Team, TeamMember
from .challenge import Category, Challenge, ChallengeFile, Hint, HintUnlock
from .submission import Submission, Solve, ChallengeView
from .core import Announcement, Notification, EventSettings, AdminLog, PasswordResetToken, Page

from app.extensions import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
