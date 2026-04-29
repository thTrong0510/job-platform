from app.extensions import db
from sqlalchemy.sql import func


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.BigInteger, primary_key=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    title   = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, server_default=func.now())

    user = db.relationship("User")
