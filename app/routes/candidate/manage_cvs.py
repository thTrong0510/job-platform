from os import abort

from flask import Blueprint, render_template, session, redirect, url_for, request, flash, render_template_string
from app.common.decorators import login_required
from app.common.info import get_current_candidate
from common.CVFormBuilder import CVFormBuilder
from services.candidate.cv_service import CVService

candidate_bp = Blueprint("candidate", __name__)

CV_TEMPLATES = [
    {
        "id": 1,
        "name": "Classic Professional",
        "description": "Simple and clean layout for professional jobs",
        "preview": "template1.png"
    },
    {
        "id": 2,
        "name": "Modern Minimal",
        "description": "Modern layout with elegant spacing",
        "preview": "template2.png"
    },
    {
        "id": 3,
        "name": "Technical Developer",
        "description": "Best for IT & Software Engineers",
        "preview": "template3.png"
    }
]


@candidate_bp.route("/templates")
def choose_template():
    return render_template("pages/candidate/choose_template.html", templates=CV_TEMPLATES)


@candidate_bp.route("/create/<int:template_id>")
def create_cv(template_id):
    selected_template = next(
        (t for t in CV_TEMPLATES if t["id"] == template_id),
        None
    )

    if not selected_template:
        return redirect(url_for("candidate.choose_template"))

    return render_template(
        "pages/cv/create_cv.html",
        template=selected_template
    )

@candidate_bp.route("/cvs", methods=["GET"])
@login_required
def manage_cvs():
    candidate = get_current_candidate()
    online_cvs, upload_cvs = CVService.get_candidate_cvs(candidate.id)
    return render_template(
        "pages/candidate/cv_dashboard.html",
        online_cvs=online_cvs,
        upload_cvs=upload_cvs
    )

@candidate_bp.route("/form-cvs", methods=["GET"])
@login_required
def form_cvs():
    return render_template("home.html")


@candidate_bp.route("/cvs", methods=["POST"])
@login_required
def upload_cv():
    return render_template("home.html")

@candidate_bp.route("/create/<int:template_id>", methods=["POST"])
@login_required
def save_online_cv(template_id):

    candidate_id = session.get("user_id")

    data = request.form.to_dict(flat=False)

    CVService.create_online_cv(
        candidate_id=candidate_id,
        template_id=template_id,
        form_data=data
    )

    flash("CV created successfully!", "success")

    return redirect(url_for("candidate.manage_cvs"))

@candidate_bp.route("/cvs/<int:cv_id>")
@login_required
def view_cv(cv_id):
    candidate_id = session.get("candidate_id")

    cv = CVService.get_cv_for_view(cv_id, candidate_id)

    # if not cv:
    #     abort(404)

    # Lấy template HTML từ DB
    html_template = cv.template.html_content

    # Parse JSON
    data = cv.content_json

    return render_template_string(
        html_template,
        data=data
    )

@candidate_bp.route("/cvs/<int:cv_id>/edit", methods=["GET"])
@login_required
def edit_cv(cv_id):
    candidate_id = session.get("candidate_id")

    cv = CVService.get_cv_for_view(cv_id, candidate_id)

    if cv.type != "ONLINE":
        return redirect(url_for("candidate.manage_cvs"))

    return render_template(
        "pages/cv/create_cv.html",
        template=cv.template,
        cv=cv,
        data=cv.content_json
    )

@candidate_bp.route("/cvs/<int:cv_id>/edit", methods=["POST"])
@login_required
def update_cv(cv_id):
    candidate_id = session.get("candidate_id")

    new_json = CVFormBuilder.build_from_request(request.form)

    CVService.update_online_cv(cv_id, candidate_id, new_json)

    return redirect(url_for("candidate.view_cv", cv_id=cv_id))

@candidate_bp.route("/cvs/<int:cv_id>/delete", methods=["POST"])
@login_required
def delete_cv(cv_id):
    candidate_id = session.get("candidate_id")

    CVService.delete_cv(cv_id, candidate_id)

    return redirect(url_for("candidate.manage_cvs"))