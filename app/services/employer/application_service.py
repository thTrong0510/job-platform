# Thêm count_unscored() để hiện số hồ sơ chưa có điểm trên UI
# Thêm delay giữa các Gemini call để tránh 429 rate limit

import time

from app.repositories.employer.application_repository import ApplicationRepository
from app.repositories.candidate.notification_repository import NotificationRepository
from app.models.notification import Notification

STATUS_MESSAGES = {
    "REVIEWED": {
        "title": "Hồ sơ của bạn đã được xem xét",
        "message": (
            'Nhà tuyển dụng <strong>{company}</strong> đã xem xét hồ sơ CV '
            '"<strong>{cv_title}</strong>" mà bạn ứng tuyển vào vị trí '
            '"<strong>{job_title}</strong>". Vui lòng chờ thông tin tiếp theo.'
        ),
    },
    "ACCEPTED": {
        "title": "🎉 Chúc mừng! Hồ sơ của bạn được chấp nhận",
        "message": (
            'Nhà tuyển dụng <strong>{company}</strong> đã chấp nhận hồ sơ CV '
            '"<strong>{cv_title}</strong>" cho vị trí '
            '"<strong>{job_title}</strong>". '
            "Họ sẽ liên hệ với bạn sớm để trao đổi thêm."
        ),
    },
    "REJECTED": {
        "title": "Thông báo về kết quả ứng tuyển",
        "message": (
            'Rất tiếc, nhà tuyển dụng <strong>{company}</strong> đã không chọn '
            'hồ sơ CV "<strong>{cv_title}</strong>" của bạn cho vị trí '
            '"<strong>{job_title}</strong>". '
            "Chúc bạn thành công ở những cơ hội tiếp theo!"
        ),
    },
    "PENDING": {
        "title": "Hồ sơ đã được đặt lại trạng thái chờ",
        "message": (
            'Hồ sơ CV "<strong>{cv_title}</strong>" của bạn tại vị trí '
            '"<strong>{job_title}</strong>" đã được đặt lại trạng thái chờ duyệt.'
        ),
    },
}

VALID_STATUSES = {"PENDING", "REVIEWED", "ACCEPTED", "REJECTED"}

# Delay (giây) giữa mỗi lần gọi Gemini để tránh vượt rate limit
# Free tier: 15 req/min → cần ít nhất 4s/req để an toàn
_GEMINI_CALL_DELAY = 4.0


class ApplicationPagination:
    """Wrap Flask-SQLAlchemy pagination, gắn match_score vào mỗi application."""

    def __init__(self, raw_pagination):
        self._p = raw_pagination
        self.items = []

        for application, score in raw_pagination.items:
            application.match_score = float(score) if score is not None else None
            self.items.append(application)

        self.total    = raw_pagination.total
        self.pages    = raw_pagination.pages
        self.page     = raw_pagination.page
        self.has_prev = raw_pagination.has_prev
        self.has_next = raw_pagination.has_next

    def iter_pages(self, **kwargs):
        return self._p.iter_pages(**kwargs)


class ApplicationService:

    # ─────────────────────────────────────────────────────────
    # Đếm số hồ sơ chưa có điểm (dùng hiển thị gợi ý trên UI)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def count_unscored(employer_id) -> int:
        return len(ApplicationRepository.get_unscored_applications(employer_id))

    # ─────────────────────────────────────────────────────────
    # Tính điểm cho application chưa có score
    # Có delay giữa các call để tránh 429
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def auto_score_unscored(employer_id):
        """
        Tìm tất cả application chưa có score → gọi Gemini → lưu DB.
        Có delay giữa các call để không vượt free-tier rate limit.
        Trả về số lượng application vừa được tính thành công.
        """
        from app.services.employer.matching_service import MatchingService

        unscored = ApplicationRepository.get_unscored_applications(employer_id)
        count = 0
        for i, app in enumerate(unscored):
            # Delay trước mỗi call (trừ call đầu tiên)
            if i > 0:
                time.sleep(_GEMINI_CALL_DELAY)
            score = MatchingService.get_or_calculate(app)
            if score is not None:
                count += 1
        return count

    # ─────────────────────────────────────────────────────────
    # Danh sách hồ sơ (score đọc từ DB, không gọi Gemini)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_applications(employer_id, filters: dict, page: int = 1):
        keyword     = filters.get("keyword", "").strip() or None
        status      = filters.get("status",  "").strip() or None
        score_level = filters.get("score_level", "").strip() or None

        raw = ApplicationRepository.get_applications_for_employer(
            employer_id=employer_id,
            keyword=keyword,
            status=status,
            score_level=score_level,
            page=page,
        )
        return ApplicationPagination(raw)

    # ─────────────────────────────────────────────────────────
    # Chi tiết 1 hồ sơ
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_application_detail(application_id, employer_id):
        application = ApplicationRepository.find_by_id_for_employer(
            application_id, employer_id
        )
        if not application:
            return None

        # Lấy score từ DB (đã tính sẵn)
        score = ApplicationRepository.get_score(
            application.cv.candidate_id, application.job_id
        )
        # Nếu chưa có (vào thẳng từ URL) → tính ngay cho 1 hồ sơ này thôi
        if score is None:
            from app.services.employer.matching_service import MatchingService
            score = MatchingService.get_or_calculate(application)

        application.match_score = score
        return application

    # ─────────────────────────────────────────────────────────
    # Cập nhật trạng thái + thông báo
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def update_status(application_id, employer_id, new_status):
        if new_status not in VALID_STATUSES:
            return False, "Trạng thái không hợp lệ."

        application = ApplicationRepository.find_by_id_for_employer(
            application_id, employer_id
        )
        if not application:
            return False, "Không tìm thấy hồ sơ hoặc bạn không có quyền."

        if application.status == new_status:
            return False, "Trạng thái không thay đổi."

        application.status = new_status
        ApplicationRepository.save(application)
        ApplicationService._create_notification(application, new_status)

        return True, "Đã cập nhật trạng thái thành công."

    # ─────────────────────────────────────────────────────────
    # Tạo notification cho ứng viên
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _create_notification(application, new_status):
        template = STATUS_MESSAGES.get(new_status)
        if not template:
            return

        notification = Notification(
            user_id=application.cv.candidate.user_id,
            title=template["title"],
            message=template["message"].format(
                company=application.job.employer.company_name,
                job_title=application.job.title,
                cv_title=application.cv.title,
            ),
        )
        NotificationRepository.save(notification)