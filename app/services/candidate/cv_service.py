from app.extensions import db
from app.models.cv import CV
from app.models.cv import CVTemplate

from app.common.CVFormBuilder import CVFormBuilder
from app.repositories.candidate.cv_repository import CVRepository
from app.repositories.candidate.cv_skill_repository import CVSkillRepository


class CVService:

    @staticmethod
    def create_online_cv(candidate_id, template_id, form_data, avatar_url, title):

        template = CVTemplate.query.get(template_id)

        content_json = CVFormBuilder.build_from_request(form_data)
        content_json['avatar'] = avatar_url

        new_cv = CV(
            candidate_id=candidate_id,
            template_id=template_id,
            template_version=template.schema_version,
            title=title,
            type="ONLINE",
            content_json=content_json
        )

        db.session.add(new_cv)
        db.session.flush()  # để lấy new_cv.id

        # Save skills nếu bạn muốn
        skills = form_data.get("skills[]", [])

        CVSkillRepository.add_cv_skill(new_cv.id, skills)

        return new_cv

    @staticmethod
    def get_candidate_cvs(candidate_id: int):

        online_cvs = CVRepository.get_online_by_candidate(candidate_id)
        upload_cvs = CVRepository.get_upload_by_candidate(candidate_id)

        return online_cvs, upload_cvs

    @staticmethod
    def get_cv_for_view(cv_id: int):
        cv = CVRepository.get_by_id(cv_id)

        if not cv:
            return None

        return cv

    @staticmethod
    def update_online_cv(cv_id: int, new_json: dict, skills: list, title: str):
        cv = CVService.get_cv_for_view(cv_id)

        cv.content_json = new_json
        cv.title = title
        CVRepository.save(cv)

        CVSkillRepository.delete_by_cv(cv_id)
        CVSkillRepository.add_cv_skill(cv_id, skills)

        return cv

    @staticmethod
    def delete_cv(cv_id: int):
        cv = CVService.get_cv_for_view(cv_id)

        CVRepository.delete(cv)

    @staticmethod
    def exists_by_title(title: str):
        return CVRepository.exists_by_title(title)
