from app.repositories.admin.admin_job_repository import AdminJobRepository


class AdminJobService:

    # ─────────────────────────────────────────────────────────
    # Danh sách job
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_jobs(filters: dict, page: int = 1):
        keyword    = filters.get("keyword",    "").strip() or None
        status     = filters.get("status",     "").strip() or None
        visibility = filters.get("visibility", "").strip()

        # is_hidden filter: "hidden" → True | "visible" → False | "" → None (tất cả)
        if visibility == "hidden":
            is_hidden = True
        elif visibility == "visible":
            is_hidden = False
        else:
            is_hidden = None

        return AdminJobRepository.get_jobs(
            keyword=keyword,
            status=status,
            is_hidden=is_hidden,
            page=page,
        )

    # ─────────────────────────────────────────────────────────
    # Stats
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_stats():
        return AdminJobRepository.count_stats()

    # ─────────────────────────────────────────────────────────
    # Chi tiết job
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_job_detail(job_id: int):
        return AdminJobRepository.find_by_id(job_id)

    # ─────────────────────────────────────────────────────────
    # Ẩn / Hiện job
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def toggle_hidden(job_id: int):
        result = AdminJobRepository.find_by_id(job_id)
        if not result:
            return False, "Không tìm thấy tin tuyển dụng."

        job, _ = result
        job.is_hidden = not job.is_hidden
        AdminJobRepository.save(job)

        action = "ẩn" if job.is_hidden else "hiện lại"
        return True, f"Đã {action} tin tuyển dụng thành công."

    # ─────────────────────────────────────────────────────────
    # Xóa job
    # Nếu đã có hồ sơ ứng tuyển → đóng tin thay vì xóa
    # Nếu chưa có → xóa hẳn
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def delete_job(job_id: int):
        result = AdminJobRepository.find_by_id(job_id)
        if not result:
            return False, "Không tìm thấy tin tuyển dụng."

        job, _ = result

        if job.applications:
            # Có hồ sơ ứng tuyển → đóng tin để bảo toàn dữ liệu
            job.status    = "CLOSED"
            job.is_hidden = True
            AdminJobRepository.save(job)
            return (
                True,
                f"Tin tuyển dụng có {len(job.applications)} hồ sơ ứng tuyển — "
                "đã đóng và ẩn tin thay vì xóa để bảo toàn dữ liệu ứng viên."
            )

        # Không có hồ sơ → xóa hẳn
        AdminJobRepository.delete(job)
        return True, "Đã xóa tin tuyển dụng thành công."