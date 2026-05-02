from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from app.common.decorators import employer_required
from app.common.info import get_current_employer
from app.services.employer.application_service import ApplicationService

employer_applications_bp = Blueprint(
    "employer_applications", __name__, url_prefix="/employer/applications"
)


# ─────────────────────────────────────────────────────────
# LIST  GET /employer/applications/
# ─────────────────────────────────────────────────────────
@employer_applications_bp.route("/")
@employer_required
def index():
    employer = get_current_employer()

    filters = {
        "keyword":     request.args.get("keyword",     "").strip(),
        "status":      request.args.get("status",      "").strip(),
        "score_level": request.args.get("score_level", "").strip(),
    }
    page       = request.args.get("page", 1, type=int)
    pagination = ApplicationService.get_applications(employer.id, filters, page)

    return render_template(
        "pages/employer/applications.html",
        employer=employer,
        pagination=pagination,
        filters=filters,
    )


# ─────────────────────────────────────────────────────────
# DETAIL  GET /employer/applications/<id>
# Tự động chuyển PENDING → REVIEWED khi mở trang xem
# ─────────────────────────────────────────────────────────
@employer_applications_bp.route("/<int:application_id>")
@employer_required
def detail(application_id):
    employer    = get_current_employer()
    application = ApplicationService.get_application_detail(application_id, employer.id)

    if not application:
        abort(404)

    # ── Auto REVIEWED: chỉ chuyển khi đang ở PENDING ──
    if application.status == "PENDING":
        success, _ = ApplicationService.update_status(
            application_id, employer.id, "REVIEWED"
        )
        if success:
            # Reload để lấy status mới
            application = ApplicationService.get_application_detail(
                application_id, employer.id
            )

    return render_template(
        "pages/employer/application_detail.html",
        employer=employer,
        application=application,
    )


# ─────────────────────────────────────────────────────────
# UPDATE STATUS  POST /employer/applications/<id>/status
# ─────────────────────────────────────────────────────────
@employer_applications_bp.route("/<int:application_id>/status", methods=["POST"])
@employer_required
def update_status(application_id):
    employer   = get_current_employer()
    new_status = request.form.get("status", "").strip()
    back_to    = request.form.get("back_to", "detail")

    success, message = ApplicationService.update_status(
        application_id, employer.id, new_status
    )
    flash(message, "success" if success else "danger")

    if back_to == "list":
        return redirect(url_for("employer_applications.index"))
    return redirect(
        url_for("employer_applications.detail", application_id=application_id)
    )