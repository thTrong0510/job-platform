from app.extensions import db
from sqlalchemy.sql import func

class JobRecommendation(db.Model):
    __tablename__ = "job_recommendations"

    candidate_id = db.Column(
        db.BigInteger,
        db.ForeignKey("candidates.id", ondelete="CASCADE"),
        primary_key=True
    )

    job_id = db.Column(
        db.BigInteger,
        db.ForeignKey("jobs.id", ondelete="CASCADE"),
        primary_key=True
    )

    score = db.Column(db.Numeric(5, 2))

    created_at = db.Column(db.DateTime, server_default=func.now())

    candidate = db.relationship("Candidate")
    job = db.relationship("Job")