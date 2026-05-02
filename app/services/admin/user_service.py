from app.repositories.admin.user_repository import UserRepository
from app.services.admin.notification_service import AdminNotificationService

VALID_STATUSES = ['ACTIVE', 'REJECTED', 'SUSPENDED', 'PENDING']
REASON_REQUIRED = ['REJECTED', 'SUSPENDED']


class AdminUserService:

    @staticmethod
    def get_users_paginated(role=None, status=None, keyword=None, page=1, per_page=10):
        return UserRepository.get_all_users(
            role=role, status=status, keyword=keyword, page=page, per_page=per_page
        )

    @staticmethod
    def get_user_detail(user_id: int):
        user = UserRepository.find_by_id(user_id)
        if not user:
            raise ValueError("Không tìm thấy người dùng.")
        return user

    @staticmethod
    def change_status(user_id: int, new_status: str, reason: str = None) -> tuple[bool, str]:
        new_status = new_status.upper()

        if new_status not in VALID_STATUSES:
            return False, "Trạng thái không hợp lệ."

        if new_status in REASON_REQUIRED and not (reason and reason.strip()):
            return False, f"Vui lòng nhập lý do khi chuyển sang trạng thái {new_status}."

        user = UserRepository.find_by_id(user_id)
        if not user:
            return False, "Không tìm thấy người dùng."

        if user.role == 'ADMIN':
            return False, "Không thể thay đổi trạng thái tài khoản Admin."

        old_status = user.status
        if old_status == new_status:
            return False, "Trạng thái đang là giá trị này rồi."

        user.status = new_status
        UserRepository.save(user)

        if new_status in ['ACTIVE', 'REJECTED', 'SUSPENDED']:
            AdminNotificationService.notify_status_change(user, new_status, reason)

        return True, f"Đã cập nhật trạng thái."

    @staticmethod
    def get_dashboard_stats() -> dict:
        return {
            'total_pending': UserRepository.count_by_status('PENDING'),
            'total_active': UserRepository.count_by_status('ACTIVE'),
            'total_suspended': UserRepository.count_by_status('SUSPENDED'),
            'total_rejected': UserRepository.count_by_status('REJECTED'),
            'total_employers': UserRepository.count_by_role('EMPLOYER'),
            'total_candidates': UserRepository.count_by_role('CANDIDATE'),
        }