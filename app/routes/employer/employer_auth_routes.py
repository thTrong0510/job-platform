from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.employer.employer_auth_service import EmployerAuthService
from app.services.employer.dashboard_service import DashboardService
from app.common.decorators import employer_required
from app.common.info import get_current_employer

employer_bp = Blueprint("employer", __name__, url_prefix="/employer")


# ─────────────────────────────────────────
# LANDING  /employer/
# ─────────────────────────────────────────
@employer_bp.route("/")
def home():
    if session.get("user_id") and session.get("user_role") == "EMPLOYER":
        return redirect(url_for("employer.dashboard"))
    return render_template("pages/employer/home.html")


# ─────────────────────────────────────────
# REGISTER  /employer/register
# ─────────────────────────────────────────
@employer_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id") and session.get("user_role") == "EMPLOYER":
        return redirect(url_for("employer.dashboard"))

    if request.method == "POST":
        data = {
            "email":               request.form.get("email", "").strip(),
            "password":            request.form.get("password", ""),
            "confirm_password":    request.form.get("confirm_password", ""),
            "company_name":        request.form.get("company_name", "").strip(),
            "location":            request.form.get("location", "").strip(),
            "company_website":     request.form.get("company_website", "").strip(),
            "company_description": request.form.get("company_description", "").strip(),
        }
        success, message = EmployerAuthService.register(data)
        flash(message, "success" if success else "danger")
        if success:
            return redirect(url_for("employer.login"))

    return render_template("pages/employer/register.html")


# ─────────────────────────────────────────
# LOGIN  /employer/login
# ─────────────────────────────────────────
@employer_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id") and session.get("user_role") == "EMPLOYER":
        return redirect(url_for("employer.dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        success, result = EmployerAuthService.login(email, password)
        if success:
            user = result
            session["user_id"]    = user.id
            session["user_email"] = user.email
            session["user_role"]  = user.role
            session["employer_id"] = user.employer.id
            return redirect(url_for("employer.dashboard"))
        else:
            flash(result, "danger")

    return render_template("pages/employer/login.html")


# ─────────────────────────────────────────
# LOGOUT  /employer/logout
# ─────────────────────────────────────────
@employer_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("employer.home"))


# ─────────────────────────────────────────
# DASHBOARD  /employer/dashboard
# ─────────────────────────────────────────
@employer_bp.route("/dashboard")
@employer_required
def dashboard():
    employer = get_current_employer()
    stats    = DashboardService.get_stats(employer.id) if employer else {}
    return render_template(
        "pages/employer/dashboard.html",
        employer=employer,
        stats=stats,
    )