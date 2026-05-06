"""
python -m pytest tests/test_admin.py -v
══════════════════════════════════════════════════════════════════
LUỒNG 5 — Admin kiểm duyệt tài khoản & quản lý tin tuyển dụng
──────────────────────────────────────────────────────────────────
IT-35  Admin xem danh sách employer → thấy đúng data
IT-36  Admin duyệt PENDING → ACTIVE → employer login được, nhận notification
IT-37  Admin từ chối employer → status=REJECTED, employer không login được
IT-38  Admin tạm khóa ACTIVE → SUSPENDED → employer không login được
IT-39  Admin xem danh sách job → thấy cả job bị ẩn
IT-40  Admin ẩn job (toggle_hidden) → job không hiện với candidate
IT-41  Admin bỏ ẩn job → job hiện lại với candidate
IT-42  Admin xóa job không có application → xóa hẳn khỏi DB
IT-43  Admin xóa job có application → chuyển CLOSED+hidden, không xóa
IT-44  Thống kê stats đúng sau khi ẩn job đã đóng
IT-45  Candidate không vào được /admin/* (403/redirect)
"""
import pytest
from conftest import (
    make_candidate_user, make_employer_user, make_admin_user,
    make_job, make_cv_template, make_online_cv, make_application,
    login_admin, login_employer, login_candidate,
)
from app.models.user import User
from app.models.job import Job
from app.models.notification import Notification


class TestAdminEmployerManagement:

    def test_IT35_admin_sees_employer_list(self, client, db):
        """IT-35: Admin vào /admin/users/ → thấy danh sách employer."""
        make_admin_user(db)
        make_employer_user(db, company_name="Visible Corp")
        login_admin(client)

        resp = client.get("/admin/users/")
        assert resp.status_code == 200
        assert b"Visible Corp" in resp.data

    def test_IT36_admin_activate_employer_can_login(self, client, db):
        """IT-36: Admin ACTIVE → employer login được + nhận notification."""
        admin = make_admin_user(db)
        user_e, employer = make_employer_user(db, status="PENDING")

        login_admin(client)

        resp = client.post(
            f"/admin/users/{user_e.id}/change-status",
            data={"status": "ACTIVE", "reason": "Đã xác minh"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        # Kiểm tra status trong DB
        db.session.refresh(user_e)
        assert user_e.status == "ACTIVE"
        assert user_e.is_active is True

        # Employer phải login được
        client.get("/employer/logout")
        resp_login = client.post("/employer/login", data={
            "email": "employer@test.com",
            "password": "password123",
        }, follow_redirects=False)
        assert resp_login.status_code == 302

        # Có notification gửi đến employer
        notif = Notification.query.filter_by(user_id=user_e.id).first()
        assert notif is not None
        assert "kích hoạt" in notif.title.lower() or "✅" in notif.title

    def test_IT37_admin_reject_employer_cannot_login(self, client, db):
        """IT-37: Admin REJECTED → employer không login được."""
        make_admin_user(db)
        user_e, employer = make_employer_user(db, status="PENDING")

        login_admin(client)
        client.post(
            f"/admin/users/{user_e.id}/change-status",
            data={"status": "REJECTED", "reason": "Thông tin không hợp lệ"},
            follow_redirects=True,
        )

        db.session.refresh(user_e)
        assert user_e.status == "REJECTED"

        # Thử login → phải thất bại
        client.get("/admin/logout")
        resp = client.post("/employer/login", data={
            "email": "employer@test.com",
            "password": "password123",
        }, follow_redirects=True)

        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_IT38_admin_suspend_active_employer(self, client, db):
        """IT-38: Admin SUSPENDED → employer active bị khóa không login được."""
        make_admin_user(db)
        user_e, employer = make_employer_user(db, status="ACTIVE")

        login_admin(client)
        client.post(
            f"/admin/users/{user_e.id}/change-status",
            data={"status": "SUSPENDED", "reason": "Vi phạm chính sách"},
            follow_redirects=True,
        )

        db.session.refresh(user_e)
        assert user_e.status == "SUSPENDED"
        assert user_e.is_active is False

        # Notification phải có từ "khóa"
        notif = Notification.query.filter_by(user_id=user_e.id).first()
        assert notif is not None
        assert "khóa" in notif.title.lower() or "⚠️" in notif.title

    def test_IT45_candidate_cannot_access_admin(self, client, db):
        """IT-45: Candidate không thể vào /admin/users/ → redirect."""
        make_candidate_user(db)
        login_candidate(client)

        resp = client.get("/admin/users/", follow_redirects=False)
        assert resp.status_code == 302


class TestAdminJobManagement:

    def test_IT39_admin_sees_all_jobs_including_hidden(self, client, db):
        """IT-39: Admin xem /admin/jobs/ → thấy cả job đang bị ẩn."""
        make_admin_user(db)
        _, employer = make_employer_user(db)
        make_job(db, employer, title="Normal Job", is_hidden=False)
        make_job(db, employer, title="Hidden Job", is_hidden=True)

        login_admin(client)

        resp = client.get("/admin/jobs/")
        assert resp.status_code == 200
        assert b"Normal Job" in resp.data
        assert b"Hidden Job" in resp.data

    def test_IT40_admin_hide_job_disappears_from_candidate(self, client, db):
        """IT-40: Admin ẩn job → candidate không thấy trong /jobs/."""
        make_admin_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer, title="To Be Hidden", is_hidden=False)

        login_admin(client)

        # Toggle hidden (False → True)
        client.post(
            f"/admin/jobs/{job.id}/toggle-hidden",
            data={"back_to": "list"},
            follow_redirects=True,
        )

        db.session.refresh(job)
        assert job.is_hidden is True

        # Candidate vào trang job list → không thấy job này
        client.get("/admin/logout")
        resp = client.get("/jobs/")
        assert b"To Be Hidden" not in resp.data

    def test_IT41_admin_restore_job_shows_to_candidate(self, client, db):
        """IT-41: Admin bỏ ẩn job → job hiện lại với candidate."""
        make_admin_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer, title="Restored Job", is_hidden=True)

        login_admin(client)

        # Toggle hidden (True → False)
        client.post(
            f"/admin/jobs/{job.id}/toggle-hidden",
            data={"back_to": "list"},
            follow_redirects=True,
        )

        db.session.refresh(job)
        assert job.is_hidden is False

        client.get("/admin/logout")
        resp = client.get("/jobs/")
        assert b"Restored Job" in resp.data

    def test_IT42_admin_delete_job_no_applications(self, client, db):
        """IT-42: Xóa job chưa có application → xóa hẳn khỏi DB."""
        make_admin_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer, title="Empty Job")
        job_id = job.id

        login_admin(client)

        client.post(
            f"/admin/jobs/{job_id}/delete",
            follow_redirects=True,
        )

        assert Job.query.get(job_id) is None

    def test_IT43_admin_delete_job_with_applications_closes_instead(self, client, db):
        """IT-43: Xóa job có application → chuyển CLOSED+hidden, không xóa."""
        make_admin_user(db)
        user_c, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer, title="Job With Apps")
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)
        make_application(db, job, cv, email=user_c.email)

        job_id = job.id
        login_admin(client)

        client.post(
            f"/admin/jobs/{job_id}/delete",
            follow_redirects=True,
        )

        # Job vẫn còn trong DB
        remaining = Job.query.get(job_id)
        assert remaining is not None
        assert remaining.status == "CLOSED"
        assert remaining.is_hidden is True

    def test_IT44_stats_correct_after_hiding_closed_job(self, client, db):
        """IT-44: Ẩn job đã CLOSED → closed count không đổi, hidden tăng."""
        from app.repositories.admin.admin_job_repository import AdminJobRepository

        make_admin_user(db)
        _, employer = make_employer_user(db)

        # 1 OPEN, 1 CLOSED
        make_job(db, employer, title="Open Job",   status="OPEN",   is_hidden=False)
        closed_job = make_job(db, employer, title="Closed Job", status="CLOSED", is_hidden=False)

        stats_before = AdminJobRepository.count_stats()
        assert stats_before["closed"] == 1
        assert stats_before["hidden"] == 0

        # Ẩn job đã đóng
        login_admin(client)
        client.post(
            f"/admin/jobs/{closed_job.id}/toggle-hidden",
            data={"back_to": "list"},
            follow_redirects=True,
        )

        stats_after = AdminJobRepository.count_stats()
        # Closed vẫn = 1 (đếm tất cả CLOSED bất kể is_hidden)
        assert stats_after["closed"] == 1
        # Hidden = 1
        assert stats_after["hidden"] == 1
        # Open vẫn = 1
        assert stats_after["open"] == 1