from app.models import Skill
from app.extensions import db


class SkillRepository:
    @staticmethod
    def find_all():
        return Skill.query.order_by(Skill.name).all()

    # @staticmethod
    # def find_by_name(name):
    #     return Skill.query.filter_by(name=name).first()
    #
    # @staticmethod
    # def find_by_id(skill_id):
    #     return Skill.query.get(skill_id)
    #
    # @staticmethod
    # def create(name):
    #     skill = Skill(name=name)
    #     db.session.add(skill)
    #     db.session.commit()
    #     return skill