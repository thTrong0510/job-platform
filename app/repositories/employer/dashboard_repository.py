from app.extensions import db
from app.models.job import Job
from app.models.application import Application
from sqlalchemy import func


class DashboardRepository:

    @staticmethod
    def get_stats(employer_id: int) -> dict:
        # Tổng tin tuyển dụng
        total_jobs = (
            db.session.query(func.count(Job.id))
            .filter(Job.employer_id == employer_id)
            .scalar() or 0
        )

        # Tổng hồ sơ nhận được (qua tất cả jobs của employer)
        total_applications = (
            db.session.query(func.count(Application.id))
            .join(Job, Job.id == Application.job_id)
            .filter(Job.employer_id == employer_id)
            .scalar() or 0
        )

        # Hồ sơ đang chờ duyệt
        pending = (
            db.session.query(func.count(Application.id))
            .join(Job, Job.id == Application.job_id)
            .filter(
                Job.employer_id == employer_id,
                Application.status == "PENDING",
            )
            .scalar() or 0
        )

        # Hồ sơ đã chấp nhận
        accepted = (
            db.session.query(func.count(Application.id))
            .join(Job, Job.id == Application.job_id)
            .filter(
                Job.employer_id == employer_id,
                Application.status == "ACCEPTED",
            )
            .scalar() or 0
        )

        return {
            "total_jobs":         total_jobs,
            "total_applications": total_applications,
            "pending":            pending,
            "accepted":           accepted,
        }