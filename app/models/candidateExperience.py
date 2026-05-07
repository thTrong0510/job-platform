from app.extensions import db
from app.models.db_types import BigIntegerPK

class CandidateExperience(db.Model):
    __tablename__ = "candidate_experiences"

    id = db.Column(BigIntegerPK, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.BigInteger, db.ForeignKey("candidates.id"))

    company = db.Column(db.String(255))
    position = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)

    candidate = db.relationship("Candidate", back_populates="experiences")