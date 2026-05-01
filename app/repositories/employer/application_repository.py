"""
Bỏ mock_score, dùng score thật từ bảng job_recommendations.
Score thực tế được tính bởi MatchingService và lưu vào DB trước khi query.
"""
from app.extensions import db
from app.models.application import Application
from app.models.cv import CV
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.recommendation import JobRecommendation
from sqlalchemy import or_, and_


class ApplicationRepository:

    # ─────────────────────────────────────────────────────────
    # Paginated list for employer
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_applications_for_employer(
        employer_id,
        keyword=None,
        status=None,
        score_level=None,
        page=1,
        per_page=10,
    ):
        q = (
            db.session.query(Application, JobRecommendation.score)
            .join(Job,       Job.id       == Application.job_id)
            .join(CV,        CV.id        == Application.cv_id)
            .join(Candidate, Candidate.id == CV.candidate_id)
            .outerjoin(
                JobRecommendation,
                and_(
                    JobRecommendation.candidate_id == CV.candidate_id,
                    JobRecommendation.job_id       == Application.job_id,
                ),
            )
            .filter(Job.employer_id == employer_id)
        )

        # ── Keyword: tên ứng viên | email | tên việc làm ──
        if keyword:
            kw = f"%{keyword}%"
            q = q.filter(
                or_(
                    Candidate.full_name.ilike(kw),
                    Application.email.ilike(kw),
                    Job.title.ilike(kw),
                )
            )

        # ── Lọc theo trạng thái ──
        if status:
            q = q.filter(Application.status == status)

        # ── Lọc theo mức phù hợp (dùng score thật từ DB) ──
        if score_level == "high":
            q = q.filter(JobRecommendation.score >= 70)
        elif score_level == "medium":
            q = q.filter(
                JobRecommendation.score >= 40,
                JobRecommendation.score < 70,
            )
        elif score_level == "low":
            q = q.filter(
                or_(
                    JobRecommendation.score < 40,
                    JobRecommendation.score.is_(None),
                )
            )

        q = q.order_by(Application.applied_at.desc())
        return q.paginate(page=page, per_page=per_page, error_out=False)

    # ─────────────────────────────────────────────────────────
    # Lấy tất cả applications chưa có score (để batch calculate)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_unscored_applications(employer_id):
        return (
            db.session.query(Application)
            .join(Job,       Job.id       == Application.job_id)
            .join(CV,        CV.id        == Application.cv_id)
            .outerjoin(
                JobRecommendation,
                and_(
                    JobRecommendation.candidate_id == CV.candidate_id,
                    JobRecommendation.job_id       == Application.job_id,
                ),
            )
            .filter(
                Job.employer_id == employer_id,
                JobRecommendation.score.is_(None),
            )
            .all()
        )

    # ─────────────────────────────────────────────────────────
    # Lấy tất cả applications (để recalculate all)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_all_applications(employer_id):
        return (
            db.session.query(Application)
            .join(Job, Job.id == Application.job_id)
            .join(CV,  CV.id  == Application.cv_id)
            .filter(Job.employer_id == employer_id)
            .all()
        )

    # ─────────────────────────────────────────────────────────
    # Find single application (verify employer)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def find_by_id_for_employer(application_id, employer_id):
        return (
            db.session.query(Application)
            .join(Job, Job.id == Application.job_id)
            .filter(
                Application.id  == application_id,
                Job.employer_id == employer_id,
            )
            .first()
        )

    # ─────────────────────────────────────────────────────────
    # Get score từ DB
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_score(candidate_id, job_id) -> float | None:
        rec = JobRecommendation.query.filter_by(
            candidate_id=candidate_id,
            job_id=job_id,
        ).first()
        if rec and rec.score is not None:
            return float(rec.score)
        return None

    # ─────────────────────────────────────────────────────────
    # Save application
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def save(application):
        db.session.add(application)
        db.session.commit()
        return application