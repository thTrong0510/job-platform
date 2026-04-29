from app.extensions import db
from sqlalchemy import Enum
from sqlalchemy.sql import func

class Application(db.Model):
    __tablename__ = "applications"
    __table_args__ = (
        db.UniqueConstraint("job_id", "cv_id"),
    )

    id = db.Column(db.BigInteger, primary_key=True)

    email = db.Column(db.String(255), nullable=False)

    job_id = db.Column(
        db.BigInteger,
        db.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False
    )

    cv_id = db.Column(
        db.BigInteger,
        db.ForeignKey("cvs.id", ondelete="CASCADE"),
        nullable=False
    )

    status = db.Column(
        Enum('PENDING','REVIEWED','ACCEPTED','REJECTED', name='application_status'),
        default='PENDING'
    )

    applied_at = db.Column(db.DateTime, server_default=func.now())

    job = db.relationship("Job", back_populates="applications")
    cv = db.relationship("CV")