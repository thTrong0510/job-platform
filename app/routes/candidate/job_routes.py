from flask import Blueprint, request, render_template, flash, url_for
from werkzeug.utils import redirect

from app.common.check_empty_dict import is_filters_empty
from app.common.info import get_current_candidate
from app.services.candidate.job_service import JobService
from app.common.decorators import login_required
from app.common.info import get_current_candidate, get_current_user
from app.services.candidate.application_service import ApplicationService
from app.services.candidate.cv_service import CVService

job_bp = Blueprint('jobs', __name__)

@job_bp.route('/', methods=['GET'])
def job_list():
    filters = {
        'keyword': request.args.get('keyword', ''),
        'location': request.args.get('location', ''),
        'salary_min': request.args.get('salary_min', ''),
        'salary_max': request.args.get('salary_max', ''),
        'experience': request.args.get('experience', ''),
    }
    page = request.args.get('page', 1, type=int)
    pagination = JobService.search_job(filters, page)
    job_list = JobService.search_all_job(filters)
    if is_filters_empty(filters):
        options = JobService.get_filter_options([])
    else:
        options = JobService.get_filter_options(job_list)

    candidate = get_current_candidate()

    recommended_jobs = []
    if candidate and is_filters_empty(filters):
        recommended_jobs = JobService.get_recommended_jobs(candidate.id)

    return render_template('pages/candidate/job_list.html',
                           jobs=pagination.items,
                           pagination=pagination,
                           filters=filters,
                           locations=options['locations'],
                           recommended_jobs=recommended_jobs)

@job_bp.route('/jobs/<int:job_id>', methods=['GET'])
def job_detail(job_id):
    online_cvs = []
    upload_cvs = []
    if get_current_candidate():
        candidate_id = get_current_candidate().id
        online_cvs, upload_cvs = CVService.get_candidate_cvs(candidate_id)
    job = JobService.get_job_detail(job_id)
    return render_template('pages/jobs/job_detail.html', job=job,
                           online_cvs=online_cvs,
                           upload_cvs=upload_cvs)

@job_bp.route("/jobs/apply/<int:job_id>", methods=["POST"])
@login_required
def apply_job(job_id):
    cv_id = request.form.get("cv_id")
    email = get_current_user().email
    try:
        ApplicationService.apply(
            email=email,
            job_id=job_id,
            cv_id=cv_id
        )

        flash("Ứng tuyển thành công!", "success")

    except ValueError as e:
        flash(str(e), "warning")

    return redirect(url_for("jobs.job_detail", job_id=job_id))