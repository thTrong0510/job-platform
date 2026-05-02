# Scoring chỉ chạy khi employer chủ động nhấn nút "Tính điểm".

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, abort
)
from app.common.decorators import employer_required
from app.common.info import get_current_employer
from app.services.employer.application_service import ApplicationService

employer_applications_bp = Blueprint(
    "employer_applications", __name__, url_prefix="/employer/applications"
)


# ─────────────────────────────────────────────────────────
# LIST  GET /employer/applications/
# KHÔNG tự động gọi Gemini — tránh vượt quota
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

    # Đếm số hồ sơ chưa có điểm để hiện gợi ý cho employer
    unscored_count = ApplicationService.count_unscored(employer.id)

    return render_template(
        "pages/employer/applications.html",
        employer=employer,
        pagination=pagination,
        filters=filters,
        unscored_count=unscored_count,
    )


# ─────────────────────────────────────────────────────────
# DETAIL  GET /employer/applications/<id>
# Tự động chuyển PENDING → REVIEWED khi mở trang xem
# ─────────────────────────────────────────────────────────
@employer_applications_bp.route("/<int:application_id>")
@employer_required
def detail(application_id):
    employer    = get_current_employer()
    application = ApplicationService.get_application_detail(
        application_id, employer.id
    )

    if not application:
        abort(404)

    # Auto REVIEWED khi nhà tuyển dụng mở xem lần đầu
    if application.status == "PENDING":
        success, _ = ApplicationService.update_status(
            application_id, employer.id, "REVIEWED"
        )
        if success:
            flash('Hồ sơ đã được chuyển sang trạng thái "Đang xem xét".', "info")
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


# ─────────────────────────────────────────────────────────
# SCORE NEW  POST /employer/applications/score-new
# Chỉ tính điểm cho hồ sơ CHƯA có score (tiết kiệm quota)
# ─────────────────────────────────────────────────────────
@employer_applications_bp.route("/score-new", methods=["POST"])
@employer_required
def score_new():
    employer = get_current_employer()

    try:
        count = ApplicationService.auto_score_unscored(employer.id)
        if count > 0:
            flash(f"Đã tính điểm thành công cho {count} hồ sơ mới.", "success")
        else:
            flash("Tất cả hồ sơ đã có điểm, không cần tính lại.", "info")
    except Exception as e:
        flash(f"Lỗi khi tính điểm: {e}", "danger")

    return redirect(url_for("employer_applications.index"))


# ─────────────────────────────────────────────────────────
# RECALCULATE ALL  POST /employer/applications/recalculate
# Force tính lại TOÀN BỘ score (tốn nhiều quota hơn)
# ─────────────────────────────────────────────────────────
@employer_applications_bp.route("/recalculate", methods=["POST"])
@employer_required
def recalculate():
    employer = get_current_employer()

    try:
        count = ApplicationService.recalculate_all(employer.id)
        flash(f"Đã tính lại điểm phù hợp cho {count} hồ sơ thành công.", "success")
    except Exception as e:
        flash(f"Lỗi khi tính lại điểm: {e}", "danger")

    return redirect(url_for("employer_applications.index"))
