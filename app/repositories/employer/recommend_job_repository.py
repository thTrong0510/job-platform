from app.models.recommendation import JobRecommendation
from app.extensions import db


class RecommendJobRepository:
    @staticmethod
    def save(candidate_id, job_id):
        rec = JobRecommendation(
            candidate_id=candidate_id,
            job_id=job_id,
        )
        db.session.add(rec)
        db.session.commit()