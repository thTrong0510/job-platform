from app.models.skill import Skill


class SkillRepository:

    @staticmethod
    def get_by_name(name):
        return Skill.query.filter_by(name=name).first()