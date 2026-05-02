from flask import Blueprint, session
from app.services.auth.auth_service import AuthService
from flask import request, redirect, url_for, render_template, flash
from app.models.user import User
from app.models.candidate import Candidate
from app.services.candidate.user_service import UserService
from app.services.candidate.candidate_service import CandidateService

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        fullname = request.form.get("fullname")

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
        email    = request.form["email"]
        password = request.form["password"]
 
        user = AuthService.login(email)
 
        if not user or not user.check_password(password):
            flash("Email hoặc mật khẩu không đúng.", "danger")
            return render_template("/pages/auth/login.html")
 
        # ── Lưu session chung ──
        session["user_id"]    = user.id
        session["user_email"] = user.email
        session["user_role"]  = user.role

        if user.role == "CANDIDATE":
            # Gán candidate_id vào session nếu có
            if hasattr(user, "candidate") and user.candidate:
                session["candidate_id"] = user.candidate.id
            return redirect("/")
 
        # Fallback
        return redirect("/")
 
    return render_template("/pages/auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")