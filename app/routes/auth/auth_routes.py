from flask import Blueprint, session
from app.services.auth.auth_service import AuthService
from flask import request, redirect, url_for, render_template
from app import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User(
            email=email,
            role="CANDIDATE",
            status="ACTIVE"
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("/pages/auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = AuthService.login(email)

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = user.role

            if user.role == "EMPLOYER" and user.employer:
                session["employer_id"] = user.employer.id
                return redirect(url_for("employer_jobs.index"))

            return redirect("/")

        return "Login failed"

    return render_template("/pages/auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")