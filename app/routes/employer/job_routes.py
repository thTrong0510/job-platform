from app.common.decorators import employer_required
from flask import Blueprint, request, render_template, session, flash, url_for, redirect

from app.repositories.employer.skill_repository import SkillRepository
from app.services.employer.job_service import JobService
from common.info import get_current_employer

employer_job_bp = Blueprint('employer_jobs',__name__, url_prefix='/employer/jobs')

@employer_job_bp.route('/create', methods=['GET', 'POST'])
@employer_required
def create():
    employer_id = get_current_employer().id
    if not employer_id:
        flash("Unauthorized", "danger")
        return redirect(url_for('auth.login'))
    all_skills = SkillRepository.find_all()

    if request.method == 'POST':
        skill_list = JobService.parse_skills(request.form)
        job, error = JobService.create_job(employer_id, request.form, skill_list)

        if error:
            flash(error, "danger")
            return render_template("pages/employer/job_create.html",
                                   all_skills=all_skills,
                                   form=request.form,
                                   selected_skill_ids=[int(id) for id in request.form.getlist("skills[]")])

        flash("Posted successfully", "success")
        return redirect(url_for("employer_jobs.detail", job_id=job.id))

    return render_template('pages/employer/job_create.html', all_skills=all_skills)


@employer_job_bp.route("/", methods=["GET"])
@employer_required
def index():
    employer_id = get_current_employer().id
    keyword = request.args.get("keyword", "").strip()
    status = request.args.get("status", "")

    jobs = JobService.search_jobs(
        keyword=keyword or None,
        status=status or None,
        employer_id=employer_id
    )
    stats = JobService.get_stats(employer_id)

    return render_template(
        "pages/employer/job_manage.html",
        jobs=jobs,
        stats=stats,
        keyword=keyword,
        status=status
    )


@employer_job_bp.route("/<int:job_id>", methods=["GET"])
@employer_required
def detail(job_id):
    employer_id = get_current_employer().id
    job, skills = JobService.get_job_detail(job_id, employer_id=employer_id)

    if not job:
        flash("Không tìm thấy tin tuyển dụng.", "danger")
        return redirect(url_for("job.index"))

    return render_template(
        "pages/employer/job_detail.html",
        job=job,
        job_skills=skills
    )