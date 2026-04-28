from functools import wraps
from flask import session, redirect, url_for


def employer_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("employer.login"))
        if session.get("user_role") != "EMPLOYER":
            return redirect(url_for("employer.login"))
        return f(*args, **kwargs)
    return wrapper