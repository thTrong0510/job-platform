from flask import Blueprint, render_template, redirect, url_for, request, session
from app.common.decorators import login_required
from app.services.candidate.notification_service import NotificationService

notifications_bp = Blueprint("notifications", __name__, url_prefix="/candidate/notifications")


# ─────────────────────────────────────────────────────────
# LIST  GET /candidate/notifications/
# ─────────────────────────────────────────────────────────
@notifications_bp.route("/")
@login_required
def index():
    user_id    = session.get("user_id")
    page       = request.args.get("page", 1, type=int)
    pagination = NotificationService.get_notifications(user_id, page=page)
    return render_template(
        "pages/candidate/notifications.html",
        pagination=pagination,
    )


# ─────────────────────────────────────────────────────────
# MARK ONE AS READ  POST /candidate/notifications/<id>/read
# ─────────────────────────────────────────────────────────
@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    user_id = session.get("user_id")
    NotificationService.mark_as_read(notification_id, user_id)
    # Redirect về trang trước
    next_url = request.args.get("next") or url_for("notifications.index")
    return redirect(next_url)


# ─────────────────────────────────────────────────────────
# MARK ALL AS READ  POST /candidate/notifications/read-all
# ─────────────────────────────────────────────────────────
@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    user_id = session.get("user_id")
    NotificationService.mark_all_as_read(user_id)
    return redirect(url_for("notifications.index"))