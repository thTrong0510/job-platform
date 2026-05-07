"""
pytest tests/test_job_search.py -v
══════════════════════════════════════════════════════════════════
LUỒNG 3 — Tìm kiếm & Ứng tuyển
──────────────────────────────────────────────────────────────────
IT-16  Tìm kiếm theo keyword → chỉ trả về job khớp
IT-17  Tìm kiếm theo location → filter đúng
IT-18  Tìm kiếm theo salary_min / salary_max
IT-19  Job bị admin ẩn (is_hidden=True) → không xuất hiện trong kết quả
IT-20  Job status=CLOSED → không xuất hiện trong tìm kiếm
IT-21  Kết quả phân trang đúng
IT-22  Apply job hợp lệ → tạo Application, flash success
IT-23  Apply job đã apply rồi → báo lỗi trùng (UniqueConstraint)
IT-24  Apply khi chưa login → redirect login
IT-25  Apply job CLOSED → không tạo application

Ghi chú về URL:
  - Danh sách job: /          (blueprint đăng ký không có url_prefix)
  - Chi tiết job:  /jobs/<id>
  - Apply:         /jobs/apply/<id>
"""
import pytest
from conftest import (
    make_candidate_user, make_employer_user,
    make_job, make_cv_template, make_online_cv,
    make_upload_cv, make_application,
    login_candidate,
)
from app.models.application import Application

# URL gốc của job list (blueprint không có url_prefix → route '/' = '/')
JOB_LIST_URL = "/"


class TestJobSearch:

    def test_IT16_keyword_search_returns_matching_jobs(self, client, db):
        """IT-16: Tìm 'Python' → chỉ trả job có 'Python' trong title."""
        _, employer = make_employer_user(db)
        make_job(db, employer, title="Python Developer")
        make_job(db, employer, title="Java Engineer")

        resp = client.get(f"{JOB_LIST_URL}?keyword=Python")
        assert resp.status_code == 200
        assert b"Python Developer" in resp.data
        assert b"Java Engineer" not in resp.data

    def test_IT17_location_filter_works(self, client, db):
        """IT-17: Filter location='Ha Noi' → không thấy job ở TP.HCM."""
        _, employer = make_employer_user(db)
        make_job(db, employer, title="Job HN", location="Ha Noi")
        make_job(db, employer, title="Job HCM", location="Ho Chi Minh")

        resp = client.get(f"{JOB_LIST_URL}?location=Ha+Noi")
        assert resp.status_code == 200
        assert b"Job HN" in resp.data
        assert b"Job HCM" not in resp.data

    def test_IT18_salary_filter_works(self, client, db):
        """IT-18: salary_min=2000 → chỉ thấy job có salary_max >= 2000."""
        _, employer = make_employer_user(db)

        from app.models.job import Job
        from datetime import datetime, timedelta

        job_high = Job(
            employer_id=employer.id,
            title="High Salary Job",
            description="desc",
            location="Ha Noi",
            salary_min=2000, salary_max=5000,
            status="OPEN", is_hidden=False,
            end_date=datetime.now() + timedelta(days=30),
        )
        job_low = Job(
            employer_id=employer.id,
            title="Low Salary Job",
            description="desc",
            location="Ha Noi",
            salary_min=300, salary_max=800,
            status="OPEN", is_hidden=False,
            end_date=datetime.now() + timedelta(days=30),
        )
        db.session.add_all([job_high, job_low])
        db.session.commit()

        resp = client.get(f"{JOB_LIST_URL}?salary_min=2000")
        assert resp.status_code == 200
        assert b"High Salary Job" in resp.data
        assert b"Low Salary Job" not in resp.data

    def test_IT19_hidden_job_not_shown_to_candidate(self, client, db):
        """IT-19: Job is_hidden=True → không xuất hiện với candidate."""
        _, employer = make_employer_user(db)
        make_job(db, employer, title="Visible Job", is_hidden=False)
        make_job(db, employer, title="Hidden Job", is_hidden=True)

        resp = client.get(JOB_LIST_URL)
        assert resp.status_code == 200
        assert b"Visible Job" in resp.data
        assert b"Hidden Job" not in resp.data

    def test_IT20_closed_job_not_shown_in_search(self, client, db):
        """IT-20: Job status=CLOSED → không xuất hiện."""
        _, employer = make_employer_user(db)
        make_job(db, employer, title="Open Job", status="OPEN")
        make_job(db, employer, title="Closed Job", status="CLOSED")

        resp = client.get(JOB_LIST_URL)
        assert resp.status_code == 200
        assert b"Open Job" in resp.data
        assert b"Closed Job" not in resp.data

    def test_IT21_pagination_works(self, client, db):
        """IT-21: Có nhiều job → phân trang hoạt động, page=1 khác page=2."""
        _, employer = make_employer_user(db)
        for i in range(10):
            make_job(db, employer, title=f"Job #{i}")

        resp_p1 = client.get(f"{JOB_LIST_URL}?page=1")
        resp_p2 = client.get(f"{JOB_LIST_URL}?page=2")
        assert resp_p1.status_code == 200
        assert resp_p2.status_code == 200
        assert resp_p1.data != resp_p2.data


class TestApplyJob:

    def test_IT22_apply_job_creates_application(self, client, db):
        """IT-22: Candidate apply job hợp lệ → tạo Application trong DB."""
        user, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer)
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)

        login_candidate(client)

        resp = client.post(
            f"/jobs/apply/{job.id}",
            data={"cv_id": cv.id},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        application = Application.query.filter_by(
            job_id=job.id, cv_id=cv.id
        ).first()
        assert application is not None
        assert application.status == "PENDING"
        assert application.email == user.email

    def test_IT23_duplicate_apply_blocked(self, client, db):
        """IT-23: Apply cùng job 2 lần → lần 2 báo lỗi, không tạo thêm."""
        user, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer)
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)

        login_candidate(client)

        # Apply lần 1
        client.post(f"/jobs/apply/{job.id}",
                    data={"cv_id": cv.id}, follow_redirects=True)
        # Apply lần 2
        resp = client.post(f"/jobs/apply/{job.id}",
                           data={"cv_id": cv.id}, follow_redirects=True)

        assert resp.status_code == 200
        count = Application.query.filter_by(job_id=job.id, cv_id=cv.id).count()
        assert count == 1

    def test_IT24_unauthenticated_apply_redirects(self, client, db):
        """IT-24: Chưa login → apply bị redirect về login."""
        _, employer = make_employer_user(db)
        job = make_job(db, employer)

        resp = client.post(
            f"/jobs/apply/{job.id}",
            data={"cv_id": 1},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"].lower()

    def test_IT25_apply_closed_job_blocked(self, client, db):
        """IT-25: Apply job đã CLOSED → không tạo application."""
        user, candidate = make_candidate_user(db)
        _, employer = make_employer_user(db)
        job = make_job(db, employer, status="CLOSED")
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)

        login_candidate(client)

        resp = client.post(
            f"/jobs/apply/{job.id}",
            data={"cv_id": cv.id},
            follow_redirects=True,
        )

        # Service phải raise ValueError cho job CLOSED → flash warning → 0 application
        assert resp.status_code == 200
        count = Application.query.filter_by(job_id=job.id).count()
        assert count == 0