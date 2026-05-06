"""
tests/conftest.py
─────────────────
Cấu hình chung cho toàn bộ test suite.
Dùng SQLite in-memory → tách biệt hoàn toàn với MySQL production.
"""
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
from app.models.skill import Skill, CandidateSkill, JobSkill
from app.models.notification import Notification
from app.models.recommendation import JobRecommendation


# ─────────────────────────────────────────────────────────────────
# APP FIXTURE — tạo Flask app với SQLite in-memory
# ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
        # Tắt Gemini và Cloudinary trong test
        "GEMINI_API_KEY": "FAKE_KEY_FOR_TEST",
        "CLOUDINARY_CLOUD_NAME": "test",
        "CLOUDINARY_API_KEY": "test",
        "CLOUDINARY_API_SECRET": "test",
    })

    with app.app_context():
        _db.create_all()
        yield app
        # _db.drop_all()


# ─────────────────────────────────────────────────────────────────
# DB FIXTURE — rollback sau mỗi test để dữ liệu độc lập
# ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()
        # Xóa toàn bộ data sau mỗi test
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


# ─────────────────────────────────────────────────────────────────
# CLIENT FIXTURE
# ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def client(app, db):
    return app.test_client()


# ─────────────────────────────────────────────────────────────────
# HELPER: đăng nhập qua test client
# ─────────────────────────────────────────────────────────────────
def login_as(client, email, password, endpoint="/login"):
    return client.post(endpoint, data={"email": email, "password": password},
                       follow_redirects=True)


def login_candidate(client, email="candidate@test.com", password="password123"):
    return login_as(client, email, password, endpoint="/login")


def login_employer(client, email="employer@test.com", password="password123"):
    return login_as(client, email, password, endpoint="/employer/login")


def login_admin(client, email="admin@test.com", password="password123"):
    return login_as(client, email, password, endpoint="/admin/login")


# ─────────────────────────────────────────────────────────────────
# DATA FACTORIES
# ─────────────────────────────────────────────────────────────────
def make_candidate_user(db, email="candidate@test.com", password="password123",
                        full_name="Nguyen Van A", status="ACTIVE"):
    user = User(email=email, role="CANDIDATE", status=status, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    candidate = Candidate(user_id=user.id, full_name=full_name)
    db.session.add(candidate)
    db.session.commit()
    return user, candidate


def make_employer_user(db, email="employer@test.com", password="password123",
                       company_name="Tech Corp", status="ACTIVE"):
    user = User(email=email, role="EMPLOYER", status=status, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    employer = Employer(user_id=user.id, company_name=company_name,
                        location="Ha Noi")
    db.session.add(employer)
    db.session.commit()
    return user, employer


def make_admin_user(db, email="admin@test.com", password="password123"):
    user = User(email=email, role="ADMIN", status="ACTIVE", is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def make_job(db, employer, title="Python Developer", status="OPEN",
             location="Ha Noi", is_hidden=False):
    job = Job(
        employer_id=employer.id,
        title=title,
        description="We need a Python developer.",
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
        html_content="<div>{{data.full_name}}</div>",
        schema_version=1,
        is_active=True,
    )
    db.session.add(tmpl)
    db.session.commit()
    return tmpl


def make_online_cv(db, candidate, template, title="My CV"):
    cv = CV(
        candidate_id=candidate.id,
        template_id=template.id,
        template_version=1,
        title=title,
        type="ONLINE",
        content_json={"full_name": "Nguyen Van A", "summary": "Python developer"},
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


def make_application(db, job, cv, email="candidate@test.com",
                     status="PENDING"):
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