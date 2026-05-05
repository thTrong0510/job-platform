from flask import Blueprint, session, flash, url_for
from app.services.auth.auth_service import AuthService
from flask import request, redirect, render_template


admin_auth_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = AuthService.login(email)

        if user and user.check_password(password) and user.role == "ADMIN":
            session["user_id"]    = user.id
            session["user_email"] = user.email
            session["user_role"]  = user.role

            return redirect(url_for("admin_users.index"))

        else:
            flash("Incorrect email or password", "danger")
    return render_template("/pages/admin/login.html")


@admin_auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))