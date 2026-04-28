from . import db
from sqlalchemy.sql import func

class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.BigInteger, primary_key=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    current_title = db.Column(db.String(255))
    total_experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    location = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    user = db.relationship("User", back_populates="candidate", uselist=False)
    cvs = db.relationship("CV", back_populates="candidate", cascade="all, delete")
    skills = db.relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    experiences = db.relationship(
        "CandidateExperience",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy=False
    )
    educations = db.relationship(
        "CandidateEducation",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy=False)