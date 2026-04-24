from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.common.decorators import login_required
from app.services.candidate.cv_upload_service import CVUploadService

cv_upload_bp = Blueprint("cv_upload", __name__, url_prefix="/candidate/cv-upload")


@cv_upload_bp.route("/", methods=["GET"])
@login_required
def index():
    user_id = session.get("user_id")
    candidate = CVUploadService.get_candidate(user_id)
    cvs = CVUploadService.get_uploaded_cvs(user_id)
    return render_template("pages/candidate/cv_upload.html", cvs=cvs, candidate=candidate)


@cv_upload_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    user_id = session.get("user_id")
    file = request.files.get("cv_file")
    title = request.form.get("title", "")

    success, message = CVUploadService.upload_cv(user_id, file, title)
    flash(message, "success" if success else "danger")

    return redirect(url_for("cv_upload.index"))


@cv_upload_bp.route("/delete/<int:cv_id>", methods=["POST"])
@login_required
def delete(cv_id):
    user_id = session.get("user_id")
    success, message = CVUploadService.delete_cv(user_id, cv_id)
    flash(message, "success" if success else "danger")

    return redirect(url_for("cv_upload.index"))