"""
python -m pytest tests/test_cv.py -v
══════════════════════════════════════════════════════════════════
LUỒNG 2 — Tạo & Quản lý CV
──────────────────────────────────────────────────────────────────
IT-08  Upload CV (PDF) → lưu DB đúng type=UPLOAD
IT-09  Upload file sai định dạng → báo lỗi, không lưu
IT-10  Upload file vượt 5MB → báo lỗi
IT-11  Xem danh sách CV upload → chỉ thấy CV của mình
IT-12  Xóa CV upload → xóa khỏi DB (file vật lý mock)
IT-13  Tạo CV online → lưu DB type=ONLINE, content_json đúng
IT-14  Xem CV online → render template thành công
IT-15  Candidate chưa login → không thể vào /candidate/cv-upload
"""
import io
import pytest
from unittest.mock import patch
from conftest import (
    make_candidate_user, make_employer_user,
    make_cv_template, make_online_cv, make_upload_cv,
    login_candidate,
)
from app.models.cv import CV


class TestCVUpload:

    def test_IT08_upload_pdf_saves_to_db(self, client, db):
        """IT-08: Upload PDF hợp lệ → tạo bản ghi CV type=UPLOAD trong DB."""
        user, candidate = make_candidate_user(db)
        login_candidate(client)

        pdf_data = b"%PDF-1.4 fake pdf content"
        data = {
            "title": "My Resume",
            "cv_file": (io.BytesIO(pdf_data), "resume.pdf", "application/pdf"),
        }

        with patch("app.services.candidate.cv_upload_service.os.makedirs"), \
             patch("app.services.candidate.cv_upload_service.open",
                   create=True) as mock_open, \
             patch("werkzeug.datastructures.FileStorage.save"):
            resp = client.post(
                "/candidate/cv-upload/upload",
                data=data,
                content_type="multipart/form-data",
                follow_redirects=True,
            )

        assert resp.status_code == 200

        cv = CV.query.filter_by(candidate_id=candidate.id, type="UPLOAD").first()
        assert cv is not None
        assert cv.title == "My Resume"
        assert cv.file_name == "resume.pdf"

    def test_IT09_upload_invalid_format_rejected(self, client, db):
        """IT-09: Upload file .exe → không lưu, flash error."""
        make_candidate_user(db)
        login_candidate(client)

        data = {
            "title": "Bad File",
            "cv_file": (io.BytesIO(b"bad data"), "virus.exe", "application/octet-stream"),
        }

        resp = client.post(
            "/candidate/cv-upload/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        assert resp.status_code == 200
        # Không có CV nào được tạo
        count = CV.query.filter_by(type="UPLOAD").count()
        assert count == 0

    def test_IT10_upload_oversized_file_rejected(self, client, db):
        """IT-10: Upload file > 5MB → không lưu, flash error."""
        make_candidate_user(db)
        login_candidate(client)

        # Tạo file > 5MB
        big_data = b"a" * (5 * 1024 * 1024 + 1)
        data = {
            "title": "Big File",
            "cv_file": (io.BytesIO(big_data), "big.pdf", "application/pdf"),
        }

        resp = client.post(
            "/candidate/cv-upload/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        assert resp.status_code == 200
        count = CV.query.filter_by(type="UPLOAD").count()
        assert count == 0

    def test_IT11_list_shows_only_own_cvs(self, client, db):
        """IT-11: Danh sách CV chỉ hiển thị CV của candidate đang đăng nhập."""
        user1, candidate1 = make_candidate_user(db, email="c1@test.com")
        user2, candidate2 = make_candidate_user(db, email="c2@test.com")

        # Tạo CV cho cả 2 candidate
        make_upload_cv(db, candidate1, title="CV of C1")
        make_upload_cv(db, candidate2, title="CV of C2")

        # Login candidate1
        login_candidate(client, email="c1@test.com")

        resp = client.get("/candidate/cv-upload/", follow_redirects=True)
        assert resp.status_code == 200
        assert b"CV of C1" in resp.data
        assert b"CV of C2" not in resp.data

    def test_IT12_delete_cv_removes_from_db(self, client, db):
        """IT-12: Xóa CV → không còn trong DB."""
        user, candidate = make_candidate_user(db)
        cv = make_upload_cv(db, candidate)
        login_candidate(client)

        cv_id = cv.id

        with patch("app.services.candidate.cv_upload_service.os.path.exists",
                   return_value=False):
            resp = client.post(
                f"/candidate/cv-upload/delete/{cv_id}",
                follow_redirects=True,
            )

        assert resp.status_code == 200
        assert CV.query.get(cv_id) is None

    def test_IT15_unauthenticated_cannot_access_cv_upload(self, client, db):
        """IT-15: Chưa login → /candidate/cv-upload/ redirect về login."""
        resp = client.get("/candidate/cv-upload/", follow_redirects=False)
        assert resp.status_code == 302
        assert "login" in resp.headers["Location"].lower()


class TestOnlineCV:

    def test_IT13_create_online_cv_saves_content_json(self, client, db):
        """IT-13: Tạo CV online → lưu DB với type=ONLINE và content_json."""
        user, candidate = make_candidate_user(db)
        template = make_cv_template(db)
        login_candidate(client)

        resp = client.post(
            f"/candidate/create-cv-by-template/{template.id}",
            data={
                "title": "Dev CV 2024",
                "full_name": "Nguyen Van A",
                "email": "candidate@test.com",
                "phone": "0901234567",
                "summary": "Experienced Python developer",
            },
            follow_redirects=True,
        )

        assert resp.status_code == 200
        cv = CV.query.filter_by(candidate_id=candidate.id, type="ONLINE").first()
        assert cv is not None
        assert cv.title == "Dev CV 2024"
        assert cv.content_json is not None
        assert cv.content_json.get("full_name") == "Nguyen Van A"

    def test_IT14_view_online_cv_renders_template(self, client, db):
        """IT-14: Xem CV online → render template HTML thành công."""
        user, candidate = make_candidate_user(db)
        template = make_cv_template(db)
        cv = make_online_cv(db, candidate, template)
        login_candidate(client)

        resp = client.get(f"/candidate/cvs/{cv.id}")
        assert resp.status_code == 200
        # Template có chứa tên ứng viên
        assert b"Nguyen Van A" in resp.data