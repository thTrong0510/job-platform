from app.models.skill import Skill

class SkillRepository:
    @staticmethod
    def get_all_skills():
        return Skill.query.order_by(Skill.name.asc()).all()

    @staticmethod
    def get_by_ids(skill_ids):
        if not skill_ids:
            return []

        return Skill.query.filter(Skill.id.in_(skill_ids)).all()