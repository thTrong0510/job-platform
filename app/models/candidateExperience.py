from app.extensions import db

class CandidateExperience(db.Model):
    __tablename__ = "candidate_experiences"

    id = db.Column(db.BigInteger, primary_key=True)
    candidate_id = db.Column(db.BigInteger, db.ForeignKey("candidates.id"))

    company = db.Column(db.String(255))
    position = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)

    candidate = db.relationship("Candidate", back_populates="experiences")