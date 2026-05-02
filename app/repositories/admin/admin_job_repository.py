from app.extensions import db
from app.models.job import Job
from app.models.employer import Employer
from sqlalchemy import or_


class AdminJobRepository:

    # ─────────────────────────────────────────────────────────
    # Danh sách job (có filter + paginate)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_jobs(keyword=None, status=None, is_hidden=None, page=1, per_page=15):
        q = (
            db.session.query(Job, Employer)
            .join(Employer, Employer.id == Job.employer_id)
        )

        if keyword:
            kw = f"%{keyword}%"
            q = q.filter(
                or_(
                    Job.title.ilike(kw),
                    Employer.company_name.ilike(kw),
                    Job.location.ilike(kw),
                )
            )

        if status:
            q = q.filter(Job.status == status)

        if is_hidden is not None:
            q = q.filter(Job.is_hidden == is_hidden)

        q = q.order_by(Job.created_at.desc())
        return q.paginate(page=page, per_page=per_page, error_out=False)

    # ─────────────────────────────────────────────────────────
    # Đếm theo trạng thái (cho stats)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def count_stats():
        total    = db.session.query(db.func.count(Job.id)).scalar() or 0
        open_    = db.session.query(db.func.count(Job.id)).filter(Job.status == "OPEN",   Job.is_hidden == False).scalar() or 0
        closed   = db.session.query(db.func.count(Job.id)).filter(Job.status == "CLOSED", Job.is_hidden == False).scalar() or 0
        hidden   = db.session.query(db.func.count(Job.id)).filter(Job.is_hidden == True).scalar() or 0
        return {
            "total":  total,
            "open":   open_,
            "closed": closed,
            "hidden": hidden,
        }

    # ─────────────────────────────────────────────────────────
    # Tìm job theo id
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def find_by_id(job_id):
        return (
            db.session.query(Job, Employer)
            .join(Employer, Employer.id == Job.employer_id)
            .filter(Job.id == job_id)
            .first()
        )

    # ─────────────────────────────────────────────────────────
    # Lưu thay đổi
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def save(job):
        db.session.add(job)
        db.session.commit()
        return job

    # ─────────────────────────────────────────────────────────
    # Xóa job
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def delete(job):
        db.session.delete(job)
        db.session.commit()