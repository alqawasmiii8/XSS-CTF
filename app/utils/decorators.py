from functools import wraps
from flask import flash, redirect, request
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access is required for this area.', 'error')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function
