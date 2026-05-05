from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper

def employer_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("employer.login"))
        if not session.get("user_role") == "EMPLOYER":
            return redirect(url_for("employer.login"))
        return f(*args, **kwargs)
    return wrapper

def candidate_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if not session.get("user_role") == "CANDIDATE":
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or not session.get('user_role') == "ADMIN":
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return wrapper