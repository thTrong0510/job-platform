from flask import Blueprint, request, render_template

from app.common.check_empty_dict import is_filters_empty
from app.common.info import get_current_candidate
from app.services.candidate.job_service import JobService

job_bp = Blueprint('jobs', __name__, url_prefix='/jobs')

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
    options = JobService.get_filter_options()

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

@job_bp.route('/<int:job_id>', methods=['GET'])
def job_detail(job_id):
    job = JobService.get_job_detail(job_id)
    return render_template('pages/jobs/job_detail.html', job=job)