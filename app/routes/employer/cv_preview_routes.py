from flask import Blueprint, render_template_string, abort
from app.common.decorators import employer_required
from app.common.info import get_current_employer
from app.models.cv import CV
from app.repositories.candidate.cv_skill_repository import CVSkillRepository

employer_cv_preview_bp = Blueprint(
    "employer_cv_preview", __name__, url_prefix="/employer/cv-preview"
)


@employer_cv_preview_bp.route("/<int:cv_id>")
@employer_required
def preview(cv_id):
    """
    Render CV online bằng html_content của template + content_json.
    Employer truy cập để nhúng vào iframe trong trang application_detail.
    Chỉ cho phép xem CV type=ONLINE, không expose thông tin nhạy cảm.
    """
    cv = CV.query.get_or_404(cv_id)

    if cv.type != "ONLINE":
        abort(404)

    if not cv.template or not cv.template.html_content:
        return "<p style='font-family:sans-serif;color:#6b7280;padding:40px;text-align:center;'>Template không còn tồn tại.</p>", 200

    # Lấy danh sách skill name
    skill_ids = CVSkillRepository.get_skill_ids_by_cv(cv_id)
    from app.repositories.candidate.skill_repository import SkillRepository
    skills_objs = SkillRepository.get_by_ids(skill_ids)
    skill_names = [s.name for s in skills_objs]

    html_template = cv.template.html_content
    data = cv.content_json or {}

    return render_template_string(html_template, data=data, skills=skill_names, back_url=None)