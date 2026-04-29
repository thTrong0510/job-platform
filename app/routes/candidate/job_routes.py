from flask import Blueprint, request, render_template

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

    return render_template('pages/candidate/job_list.html',
                           jobs=pagination.items,
                           pagination=pagination,
                           filters=filters,
                           locations=options['locations'])

@job_bp.route('/<int:job_id>', methods=['GET'])
def job_detail(job_id):
    job = JobService.get_job_detail(job_id)
    return render_template('pages/jobs/job_detail.html', job=job)