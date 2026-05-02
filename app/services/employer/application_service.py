from app.repositories.employer.application_repository import ApplicationRepository
from app.repositories.candidate.notification_repository import NotificationRepository
from app.models.notification import Notification


# ── Nội dung thông báo theo từng trạng thái ──────────────────────
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


class ApplicationPagination:
    """
    Wrap Flask-SQLAlchemy pagination.
    Repository gán _mock_items = list of (application, score).
    """

    def __init__(self, raw_pagination):
        self._p = raw_pagination

        # Dùng _mock_items nếu repository đã xử lý score + filter
        source = getattr(raw_pagination, '_mock_items', None)
        if source is None:
            # fallback: items là list tuple (application, score) thô
            source = [(a, s) for a, s in raw_pagination.items]

        self.items = []
        for application, score in source:
            application.match_score = score
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
    # Danh sách hồ sơ ứng tuyển
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_applications(employer_id, filters: dict, page: int = 1):
        keyword     = filters.get("keyword", "").strip() or None
        status      = filters.get("status", "").strip() or None
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

        score = ApplicationRepository.get_score(
            application.cv.candidate_id, application.job_id
        )
        application.match_score = score
        return application

    # ─────────────────────────────────────────────────────────
    # Cập nhật trạng thái + gửi thông báo hệ thống
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

        old_status = application.status
        if old_status == new_status:
            return False, "Trạng thái không thay đổi."

        application.status = new_status
        ApplicationRepository.save(application)

        ApplicationService._create_notification(application, new_status)

        return True, f"Đã cập nhật trạng thái thành công."

    # ─────────────────────────────────────────────────────────
    # Tạo Notification record
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _create_notification(application, new_status):
        template = STATUS_MESSAGES.get(new_status)
        if not template:
            return

        company   = application.job.employer.company_name
        job_title = application.job.title
        cv_title  = application.cv.title

        notification = Notification(
            user_id=application.cv.candidate.user_id,
            title=template["title"],
            message=template["message"].format(
                company=company,
                job_title=job_title,
                cv_title=cv_title,
            ),
        )
        NotificationRepository.save(notification)