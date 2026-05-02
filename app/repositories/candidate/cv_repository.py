from app.models.cv import CV
from app.extensions import db

class CVRepository:

    @staticmethod
    def save(cv):
        db.session.add(cv)
        db.session.commit()

    @staticmethod
    def get_all_by_candidate(candidate_id: int):
        return (CV.query.filter_by(candidate_id=candidate_id)
                .order_by(CV.created_at.desc())
                .all())

    @staticmethod
    def get_online_by_candidate(candidate_id: int):
        return CV.query.filter_by(
            candidate_id=candidate_id,
            type="ONLINE"
        ).order_by(CV.created_at.desc()).all()

    @staticmethod
    def get_upload_by_candidate(candidate_id: int):
        return CV.query.filter_by(
            candidate_id=candidate_id,
            type="UPLOAD"
        ).order_by(CV.created_at.desc()).all()

    @staticmethod
    def get_by_id(cv_id: int):
        return CV.query.get(cv_id)
    
    @staticmethod
    def delete(cv):
        db.session.delete(cv)
        db.session.commit()

    @staticmethod
    def exists_by_title(title):
        return CV.query.filter_by(title=title).first() is not None

    @staticmethod
    def find_by_id_and_candidate(cv_id: int, candidate_id: int):
        return CV.query.filter_by(
            id=cv_id,
            candidate_id=candidate_id,
        ).first()