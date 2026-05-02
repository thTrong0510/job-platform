from app.extensions import db
from app.models.application import Application
from app.models.cv import CV
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.recommendation import JobRecommendation
from sqlalchemy import or_, and_


def _mock_score(candidate_id, job_id):
    """
    Tạo mock score tạm thời cho đến khi có thuật toán matching thực.
    Dùng hash từ candidate_id + job_id để cho kết quả nhất quán
    (cùng cặp candidate-job luôn ra cùng 1 điểm).
    Trả về float trong khoảng 20.0 – 95.0.
    """
    seed = (candidate_id * 2654435761 ^ job_id * 2246822519) & 0xFFFFFFFF
    # Đưa về khoảng [20, 95]
    return round(20.0 + (seed % 1000) / 1000 * 75, 1)


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

        q = q.order_by(Application.applied_at.desc())

        raw_pagination = q.paginate(page=page, per_page=per_page, error_out=False)

        # ── Gán mock score vào từng application ──
        # (score_level filter được thực hiện sau khi có mock score)
        items_with_score = []
        for application, real_score in raw_pagination.items:
            if real_score is not None:
                score = float(real_score)
            else:
                score = _mock_score(
                    application.cv.candidate_id,
                    application.job_id
                )
            items_with_score.append((application, score))

        # ── Lọc theo mức phù hợp (sau khi đã có score) ──
        if score_level:
            if score_level == "high":
                items_with_score = [(a, s) for a, s in items_with_score if s >= 70]
            elif score_level == "medium":
                items_with_score = [(a, s) for a, s in items_with_score if 40 <= s < 70]
            elif score_level == "low":
                items_with_score = [(a, s) for a, s in items_with_score if s < 40]

        # Wrap lại để service dùng được (giữ interface cũ)
        raw_pagination._mock_items = items_with_score
        return raw_pagination

    # ─────────────────────────────────────────────────────────
    # Find single application (verify employer ownership)
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
    # Get match score — real nếu có, mock nếu không
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def get_score(candidate_id, job_id):
        rec = JobRecommendation.query.filter_by(
            candidate_id=candidate_id,
            job_id=job_id,
        ).first()
        if rec and rec.score is not None:
            return float(rec.score)
        # Dùng mock score cho đến khi có thuật toán thực
        return _mock_score(candidate_id, job_id)

    # ─────────────────────────────────────────────────────────
    # Save (update status)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def save(application):
        db.session.add(application)
        db.session.commit()
        return application