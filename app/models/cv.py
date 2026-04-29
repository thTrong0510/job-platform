from app.extensions import db
from sqlalchemy import Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON

class CVTemplate(db.Model):
    __tablename__ = "cv_templates"

    id = db.Column(db.BigInteger, primary_key=True)

    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)

    description = db.Column(db.Text)
    preview_image = db.Column(db.String(500))

    html_content = db.Column(db.Text, nullable=False)
    schema_version = db.Column(db.Integer, nullable=False, default=1)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime,
                           server_default=func.now(),
                           onupdate=func.now())

    cvs = db.relationship("CV", back_populates="template")

class CV(db.Model):
    __tablename__ = "cvs"

    id = db.Column(db.BigInteger, primary_key=True)

    candidate_id = db.Column(
        db.BigInteger,
        db.ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False
    )

    template_id = db.Column(
        db.BigInteger,
        db.ForeignKey("cv_templates.id", ondelete="SET NULL"),
        nullable=True
    )

    template_version = db.Column(db.Integer)

    title = db.Column(db.String(255), nullable=False)

    type = db.Column(
        Enum('ONLINE', 'UPLOAD', name='cv_type'),
        nullable=False
    )

    # ONLINE
    content_json = db.Column(JSON)

    # UPLOAD
    file_url = db.Column(db.String(500))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.BigInteger)

    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime,
                           server_default=func.now(),
                           onupdate=func.now())

    # Relationships
    candidate = db.relationship("Candidate", back_populates="cvs")
    template = db.relationship("CVTemplate", back_populates="cvs")
    skills = db.relationship("CVSkill", back_populates="cv", cascade="all, delete")