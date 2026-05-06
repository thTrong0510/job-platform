"""
python -m pytest tests/test_application.py -v
══════════════════════════════════════════════════════════════════
LUỒNG 4 — Employer quản lý hồ sơ ứng tuyển
LUỒNG 6 — Thông báo (notification)
──────────────────────────────────────────────────────────────────
IT-26  Employer xem danh sách application của job mình → đúng data
IT-27  Employer không thấy application của employer khác
IT-28  Mở chi tiết application → status tự chuyển PENDING→REVIEWED
IT-28b Mở chi tiết application status=REVIEWED → không đổi lại PENDING
IT-29  Employer đổi status → ACCEPTED → tạo Notification cho candidate
IT-30  Employer đổi status → REJECTED → tạo Notification đúng title
IT-31  Đổi status = status cũ → không tạo notification thừa
IT-32  Filter theo status=ACCEPTED → chỉ thấy đúng loại
IT-33  Candidate nhận notification → đọc → unread_count giảm
IT-34  Đánh dấu tất cả đã đọc → unread_count = 0
"""
import pytest
from conftest import (
    make_candidate_user, make_employer_user,
    make_job, make_cv_template, make_online_cv,
    make_application, make_upload_cv,
    login_candidate, login_employer,
)
from app.models.application import Application
from app.models.notification import Notification
from app.repositories.candidate.notification_repository import NotificationRepository


class TestApplicationManagement:

    def test_IT26_employer_sees_own_applications(self, client, db):
        """IT-26: Employer thấy application của job mình đã đăng."""
        user_c, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer)
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)
        make_application(db, job, cv, email=user_c.email)

        login_employer(client)

        resp = client.get("/employer/applications/")
        assert resp.status_code == 200
        assert candidate.full_name.encode() in resp.data

    def test_IT27_employer_cannot_see_other_employer_applications(self, client, db):
        """IT-27: Employer A không thấy application của job Employer B."""
        user_c, candidate = make_candidate_user(db)

        _, employer_a = make_employer_user(db, email="empA@test.com",
                                           company_name="Corp A")
        _, employer_b = make_employer_user(db, email="empB@test.com",
                                           company_name="Corp B")

        job_b = make_job(db, employer_b, title="Job of B")
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)
        make_application(db, job_b, cv, email=user_c.email)

        # Login employer A
        login_employer(client, email="empA@test.com")

        resp = client.get("/employer/applications/")
        assert resp.status_code == 200
        assert b"Job of B" not in resp.data

    def test_IT28_opening_detail_auto_sets_reviewed(self, client, db):
        """IT-28: Mở chi tiết application PENDING → status chuyển REVIEWED."""
        user_c, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer)
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)
        app_obj = make_application(db, job, cv, email=user_c.email,
                                   status="PENDING")

        login_employer(client)

        resp = client.get(f"/employer/applications/{app_obj.id}")
        assert resp.status_code == 200

        db.session.refresh(app_obj)
        assert app_obj.status == "REVIEWED"

    def test_IT28b_reviewed_stays_reviewed_on_reopen(self, client, db):
        """IT-28b: Application đã REVIEWED → mở lại không đổi status."""
        user_c, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer)
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)
        app_obj = make_application(db, job, cv, email=user_c.email,
                                   status="REVIEWED")

        login_employer(client)
        client.get(f"/employer/applications/{app_obj.id}")

        db.session.refresh(app_obj)
        assert app_obj.status == "REVIEWED"

    def test_IT32_filter_by_status_accepted(self, client, db):
        """IT-32: Filter status=ACCEPTED → chỉ thấy hồ sơ được chấp nhận."""
        user_c, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer)
        template = make_cv_template(db)

        cv1 = make_online_cv(db, candidate, template, title="CV Accepted")
        cv2 = make_upload_cv(db, candidate, title="CV Pending")

        make_application(db, job, cv1, email=user_c.email, status="ACCEPTED")

        # Tạo job khác để tránh UniqueConstraint(job_id, cv_id)
        job2 = make_job(db, employer, title="Job 2")
        make_application(db, job2, cv2, email=user_c.email, status="PENDING")

        login_employer(client)

        resp = client.get("/employer/applications/?status=ACCEPTED")
        assert resp.status_code == 200
        assert b"CV Accepted" in resp.data
        assert b"CV Pending" not in resp.data


class TestStatusUpdateAndNotification:

    def _setup(self, db):
        """Helper tạo đủ data cho test notification."""
        user_c, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer)
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)
        app_obj = make_application(db, job, cv, email=user_c.email,
                                   status="REVIEWED")
        return user_c, candidate, employer, job, cv, app_obj

    def test_IT29_accepted_creates_notification(self, client, db):
        """IT-29: Đổi status → ACCEPTED → tạo Notification cho candidate."""
        user_c, candidate, employer, job, cv, app_obj = self._setup(db)
        login_employer(client)

        resp = client.post(
            f"/employer/applications/{app_obj.id}/status",
            data={"status": "ACCEPTED", "back_to": "detail"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        notif = Notification.query.filter_by(user_id=user_c.id).first()
        assert notif is not None
        assert "chấp nhận" in notif.title.lower() or "🎉" in notif.title

    def test_IT30_rejected_creates_correct_notification(self, client, db):
        """IT-30: Đổi status → REJECTED → tạo Notification đúng nội dung."""
        user_c, candidate, employer, job, cv, app_obj = self._setup(db)
        login_employer(client)

        client.post(
            f"/employer/applications/{app_obj.id}/status",
            data={"status": "REJECTED", "back_to": "detail"},
            follow_redirects=True,
        )

        notif = Notification.query.filter_by(user_id=user_c.id).first()
        assert notif is not None
        assert "từ chối" in notif.title.lower() or "kết quả" in notif.title.lower()
        # Nội dung chứa tên job
        assert job.title in notif.message

    def test_IT31_same_status_no_extra_notification(self, client, db):
        """IT-31: Đổi status = status cũ → không tạo notification mới."""
        user_c, candidate, employer, job, cv, app_obj = self._setup(db)
        # app_obj đang REVIEWED
        login_employer(client)

        before_count = Notification.query.filter_by(user_id=user_c.id).count()

        client.post(
            f"/employer/applications/{app_obj.id}/status",
            data={"status": "REVIEWED", "back_to": "detail"},
            follow_redirects=True,
        )

        after_count = Notification.query.filter_by(user_id=user_c.id).count()
        assert after_count == before_count  # Không tăng

    def test_IT33_candidate_reads_notification_decreases_unread(self, client, db):
        """IT-33: Candidate đọc 1 notification → unread_count giảm 1."""
        user_c, candidate = make_candidate_user(db)

        # Tạo 2 notification chưa đọc
        n1 = Notification(user_id=user_c.id, title="Notif 1",
                          message="msg1", is_read=False)
        n2 = Notification(user_id=user_c.id, title="Notif 2",
                          message="msg2", is_read=False)
        db.session.add_all([n1, n2])
        db.session.commit()

        login_candidate(client)

        unread_before = NotificationRepository.count_unread(user_c.id)
        assert unread_before == 2

        # Đọc notification 1
        client.post(f"/candidate/notifications/{n1.id}/read",
                    follow_redirects=True)

        unread_after = NotificationRepository.count_unread(user_c.id)
        assert unread_after == 1

    def test_IT34_mark_all_read_sets_unread_to_zero(self, client, db):
        """IT-34: Đánh dấu tất cả đã đọc → unread_count = 0."""
        user_c, candidate = make_candidate_user(db)

        for i in range(5):
            n = Notification(user_id=user_c.id, title=f"Notif {i}",
                             message="msg", is_read=False)
            db.session.add(n)
        db.session.commit()

        login_candidate(client)

        assert NotificationRepository.count_unread(user_c.id) == 5

        client.post("/candidate/notifications/read-all", follow_redirects=True)

        assert NotificationRepository.count_unread(user_c.id) == 0