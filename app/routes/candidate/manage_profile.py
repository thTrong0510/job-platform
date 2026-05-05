from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.services.candidate.candidate_service import CandidateService
from app.common.decorators import candidate_required
from app.common.info import get_current_candidate
from app.services.candidate.skill_service import SkillService
from app.services.candidate.user_service import UserService
from datetime import datetime

from app.common.ProfileFromBuilder import parse_nested_form

candidate_profile_bp = Blueprint("candidate_profile", __name__, url_prefix="/candidate")

@candidate_profile_bp.route("/profile", methods=["GET"])
@candidate_required
def view_profile():
    candidate_id = get_current_candidate().id

    candidate = CandidateService.get_candidate_profile(candidate_id)

    return render_template(
        "pages/candidate/profile.html",
        candidate=candidate
    )

@candidate_profile_bp.route("/profile/edit", methods=["GET", "POST"])
@candidate_required
def edit_profile():
    candidate_id = get_current_candidate().id
    form_data = request.form
    section = form_data.get('section')

    if request.method == "POST":

        if section in ['experiences', 'all']:
            experiences = parse_nested_form(form_data, 'experiences')
            for exp in experiences:
                start_str = exp.get('start_date')
                end_str = exp.get('end_date')

                if start_str and end_str:
                    start_date = datetime.strptime(start_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_str, '%Y-%m-%d')

                    if start_date > end_date:
                        flash(
                            f"Lỗi tại Kinh nghiệm ({exp.get('company', 'N/A')}): Ngày kết thúc phải sau ngày bắt đầu.",
                            "danger")
                        return redirect(request.referrer)

        if section in ['educations', 'all']:
            educations = parse_nested_form(form_data, 'educations')
            for edu in educations:
                start_str = edu.get('start_date')
                end_str = edu.get('end_date')

                if start_str and end_str:
                    start_date = datetime.strptime(start_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_str, '%Y-%m-%d')

                    if start_date > end_date:
                        flash(f"Lỗi tại Học vấn ({edu.get('school', 'N/A')}): Ngày kết thúc phải sau ngày bắt đầu.",
                              "danger")
                        return redirect(request.referrer)

        CandidateService.update_profile(candidate_id, request.form)
        return redirect(url_for("candidate_profile.view_profile"))

    section = request.args.get("section", "basic")
    candidate = CandidateService.get_full_profile(candidate_id)
    all_skills = SkillService.get_all_skills()

    if not candidate:
        return redirect(url_for("jobs.job_list"))

    return render_template(
        "pages/candidate/profile_edit.html",
        candidate=candidate,
        all_skills=all_skills,
        section=section
    )

@candidate_profile_bp.route("/upload-avatar", methods=["POST"])
@candidate_required
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