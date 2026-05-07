from app.extensions import db
from app.models.cv import CV
from app.models.candidate import Candidate
from app.models.application import Application


class CVUploadRepository:

    @staticmethod
    def find_candidate_by_user_id(user_id):
        return Candidate.query.filter_by(user_id=user_id).first()

    @staticmethod
    def save_cv(cv):
        db.session.add(cv)
        db.session.commit()
        return cv

    @staticmethod
    def find_cvs_by_candidate_id(candidate_id):
        return (
            CV.query
            .filter_by(candidate_id=candidate_id, type="UPLOAD", is_active=True)
            .order_by(CV.created_at.desc())
            .all()
        )

    @staticmethod
    def find_cv_by_id(cv_id):
        return CV.query.get(cv_id)

    @staticmethod
    def delete_cv(cv):
        db.session.delete(cv)
        db.session.commit()

    @staticmethod
    def has_applications(cv_id):
        return db.session.query(
            db.session.query(Application).filter_by(cv_id=cv_id).exists()
        ).scalar()

    @staticmethod
    def update_status(cv, is_active=False):
        try:
            cv.is_active = is_active
            db.session.add(cv)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e