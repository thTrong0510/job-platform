from app.models.application import Application
from app.repositories.candidate.application_repository import ApplicationRepository
from app.models.job import Job


class ApplicationService:

    @staticmethod
    def apply(email, job_id, cv_id):
        # Kiểm tra job có tồn tại và còn OPEN không
        job = Job.query.get(job_id)
        if job is None:
            raise ValueError("Công việc không tồn tại.")
        if job.status != "OPEN":
            raise ValueError("Công việc này đã đóng, không thể ứng tuyển.")
        if job.is_hidden:
            raise ValueError("Công việc này không còn khả dụng.")

        # Kiểm tra đã ứng tuyển chưa
        if (ApplicationRepository.find_by_job_and_cv(job_id, cv_id)
                or ApplicationRepository.find_by_job_and_email(job_id, email)):
            raise ValueError("Bạn đã ứng tuyển bằng CV này rồi.")

        application = Application(
            email=email,
            job_id=job_id,
            cv_id=cv_id,
            status="PENDING"
        )

        ApplicationRepository.save(application)

    @staticmethod
    def get_candidate_history(email):
        if not email:
            return []
        return ApplicationRepository.get_by_candidate_email(email)