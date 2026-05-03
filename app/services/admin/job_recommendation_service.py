from flask import current_app

from app.repositories.candidate.candidate_repository import CandidateRepository

from app.services.admin.notification_service import MailService
from app.services.candidate.job_service import JobService


class JobRecommendationService:

    @staticmethod
    def send_weekly_recommendations():
        candidates = CandidateRepository.find_all_candidate()
        success_count = 0
        for candidate in candidates:
            try:
                jobs = JobService.get_recommended_jobs(candidate.id, limit=5)
                print(f"Candidate {candidate.id} - jobs:", jobs)
                current_app.logger.info(
                    f"Candidate {candidate.id} jobs: {[job.title for job in jobs]}"
                )
                if not jobs:
                    continue

                MailService.send_recommendation_email(
                    email = candidate.user.email,
                    candidate_name=candidate.full_name,
                    jobs=jobs
                )
                success_count += 1

            except Exception as e:
                current_app.logger.error(f"Error sending email to candidate_id={candidate.id}: {e}")

        current_app.logger.info(f"[RecommendationMail] {success_count} emails were successfully sent to candidates")