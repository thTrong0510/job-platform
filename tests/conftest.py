"""
tests/conftest.py — Integration test fixtures

Thứ tự khởi động quan trọng:
  1. load_dotenv(.env.test, override=True)   ← PHẢI chạy trước mọi import từ app
  2. import create_app                        ← lúc này config.py đọc SQLite URI
  3. Tạo bảng trong SQLite in-memory
"""

import os
from dotenv import load_dotenv

# ── Bước 1: nạp .env.test TRƯỚC KHI import bất cứ thứ gì từ app ──
# override=True đảm bảo .env.test luôn thắng .env
_env_test_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")
load_dotenv(dotenv_path=_env_test_path, override=True)

# ── Bước 2: import app (config.py đã đọc SQLALCHEMY_DATABASE_URI=sqlite) ──
import pytest
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.candidate import Candidate
from app.models.employer import Employer
from app.models.job import Job
from app.models.cv import CV, CVTemplate
from app.models.application import Application
from app.models.skill import Skill, JobSkill
from app.models.notification import Notification
from app.models.recommendation import JobRecommendation


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """Tạo Flask app một lần cho cả session test.
    SQLite in-memory đã được chọn thông qua .env.test nên không cần
    ghi đè SQLALCHEMY_DATABASE_URI ở đây nữa.
    """
    _app = create_app()

    _app.config.update({
        "TESTING":       True,
        "WTF_CSRF_ENABLED": False,
        # SQLite URI đã được set từ .env.test — không cần lặp lại
        # Chỉ giữ những override thực sự cần thiết cho test
    })

    with _app.app_context():
        _db.create_all()   # Tạo schema trong SQLite in-memory
        yield _app
        _db.drop_all()     # Dọn dẹp sau session (chỉ SQLite — MySQL không bị đụng)


@pytest.fixture(scope="function")
def db(app):
    """Cung cấp DB session cho từng test function.
    Sau mỗi test: rollback + xóa toàn bộ data (giữ nguyên schema).
    """
    with app.app_context():
        yield _db
        _db.session.rollback()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture(scope="function")
def client(app, db):
    """Test client Flask."""
    with app.test_client() as c:
        yield c


# ────────────────────────────────────────────────────────────────────────────
# Helper login functions
# ────────────────────────────────────────────────────────────────────────────

def login_candidate(client, email="candidate@test.com", password="password123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def login_employer(client, email="employer@test.com", password="password123"):
    return client.post(
        "/employer/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def login_admin(client, email="admin@test.com", password="password123"):
    return client.post(
        "/admin/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


# ────────────────────────────────────────────────────────────────────────────
# Factory helpers — tạo dữ liệu mẫu nhanh
# ────────────────────────────────────────────────────────────────────────────

def make_candidate_user(
    db,
    email="candidate@test.com",
    password="password123",
    full_name="Nguyen Van A",
    status="ACTIVE",
):
    user = User(email=email, role="CANDIDATE", status=status, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    candidate = Candidate(user_id=user.id, full_name=full_name)
    db.session.add(candidate)
    db.session.commit()
    return user, candidate


def make_employer_user(
    db,
    email="employer@test.com",
    password="password123",
    company_name="Tech Corp",
    status="ACTIVE",
):
    user = User(email=email, role="EMPLOYER", status=status, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    employer = Employer(user_id=user.id, company_name=company_name, location="Ha Noi")
    db.session.add(employer)
    db.session.commit()
    return user, employer


def make_admin_user(db, email="admin@test.com", password="password123"):
    user = User(email=email, role="ADMIN", status="ACTIVE", is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def make_job(
    db,
    employer,
    title="Python Developer",
    status="OPEN",
    location="Ha Noi",
    is_hidden=False,
):
    job = Job(
        employer_id=employer.id,
        title=title,
        description="We need a Python developer with 3+ years experience.",
        location=location,
        salary_min=1000,
        salary_max=3000,
        experience_required=2,
        status=status,
        is_hidden=is_hidden,
        end_date=datetime.now() + timedelta(days=30),
    )
    db.session.add(job)
    db.session.commit()
    return job


def make_cv_template(db):
    tmpl = CVTemplate(
        name="Basic Template",
        slug="basic-template",
        html_content="<div>{{ data.full_name }}</div>",
        schema_version=1,
        is_active=True,
    )
    db.session.add(tmpl)
    db.session.commit()
    return tmpl


def make_online_cv(db, candidate, template, title="My Online CV"):
    cv = CV(
        candidate_id=candidate.id,
        template_id=template.id,
        template_version=1,
        title=title,
        type="ONLINE",
        content_json={
            "full_name": "Nguyen Van A",
            "summary":   "Experienced Python developer",
            "email":     "candidate@test.com",
        },
    )
    db.session.add(cv)
    db.session.commit()
    return cv


def make_upload_cv(db, candidate, title="Uploaded CV"):
    cv = CV(
        candidate_id=candidate.id,
        title=title,
        type="UPLOAD",
        file_url="/static/uploads/cvs/test.pdf",
        file_name="test.pdf",
        file_size=1024,
    )
    db.session.add(cv)
    db.session.commit()
    return cv


def make_application(
    db,
    job,
    cv,
    email="candidate@test.com",
    status="PENDING",
):
    app_obj = Application(
        email=email,
        job_id=job.id,
        cv_id=cv.id,
        status=status,
    )
    db.session.add(app_obj)
    db.session.commit()
    return app_obj


def make_skill(db, name="Python"):
    skill = Skill(name=name)
    db.session.add(skill)
    db.session.commit()
    return skill