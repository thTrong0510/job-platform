from flask import Blueprint, render_template, redirect, url_for, request, flash, render_template_string
from app.common.info import get_current_candidate
from app.common.CVFormBuilder import CVFormBuilder
from app.services.candidate.candidate_service import CandidateService
from app.services.candidate.cv_service import CVService
from app.services.candidate.cv_skill_service import CVSkillService
from app.services.candidate.cv_template_service import CvTemplateService
from app.services.candidate.skill_service import SkillService
from app.common.info import get_current_user
from common.decorators import candidate_required

candidate_bp = Blueprint("candidate", __name__, url_prefix="/candidate")

@candidate_bp.route("/cvs", methods=["GET"])
@candidate_required
def manage_cvs():
    candidate = get_current_candidate()
    online_cvs, upload_cvs = CVService.get_candidate_cvs(candidate.id)
    return render_template(
        "pages/candidate/cv_dashboard.html",
        online_cvs=online_cvs,
        upload_cvs=upload_cvs
    )

@candidate_bp.route("/cv-templates")
def choose_template():
    templates = CvTemplateService.get_active_templates()
    return render_template("pages/candidate/choose_template.html", templates=templates)

@candidate_bp.route("/create-cv-by-template/<int:template_id>", methods=["GET", "POST"])
def create_cv_by_template(template_id):

    candidate_id = get_current_candidate().id
    user = get_current_user()

    if request.method == "POST":

        data = request.form.to_dict(flat=False)
        title = request.form.get("title")

        if CVService.exists_by_title(data['title'].pop() if data['title'] else ''):
            flash("CV title already exists. Please choose another title.", "danger")
            return redirect(request.referrer)

        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            from common.CloudinaryUtil import CloudinaryUtil
            avatar_url = CloudinaryUtil.upload_image(avatar_file)
        else:
            avatar_url = user.avatar_url

        CVService.create_online_cv(
            candidate_id=candidate_id,
            template_id=template_id,
            form_data=data,
            avatar_url=avatar_url,
            title=title
        )

        flash("CV created successfully!", "success")
        return redirect(url_for("candidate.manage_cvs"))

    selected_template = CvTemplateService.get_template(template_id)
    candidate = CandidateService.get_candidate_by_id(candidate_id)
    all_skills = SkillService.get_all_skills()

    if not selected_template:
        return redirect(url_for("candidate.choose_template"))

    return render_template(
        "pages/cv/create_cv.html",
        user=user,
        candidate=candidate,
        all_skills=all_skills,
        template=selected_template
    )

@candidate_bp.route("/cvs/<int:cv_id>")
@candidate_required
def view_cv(cv_id):
    cv = CVService.get_cv_for_view(cv_id)
    html_template = cv.template.html_content

    # Parse JSON
    data = cv.content_json
    skills = CVSkillService.get_skill_names_by_cv(cv.id)

    target = request.args.get('next')
    back_url = target if target else url_for("candidate.manage_cvs")

    return render_template_string(
        html_template,
        data=data,
        skills=skills,
        back_url=back_url
    )

@candidate_bp.route("/cvs/<int:cv_id>/edit", methods=["GET", "POST"])
@candidate_required
def edit_cv(cv_id):
    cv = CVService.get_cv_for_view(cv_id)

    if request.method == "POST":
        new_json = CVFormBuilder.build_from_request(request.form)
        avatar_file = request.files.get("avatar")
        skills = request.form.getlist("skills")
        title = request.form.get("title")

        if CVService.exists_by_title(title) and not title.__eq__(cv.title):
            flash("CV title already exists. Please choose another title.", "danger")
            return redirect(request.referrer)

        if avatar_file and avatar_file.filename:
            from common.CloudinaryUtil import CloudinaryUtil
            new_json["avatar"] = CloudinaryUtil.upload_image(avatar_file)
        else:
            new_json["avatar"] = cv.content_json['avatar']

        CVService.update_online_cv(cv_id, new_json, skills, title)
        return redirect(url_for("candidate.view_cv", cv_id=cv_id))

    all_skills = SkillService.get_all_skills()
    cv_skills = CVSkillService.get_by_cv(cv_id)

    if cv.type != "ONLINE":
        return redirect(url_for("candidate.manage_cvs"))

    return render_template(
        "pages/cv/create_cv.html",
        template=cv.template,
        cv=cv,
        data=cv.content_json,
        all_skills=all_skills,
        cv_skills=cv_skills
    )

@candidate_bp.route("/delete-cv/<int:cv_id>", methods=["POST"])
@candidate_required
def delete_cv(cv_id):
    CVService.delete_cv(cv_id)
    flash("CV deleted successfully!", "info")
    return redirect(url_for("candidate.manage_cvs"))

@candidate_bp.route("/", methods=["GET"])
@candidate_required
def upload_cv():
    return redirect(url_for("cv_upload.index"))