from app.models.application import Application
from app.extensions import db


class ApplicationRepository:

    @staticmethod
    def find_by_job_and_cv(job_id, cv_id):
        return Application.query.filter_by(
            job_id=job_id,
            cv_id=cv_id
        ).first()

    @staticmethod
    def save(application):
        db.session.add(application)
        db.session.commit()

    @staticmethod
    def get_by_candidate_email(email):
        return Application.query.filter_by(email=email) \
            .order_by(Application.applied_at.desc()).all()