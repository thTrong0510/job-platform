from app.models.notification import Notification
from app.extensions import db


class NotificationRepository:

    @staticmethod
    def find_by_user_id(user_id, page=1, per_page=15):
        return (
            Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @staticmethod
    def count_unread(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def find_by_id_and_user(notification_id, user_id):
        return Notification.query.filter_by(id=notification_id, user_id=user_id).first()

    @staticmethod
    def mark_all_as_read(user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
        db.session.commit()

    @staticmethod
    def save(notification):
        db.session.add(notification)
        db.session.commit()
        return notification