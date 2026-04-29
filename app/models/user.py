from app.extensions import db
from sqlalchemy import Enum
from sqlalchemy.sql import func
from werkzeug.security import check_password_hash, generate_password_hash

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    avatar_url = db.Column(db.String(500))

    role = db.Column(
        Enum('CANDIDATE', 'EMPLOYER', 'ADMIN', name='user_role'),
        nullable=False
    )

    is_active = db.Column(db.Boolean, default=True)

    status = db.Column(
        Enum('PENDING', 'ACTIVE', 'REJECTED', 'SUSPENDED', name='user_status'),
        default='PENDING'
    )

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # relationships
    candidate = db.relationship("Candidate", back_populates="user", uselist=False, cascade="all, delete")
    employer = db.relationship("Employer", back_populates="user", uselist=False, cascade="all, delete")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)