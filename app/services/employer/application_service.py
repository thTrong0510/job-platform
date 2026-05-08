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
 
# ── Luật chuyển trạng thái ────────────────────────────────────────
# ACCEPTED / REJECTED là trạng thái cuối — không thể thay đổi nữa.
# REVIEWED không thể quay lại PENDING.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "PENDING":  {"REVIEWED", "ACCEPTED", "REJECTED"},
    "REVIEWED": {"ACCEPTED", "REJECTED"},
    "ACCEPTED": set(),
    "REJECTED": set(),
}

# Delay (giây) giữa mỗi lần gọi Gemini — free tier ~15 req/min
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
    # Đếm số hồ sơ chưa có điểm
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def count_unscored(employer_id) -> int:
        return len(ApplicationRepository.get_unscored_applications(employer_id))

    # ─────────────────────────────────────────────────────────
    # Tính điểm cho hồ sơ chưa có score (employer nhấn nút)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def auto_score_unscored(employer_id):
        from app.services.employer.matching_service import MatchingService
        unscored = ApplicationRepository.get_unscored_applications(employer_id)
        count = 0
        for i, app in enumerate(unscored):
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
        raw = ApplicationRepository.get_applications_for_employer(
            employer_id=employer_id,
            keyword=filters.get("keyword", "").strip() or None,
            status=filters.get("status",  "").strip() or None,
            score_level=filters.get("score_level", "").strip() or None,
            page=page,
        )
        return ApplicationPagination(raw)

    # ─────────────────────────────────────────────────────────
    # Chi tiết 1 hồ sơ — KHÔNG tự tính điểm
    # Score chỉ được đọc từ DB nếu đã tính trước đó.
    # Employer muốn có điểm → nhấn nút "Tính điểm mới" ở trang list.
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_application_detail(application_id, employer_id):
        application = ApplicationRepository.find_by_id_for_employer(
            application_id, employer_id
        )
        if not application:
            return None

        # Chỉ đọc score từ DB — không gọi Gemini ở đây
        score = ApplicationRepository.get_score(
            application.cv.candidate_id, application.job_id
        )
        application.match_score = score   # None nếu chưa tính
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
 
        current = application.status
 
        if current == new_status:
            return False, "Trạng thái không thay đổi."
 
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if not allowed:
            return False, f"Hồ sơ đã ở trạng thái '{current}' — không thể thay đổi thêm."
        if new_status not in allowed:
            return False, f"Không thể chuyển từ '{current}' sang '{new_status}'."
 
        application.status = new_status
        ApplicationRepository.save(application)
        ApplicationService._create_notification(application, new_status)
        return True, "Đã cập nhật trạng thái thành công."
 
    @staticmethod
    def get_allowed_transitions(current_status: str) -> set[str]:
        """Trả về tập trạng thái được phép chuyển sang — dùng cho template."""
        return ALLOWED_TRANSITIONS.get(current_status, set())

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