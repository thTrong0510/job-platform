from flask import Blueprint, session, current_app
from flask_dance.contrib.google import make_google_blueprint, google
import os
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


google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ])


from flask_dance.consumer import oauth_authorized

@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Đăng nhập Google thất bại.", "danger")
        return False

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Không lấy được thông tin từ Google.", "danger")
        return False

    info = resp.json()
    user = AuthService.login_or_register_google(info)

    if not user or not user.is_active:
        flash("Tài khoản bị khóa.", "danger")
        return False

    session["user_id"]    = user.id
    session["user_email"] = user.email
    session["user_role"]  = user.role

    if user.role == "CANDIDATE" and hasattr(user, "candidate") and user.candidate:
        session["candidate_id"] = user.candidate.id

    return False  # False = không lưu token vào DB, dùng session thôi
