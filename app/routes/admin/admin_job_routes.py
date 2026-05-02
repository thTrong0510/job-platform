"""
app/routes/admin/admin_job_routes.py
"""
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, abort
)
from app.common.decorators import admin_required
from app.services.admin.admin_job_service import AdminJobService

admin_jobs_bp = Blueprint("admin_jobs", __name__, url_prefix="/admin/jobs")


# ─────────────────────────────────────────────────────────
# LIST  GET /admin/jobs/
# ─────────────────────────────────────────────────────────
@admin_jobs_bp.route("/")
@admin_required
def index():
    filters = {
        "keyword":    request.args.get("keyword",    "").strip(),
        "status":     request.args.get("status",     "").strip(),
        "visibility": request.args.get("visibility", "").strip(),
    }
    page       = request.args.get("page", 1, type=int)
    pagination = AdminJobService.get_jobs(filters, page)
    stats      = AdminJobService.get_stats()

    return render_template(
        "pages/admin/jobs.html",
        pagination=pagination,
        filters=filters,
        stats=stats,
    )


# ─────────────────────────────────────────────────────────
# DETAIL  GET /admin/jobs/<job_id>
# ─────────────────────────────────────────────────────────
@admin_jobs_bp.route("/<int:job_id>")
@admin_required
def detail(job_id):
    result = AdminJobService.get_job_detail(job_id)
    if not result:
        flash("Không tìm thấy tin tuyển dụng.", "danger")
        return redirect(url_for("admin_jobs.index"))

    job, employer = result
    return render_template(
        "pages/admin/job_detail.html",
        job=job,
        employer=employer,
    )


# ─────────────────────────────────────────────────────────
# TOGGLE HIDDEN  POST /admin/jobs/<job_id>/toggle-hidden
# ─────────────────────────────────────────────────────────
@admin_jobs_bp.route("/<int:job_id>/toggle-hidden", methods=["POST"])
@admin_required
def toggle_hidden(job_id):
    back_to = request.form.get("back_to", "list")
    success, message = AdminJobService.toggle_hidden(job_id)
    flash(message, "success" if success else "danger")

    if back_to == "detail":
        return redirect(url_for("admin_jobs.detail", job_id=job_id))
    return redirect(url_for("admin_jobs.index"))


# ─────────────────────────────────────────────────────────
# DELETE  POST /admin/jobs/<job_id>/delete
# ─────────────────────────────────────────────────────────
@admin_jobs_bp.route("/<int:job_id>/delete", methods=["POST"])
@admin_required
def delete(job_id):
    success, message = AdminJobService.delete_job(job_id)
    flash(message, "success" if success else "danger")
    return redirect(url_for("admin_jobs.index"))