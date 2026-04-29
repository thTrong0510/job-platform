from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.services.candidate.candidate_service import CandidateService
from app.common.decorators import login_required
from app.common.info import get_current_candidate
from app.services.candidate.skill_service import SkillService
from app.services.candidate.user_service import UserService

candidate_profile_bp = Blueprint("candidate_profile", __name__, url_prefix="/candidate")

@candidate_profile_bp.route("/profile", methods=["GET"])
@login_required
def view_profile():
    candidate_id = get_current_candidate().id

    candidate = CandidateService.get_candidate_profile(candidate_id)

    return render_template(
        "pages/candidate/profile.html",
        candidate=candidate
    )

@candidate_profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    candidate_id = get_current_candidate().id

    if request.method == "POST":
        CandidateService.update_profile(candidate_id, request.form)
        return redirect(url_for("candidate_profile.view_profile"))

    section = request.args.get("section", "basic")
    candidate = CandidateService.get_full_profile(candidate_id)
    all_skills = SkillService.get_all_skills()

    if not candidate:
        return redirect(url_for("main.home"))

    return render_template(
        "pages/candidate/profile_edit.html",
        candidate=candidate,
        all_skills=all_skills,
        section=section
    )

@candidate_profile_bp.route("/upload-avatar", methods=["POST"])
@login_required
def upload_avatar():
    file = request.files.get("avatar")
    candidate_id = get_current_candidate().id

    if not file:
        return redirect(url_for("candidate_profile.view_profile"))

    try:
        UserService.update_avatar(candidate_id, file)
    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("candidate_profile.view_profile"))
