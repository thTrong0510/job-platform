from . import db
from sqlalchemy import Enum
from sqlalchemy.sql import func

class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.BigInteger, primary_key=True)

    employer_id = db.Column(
        db.BigInteger,
        db.ForeignKey("employers.id", ondelete="CASCADE"),
        nullable=False
    )

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255))

    salary_min = db.Column(db.Numeric(15, 2))
    salary_max = db.Column(db.Numeric(15, 2))
    experience_required = db.Column(db.Integer)

    status = db.Column(
        Enum('OPEN', 'CLOSED', name='job_status'),
        default='OPEN'
    )

    created_at = db.Column(db.DateTime, server_default=func.now())
    end_date = db.Column(db.DateTime, server_default=func.now())

    employer = db.relationship("Employer", back_populates="jobs")
    skills = db.relationship("JobSkill", back_populates="job", cascade="all, delete")
    applications = db.relationship("Application", back_populates="job", cascade="all, delete")