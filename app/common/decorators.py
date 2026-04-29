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
        if not session.get("user_role").__eq__("EMPLOYER"):
            return redirect(url_for("employer.login"))
        return f(*args, **kwargs)
    return wrapper