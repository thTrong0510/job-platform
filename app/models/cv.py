from . import db
from sqlalchemy import Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON

class CV(db.Model):
    __tablename__ = "cvs"

    id = db.Column(db.BigInteger, primary_key=True)

    candidate_id = db.Column(
        db.BigInteger,
        db.ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False
    )

    title = db.Column(db.String(255), nullable=False)

    type = db.Column(
        Enum('ONLINE', 'UPLOAD', name='cv_type'),
        nullable=False
    )

    content_json = db.Column(JSON)

    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    candidate = db.relationship("Candidate", back_populates="cvs")
    files = db.relationship("CVFile", back_populates="cv", cascade="all, delete")
    skills = db.relationship("CVSkill", back_populates="cv", cascade="all, delete")


class CVFile(db.Model):
    __tablename__ = "cv_files"

    id = db.Column(db.BigInteger, primary_key=True)

    cv_id = db.Column(
        db.BigInteger,
        db.ForeignKey("cvs.id", ondelete="CASCADE"),
        nullable=False
    )

    file_url = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.BigInteger)

    uploaded_at = db.Column(db.DateTime, server_default=func.now())

    cv = db.relationship("CV", back_populates="files")