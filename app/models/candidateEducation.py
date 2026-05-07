from app.extensions import db
from app.models.db_types import BigIntegerPK

class CandidateEducation(db.Model):
    __tablename__ = "candidate_educations"

    id = db.Column(BigIntegerPK, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.BigInteger, db.ForeignKey("candidates.id"))

    school = db.Column(db.String(255))
    degree = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    candidate = db.relationship("Candidate", back_populates="educations")