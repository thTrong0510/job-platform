from flask import Blueprint, render_template, session, redirect, url_for
from app.services.candidate.application_service import ApplicationService
from common.info import get_current_user

application_bp = Blueprint('application', __name__)


@application_bp.route('/my-applications')
def application_history():
    # Lấy email từ session
    user_email = get_current_user().email

    if not user_email:
        return redirect(url_for('auth.login'))

    applications = ApplicationService.get_candidate_history(user_email)

    return render_template(
        "pages/candidate/application_history.html",
        applications=applications
    )