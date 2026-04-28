from models.skill import Skill


class CandidateRepository:
    @staticmethod
    def get_all_skills():
        return Skill.query.order_by(Skill.name.asc()).all()