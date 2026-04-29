from app.repositories.candidate.skill_repository import SkillRepository


class SkillService:
    @staticmethod
    def get_all_skills():
        return SkillRepository.get_all_skills()