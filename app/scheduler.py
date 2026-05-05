from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

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

    scheduler.add_job(
        func=_send_recommendations,
        trigger=CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="weekly_recommendation_email",
        replace_existing=True,
        coalesce=True,
        max_instances=1
    )

    scheduler.start()