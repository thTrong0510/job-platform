"""
python -m pytest tests/test_employer_jobs.py -v
══════════════════════════════════════════════════════════════════
LUỒNG 8 — Employer quản lý tin tuyển dụng
──────────────────────────────────────────────────────────────────
IT-46  Đăng tin hợp lệ → tạo Job trong DB, redirect detail
IT-47  Đăng tin thiếu title → báo lỗi, không tạo
IT-48  Đăng tin salary_min > salary_max → báo lỗi validate
IT-49  Đăng tin deadline quá khứ → báo lỗi
IT-50  Xem danh sách tin → chỉ thấy tin của mình + stats đúng
IT-51  Chỉnh sửa tin → cập nhật đúng DB
IT-52  Chỉnh sửa end_date < start_date → báo lỗi
IT-53  Xóa tin chưa có application → xóa hẳn
IT-54  Xóa tin đã có application → chuyển CLOSED, không xóa
IT-55  Employer không chỉnh sửa được tin của employer khác
IT-56  Tin bị admin ẩn → employer thấy badge cảnh báo
IT-57  Dashboard stats: total, open, closed đúng
"""
import pytest
from datetime import datetime, timedelta
from conftest import (
    make_candidate_user, make_employer_user,
    make_job, make_cv_template, make_online_cv,
    make_application, login_employer,
)
from app.models.job import Job


class TestCreateJob:

    def test_IT46_create_valid_job(self, client, db):
        """IT-46: Đăng tin hợp lệ → tạo Job trong DB."""
        _, employer = make_employer_user(db)
        login_employer(client)

        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        resp = client.post("/employer/jobs/create", data={
            "title":               "Senior Python Dev",
            "description":         "We need a senior Python developer.",
            "location":            "Ha Noi",
            "salary_min":          "2000",
            "salary_max":          "4000",
            "experience_required": "3",
            "end_date":            future_date,
        }, follow_redirects=False)

        # Redirect về detail page sau khi tạo thành công
        assert resp.status_code == 302
        assert "/employer/jobs/" in resp.headers["Location"]

        job = Job.query.filter_by(title="Senior Python Dev").first()
        assert job is not None
        assert job.employer_id == employer.id
        assert job.status == "OPEN"

    def test_IT47_create_job_missing_title_rejected(self, client, db):
        """IT-47: Thiếu title → không tạo job, flash error."""
        make_employer_user(db)
        login_employer(client)

        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        resp = client.post("/employer/jobs/create", data={
            "title":       "",
            "description": "Some description",
            "location":    "Ha Noi",
            "end_date":    future_date,
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert Job.query.count() == 0

    def test_IT48_create_job_salary_min_gt_max_rejected(self, client, db):
        """IT-48: salary_min > salary_max → validation fail."""
        make_employer_user(db)
        login_employer(client)

        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        resp = client.post("/employer/jobs/create", data={
            "title":       "Bad Salary Job",
            "description": "desc",
            "location":    "Ha Noi",
            "salary_min":  "5000",
            "salary_max":  "1000",
            "end_date":    future_date,
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert Job.query.filter_by(title="Bad Salary Job").first() is None

    def test_IT49_create_job_past_deadline_rejected(self, client, db):
        """IT-49: Deadline trong quá khứ → validation fail."""
        make_employer_user(db)
        login_employer(client)

        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        resp = client.post("/employer/jobs/create", data={
            "title":       "Expired Job",
            "description": "desc",
            "location":    "Ha Noi",
            "end_date":    past_date,
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert Job.query.filter_by(title="Expired Job").first() is None


class TestListAndStats:

    def test_IT50_list_shows_only_own_jobs(self, client, db):
        """IT-50: Danh sách tin → chỉ thấy tin của employer đang login."""
        _, employer_a = make_employer_user(db, email="empA@test.com",
                                           company_name="Corp A")
        _, employer_b = make_employer_user(db, email="empB@test.com",
                                           company_name="Corp B")

        make_job(db, employer_a, title="Job of A")
        make_job(db, employer_b, title="Job of B")

        login_employer(client, email="empA@test.com")

        resp = client.get("/employer/jobs/")
        assert resp.status_code == 200
        assert b"Job of A" in resp.data
        assert b"Job of B" not in resp.data

    def test_IT57_dashboard_stats_correct(self, client, db):
        """IT-57: Dashboard stats: total, open, closed đúng số lượng."""
        from app.services.employer.dashboard_service import DashboardService

        _, employer = make_employer_user(db)
        make_job(db, employer, title="Open 1", status="OPEN")
        make_job(db, employer, title="Open 2", status="OPEN")
        make_job(db, employer, title="Closed 1", status="CLOSED")

        stats = DashboardService.get_stats(employer.id)

        assert stats["total_jobs"] == 3
        assert stats["open"] == 2
        assert stats["closed"] == 1


class TestEditJob:

    def test_IT51_edit_job_updates_db(self, client, db):
        """IT-51: Chỉnh sửa tin → cập nhật đúng trong DB."""
        _, employer = make_employer_user(db)
        job = make_job(db, employer, title="Old Title")
        login_employer(client)

        future_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")

        resp = client.post(f"/employer/jobs/{job.id}/edit", data={
            "title":               "New Title",
            "description":         "Updated description",
            "location":            "Ho Chi Minh",
            "salary_min":          "3000",
            "salary_max":          "6000",
            "experience_required": "5",
            "end_date":            future_date,
        }, follow_redirects=True)

        assert resp.status_code == 200
        db.session.refresh(job)
        assert job.title == "New Title"
        assert job.location == "Ho Chi Minh"

    def test_IT52_edit_end_before_start_rejected(self, client, db):
        """IT-52: end_date < start_date khi edit → flash error, không cập nhật."""
        _, employer = make_employer_user(db)
        job = make_job(db, employer, title="Date Job")
        login_employer(client)

        resp = client.post(f"/employer/jobs/{job.id}/edit", data={
            "title":       "Date Job",
            "description": "desc",
            "location":    "Ha Noi",
            "start_date":  "2025-12-01",
            "end_date":    "2025-01-01",   # end < start
        }, follow_redirects=True)

        assert resp.status_code == 200
        # Title không đổi
        db.session.refresh(job)
        assert job.title == "Date Job"

    def test_IT55_employer_cannot_edit_other_employer_job(self, client, db):
        """IT-55: Employer A không chỉnh sửa được job của Employer B."""
        _, employer_a = make_employer_user(db, email="empA@test.com",
                                           company_name="Corp A")
        _, employer_b = make_employer_user(db, email="empB@test.com",
                                           company_name="Corp B")

        job_b = make_job(db, employer_b, title="B's Job")
        login_employer(client, email="empA@test.com")

        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        resp = client.post(f"/employer/jobs/{job_b.id}/edit", data={
            "title":       "Hacked Title",
            "description": "desc",
            "location":    "Ha Noi",
            "end_date":    future_date,
        }, follow_redirects=True)

        # Job B không bị thay đổi
        db.session.refresh(job_b)
        assert job_b.title == "B's Job"


class TestDeleteJob:

    def test_IT53_delete_job_no_applications(self, client, db):
        """IT-53: Xóa tin chưa có application → xóa hẳn khỏi DB."""
        _, employer = make_employer_user(db)
        job = make_job(db, employer, title="Empty Job")
        job_id = job.id
        login_employer(client)

        resp = client.post(f"/employer/jobs/{job_id}/delete",
                           follow_redirects=True)
        assert resp.status_code == 200
        assert Job.query.get(job_id) is None

    def test_IT54_delete_job_with_applications_closes_it(self, client, db):
        """IT-54: Xóa tin đã có application → chuyển CLOSED, không xóa hẳn."""
        user_c, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer, title="Job With Apps")
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)
        make_application(db, job, cv, email=user_c.email)

        job_id = job.id
        login_employer(client)

        resp = client.post(f"/employer/jobs/{job_id}/delete",
                           follow_redirects=True)
        assert resp.status_code == 200

        # Vẫn còn trong DB nhưng status = CLOSED
        remaining = Job.query.get(job_id)
        assert remaining is not None
        assert remaining.status == "CLOSED"

    def test_IT56_hidden_job_shows_warning_badge_to_employer(self, client, db):
        """IT-56: Job bị admin ẩn → employer thấy badge cảnh báo."""
        _, employer = make_employer_user(db)
        make_job(db, employer, title="Admin Hidden Job", is_hidden=True)
        login_employer(client)

        resp = client.get("/employer/jobs/")
        assert resp.status_code == 200
        # Template hiển thị badge "Bị ẩn bởi Admin"
        assert "Admin Hidden Job".encode() in resp.data
        assert "Bị Admin ẩn".encode() in resp.data or \
               "is_hidden".encode() in resp.data or \
               "ẩn".encode() in resp.data