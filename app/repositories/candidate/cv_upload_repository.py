from app.extensions import db
from app.models.cv import CV
from app.models.candidate import Candidate


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
            .filter_by(candidate_id=candidate_id, type="UPLOAD")
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