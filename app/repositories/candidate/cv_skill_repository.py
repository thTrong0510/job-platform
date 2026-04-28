from app.models.skill import CVSkill
from app import db


class CVSkillRepository:

    @staticmethod
    def add_cv_skill(cv_id, skill_ids):
        for skill_id in skill_ids:
            cv_skill = CVSkill(
                cv_id=cv_id,
                skill_id=int(skill_id)
            )
            db.session.add(cv_skill)

        db.session.commit()

    @staticmethod
    def get_by_cv(cv_id):
        return CVSkill.query.filter_by(cv_id=cv_id).all()

    @staticmethod
    def delete_by_cv(cv_id):
        CVSkill.query.filter_by(cv_id=cv_id).delete()
        db.session.commit()

    @staticmethod
    def get_skill_ids_by_cv(cv_id):
        results = (
            db.session.query(CVSkill.skill_id)
            .filter(CVSkill.cv_id == cv_id)
            .all()
        )

        return [r[0] for r in results]