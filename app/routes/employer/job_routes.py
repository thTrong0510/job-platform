from datetime import datetime

from app.common.decorators import employer_required
from flask import Blueprint, request, render_template, session, flash, url_for, redirect

from app.repositories.employer.skill_repository import SkillRepository
from app.services.employer.job_service import JobService
from app.common.info import get_current_employer

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


@employer_job_bp.route("/<int:job_id>/edit", methods=["GET", "POST"])
@employer_required
def edit(job_id):
    employer_id = get_current_employer().id
    job, job_skills = JobService.get_job_detail(job_id, employer_id=employer_id)

    if not job:
        flash("Không tìm thấy tin tuyển dụng hoặc bạn không có quyền chỉnh sửa.", "danger")
        return redirect(url_for("employer_jobs.index"))

    all_skills = SkillRepository.find_all()

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

            if start_date > end_date:
                flash(
                    "Ngày kết thúc phải sau ngày bắt đầu.",
                    "danger")
                return redirect(request.referrer)
        skill_list = JobService.parse_skills(request.form)
        updated_job, error = JobService.update_job(job_id, employer_id, request.form, skill_list)

        if error:
            flash(error, "danger")
            current_skill_ids = [s.skill_id for s in job_skills]
            return render_template("pages/employer/job_create.html",
                                   job=job,
                                   all_skills=all_skills,
                                   current_skill_ids=current_skill_ids)

        flash("Cập nhật tin tuyển dụng thành công!", "success")
        return redirect(url_for("employer_jobs.detail", job_id=job.id))

    # Lấy danh sách ID kỹ năng hiện tại để hiển thị trên form edit
    current_skill_ids = [s.skill_id for s in job_skills]

    return render_template("pages/employer/job_create.html",
                           job=job,
                           all_skills=all_skills,
                           current_skill_ids=current_skill_ids)


@employer_job_bp.route("/<int:job_id>/delete", methods=["POST"])
@employer_required
def delete(job_id):
    employer_id = get_current_employer().id

    # Gọi service xử lý logic xóa
    success, message = JobService.delete_job_safely(job_id, employer_id)

    if success:
        flash(message, "success")
    else:
        # Nếu không xóa được (do có người ứng tuyển), message sẽ là lời báo lỗi
        flash(message, "warning")

    return redirect(url_for("employer_jobs.index"))