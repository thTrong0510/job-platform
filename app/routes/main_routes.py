from flask import Blueprint, render_template, session
from app.common.decorators import login_required
from app.repositories.user_repository import UserRepository

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
@login_required
def home():
    user_id = session.get("user_id")
    user = UserRepository.find_by_id(user_id)
    session["user_email"] = user.email

    return render_template("home.html")