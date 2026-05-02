from app.models.application import Application
from app.repositories.candidate.application_repository import ApplicationRepository


class ApplicationService:

    @staticmethod
    def apply(email, job_id, cv_id):

        existing = ApplicationRepository.find_by_job_and_cv(job_id, cv_id)

        if existing:
            raise ValueError("Bạn đã ứng tuyển bằng CV này rồi.")

        application = Application(
            email=email,
            job_id=job_id,
            cv_id=cv_id,
            status="PENDING"
        )

        ApplicationRepository.save(application)