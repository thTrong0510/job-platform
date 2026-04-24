from flask import Blueprint, session
from app.services.auth.auth_service import AuthService
from flask import request, redirect, url_for, render_template
from app.models.user import User
from app.models.candidate import Candidate
from app.services.candidate.user_service import UserService
from services.candidate.candidate_service import CandidateService

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")

        user = User(
            email=email,
            role="CANDIDATE",
            status="ACTIVE"
        )
        user.set_password(password)

        UserService.save_user(user)

        candidate = Candidate(
            full_name=fullname,
            user=user
        )

        CandidateService.save_candidate(candidate)

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
            return redirect("/")

        return "Login failed"

    return render_template("/pages/auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")