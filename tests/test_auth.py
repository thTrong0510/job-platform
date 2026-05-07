"""
pytest tests/test_auth.py -v 
══════════════════════════════════════════════════════════════════
LUỒNG 1 — Auth & Session
──────────────────────────────────────────────────────────────────
IT-01  Candidate đăng ký → login → session đúng role
IT-02  Login sai mật khẩu → báo lỗi, không tạo session
IT-03  Employer PENDING → không thể login → admin duyệt → login được
IT-04  Admin login đúng → session role = ADMIN
IT-05  Logout xóa session, redirect đúng trang
IT-06  Truy cập route cần auth khi chưa login → redirect login
IT-07  Employer login bằng tài khoản candidate → báo lỗi role sai
"""
import pytest
from conftest import (
    make_candidate_user, make_employer_user, make_admin_user,
    login_candidate, login_employer, login_admin,
)


class TestCandidateAuth:

    def test_IT01_register_then_login_sets_correct_session(self, client, db):
        """IT-01: Đăng ký candidate → login → session có user_id, role=CANDIDATE."""
        # Đăng ký
        resp = client.post("/register", data={
            "fullname": "Nguyen Van A",
            "email": "newcandidate@test.com",
            "password": "password123",
            "confirm_password": "password123",
        }, follow_redirects=False)
        # Redirect về login sau khi đăng ký thành công
        assert resp.status_code == 302

        # Login
        resp = client.post("/login", data={
            "email": "newcandidate@test.com",
            "password": "password123",
        }, follow_redirects=False)
        assert resp.status_code == 302

        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["user_role"] == "CANDIDATE"

    def test_IT02_login_wrong_password_no_session(self, client, db):
        """IT-02: Login sai mật khẩu → không tạo session."""
        make_candidate_user(db)

        resp = client.post("/login", data={
            "email": "candidate@test.com",
            "password": "wrongpassword",
        }, follow_redirects=True)

        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_IT02b_login_wrong_email_no_session(self, client, db):
        """IT-02b: Login email không tồn tại → không tạo session."""
        resp = client.post("/login", data={
            "email": "notexist@test.com",
            "password": "password123",
        }, follow_redirects=True)

        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_IT06_protected_route_redirects_to_login(self, client, db):
        """IT-06: Truy cập route cần auth khi chưa login → redirect."""
        resp = client.get("/candidate/cvs", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_IT05_logout_clears_session(self, client, db):
        """IT-05: Sau khi logout, session bị xóa."""
        make_candidate_user(db)
        login_candidate(client)

        # Xác nhận đã login
        with client.session_transaction() as sess:
            assert "user_id" in sess

        # Logout
        client.get("/logout", follow_redirects=True)

        with client.session_transaction() as sess:
            assert "user_id" not in sess


class TestEmployerAuth:

    def test_IT03_employer_pending_cannot_login(self, client, db):
        """IT-03a: Employer status=PENDING → login bị chặn."""
        make_employer_user(db, status="PENDING")

        resp = client.post("/employer/login", data={
            "email": "employer@test.com",
            "password": "password123",
        }, follow_redirects=True)

        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_IT03_employer_active_can_login(self, client, db):
        """IT-03b: Employer status=ACTIVE → login thành công."""
        make_employer_user(db, status="ACTIVE")

        resp = client.post("/employer/login", data={
            "email": "employer@test.com",
            "password": "password123",
        }, follow_redirects=False)

        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["user_role"] == "EMPLOYER"

    def test_IT07_candidate_cannot_login_as_employer(self, client, db):
        """IT-07: Candidate dùng endpoint /employer/login → bị chặn."""
        make_candidate_user(db)

        resp = client.post("/employer/login", data={
            "email": "candidate@test.com",
            "password": "password123",
        }, follow_redirects=True)

        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_IT05_employer_logout_redirects_to_employer_home(self, client, db):
        """IT-05: Employer logout → về /employer/ (không về /login của candidate)."""
        make_employer_user(db)
        login_employer(client)

        resp = client.get("/employer/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/employer" in resp.headers["Location"]


class TestAdminAuth:

    def test_IT04_admin_login_sets_role(self, client, db):
        """IT-04: Admin login đúng → session role = ADMIN."""
        make_admin_user(db)

        resp = client.post("/admin/login", data={
            "email": "admin@test.com",
            "password": "password123",
        }, follow_redirects=False)

        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess["user_role"] == "ADMIN"

    def test_IT04_candidate_cannot_access_admin(self, client, db):
        """IT-04b: Candidate không thể vào route /admin/jobs/."""
        make_candidate_user(db)
        login_candidate(client)

        resp = client.get("/admin/jobs/", follow_redirects=False)
        assert resp.status_code == 302