from app.repositories.candidate.cv_skill_repository import CVSkillRepository
from app.repositories.candidate.skill_repository import SkillRepository


class CVSkillService:
    @staticmethod
    def get_by_cv(cv_id):
        cv_skills = CVSkillRepository.get_by_cv(cv_id)
        return cv_skills

    @staticmethod
    def delete_by_cv(cv_id):
        CVSkillRepository.delete_by_cv(cv_id)

    @staticmethod
    def get_skills_by_cv(cv_id):
        skill_ids = CVSkillRepository.get_skill_ids_by_cv(cv_id)

        if not skill_ids:
            return []

        skills = SkillRepository.get_by_ids(skill_ids)

        return skills

    @staticmethod
    def get_skill_names_by_cv(cv_id):
        skills = CVSkillService.get_skills_by_cv(cv_id)

        return [skill.name for skill in skills]
