from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os

scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")

def init_scheduler(app):
    def _send_recommendations():
        # Sử dụng test_request_context để giả lập môi trường HTTP request
        with app.test_request_context():
            try:
                from app.services.admin.job_recommendation_service import JobRecommendationService
                JobRecommendationService.send_weekly_recommendations()
            except Exception as e:
                app.logger.error(f"[Scheduler] Lỗi job gửi mail: {e}")

    def _auto_close_jobs():
        with app.app_context():
            try:
                from app.services.candidate.job_service import JobService
                JobService.auto_close_expired_jobs()
            except Exception as e:
                app.logger.error(f"[Scheduler] Lỗi auto close job: {e}")

    scheduler.add_job(
        func=_send_recommendations,
        trigger=CronTrigger(day_of_week="thu", hour=0, minute=51),
        id="weekly_recommendation_email",
        replace_existing=True,
        coalesce=True,
        max_instances=1
    )

    scheduler.add_job(
        func=_auto_close_jobs,
        trigger="cron",
        hour=0,
        minute=0,
        id="auto_close_jobs",
        replace_existing=True
    )

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.start()