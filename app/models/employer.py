from app.extensions import db
from sqlalchemy.sql import func

class Employer(db.Model):
    __tablename__ = "employers"

    id = db.Column(db.BigInteger, primary_key=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    company_name = db.Column(db.String(255), nullable=False)
    company_description = db.Column(db.Text)
    company_website = db.Column(db.String(255))
    location = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, server_default=func.now())

    user = db.relationship("User", back_populates="employer")
    jobs = db.relationship("Job", back_populates="employer", cascade="all, delete")