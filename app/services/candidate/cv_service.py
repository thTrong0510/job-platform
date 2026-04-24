from os import abort

from app import db
from app.models.cv import CV
from app.models.skill import CVSkill
from app.models.skill import Skill
from app.models.cv import CVTemplate
import json

from common.CVFormBuilder import CVFormBuilder
from repositories.candidate.cv_repository import CVRepository


class CVService:

    @staticmethod
    def create_online_cv(candidate_id, template_id, form_data):

        template = CVTemplate.query.get(template_id)

        content_json = CVFormBuilder.build_from_request(form_data)

        new_cv = CV(
            candidate_id=candidate_id,
            template_id=template_id,
            template_version=template.schema_version,
            title=form_data.get("full_name", ["My CV"])[0],
            type="ONLINE",
            content_json=content_json
        )

        db.session.add(new_cv)
        db.session.flush()  # để lấy new_cv.id

        # Save skills nếu bạn muốn
        skills = form_data.get("skills[]", [])

        for skill_name in skills:
            skill = Skill.query.filter_by(name=skill_name).first()

            if skill:
                cv_skill = CVSkill(
                    cv_id=new_cv.id,
                    skill_id=skill.id,
                    level="INTERMEDIATE"
                )
                db.session.add(cv_skill)

        db.session.commit()

        return new_cv

    @staticmethod
    def get_candidate_cvs(candidate_id: int):

        online_cvs = CVRepository.get_online_by_candidate(candidate_id)
        upload_cvs = CVRepository.get_upload_by_candidate(candidate_id)

        return online_cvs, upload_cvs

    @staticmethod
    def get_cv_for_view(cv_id: int, candidate_id: int):
        cv = CVRepository.get_by_id(cv_id)

        if not cv:
            return None

        # if cv.candidate_id != candidate_id:
        #     abort(403)

        return cv

    @staticmethod
    def update_online_cv(cv_id: int, candidate_id: int, new_json: dict):
        cv = CVService.get_cv_for_view(cv_id, candidate_id)

        # if cv.type != "ONLINE":
        #     abort(400)

        cv.content_json = new_json
        CVRepository.save(cv)

        return cv

    @staticmethod
    def delete_cv(cv_id: int, candidate_id: int):
        cv = CVService.get_cv_for_view(cv_id, candidate_id)

        CVRepository.delete(cv)
