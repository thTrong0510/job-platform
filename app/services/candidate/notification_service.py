from app.repositories.candidate.notification_repository import NotificationRepository


class NotificationService:

    @staticmethod
    def get_notifications(user_id, page=1):
        return NotificationRepository.find_by_user_id(user_id, page=page)

    @staticmethod
    def count_unread(user_id):
        return NotificationRepository.count_unread(user_id)

    @staticmethod
    def mark_as_read(notification_id, user_id):
        notif = NotificationRepository.find_by_id_and_user(notification_id, user_id)
        if notif and not notif.is_read:
            notif.is_read = True
            NotificationRepository.save(notif)
        return notif

    @staticmethod
    def mark_all_as_read(user_id):
        NotificationRepository.mark_all_as_read(user_id)