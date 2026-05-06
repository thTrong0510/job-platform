## python -m pytest tests/test_services.py -v

import pytest
from unittest.mock import patch, MagicMock

from flask import Flask

from app.services.admin.admin_job_service import AdminJobService
from app.services.admin.job_recommendation_service import JobRecommendationService
from app.services.admin.user_service import AdminUserService


@pytest.fixture
def app_context():
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.app_context():
        yield app

# ══════════════════════════════════════════════════════════════════════
# 1. AdminJobService
#    file: app/services/admin/admin_job_service.py
# ══════════════════════════════════════════════════════════════════════

class TestAdminJobService:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.repo_mock = MagicMock()

        patcher = patch(
            "app.services.admin.admin_job_service.AdminJobRepository",
            self.repo_mock
        )
        patcher.start()
        yield
        patcher.stop()

    # -- get_jobs --
    def test_get_jobs_no_filter(self):
        self.repo_mock.get_jobs.return_value = []

        result = AdminJobService.get_jobs({})
        assert result == []
        self.repo_mock.get_jobs.assert_called_once_with(
            keyword=None, status=None, is_hidden=None, page=1)

    @pytest.mark.parametrize("filters, expected_hidden", [
        ({"visibility": "hidden"}, True),
        ({"visibility": "visible"}, False),
        ({"visibility": ""}, None),
    ])
    def test_get_jobs_visibility_logic(self, filters, expected_hidden):
        self.repo_mock.get_jobs.return_value = []
        AdminJobService.get_jobs(filters)
        self.repo_mock.get_jobs.assert_called_once_with(
            keyword=None, status=None, is_hidden=expected_hidden, page=1
        )

    def test_get_jobs_keyword_is_stripped(self):
        self.repo_mock.get_jobs.return_value = []
        AdminJobService.get_jobs({"keyword": "   python   "})
        self.repo_mock.get_jobs.assert_called_once_with(
            keyword="python", status=None, is_hidden=None, page=1
        )

    def test_get_jobs_keyword_becomes_none(self):
        self.repo_mock.get_jobs.return_value = []
        AdminJobService.get_jobs({"keyword": ""})
        self.repo_mock.get_jobs.assert_called_once_with(
            keyword=None, status=None, is_hidden=None, page=1
        )

    def test_get_jobs_status_is_passed_through(self):
        self.repo_mock.get_jobs.return_value = []
        AdminJobService.get_jobs({"status": "OPEN"})
        kwargs = self.repo_mock.get_jobs.call_args.kwargs
        assert kwargs["status"] == "OPEN"

    def test_get_jobs_blank_status_becomes_none(self):
        self.repo_mock.get_jobs.return_value = []
        AdminJobService.get_jobs({"status": "   "})
        kwargs = self.repo_mock.get_jobs.call_args.kwargs
        assert kwargs["status"] is None

    def test_get_jobs_page_param_forwarded(self):
        self.repo_mock.get_jobs.return_value = []
        AdminJobService.get_jobs({}, page=5)
        kwargs = self.repo_mock.get_jobs.call_args.kwargs
        assert kwargs["page"] == 5

    def test_get_jobs_returns_repo_result(self):
        fake_pagination = MagicMock()
        self.repo_mock.get_jobs.return_value = fake_pagination
        result = AdminJobService.get_jobs({})
        assert result is fake_pagination

    # -- get_stats --
    def test_get_stats(self):
        expected_stats = {"total": 10, "open": 5, "closed": 5, "hidden": 3}
        self.repo_mock.count_stats.return_value = expected_stats

        result = AdminJobService.get_stats()

        assert result == expected_stats
        self.repo_mock.count_stats.assert_called_once()

    # -- get_job_detail --
    def test_get_job_detail(self):
        job_id = 123
        fake_job = MagicMock()
        fake_employer = MagicMock()
        self.repo_mock.find_by_id.return_value = (fake_job, fake_employer)

        result = AdminJobService.get_job_detail(job_id)

        assert result == (fake_job, fake_employer)
        self.repo_mock.find_by_id.assert_called_once_with(job_id)

    # -- toggle_hidden --
    def test_toggle_hidden_job_not_found(self):
        self.repo_mock.find_by_id.return_value = None

        success, message = AdminJobService.toggle_hidden(999)

        assert success is False
        assert "Không tìm thấy" in message
        self.repo_mock.save.assert_not_called()

    def test_toggle_hidden_to_hide(self):
        # Giả lập job đang hiện (is_hidden = False)
        fake_job = MagicMock()
        fake_job.is_hidden = False
        self.repo_mock.find_by_id.return_value = (fake_job, None)

        success, message = AdminJobService.toggle_hidden(1)

        assert success is True
        assert fake_job.is_hidden is True  # Đã chuyển thành ẩn
        assert "Đã ẩn tin tuyển dụng thành công." in message
        self.repo_mock.save.assert_called_once_with(fake_job)

    def test_toggle_hidden_to_show(self):
        # Giả lập job đang ẩn (is_hidden = True)
        fake_job = MagicMock()
        fake_job.is_hidden = True
        self.repo_mock.find_by_id.return_value = (fake_job, None)

        success, message = AdminJobService.toggle_hidden(1)

        assert success is True
        assert fake_job.is_hidden is False  # Đã chuyển thành hiện lại
        assert "hiện lại" in message
        self.repo_mock.save.assert_called_once_with(fake_job)

    # -- delete_job --
    def test_delete_job_success(self):
        fake_job = MagicMock()
        self.repo_mock.find_by_id.return_value = (fake_job, None)

        success, message = AdminJobService.delete_job(1)

        assert success is True
        assert "Đã xóa" in message
        self.repo_mock.delete.assert_called_once_with(fake_job)

    def test_delete_job_not_found(self):
        self.repo_mock.find_by_id.return_value = None

        success, message = AdminJobService.delete_job(999)

        assert success is False
        assert "Không tìm thấy" in message
        self.repo_mock.delete.assert_not_called()

# ══════════════════════════════════════════════════════════════════════
# 2. AdminUserService
#    file: app/services/admin/user_service.py
# ═════════════════════════════════════════════════════════════════════
class TestAdminUserService:

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        # Mock cả UserRepository và MailService, tự động clean
        with patch("app.services.admin.user_service.UserRepository") as mock_repo, \
                patch("app.services.admin.user_service.MailService") as mock_mail:
            self.repo_mock = mock_repo
            self.mail_mock = mock_mail
            yield

    # -- get_users_paginated --
    def test_get_users_paginated_forwards_all_params(self):
        self.repo_mock.get_all_users.return_value = []
        result = AdminUserService.get_users_paginated(role='EMPLOYER', status="ACTIVE", keyword="nhi", page=2, per_page=5)
        assert result == []
        self.repo_mock.get_all_users.assert_called_once_with(role='EMPLOYER', status="ACTIVE", keyword="nhi", page=2, per_page=5)

    def test_get_users_paginated_default_per_page_is_10(self):
        self.repo_mock.get_all_users.return_value = []
        AdminUserService.get_users_paginated()
        kwargs = self.repo_mock.get_all_users.call_args.kwargs
        assert kwargs["per_page"] == 10

    def test_get_user_detail_success(self):
        fake_user = MagicMock(id=1)
        self.repo_mock.find_by_id.return_value = fake_user

        result = AdminUserService.get_user_detail(1)
        assert result is fake_user

    def test_get_user_detail_not_found(self):
        self.repo_mock.find_by_id.return_value = None
        with pytest.raises(ValueError, match="Không tìm thấy người dùng"):
            AdminUserService.get_user_detail(999)

    # -- change_status --
    @pytest.mark.parametrize("status, reason, expected_msg", [
        ("INVALID", None, "Trạng thái không hợp lệ"),
        ("REJECTED", "", "Vui lòng nhập lý do"),
        ("SUSPENDED", "   ", "Vui lòng nhập lý do"),
    ])
    def test_change_status_validation_errors(self, status, reason, expected_msg):
        success, msg = AdminUserService.change_status(1, status, reason)
        assert success is False
        assert expected_msg in msg

    def test_change_status_user_not_found(self):
        self.repo_mock.find_by_id.return_value = None
        success, msg = AdminUserService.change_status(999, "ACTIVE")
        assert success is False
        assert "Không tìm thấy" in msg

    def test_change_status_admin_protection(self):
        fake_admin = MagicMock(role='ADMIN', status='ACTIVE')
        self.repo_mock.find_by_id.return_value = fake_admin

        success, msg = AdminUserService.change_status(1, 'SUSPENDED', 'Reason')
        assert success is False
        assert "Không thể thay đổi trạng thái tài khoản Admin" in msg

    def test_change_status_rejected_logic(self):
        # Thử chuyển sang REJECTED khi status không phải PENDING
        fake_user = MagicMock(role='CANDIDATE', status='ACTIVE')
        self.repo_mock.find_by_id.return_value = fake_user

        success, msg = AdminUserService.change_status(1, 'REJECTED', 'Reason')
        assert success is False
        assert "Chỉ khi trạng thái là PENDING" in msg

    def test_change_status_same_status(self):
        fake_user = MagicMock(role='CANDIDATE', status='ACTIVE')
        self.repo_mock.find_by_id.return_value = fake_user
        success, msg = AdminUserService.change_status(1, 'ACTIVE', 'Reason')
        assert success is False
        assert "đang là" in msg

    def test_change_status_success(self):
        fake_user = MagicMock(role='EMPLOYER', status='PENDING')
        self.repo_mock.find_by_id.return_value = fake_user

        success, msg = AdminUserService.change_status(1, 'ACTIVE')

        assert success is True
        assert fake_user.status == 'ACTIVE'
        self.repo_mock.save.assert_called_once_with(fake_user)
        self.mail_mock.notify_status_change.assert_called_once()

    def test_change_status_rejected_from_pending_success(self):
        fake_user = MagicMock(role="EMPLOYER", status="PENDING")
        self.repo_mock.find_by_id.return_value = fake_user
        ok, _ = AdminUserService.change_status(1, "REJECTED", "Reason")
        assert ok is True
        assert fake_user.status == "REJECTED"

    # -- get_dashboard_stats
    def test_get_dashboard_stats(self):
        self.repo_mock.count_by_status.return_value = 5
        self.repo_mock.count_by_role.return_value = 10

        stats = AdminUserService.get_dashboard_stats()
        expected_keys = {
            "total_pending", "total_active", "total_suspended",
            "total_rejected", "total_employers", "total_candidates",
        }
        roles_called = [c.args[0] for c in self.repo_mock.count_by_role.call_args_list]
        statuses_called = [c.args[0] for c in self.repo_mock.count_by_status.call_args_list]
        assert set(statuses_called) == {"PENDING", "ACTIVE", "SUSPENDED", "REJECTED"}
        assert set(roles_called) == {"EMPLOYER", "CANDIDATE"}
        assert stats['total_pending'] == 5
        assert stats['total_employers'] == 10
        assert self.repo_mock.count_by_status.call_count == 4
        assert self.repo_mock.count_by_role.call_count == 2
        assert expected_keys == set(stats.keys())

#══════════════════════════════════════════════════════════════════════
# 3. MailService  (admin notification)
#     file: app/services/admin/notification_service.py
# ══════════════════════════════════════════════════════════════════════

class TestMailService:
   @pytest.fixture(autouse=True)
   def setup(self):
       self.mail_ext   = MagicMock()
       self.msg_cls    = MagicMock()
       self.cur_app    = MagicMock()
       self.render_tpl = MagicMock(return_value="<html/>")


       with patch("app.services.admin.notification_service.mail", self.mail_ext), \
            patch("app.services.admin.notification_service.Message", self.msg_cls), \
            patch("app.services.admin.notification_service.current_app", self.cur_app), \
            patch("app.services.admin.notification_service.render_template", self.render_tpl):
           from app.services.admin.notification_service import MailService
           self.svc = MailService
           yield


   # -- notify_status_change --
   def test_notify_status_change_unknown_status_does_nothing(self):
       user = MagicMock()
       self.svc.notify_status_change(user, "UNKNOWN")
       self.mail_ext.send.assert_not_called()


   def test_notify_status_change_active_sends_mail(self):
       user = MagicMock(email="a@b.com", employer=None, candidate=None)
       self.svc.notify_status_change(user, "ACTIVE")
       self.mail_ext.send.assert_called_once()


   def test_notify_status_change_rejected_sends_mail(self):
       user = MagicMock(email="a@b.com", employer=None, candidate=None)
       self.svc.notify_status_change(user, "REJECTED", reason="Hồ sơ giả")
       self.mail_ext.send.assert_called_once()


   def test_notify_status_change_suspended_sends_mail(self):
       user = MagicMock(email="a@b.com", employer=None, candidate=None)
       self.svc.notify_status_change(user, "SUSPENDED", reason="Vi phạm")
       self.mail_ext.send.assert_called_once()


   def test_notify_status_change_uses_company_name_for_employer(self):
       employer = MagicMock(company_name="TechCorp")
       user = MagicMock(email="a@b.com", employer=employer, candidate=None)
       self.svc.notify_status_change(user, "ACTIVE")
       # Chỉ cần verify mail.send được gọi (display_name resolve đúng)
       self.mail_ext.send.assert_called_once()


   def test_notify_status_change_uses_full_name_for_candidate(self):
       candidate = MagicMock(full_name="Nguyen Van A")
       user = MagicMock(email="a@b.com", employer=None, candidate=candidate)
       self.svc.notify_status_change(user, "ACTIVE")
       self.mail_ext.send.assert_called_once()


   def test_notify_status_change_mail_exception_logs_error(self):
       user = MagicMock(email="a@b.com", employer=None, candidate=None)
       self.mail_ext.send.side_effect = Exception("SMTP error")
       # Không raise — chỉ log
       self.svc.notify_status_change(user, "ACTIVE")
       self.cur_app.logger.error.assert_called_once()


   # -- send_recommendation_email --
   def test_send_recommendation_email_sends_mail(self):
       msg_instance = MagicMock()
       self.msg_cls.return_value = msg_instance
       self.svc.send_recommendation_email("a@b.com", "Nguyen Van A", [MagicMock()])
       self.mail_ext.send.assert_called_once_with(msg_instance)


   def test_send_recommendation_email_calls_render_template(self):
       msg_instance = MagicMock()
       self.msg_cls.return_value = msg_instance
       jobs = [MagicMock()]
       self.svc.send_recommendation_email("a@b.com", "Nhi", jobs)
       self.render_tpl.assert_called_once_with(
           "pages/admin/recommendation.html",
           candidate_name="Nhi",
           jobs=jobs,
       )

# ══════════════════════════════════════════════════════════════════════
# 4. JobRecommendationService
#    file: app/services/admin/job_recommendation_service.py
# ═════════════════════════════════════════════════════════════════════

class TestJobRecommendationService:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cur_app = MagicMock()
        with patch("app.services.admin.job_recommendation_service.CandidateRepository") as mock_candidate_repo, \
             patch("app.services.admin.job_recommendation_service.JobService") as mock_job_service, \
             patch("app.services.admin.job_recommendation_service.MailService") as mock_mail_service, \
             patch("app.services.admin.job_recommendation_service.current_app", self.cur_app):

            self.candidate_repo = mock_candidate_repo
            self.job_service = mock_job_service
            self.mail_service = mock_mail_service

            yield

    # -- send_weekly_recommendations --

    def test_send_recommendations_success(self):
        fake_candidate = MagicMock()
        fake_candidate.id = 1
        fake_candidate.full_name = "A"
        fake_candidate.user.email = "a@gmail.com"

        fake_job = MagicMock()
        fake_job.title = "Dev"

        self.candidate_repo.find_all_candidate.return_value = [fake_candidate]
        self.job_service.get_recommended_jobs.return_value = [fake_job]

        JobRecommendationService.send_weekly_recommendations()

        self.mail_service.send_recommendation_email.assert_called_once()

    def test_no_jobs_no_email(self):
        fake_candidate = MagicMock()
        fake_candidate.id = 1
        fake_candidate.full_name = "A"
        fake_candidate.user.email = "a@gmail.com"

        self.candidate_repo.find_all_candidate.return_value = [fake_candidate]
        self.job_service.get_recommended_jobs.return_value = []

        JobRecommendationService.send_weekly_recommendations()

        self.mail_service.send_recommendation_email.assert_not_called()

    def test_multiple_candidates(self):
        c1 = MagicMock(id=1)
        c1.full_name = "A"
        c1.user.email = "a@gmail.com"

        c2 = MagicMock(id=2)
        c2.full_name = "B"
        c2.user.email = "b@gmail.com"

        fake_job = MagicMock(title="Dev")

        self.candidate_repo.find_all_candidate.return_value = [c1, c2]
        self.job_service.get_recommended_jobs.return_value = [fake_job]

        JobRecommendationService.send_weekly_recommendations()

        assert self.mail_service.send_recommendation_email.call_count == 2

    def test_send_weekly_recommendations_resilience(self):
        c1 = MagicMock(id=1, full_name="A")

        c2 = MagicMock(id=2, full_name = "B")
        c2.user.email = "b@gmail.com"

        self.candidate_repo.find_all_candidate.return_value = [c1, c2]
        self.job_service.get_recommended_jobs.side_effect = [Exception("Error"), [MagicMock(title="Dev")]]

        JobRecommendationService.send_weekly_recommendations()

        assert self.mail_service.send_recommendation_email.call_count == 1

#══════════════════════════════════════════════════════════════════════
# 5. AuthService  (candidate login)
#    file: app/services/candidate/auth_service.py
# ══════════════════════════════════════════════════════════════════════


class TestAuthService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.repo = MagicMock()
       with patch("app.services.auth.auth_service.UserRepository", self.repo):
           from app.services.auth.auth_service import AuthService
           self.svc = AuthService
           yield


   def test_login_user_not_found_returns_none(self):
       self.repo.find_by_email.return_value = None
       assert self.svc.login("a@b.com") is None


   def test_login_inactive_user_returns_none(self):
       user = MagicMock(is_active=False)
       self.repo.find_by_email.return_value = user
       assert self.svc.login("a@b.com") is None


   def test_login_active_user_returns_user(self):
       user = MagicMock(is_active=True)
       self.repo.find_by_email.return_value = user
       assert self.svc.login("a@b.com") is user


   def test_login_calls_find_by_email_with_given_email(self):
       self.repo.find_by_email.return_value = None
       self.svc.login("test@example.com")
       self.repo.find_by_email.assert_called_once_with("test@example.com")




# ══════════════════════════════════════════════════════════════════════
# 6. ApplicationService  (candidate — ứng tuyển)
#    file: app/services/candidate/application_service.py
# ══════════════════════════════════════════════════════════════════════


class TestCandidateApplicationService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.repo = MagicMock()
       self.app_cls = MagicMock()
       with patch("app.services.candidate.application_service.ApplicationRepository", self.repo), \
            patch("app.services.candidate.application_service.Application", self.app_cls):
           from app.services.candidate.application_service import ApplicationService
           self.svc = ApplicationService
           yield


   def test_apply_duplicate_cv_raises_value_error(self):
       self.repo.find_by_job_and_cv.return_value = MagicMock()
       with pytest.raises(ValueError, match="đã ứng tuyển"):
           self.svc.apply("a@b.com", job_id=1, cv_id=1)


   def test_apply_duplicate_does_not_call_save(self):
       self.repo.find_by_job_and_cv.return_value = MagicMock()
       with pytest.raises(ValueError):
           self.svc.apply("a@b.com", job_id=1, cv_id=1)
       self.repo.save.assert_not_called()


   def test_apply_success_calls_save(self):
       self.repo.find_by_job_and_cv.return_value = None
       self.svc.apply("a@b.com", job_id=1, cv_id=2)
       self.repo.save.assert_called_once()


   def test_apply_success_creates_application_with_pending_status(self):
       self.repo.find_by_job_and_cv.return_value = None
       self.svc.apply("a@b.com", job_id=1, cv_id=2)
       kwargs = self.app_cls.call_args.kwargs
       assert kwargs["status"] == "PENDING"
       assert kwargs["email"] == "a@b.com"
       assert kwargs["job_id"] == 1
       assert kwargs["cv_id"] == 2


   def test_apply_calls_find_with_correct_job_and_cv(self):
       self.repo.find_by_job_and_cv.return_value = None
       self.svc.apply("a@b.com", job_id=10, cv_id=20)
       self.repo.find_by_job_and_cv.assert_called_once_with(10, 20)




# ══════════════════════════════════════════════════════════════════════
# 7. CandidateService
#    file: app/services/candidate/candidate_service.py
# ══════════════════════════════════════════════════════════════════════


class TestCandidateService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.cand_repo  = MagicMock()
       self.edu_repo   = MagicMock()
       self.exp_repo   = MagicMock()
       self.skill_repo = MagicMock()
       self.sk_repo    = MagicMock()
       self.db         = MagicMock()


       with patch("app.services.candidate.candidate_service.CandidateRepository", self.cand_repo), \
            patch("app.services.candidate.candidate_service.CandidateEducationRepository", self.edu_repo), \
            patch("app.services.candidate.candidate_service.CandidateExperienceRepository", self.exp_repo), \
            patch("app.services.candidate.candidate_service.CandidateSkillRepository", self.skill_repo), \
            patch("app.services.candidate.candidate_service.SkillRepository", self.sk_repo), \
            patch("app.services.candidate.candidate_service.db", self.db):
           from app.services.candidate.candidate_service import CandidateService
           self.svc = CandidateService
           yield


   # ── get_candidate_profile ─────────────────────────────────────────


   def test_get_candidate_profile_found_returns_candidate(self):
       candidate = MagicMock()
       self.cand_repo.get_full_profile.return_value = candidate
       assert self.svc.get_candidate_profile(1) is candidate


   def test_get_candidate_profile_not_found_returns_none(self):
       self.cand_repo.get_full_profile.return_value = None
       assert self.svc.get_candidate_profile(99) is None


   # ── get_full_profile / get_candidate_by_id ────────────────────────


   def test_get_full_profile_calls_repo(self):
       self.svc.get_full_profile(1)
       self.cand_repo.get_full_by_id.assert_called_once_with(1)


   def test_get_candidate_by_id_calls_repo(self):
       self.svc.get_candidate_by_id(5)
       self.cand_repo.get_full_by_id.assert_called_once_with(5)


   # ── update_profile ────────────────────────────────────────────────


   def test_update_profile_section_all_calls_all_repos(self):
       self.svc.update_profile(1, {"section": "all"})
       self.cand_repo.update_basic_info.assert_called_once()
       self.cand_repo.update_bio.assert_called_once()
       self.exp_repo.replace_all.assert_called_once()
       self.edu_repo.replace_all.assert_called_once()
       self.skill_repo.replace_all.assert_called_once()


   def test_update_profile_section_basic_calls_only_basic(self):
       self.svc.update_profile(1, {"section": "basic"})
       self.cand_repo.update_basic_info.assert_called_once()
       self.cand_repo.update_bio.assert_not_called()
       self.exp_repo.replace_all.assert_not_called()


   def test_update_profile_section_bio_calls_only_bio(self):
       self.svc.update_profile(1, {"section": "bio"})
       self.cand_repo.update_bio.assert_called_once()
       self.cand_repo.update_basic_info.assert_not_called()


   def test_update_profile_section_experiences_calls_only_exp(self):
       self.svc.update_profile(1, {"section": "experiences"})
       self.exp_repo.replace_all.assert_called_once()
       self.edu_repo.replace_all.assert_not_called()


   def test_update_profile_section_educations_calls_only_edu(self):
       self.svc.update_profile(1, {"section": "educations"})
       self.edu_repo.replace_all.assert_called_once()
       self.exp_repo.replace_all.assert_not_called()


   def test_update_profile_section_skills_calls_only_skills(self):
       self.svc.update_profile(1, {"section": "skills"})
       self.skill_repo.replace_all.assert_called_once()
       self.cand_repo.update_basic_info.assert_not_called()


   def test_update_profile_unknown_section_calls_nothing(self):
       self.svc.update_profile(1, {"section": "unknown"})
       self.cand_repo.update_basic_info.assert_not_called()
       self.cand_repo.update_bio.assert_not_called()


   # ── save_extracted_profile ────────────────────────────────────────


   def test_save_extracted_profile_calls_update_basic_info(self):
       self.cand_repo.get_full_by_id.return_value = MagicMock()
       self.svc.save_extracted_profile(1, {"experiences": [], "educations": [], "skills": []})
       self.cand_repo.update_basic_info.assert_called_once()


   def test_save_extracted_profile_calls_replace_all_from_list_for_exp(self):
       self.cand_repo.get_full_by_id.return_value = MagicMock()
       exps = [{"company": "A"}]
       self.svc.save_extracted_profile(1, {"experiences": exps, "educations": [], "skills": []})
       self.exp_repo.replace_all_from_list.assert_called_once_with(1, exps)


   def test_save_extracted_profile_numeric_skill_converted_to_int(self):
       self.cand_repo.get_full_by_id.return_value = MagicMock()
       self.svc.save_extracted_profile(1, {
           "experiences": [], "educations": [], "skills": ["5", "10"]
       })
       self.skill_repo.replace_all_from_ids.assert_called_once_with(1, [5, 10])
       self.sk_repo.get_or_create.assert_not_called()


   def test_save_extracted_profile_string_skill_calls_get_or_create(self):
       skill_obj = MagicMock(id=99)
       self.sk_repo.get_or_create.return_value = skill_obj
       self.cand_repo.get_full_by_id.return_value = MagicMock()
       self.svc.save_extracted_profile(1, {
           "experiences": [], "educations": [], "skills": ["python"]
       })
       self.sk_repo.get_or_create.assert_called_once_with("python")
       self.skill_repo.replace_all_from_ids.assert_called_once_with(1, [99])


   def test_save_extracted_profile_mixed_skills(self):
       skill_obj = MagicMock(id=77)
       self.sk_repo.get_or_create.return_value = skill_obj
       self.cand_repo.get_full_by_id.return_value = MagicMock()
       self.svc.save_extracted_profile(1, {
           "experiences": [], "educations": [], "skills": ["3", "flask"]
       })
       self.skill_repo.replace_all_from_ids.assert_called_once_with(1, [3, 77])


   def test_save_extracted_profile_commits_db(self):
       self.cand_repo.get_full_by_id.return_value = MagicMock()
       self.svc.save_extracted_profile(1, {"experiences": [], "educations": [], "skills": []})
       self.db.session.commit.assert_called_once()


   def test_save_extracted_profile_returns_candidate(self):
       candidate = MagicMock()
       self.cand_repo.get_full_by_id.return_value = candidate
       result = self.svc.save_extracted_profile(1, {"experiences": [], "educations": [], "skills": []})
       assert result is candidate




# ══════════════════════════════════════════════════════════════════════
# 8. CVService
#    file: app/services/candidate/cv_service.py
# ══════════════════════════════════════════════════════════════════════


class TestCVService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.cv_repo    = MagicMock()
       self.skill_repo = MagicMock()
       self.db         = MagicMock()
       self.cv_cls     = MagicMock()
       self.tpl_cls    = MagicMock()
       self.builder    = MagicMock()


       with patch("app.services.candidate.cv_service.CVRepository", self.cv_repo), \
            patch("app.services.candidate.cv_service.CVSkillRepository", self.skill_repo), \
            patch("app.services.candidate.cv_service.db", self.db), \
            patch("app.services.candidate.cv_service.CV", self.cv_cls), \
            patch("app.services.candidate.cv_service.CVTemplate", self.tpl_cls), \
            patch("app.services.candidate.cv_service.CVFormBuilder", self.builder):
           from app.services.candidate.cv_service import CVService
           self.svc = CVService
           yield


   # ── create_online_cv ──────────────────────────────────────────────


   def test_create_online_cv_adds_to_session(self):
       template = MagicMock(schema_version=1)
       self.tpl_cls.query.get.return_value = template
       self.builder.build_from_request.return_value = {}
       form_data = MagicMock()
       form_data.get.return_value = []
       self.svc.create_online_cv(1, 2, form_data, "avatar.png", "My CV")
       self.db.session.add.assert_called_once()


   def test_create_online_cv_saves_skills(self):
       template = MagicMock(schema_version=1)
       self.tpl_cls.query.get.return_value = template
       self.builder.build_from_request.return_value = {}
       form_data = MagicMock()
       form_data.get.return_value = [1, 2]
       self.svc.create_online_cv(1, 2, form_data, "avatar.png", "My CV")
       self.skill_repo.add_cv_skill.assert_called_once()


   def test_create_online_cv_sets_avatar_in_content_json(self):
       template = MagicMock(schema_version=1)
       self.tpl_cls.query.get.return_value = template
       content = {}
       self.builder.build_from_request.return_value = content
       form_data = MagicMock()
       form_data.get.return_value = []
       self.svc.create_online_cv(1, 2, form_data, "https://cdn/avatar.png", "My CV")
       assert content["avatar"] == "https://cdn/avatar.png"


   # ── get_candidate_cvs ─────────────────────────────────────────────


   def test_get_candidate_cvs_returns_online_and_upload(self):
       self.cv_repo.get_online_by_candidate.return_value = ["online_cv"]
       self.cv_repo.get_upload_by_candidate.return_value = ["upload_cv"]
       online, upload = self.svc.get_candidate_cvs(1)
       assert online == ["online_cv"]
       assert upload == ["upload_cv"]


   def test_get_candidate_cvs_calls_repos_with_correct_id(self):
       self.cv_repo.get_online_by_candidate.return_value = []
       self.cv_repo.get_upload_by_candidate.return_value = []
       self.svc.get_candidate_cvs(42)
       self.cv_repo.get_online_by_candidate.assert_called_once_with(42)
       self.cv_repo.get_upload_by_candidate.assert_called_once_with(42)


   # ── get_cv_for_view ───────────────────────────────────────────────


   def test_get_cv_for_view_found_returns_cv(self):
       cv = MagicMock()
       self.cv_repo.get_by_id.return_value = cv
       assert self.svc.get_cv_for_view(1) is cv


   def test_get_cv_for_view_not_found_returns_none(self):
       self.cv_repo.get_by_id.return_value = None
       assert self.svc.get_cv_for_view(99) is None


   # ── update_online_cv ──────────────────────────────────────────────


   def test_update_online_cv_sets_content_json_and_title(self):
       cv = MagicMock()
       self.cv_repo.get_by_id.return_value = cv
       self.svc.update_online_cv(1, {"key": "val"}, [], "New Title")
       assert cv.content_json == {"key": "val"}
       assert cv.title == "New Title"


   def test_update_online_cv_saves_cv(self):
       cv = MagicMock()
       self.cv_repo.get_by_id.return_value = cv
       self.svc.update_online_cv(1, {}, [], "T")
       self.cv_repo.save.assert_called_once_with(cv)


   def test_update_online_cv_deletes_old_skills_then_adds_new(self):
       cv = MagicMock()
       self.cv_repo.get_by_id.return_value = cv
       self.svc.update_online_cv(1, {}, [10, 20], "T")
       self.skill_repo.delete_by_cv.assert_called_once_with(1)
       self.skill_repo.add_cv_skill.assert_called_once_with(1, [10, 20])


   def test_update_online_cv_returns_cv(self):
       cv = MagicMock()
       self.cv_repo.get_by_id.return_value = cv
       result = self.svc.update_online_cv(1, {}, [], "T")
       assert result is cv


   # ── delete_cv ────────────────────────────────────────────────────


   def test_delete_cv_calls_repo_delete_with_cv(self):
       cv = MagicMock()
       self.cv_repo.get_by_id.return_value = cv
       self.svc.delete_cv(1)
       self.cv_repo.delete.assert_called_once_with(cv)


   # ── exists_by_title ───────────────────────────────────────────────


   def test_exists_by_title_true(self):
       self.cv_repo.exists_by_title.return_value = True
       assert self.svc.exists_by_title("My CV") is True


   def test_exists_by_title_false(self):
       self.cv_repo.exists_by_title.return_value = False
       assert self.svc.exists_by_title("Unknown") is False




# ══════════════════════════════════════════════════════════════════════
# 9. CVSkillService
#    file: app/services/candidate/cv_skill_service.py
# ══════════════════════════════════════════════════════════════════════


class TestCVSkillService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.cv_skill_repo = MagicMock()
       self.skill_repo    = MagicMock()
       with patch("app.services.candidate.cv_skill_service.CVSkillRepository", self.cv_skill_repo), \
            patch("app.services.candidate.cv_skill_service.SkillRepository", self.skill_repo):
           from app.services.candidate.cv_skill_service import CVSkillService
           self.svc = CVSkillService
           yield


   def test_get_by_cv_returns_repo_result(self):
       self.cv_skill_repo.get_by_cv.return_value = ["s1", "s2"]
       assert self.svc.get_by_cv(1) == ["s1", "s2"]


   def test_get_by_cv_calls_repo_with_id(self):
       self.cv_skill_repo.get_by_cv.return_value = []
       self.svc.get_by_cv(7)
       self.cv_skill_repo.get_by_cv.assert_called_once_with(7)


   def test_delete_by_cv_calls_repo(self):
       self.svc.delete_by_cv(3)
       self.cv_skill_repo.delete_by_cv.assert_called_once_with(3)


   def test_get_skills_by_cv_returns_empty_when_no_skill_ids(self):
       self.cv_skill_repo.get_skill_ids_by_cv.return_value = []
       assert self.svc.get_skills_by_cv(1) == []


   def test_get_skills_by_cv_does_not_call_skill_repo_when_empty(self):
       self.cv_skill_repo.get_skill_ids_by_cv.return_value = []
       self.svc.get_skills_by_cv(1)
       self.skill_repo.get_by_ids.assert_not_called()


   def test_get_skills_by_cv_returns_skills_when_ids_exist(self):
       self.cv_skill_repo.get_skill_ids_by_cv.return_value = [1, 2]
       skills = [MagicMock(), MagicMock()]
       self.skill_repo.get_by_ids.return_value = skills
       result = self.svc.get_skills_by_cv(1)
       assert result == skills


   def test_get_skills_by_cv_calls_get_by_ids_with_correct_ids(self):
       self.cv_skill_repo.get_skill_ids_by_cv.return_value = [5, 10]
       self.skill_repo.get_by_ids.return_value = []
       self.svc.get_skills_by_cv(1)
       self.skill_repo.get_by_ids.assert_called_once_with([5, 10])


   def test_get_skill_names_by_cv_returns_name_list(self):
       s1, s2 = MagicMock(), MagicMock()
       s1.name = "Python"
       s2.name = "Flask"
       self.cv_skill_repo.get_skill_ids_by_cv.return_value = [1, 2]
       self.skill_repo.get_by_ids.return_value = [s1, s2]
       assert self.svc.get_skill_names_by_cv(1) == ["Python", "Flask"]


   def test_get_skill_names_by_cv_empty_when_no_skills(self):
       self.cv_skill_repo.get_skill_ids_by_cv.return_value = []
       assert self.svc.get_skill_names_by_cv(1) == []




# ══════════════════════════════════════════════════════════════════════
# 10. CvTemplateService
#    file: app/services/candidate/cv_template_service.py
# ══════════════════════════════════════════════════════════════════════


class TestCvTemplateService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.repo = MagicMock()
       with patch("app.services.candidate.cv_template_service.CVTemplateRepository", self.repo):
           from app.services.candidate.cv_template_service import CvTemplateService
           self.svc = CvTemplateService
           yield


   def test_get_template_not_found_returns_none(self):
       self.repo.get_by_id.return_value = None
       assert self.svc.get_template(99) is None


   def test_get_template_found_returns_dict_with_all_keys(self):
       tpl = MagicMock(id=1, slug="modern", description="desc",
           preview_image="img.png", html_content="<html/>",
           schema_version=2, is_active=True,)

       tpl.name="Modern"

       self.repo.get_by_id.return_value = tpl
       result = self.svc.get_template(1)
       assert result["id"] == 1
       assert result["name"] == "Modern"
       assert result["slug"] == "modern"
       assert result["description"] == "desc"
       assert result["preview"] == "img.png"
       assert result["html_content"] == "<html/>"
       assert result["schema_version"] == 2
       assert result["is_active"] is True


   def test_get_template_calls_repo_with_id(self):
       self.repo.get_by_id.return_value = None
       self.svc.get_template(5)
       self.repo.get_by_id.assert_called_once_with(5)


   def test_get_active_templates_returns_list_of_dicts(self):
       t = MagicMock()
       t.id = 1
       t.name = "A"
       t.slug = "a"
       t.preview_image = "p.png"
       self.repo.get_active_templates.return_value = [t]
       result = self.svc.get_active_templates()
       assert len(result) == 1
       assert result[0] == {"id": 1, "name": "A", "slug": "a", "preview": "p.png"}


   def test_get_active_templates_empty_returns_empty_list(self):
       self.repo.get_active_templates.return_value = []
       assert self.svc.get_active_templates() == []


   def test_get_active_templates_multiple(self):
       t1 = MagicMock(id=1, name="A", slug="a", preview_image="1.png")
       t2 = MagicMock(id=2, name="B", slug="b", preview_image="2.png")
       self.repo.get_active_templates.return_value = [t1, t2]
       result = self.svc.get_active_templates()
       assert len(result) == 2
       assert result[1]["slug"] == "b"




# ══════════════════════════════════════════════════════════════════════
# 11. CVUploadService
#    file: app/services/candidate/cv_upload_service.py
# ══════════════════════════════════════════════════════════════════════


class TestCVUploadService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.repo   = MagicMock()
       self.cv_cls = MagicMock()
       with patch("app.services.candidate.cv_upload_service.CVUploadRepository", self.repo), \
            patch("app.services.candidate.cv_upload_service.CV", self.cv_cls), \
            patch("app.services.candidate.cv_upload_service.os.makedirs"), \
            patch("app.services.candidate.cv_upload_service.os.path.exists", return_value=False):
           from app.services.candidate.cv_upload_service import CVUploadService
           self.svc = CVUploadService
           yield


   # ── allowed_file ──────────────────────────────────────────────────


   def test_allowed_file_pdf_returns_true(self):
       assert self.svc.allowed_file("resume.pdf") is True


   def test_allowed_file_docx_returns_true(self):
       assert self.svc.allowed_file("resume.docx") is True


   def test_allowed_file_doc_returns_true(self):
       assert self.svc.allowed_file("resume.doc") is True


   def test_allowed_file_uppercase_ext_returns_true(self):
       assert self.svc.allowed_file("RESUME.PDF") is True


   def test_allowed_file_txt_returns_false(self):
       assert self.svc.allowed_file("resume.txt") is False


   def test_allowed_file_exe_returns_false(self):
       assert self.svc.allowed_file("virus.exe") is False


   def test_allowed_file_no_extension_returns_false(self):
       assert self.svc.allowed_file("noextension") is False


   # ── get_candidate ─────────────────────────────────────────────────


   def test_get_candidate_calls_repo(self):
       self.svc.get_candidate(1)
       self.repo.find_candidate_by_user_id.assert_called_once_with(1)


   # ── get_uploaded_cvs ──────────────────────────────────────────────


   def test_get_uploaded_cvs_no_candidate_returns_empty(self):
       self.repo.find_candidate_by_user_id.return_value = None
       assert self.svc.get_uploaded_cvs(1) == []


   def test_get_uploaded_cvs_with_candidate_returns_cvs(self):
       candidate = MagicMock(id=10)
       self.repo.find_candidate_by_user_id.return_value = candidate
       self.repo.find_cvs_by_candidate_id.return_value = ["cv1"]
       result = self.svc.get_uploaded_cvs(1)
       assert result == ["cv1"]
       self.repo.find_cvs_by_candidate_id.assert_called_once_with(10)


   # ── upload_cv ─────────────────────────────────────────────────────


   def test_upload_cv_no_candidate_returns_false(self):
       self.repo.find_candidate_by_user_id.return_value = None
       ok, msg = self.svc.upload_cv(1, MagicMock(filename="cv.pdf"), "title")
       assert ok is False
       assert "hồ sơ ứng viên" in msg


   def test_upload_cv_no_file_returns_false(self):
       self.repo.find_candidate_by_user_id.return_value = MagicMock()
       ok, msg = self.svc.upload_cv(1, None, "title")
       assert ok is False
       assert "chọn file" in msg


   def test_upload_cv_empty_filename_returns_false(self):
       self.repo.find_candidate_by_user_id.return_value = MagicMock()
       file = MagicMock(filename="")
       ok, msg = self.svc.upload_cv(1, file, "title")
       assert ok is False


   def test_upload_cv_invalid_extension_returns_false(self):
       self.repo.find_candidate_by_user_id.return_value = MagicMock()
       file = MagicMock(filename="cv.txt")
       ok, msg = self.svc.upload_cv(1, file, "title")
       assert ok is False
       assert "Định dạng" in msg


   def test_upload_cv_file_too_large_returns_false(self):
       self.repo.find_candidate_by_user_id.return_value = MagicMock()
       file = MagicMock(filename="cv.pdf")
       file.seek = MagicMock()
       file.tell = MagicMock(return_value=6 * 1024 * 1024)  # 6MB > 5MB
       ok, msg = self.svc.upload_cv(1, file, "title")
       assert ok is False
       assert "5MB" in msg


   def test_upload_cv_success_saves_cv(self):
       candidate = MagicMock(id=5)
       self.repo.find_candidate_by_user_id.return_value = candidate
       file = MagicMock(filename="cv.pdf")
       file.seek = MagicMock()
       file.tell = MagicMock(return_value=1024)
       file.save = MagicMock()
       with patch("app.services.candidate.cv_upload_service.secure_filename", return_value="cv.pdf"), \
            patch("app.services.candidate.cv_upload_service.uuid.uuid4") as mock_uuid:
           mock_uuid.return_value.hex = "abc123"
           ok, msg = self.svc.upload_cv(1, file, "My Resume")
       assert ok is True
       assert "thành công" in msg
       self.repo.save_cv.assert_called_once()


   def test_upload_cv_uses_original_filename_when_title_empty(self):
       candidate = MagicMock(id=5)
       self.repo.find_candidate_by_user_id.return_value = candidate
       file = MagicMock(filename="my_cv.pdf")
       file.seek = MagicMock()
       file.tell = MagicMock(return_value=1024)
       file.save = MagicMock()
       with patch("app.services.candidate.cv_upload_service.secure_filename", return_value="my_cv.pdf"), \
            patch("app.services.candidate.cv_upload_service.uuid.uuid4") as mock_uuid:
           mock_uuid.return_value.hex = "xyz"
           self.svc.upload_cv(1, file, "")
       cv_kwargs = self.cv_cls.call_args.kwargs
       assert cv_kwargs["title"] == "my_cv.pdf"


   # ── delete_cv ────────────────────────────────────────────────────


   def test_delete_cv_no_candidate_returns_false(self):
       self.repo.find_candidate_by_user_id.return_value = None
       ok, msg = self.svc.delete_cv(1, 10)
       assert ok is False
       assert "hồ sơ ứng viên" in msg


   def test_delete_cv_cv_not_found_returns_false(self):
       self.repo.find_candidate_by_user_id.return_value = MagicMock(id=1)
       self.repo.find_cv_by_id.return_value = None
       ok, msg = self.svc.delete_cv(1, 10)
       assert ok is False


   def test_delete_cv_wrong_owner_returns_false(self):
       candidate = MagicMock(id=1)
       self.repo.find_candidate_by_user_id.return_value = candidate
       cv = MagicMock(candidate_id=999)  # khác candidate.id
       self.repo.find_cv_by_id.return_value = cv
       ok, msg = self.svc.delete_cv(1, 10)
       assert ok is False
       assert "quyền" in msg


   def test_delete_cv_success_calls_delete_cv(self):
       candidate = MagicMock(id=1)
       cv = MagicMock(candidate_id=1, file_url="/static/uploads/cvs/file.pdf")
       self.repo.find_candidate_by_user_id.return_value = candidate
       self.repo.find_cv_by_id.return_value = cv
       with patch("app.services.candidate.cv_upload_service.os.path.exists", return_value=False):
           ok, msg = self.svc.delete_cv(1, 10)
       assert ok is True
       self.repo.delete_cv.assert_called_once_with(cv)


   def test_delete_cv_deletes_physical_file_when_exists(self):
       candidate = MagicMock(id=1)
       cv = MagicMock(candidate_id=1, file_url="/static/uploads/cvs/file.pdf")
       self.repo.find_candidate_by_user_id.return_value = candidate
       self.repo.find_cv_by_id.return_value = cv
       with patch("app.services.candidate.cv_upload_service.os.path.exists", return_value=True), \
            patch("app.services.candidate.cv_upload_service.os.remove") as mock_rm:
           self.svc.delete_cv(1, 10)
           mock_rm.assert_called_once()




# ══════════════════════════════════════════════════════════════════════
# 12. JobService  (candidate — tìm kiếm & recommendation)
#     file: app/services/candidate/job_service.py
# ══════════════════════════════════════════════════════════════════════


class TestCandidateJobService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.job_repo        = MagicMock()
       self.candidate_skill = MagicMock()
       self.candidate_exp   = MagicMock()
       self.job_model       = MagicMock()


       with patch("app.services.candidate.job_service.JobRepository", self.job_repo), \
            patch("app.services.candidate.job_service.CandidateSkill", self.candidate_skill), \
            patch("app.services.candidate.job_service.CandidateExperience", self.candidate_exp), \
            patch("app.services.candidate.job_service.Job", self.job_model):
           from app.services.candidate.job_service import JobService
           self.svc = JobService
           yield


   # ── search_job ────────────────────────────────────────────────────


   def test_search_job_no_filter_passes_all_none(self):
       self.job_repo.search_jobs.return_value = MagicMock()
       self.svc.search_job({})
       kwargs = self.job_repo.search_jobs.call_args.kwargs
       assert kwargs["keyword"] is None
       assert kwargs["location"] is None
       assert kwargs["salary_min"] is None
       assert kwargs["salary_max"] is None
       assert kwargs["experience"] is None


   def test_search_job_keyword_is_stripped(self):
       self.job_repo.search_jobs.return_value = MagicMock()
       self.svc.search_job({"keyword": "  flask  "})
       kwargs = self.job_repo.search_jobs.call_args.kwargs
       assert kwargs["keyword"] == "flask"


   def test_search_job_blank_keyword_becomes_none(self):
       self.job_repo.search_jobs.return_value = MagicMock()
       self.svc.search_job({"keyword": "   "})
       kwargs = self.job_repo.search_jobs.call_args.kwargs
       assert kwargs["keyword"] is None


   def test_search_job_valid_salary_parsed_to_int(self):
       self.job_repo.search_jobs.return_value = MagicMock()
       self.svc.search_job({"salary_min": "1000", "salary_max": "5000"})
       kwargs = self.job_repo.search_jobs.call_args.kwargs
       assert kwargs["salary_min"] == 1000
       assert kwargs["salary_max"] == 5000


   def test_search_job_invalid_salary_becomes_none(self):
       self.job_repo.search_jobs.return_value = MagicMock()
       self.svc.search_job({"salary_min": "abc", "salary_max": "xyz"})
       kwargs = self.job_repo.search_jobs.call_args.kwargs
       assert kwargs["salary_min"] is None
       assert kwargs["salary_max"] is None


   def test_search_job_page_param_forwarded(self):
       self.job_repo.search_jobs.return_value = MagicMock()
       self.svc.search_job({}, page=3)
       kwargs = self.job_repo.search_jobs.call_args.kwargs
       assert kwargs["page"] == 3


   def test_search_job_returns_pagination(self):
       pagination = MagicMock()
       self.job_repo.search_jobs.return_value = pagination
       assert self.svc.search_job({}) is pagination


   # ── get_filter_options ────────────────────────────────────────────


   def test_get_filter_options_returns_locations(self):
       self.job_repo.get_distinct_locations.return_value = ["HCM", "HN"]
       result = self.svc.get_filter_options()
       assert result == {"locations": ["HCM", "HN"]}


   # ── get_job_detail ────────────────────────────────────────────────


   def test_get_job_detail_calls_repo_and_returns_result(self):
       job = MagicMock()
       self.job_repo.find_by_id.return_value = job
       assert self.svc.get_job_detail(5) is job
       self.job_repo.find_by_id.assert_called_once_with(5)


   # ── get_recommended_jobs ──────────────────────────────────────────


   def test_get_recommended_no_skills_no_exp_returns_empty(self):
       self.candidate_skill.query.filter_by.return_value.all.return_value = []
       self.candidate_exp.query.filter_by.return_value.all.return_value = []
       assert self.svc.get_recommended_jobs(1) == []


   def test_get_recommended_skill_match_100pct_score_70_included(self):
       # Ứng viên có skill_id=5, job yêu cầu skill_id=5 → score=70 > 20
       skill = MagicMock(skill_id=5)
       self.candidate_skill.query.filter_by.return_value.all.return_value = [skill]
       self.candidate_exp.query.filter_by.return_value.all.return_value = []


       job = MagicMock(title="Python Dev")
       js  = MagicMock(skill_id=5)
       job.skills = [js]
       self.job_model.query.filter_by.return_value.all.return_value = [job]


       result = self.svc.get_recommended_jobs(1)
       assert job in result


   def test_get_recommended_no_skill_match_score_0_excluded(self):
       # Ứng viên có skill_id=1, job yêu cầu skill_id=99 → score=0 ≤ 20
       skill = MagicMock(skill_id=1)
       self.candidate_skill.query.filter_by.return_value.all.return_value = [skill]
       self.candidate_exp.query.filter_by.return_value.all.return_value = []


       job = MagicMock(title="Java Dev")
       js  = MagicMock(skill_id=99)
       job.skills = [js]
       self.job_model.query.filter_by.return_value.all.return_value = [job]


       assert self.svc.get_recommended_jobs(1) == []


   def test_get_recommended_position_match_adds_30_points(self):
       # Không có skill, exp position khớp với job title → score=30 > 20
       self.candidate_skill.query.filter_by.return_value.all.return_value = []
       exp = MagicMock(position="python developer")
       self.candidate_exp.query.filter_by.return_value.all.return_value = [exp]


       job = MagicMock(title="Python Developer")
       job.skills = []
       self.job_model.query.filter_by.return_value.all.return_value = [job]


       result = self.svc.get_recommended_jobs(1)
       assert job in result


   def test_get_recommended_respects_limit(self):
       skill = MagicMock(skill_id=1)
       self.candidate_skill.query.filter_by.return_value.all.return_value = [skill]
       self.candidate_exp.query.filter_by.return_value.all.return_value = []


       jobs = []
       for i in range(10):
           j = MagicMock(title=f"Job {i}")
           j.skills = [MagicMock(skill_id=1)]
           jobs.append(j)
       self.job_model.query.filter_by.return_value.all.return_value = jobs


       result = self.svc.get_recommended_jobs(1, limit=3)
       assert len(result) == 3


   def test_get_recommended_sorted_by_score_descending(self):
       # Job A: 1/2 skills → score=35; Job B: 2/2 skills → score=70
       cand_skills = [MagicMock(skill_id=1), MagicMock(skill_id=2)]
       self.candidate_skill.query.filter_by.return_value.all.return_value = cand_skills
       self.candidate_exp.query.filter_by.return_value.all.return_value = []


       job_a = MagicMock(title="Job A")
       job_a.skills = [MagicMock(skill_id=1), MagicMock(skill_id=99)]  # 1/2


       job_b = MagicMock(title="Job B")
       job_b.skills = [MagicMock(skill_id=1), MagicMock(skill_id=2)]   # 2/2


       self.job_model.query.filter_by.return_value.all.return_value = [job_a, job_b]


       result = self.svc.get_recommended_jobs(1)
       assert result[0] is job_b   # điểm cao hơn đứng trước
       assert result[1] is job_a

#══════════════════════════════════════════════════════════════════════
# 13. NotificationService  (candidate)
#     file: app/services/candidate/notification_service.py
# ══════════════════════════════════════════════════════════════════════


class TestNotificationService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.repo = MagicMock()
       with patch("app.services.candidate.notification_service.NotificationRepository", self.repo):
           from app.services.candidate.notification_service import NotificationService
           self.svc = NotificationService
           yield


   def test_get_notifications_calls_repo_with_user_id_and_page(self):
       self.repo.find_by_user_id.return_value = []
       self.svc.get_notifications(1, page=2)
       self.repo.find_by_user_id.assert_called_once_with(1, page=2)


   def test_get_notifications_returns_result(self):
       self.repo.find_by_user_id.return_value = ["notif"]
       assert self.svc.get_notifications(1) == ["notif"]


   def test_count_unread_returns_count(self):
       self.repo.count_unread.return_value = 7
       assert self.svc.count_unread(1) == 7


   def test_count_unread_calls_repo_with_user_id(self):
       self.repo.count_unread.return_value = 0
       self.svc.count_unread(42)
       self.repo.count_unread.assert_called_once_with(42)


   def test_mark_as_read_not_found_returns_none(self):
       self.repo.find_by_id_and_user.return_value = None
       result = self.svc.mark_as_read(99, 1)
       assert result is None


   def test_mark_as_read_already_read_does_not_call_save(self):
       notif = MagicMock(is_read=True)
       self.repo.find_by_id_and_user.return_value = notif
       self.svc.mark_as_read(1, 1)
       self.repo.save.assert_not_called()


   def test_mark_as_read_unread_sets_is_read_true(self):
       notif = MagicMock(is_read=False)
       self.repo.find_by_id_and_user.return_value = notif
       self.svc.mark_as_read(1, 1)
       assert notif.is_read is True


   def test_mark_as_read_unread_calls_save(self):
       notif = MagicMock(is_read=False)
       self.repo.find_by_id_and_user.return_value = notif
       self.svc.mark_as_read(1, 1)
       self.repo.save.assert_called_once_with(notif)


   def test_mark_as_read_returns_notif(self):
       notif = MagicMock(is_read=False)
       self.repo.find_by_id_and_user.return_value = notif
       result = self.svc.mark_as_read(1, 1)
       assert result is notif


   def test_mark_all_as_read_calls_repo(self):
       self.svc.mark_all_as_read(5)
       self.repo.mark_all_as_read.assert_called_once_with(5)




# ══════════════════════════════════════════════════════════════════════
# 14. SkillService
#     file: app/services/candidate/skill_service.py
# ══════════════════════════════════════════════════════════════════════


class TestSkillService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.repo = MagicMock()
       with patch("app.services.candidate.skill_service.SkillRepository", self.repo):
           from app.services.candidate.skill_service import SkillService
           self.svc = SkillService
           yield


   def test_get_all_skills_calls_repo(self):
       self.repo.get_all_skills.return_value = []
       self.svc.get_all_skills()
       self.repo.get_all_skills.assert_called_once()


   def test_get_all_skills_returns_result(self):
       skills = [MagicMock(), MagicMock()]
       self.repo.get_all_skills.return_value = skills
       assert self.svc.get_all_skills() == skills




# ══════════════════════════════════════════════════════════════════════
# 15. UserService  (candidate — profile / avatar)
#     file: app/services/candidate/user_service.py
# ══════════════════════════════════════════════════════════════════════


class TestUserService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.repo       = MagicMock()
       self.cloudinary = MagicMock()
       with patch("app.services.candidate.user_service.UserRepository", self.repo), \
            patch("app.services.candidate.user_service.CloudinaryUtil", self.cloudinary):
           from app.services.candidate.user_service import UserService
           self.svc = UserService
           yield


   # ── _allowed_file ─────────────────────────────────────────────────


   def test_allowed_file_jpg_returns_true(self):
       assert self.svc._allowed_file("photo.jpg") is True


   def test_allowed_file_png_returns_true(self):
       assert self.svc._allowed_file("photo.png") is True


   def test_allowed_file_jpeg_returns_true(self):
       assert self.svc._allowed_file("photo.jpeg") is True


   def test_allowed_file_webp_returns_true(self):
       assert self.svc._allowed_file("photo.webp") is True


   def test_allowed_file_uppercase_returns_true(self):
       assert self.svc._allowed_file("photo.JPG") is True


   def test_allowed_file_pdf_returns_false(self):
       assert self.svc._allowed_file("doc.pdf") is False


   def test_allowed_file_no_extension_returns_false(self):
       assert self.svc._allowed_file("noext") is False


   # ── update_avatar ─────────────────────────────────────────────────


   def test_update_avatar_invalid_type_raises_exception(self):
       file = MagicMock(filename="doc.pdf")
       with pytest.raises(Exception, match="Invalid file type"):
           self.svc.update_avatar(1, file)


   def test_update_avatar_cloudinary_fail_raises_exception(self):
       self.cloudinary.upload_image.return_value = None
       file = MagicMock(filename="photo.jpg")
       with pytest.raises(Exception, match="Upload failed"):
           self.svc.update_avatar(1, file)


   def test_update_avatar_success_calls_update_avatar_repo(self):
       self.cloudinary.upload_image.return_value = "https://cdn/img.jpg"
       file = MagicMock(filename="photo.jpg")
       self.svc.update_avatar(1, file)
       self.repo.update_avatar.assert_called_once_with(1, "https://cdn/img.jpg")


   def test_update_avatar_does_not_call_repo_on_invalid_file(self):
       file = MagicMock(filename="virus.exe")
       with pytest.raises(Exception):
           self.svc.update_avatar(1, file)
       self.repo.update_avatar.assert_not_called()


   # ── get_user_by_id ────────────────────────────────────────────────


   def test_get_user_by_id_returns_user(self):
       user = MagicMock()
       self.repo.find_by_id.return_value = user
       assert self.svc.get_user_by_id(1) is user


   def test_get_user_by_id_calls_repo_with_id(self):
       self.repo.find_by_id.return_value = None
       self.svc.get_user_by_id(99)
       self.repo.find_by_id.assert_called_once_with(99)




# ══════════════════════════════════════════════════════════════════════
# 16. EmployerAuthService
#     file: app/services/employer/employer_auth_service.py
# ══════════════════════════════════════════════════════════════════════


class TestEmployerAuthService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.user_repo     = MagicMock()
       self.employer_repo = MagicMock()
       self.user_cls      = MagicMock()
       self.employer_cls  = MagicMock()


       with patch("app.services.employer.employer_auth_service.UserRepository", self.user_repo), \
            patch("app.services.employer.employer_auth_service.EmployerRepository", self.employer_repo), \
            patch("app.services.employer.employer_auth_service.User", self.user_cls), \
            patch("app.services.employer.employer_auth_service.Employer", self.employer_cls):
           from app.services.employer.employer_auth_service import EmployerAuthService
           self.svc = EmployerAuthService
           yield


   # ── register ──────────────────────────────────────────────────────


   def test_register_missing_email_returns_false(self):
       ok, msg = self.svc.register({"password": "123456", "confirm_password": "123456", "company_name": "ABC"})
       assert ok is False
       assert "bắt buộc" in msg


   def test_register_missing_password_returns_false(self):
       ok, msg = self.svc.register({"email": "a@b.com", "confirm_password": "", "company_name": "ABC"})
       assert ok is False


   def test_register_missing_company_name_returns_false(self):
       ok, msg = self.svc.register({"email": "a@b.com", "password": "123456", "confirm_password": "123456"})
       assert ok is False


   def test_register_password_mismatch_returns_false(self):
       ok, msg = self.svc.register({
           "email": "a@b.com", "password": "123456",
           "confirm_password": "999999", "company_name": "ABC"
       })
       assert ok is False
       assert "xác nhận" in msg


   def test_register_password_too_short_returns_false(self):
       ok, msg = self.svc.register({
           "email": "a@b.com", "password": "12",
           "confirm_password": "12", "company_name": "ABC"
       })
       assert ok is False
       assert "6 ký tự" in msg


   def test_register_email_already_exists_returns_false(self):
       self.user_repo.find_by_email.return_value = MagicMock()
       ok, msg = self.svc.register({
           "email": "a@b.com", "password": "123456",
           "confirm_password": "123456", "company_name": "ABC"
       })
       assert ok is False
       assert "Email" in msg


   def test_register_company_already_exists_returns_false(self):
       self.user_repo.find_by_email.return_value = None
       self.employer_repo.find_by_company_name.return_value = MagicMock()
       ok, msg = self.svc.register({
           "email": "new@b.com", "password": "123456",
           "confirm_password": "123456", "company_name": "Existing Corp"
       })
       assert ok is False
       assert "Tên công ty" in msg


   def test_register_success_returns_true(self):
       self.user_repo.find_by_email.return_value = None
       self.employer_repo.find_by_company_name.return_value = None
       self.user_cls.return_value = MagicMock()
       ok, msg = self.svc.register({
           "email": "new@b.com", "password": "123456",
           "confirm_password": "123456", "company_name": "New Corp"
       })
       assert ok is True
       assert "thành công" in msg


   def test_register_success_saves_user_and_employer(self):
       self.user_repo.find_by_email.return_value = None
       self.employer_repo.find_by_company_name.return_value = None
       user_instance = MagicMock()
       self.user_cls.return_value = user_instance
       self.svc.register({
           "email": "new@b.com", "password": "123456",
           "confirm_password": "123456", "company_name": "New Corp"
       })
       self.user_repo.save.assert_called_once_with(user_instance)
       self.employer_repo.save.assert_called_once()


   def test_register_sets_user_status_pending_and_role_employer(self):
       self.user_repo.find_by_email.return_value = None
       self.employer_repo.find_by_company_name.return_value = None
       self.svc.register({
           "email": "new@b.com", "password": "123456",
           "confirm_password": "123456", "company_name": "Corp"
       })
       kwargs = self.user_cls.call_args.kwargs
       assert kwargs["status"] == "PENDING"
       assert kwargs["role"] == "EMPLOYER"


   # ── login ─────────────────────────────────────────────────────────


   def test_login_empty_email_returns_false(self):
       ok, msg = self.svc.login("", "pass")
       assert ok is False


   def test_login_empty_password_returns_false(self):
       ok, msg = self.svc.login("a@b.com", "")
       assert ok is False


   def test_login_email_not_found_returns_false(self):
       self.user_repo.find_by_email.return_value = None
       ok, msg = self.svc.login("x@x.com", "pass")
       assert ok is False
       assert "Email" in msg


   def test_login_wrong_role_returns_false(self):
       user = MagicMock(role="CANDIDATE")
       self.user_repo.find_by_email.return_value = user
       ok, msg = self.svc.login("x@x.com", "pass")
       assert ok is False
       assert "Nhà tuyển dụng" in msg


   def test_login_wrong_password_returns_false(self):
       user = MagicMock(role="EMPLOYER")
       user.check_password.return_value = False
       self.user_repo.find_by_email.return_value = user
       ok, msg = self.svc.login("x@x.com", "wrong")
       assert ok is False
       assert "Mật khẩu" in msg


   def test_login_status_pending_returns_false(self):
       user = MagicMock(role="EMPLOYER", status="PENDING")
       user.check_password.return_value = True
       self.user_repo.find_by_email.return_value = user
       ok, msg = self.svc.login("x@x.com", "pass")
       assert ok is False
       assert "chờ" in msg.lower()


   def test_login_status_rejected_returns_false(self):
       user = MagicMock(role="EMPLOYER", status="REJECTED")
       user.check_password.return_value = True
       self.user_repo.find_by_email.return_value = user
       ok, msg = self.svc.login("x@x.com", "pass")
       assert ok is False
       assert "từ chối" in msg


   def test_login_status_suspended_returns_false(self):
       user = MagicMock(role="EMPLOYER", status="SUSPENDED")
       user.check_password.return_value = True
       self.user_repo.find_by_email.return_value = user
       ok, msg = self.svc.login("x@x.com", "pass")
       assert ok is False
       assert "tạm khóa" in msg


   def test_login_inactive_user_returns_false(self):
       user = MagicMock(role="EMPLOYER", status="ACTIVE", is_active=False)
       user.check_password.return_value = True
       self.user_repo.find_by_email.return_value = user
       ok, msg = self.svc.login("x@x.com", "pass")
       assert ok is False


   def test_login_success_returns_true_and_user(self):
       user = MagicMock(role="EMPLOYER", status="ACTIVE", is_active=True)
       user.check_password.return_value = True
       self.user_repo.find_by_email.return_value = user
       ok, result = self.svc.login("x@x.com", "pass")
       assert ok is True
       assert result is user


   # ── get_employer_profile ──────────────────────────────────────────


   def test_get_employer_profile_calls_repo_with_user_id(self):
       profile = MagicMock()
       self.employer_repo.find_by_user_id.return_value = profile
       result = self.svc.get_employer_profile(3)
       assert result is profile
       self.employer_repo.find_by_user_id.assert_called_once_with(3)




# ══════════════════════════════════════════════════════════════════════
# 17. JobService  (employer — đăng tin tuyển dụng)
#     file: app/services/employer/job_service.py
# ══════════════════════════════════════════════════════════════════════


class TestEmployerJobService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.repo    = MagicMock()
       self.job_cls = MagicMock()
       with patch("app.services.employer.job_service.JobRepository", self.repo), \
            patch("app.services.employer.job_service.Job", self.job_cls):
           from app.services.employer.job_service import JobService
           self.svc = JobService
           yield


   # ── parse_skills ──────────────────────────────────────────────────


   def test_parse_skills_returns_list_of_dicts(self):
       form = MagicMock()
       form.getlist.return_value = ["1", "2", "3"]
       result = self.svc.parse_skills(form)
       assert result == [{"skill_id": 1}, {"skill_id": 2}, {"skill_id": 3}]


   def test_parse_skills_empty_form_returns_empty_list(self):
       form = MagicMock()
       form.getlist.return_value = []
       assert self.svc.parse_skills(form) == []


   def test_parse_skills_converts_str_to_int(self):
       form = MagicMock()
       form.getlist.return_value = ["10"]
       result = self.svc.parse_skills(form)
       assert result[0]["skill_id"] == 10
       assert isinstance(result[0]["skill_id"], int)


   # ── _validate ─────────────────────────────────────────────────────


   def test_validate_missing_title_returns_error(self):
       err = self.svc._validate({
           "title": "", "location": "HCM",
           "description": "d", "end_date": "2099-01-01"
       })
       assert err is not None
       assert "Title" in err


   def test_validate_missing_location_returns_error(self):
       err = self.svc._validate({
           "title": "Dev", "location": "",
           "description": "d", "end_date": "2099-01-01"
       })
       assert err is not None
       assert "Location" in err


   def test_validate_missing_description_returns_error(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM",
           "description": "", "end_date": "2099-01-01"
       })
       assert err is not None


   def test_validate_missing_end_date_returns_error(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM",
           "description": "d", "end_date": ""
       })
       assert err is not None


   def test_validate_past_end_date_returns_error(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM",
           "description": "d", "end_date": "2000-01-01"
       })
       assert err is not None
       assert "future" in err.lower()


   def test_validate_invalid_end_date_format_returns_error(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM",
           "description": "d", "end_date": "not-a-date"
       })
       assert err is not None


   def test_validate_salary_min_greater_than_max_returns_error(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM", "description": "d",
           "end_date": "2099-01-01",
           "salary_min": "1000", "salary_max": "500"
       })
       assert err is not None
       assert "Salary" in err


   def test_validate_negative_experience_returns_error(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM", "description": "d",
           "end_date": "2099-01-01", "experience_required": "-1"
       })
       assert err is not None


   def test_validate_non_numeric_experience_returns_error(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM", "description": "d",
           "end_date": "2099-01-01", "experience_required": "abc"
       })
       assert err is not None


   def test_validate_valid_data_returns_none(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM", "description": "d",
           "end_date": "2099-12-31",
           "salary_min": "500", "salary_max": "2000",
           "experience_required": "2"
       })
       assert err is None


   def test_validate_salary_equal_min_max_is_valid(self):
       err = self.svc._validate({
           "title": "Dev", "location": "HCM", "description": "d",
           "end_date": "2099-12-31",
           "salary_min": "1000", "salary_max": "1000"
       })
       assert err is None


   # ── get_stats ─────────────────────────────────────────────────────


   def test_get_stats_calculates_closed_correctly(self):
       self.repo.count_by_employer.return_value = 10
       self.repo.count_open_by_employer.return_value = 6
       stats = self.svc.get_stats(1)
       assert stats["total"] == 10
       assert stats["open"] == 6
       assert stats["closed"] == 4


   def test_get_stats_all_closed(self):
       self.repo.count_by_employer.return_value = 5
       self.repo.count_open_by_employer.return_value = 0
       stats = self.svc.get_stats(1)
       assert stats["closed"] == 5


   def test_get_stats_calls_repos_with_employer_id(self):
       self.repo.count_by_employer.return_value = 0
       self.repo.count_open_by_employer.return_value = 0
       self.svc.get_stats(7)
       self.repo.count_by_employer.assert_called_once_with(7)
       self.repo.count_open_by_employer.assert_called_once_with(7)


   # ── search_jobs ───────────────────────────────────────────────────


   def test_search_jobs_calls_repo_search(self):
       self.repo.search.return_value = []
       self.svc.search_jobs(keyword="dev", status="OPEN", employer_id=1)
       self.repo.search.assert_called_once_with(
           keyword="dev", status="OPEN", employer_id=1
       )


   # ── delete_job_safely ─────────────────────────────────────────────


   def test_delete_job_safely_not_found_returns_false(self):
       self.repo.find_by_id_and_employer.return_value = None
       ok, msg = self.svc.delete_job_safely(1, 1)
       assert ok is False
       assert "không tồn tại" in msg


   def test_delete_job_safely_has_applicants_closes_instead_of_delete(self):
       self.repo.find_by_id_and_employer.return_value = MagicMock()
       self.repo.count_applicants.return_value = 5
       ok, msg = self.svc.delete_job_safely(1, 1)
       assert ok is False
       self.repo.update_status.assert_called_once_with(1, "CLOSED")
       self.repo.delete.assert_not_called()


   def test_delete_job_safely_has_applicants_message_contains_count(self):
       self.repo.find_by_id_and_employer.return_value = MagicMock()
       self.repo.count_applicants.return_value = 3
       _, msg = self.svc.delete_job_safely(1, 1)
       assert "3" in msg


   def test_delete_job_safely_no_applicants_calls_delete(self):
       self.repo.find_by_id_and_employer.return_value = MagicMock()
       self.repo.count_applicants.return_value = 0
       ok, msg = self.svc.delete_job_safely(1, 1)
       assert ok is True
       self.repo.delete.assert_called_once_with(1)


   def test_delete_job_safely_no_applicants_message_success(self):
       self.repo.find_by_id_and_employer.return_value = MagicMock()
       self.repo.count_applicants.return_value = 0
       _, msg = self.svc.delete_job_safely(1, 1)
       assert "thành công" in msg




# ══════════════════════════════════════════════════════════════════════
# 18. ApplicationService  (employer — quản lý hồ sơ ứng tuyển)
#     file: app/services/employer/application_service.py
# ══════════════════════════════════════════════════════════════════════


class TestEmployerApplicationService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.app_repo   = MagicMock()
       self.notif_repo = MagicMock()
       self.notif_cls  = MagicMock()


       with patch("app.services.employer.application_service.ApplicationRepository", self.app_repo), \
            patch("app.services.employer.application_service.NotificationRepository", self.notif_repo), \
            patch("app.services.employer.application_service.Notification", self.notif_cls):
           from app.services.employer.application_service import ApplicationService
           self.svc = ApplicationService
           yield


   # ── count_unscored ────────────────────────────────────────────────


   def test_count_unscored_returns_correct_count(self):
       self.app_repo.get_unscored_applications.return_value = [MagicMock(), MagicMock()]
       assert self.svc.count_unscored(1) == 2


   def test_count_unscored_empty_returns_zero(self):
       self.app_repo.get_unscored_applications.return_value = []
       assert self.svc.count_unscored(1) == 0


   # ── get_applications ──────────────────────────────────────────────


   def test_get_applications_passes_filters_to_repo(self):
       raw = MagicMock()
       raw.items = []
       raw.total = 0; raw.pages = 0; raw.page = 1
       raw.has_prev = False; raw.has_next = False
       raw.iter_pages = MagicMock(return_value=iter([]))
       self.app_repo.get_applications_for_employer.return_value = raw


       self.svc.get_applications(1, {"keyword": "nhi", "status": "PENDING"}, page=2)


       self.app_repo.get_applications_for_employer.assert_called_once_with(
           employer_id=1, keyword="nhi", status="PENDING",
           score_level=None, page=2,
       )


   def test_get_applications_blank_filters_become_none(self):
       raw = MagicMock()
       raw.items = []
       raw.total = 0; raw.pages = 0; raw.page = 1
       raw.has_prev = False; raw.has_next = False
       raw.iter_pages = MagicMock(return_value=iter([]))
       self.app_repo.get_applications_for_employer.return_value = raw


       self.svc.get_applications(1, {"keyword": "   ", "status": ""}, page=1)
       kwargs = self.app_repo.get_applications_for_employer.call_args.kwargs
       assert kwargs["keyword"] is None
       assert kwargs["status"] is None


   def test_get_applications_attaches_match_score_to_items(self):
       app = MagicMock()
       raw = MagicMock()
       raw.items = [(app, 85.5)]
       raw.total = 1; raw.pages = 1; raw.page = 1
       raw.has_prev = False; raw.has_next = False
       raw.iter_pages = MagicMock(return_value=iter([]))
       self.app_repo.get_applications_for_employer.return_value = raw


       result = self.svc.get_applications(1, {})
       assert result.items[0].match_score == 85.5


   def test_get_applications_none_score_becomes_none(self):
       app = MagicMock()
       raw = MagicMock()
       raw.items = [(app, None)]
       raw.total = 1; raw.pages = 1; raw.page = 1
       raw.has_prev = False; raw.has_next = False
       raw.iter_pages = MagicMock(return_value=iter([]))
       self.app_repo.get_applications_for_employer.return_value = raw


       result = self.svc.get_applications(1, {})
       assert result.items[0].match_score is None


   # ── update_status ─────────────────────────────────────────────────


   def test_update_status_invalid_status_returns_false(self):
       ok, msg = self.svc.update_status(1, 1, "INVALID")
       assert ok is False
       assert "không hợp lệ" in msg


   def test_update_status_application_not_found_returns_false(self):
       self.app_repo.find_by_id_for_employer.return_value = None
       ok, msg = self.svc.update_status(1, 1, "REVIEWED")
       assert ok is False


   def test_update_status_same_status_returns_false(self):
       app = MagicMock(status="REVIEWED")
       self.app_repo.find_by_id_for_employer.return_value = app
       ok, msg = self.svc.update_status(1, 1, "REVIEWED")
       assert ok is False
       assert "không thay đổi" in msg


   def test_update_status_success_returns_true(self):
       app = MagicMock(status="PENDING")
       app.cv.candidate.user_id = 10
       app.job.employer.company_name = "Corp"
       app.job.title = "Dev"
       app.cv.title = "My CV"
       self.app_repo.find_by_id_for_employer.return_value = app
       ok, _ = self.svc.update_status(1, 1, "REVIEWED")
       assert ok is True


   def test_update_status_success_updates_status_field(self):
       app = MagicMock(status="PENDING")
       app.cv.candidate.user_id = 10
       app.job.employer.company_name = "Corp"
       app.job.title = "Dev"
       app.cv.title = "My CV"
       self.app_repo.find_by_id_for_employer.return_value = app
       self.svc.update_status(1, 1, "ACCEPTED")
       assert app.status == "ACCEPTED"


   def test_update_status_success_saves_application(self):
       app = MagicMock(status="PENDING")
       app.cv.candidate.user_id = 10
       app.job.employer.company_name = "Corp"
       app.job.title = "Dev"
       app.cv.title = "My CV"
       self.app_repo.find_by_id_for_employer.return_value = app
       self.svc.update_status(1, 1, "REVIEWED")
       self.app_repo.save.assert_called_once_with(app)


   def test_update_status_creates_notification(self):
       app = MagicMock(status="PENDING")
       app.cv.candidate.user_id = 10
       app.job.employer.company_name = "Corp"
       app.job.title = "Dev"
       app.cv.title = "My CV"
       self.app_repo.find_by_id_for_employer.return_value = app
       self.svc.update_status(1, 1, "ACCEPTED")
       self.notif_repo.save.assert_called_once()


   def test_update_status_all_valid_statuses_succeed(self):
       for new_status, old_status in [
           ("REVIEWED", "PENDING"), ("ACCEPTED", "REVIEWED"),
           ("REJECTED", "ACCEPTED"), ("PENDING", "REVIEWED"),
       ]:
           app = MagicMock(status=old_status)
           app.cv.candidate.user_id = 1
           app.job.employer.company_name = "Corp"
           app.job.title = "Dev"
           app.cv.title = "CV"
           self.app_repo.find_by_id_for_employer.return_value = app
           self.notif_repo.reset_mock()
           self.app_repo.reset_mock()
           self.app_repo.find_by_id_for_employer.return_value = app
           ok, _ = self.svc.update_status(1, 1, new_status)
           assert ok is True, f"Status {new_status} should be valid"




# ══════════════════════════════════════════════════════════════════════
# 19. MatchingService
#     file: app/services/employer/matching_service.py
# ══════════════════════════════════════════════════════════════════════


class TestMatchingService:


   @pytest.fixture(autouse=True)
   def setup(self):
       self.db            = MagicMock()
       self.job_rec_model = MagicMock()
       self.cv_skill_repo = MagicMock()
       self.skill_repo    = MagicMock()
       self.cv_extractor  = MagicMock()


       with patch("app.services.employer.matching_service.db", self.db), \
            patch("app.services.employer.matching_service.JobRecommendation", self.job_rec_model), \
            patch("app.services.employer.matching_service.CVSkillRepository", self.cv_skill_repo), \
            patch("app.services.employer.matching_service.SkillRepository", self.skill_repo), \
            patch("app.services.employer.matching_service.CVTextExtractor", self.cv_extractor):
           from app.services.employer.matching_service import MatchingService
           self.svc = MatchingService
           yield


   def _make_application(self, candidate_id=1, job_id=1):
       app = MagicMock()
       app.cv.candidate_id = candidate_id
       app.job_id = job_id
       return app


   # ── get_or_calculate ─────────────────────────────────────────────


   def test_get_or_calculate_returns_cached_score_from_db(self):
       rec = MagicMock(score=75.0)
       self.job_rec_model.query.filter_by.return_value.first.return_value = rec
       app = self._make_application()
       result = self.svc.get_or_calculate(app)
       assert result == 75.0


   def test_get_or_calculate_calls_calculate_when_no_cache(self):
       self.job_rec_model.query.filter_by.return_value.first.return_value = None
       app = self._make_application()
       with patch.object(self.svc, "_calculate_and_save", return_value=88.0) as mock_calc:
           result = self.svc.get_or_calculate(app)
           mock_calc.assert_called_once_with(app)
           assert result == 88.0


   def test_get_or_calculate_rec_with_none_score_triggers_calculate(self):
       rec = MagicMock(score=None)
       self.job_rec_model.query.filter_by.return_value.first.return_value = rec
       app = self._make_application()
       with patch.object(self.svc, "_calculate_and_save", return_value=50.0):
           result = self.svc.get_or_calculate(app)
           assert result == 50.0


   # ── recalculate ───────────────────────────────────────────────────


   def test_recalculate_deletes_old_record_then_calculates(self):
       app = self._make_application()
       with patch.object(self.svc, "_delete_from_db") as mock_del, \
            patch.object(self.svc, "_calculate_and_save", return_value=60.0) as mock_calc:
           result = self.svc.recalculate(app)
           mock_del.assert_called_once_with(app.cv.candidate_id, app.job_id)
           mock_calc.assert_called_once_with(app)
           assert result == 60.0


   # ── _load_from_db ─────────────────────────────────────────────────


   def test_load_from_db_returns_float_when_found(self):
       rec = MagicMock(score=55)
       self.job_rec_model.query.filter_by.return_value.first.return_value = rec
       result = self.svc._load_from_db(1, 1)
       assert result == 55.0
       assert isinstance(result, float)


   def test_load_from_db_returns_none_when_not_found(self):
       self.job_rec_model.query.filter_by.return_value.first.return_value = None
       assert self.svc._load_from_db(1, 1) is None


   def test_load_from_db_returns_none_when_score_is_none(self):
       rec = MagicMock(score=None)
       self.job_rec_model.query.filter_by.return_value.first.return_value = rec
       assert self.svc._load_from_db(1, 1) is None


   # ── _delete_from_db ───────────────────────────────────────────────


   def test_delete_from_db_calls_delete_and_commit(self):
       self.job_rec_model.query.filter_by.return_value.delete = MagicMock()
       self.svc._delete_from_db(1, 1)
       self.job_rec_model.query.filter_by.return_value.delete.assert_called_once()
       self.db.session.commit.assert_called_once()


   # ── _call_gemini ──────────────────────────────────────────────────


   def test_call_gemini_parses_integer_response(self):
       with patch("app.services.employer.matching_service._get_client") as mock_client:
           response = MagicMock()
           response.text = "85"
           mock_client.return_value.models.generate_content.return_value = response
           result = self.svc._call_gemini("Dev", "desc", ["Python"], 2, "cv text")
           assert result == 85.0


   def test_call_gemini_clamps_score_above_100(self):
       with patch("app.services.employer.matching_service._get_client") as mock_client:
           response = MagicMock()
           response.text = "150"
           mock_client.return_value.models.generate_content.return_value = response
           result = self.svc._call_gemini("Dev", "desc", [], None, "cv")
           assert result == 100.0


   def test_call_gemini_returns_none_on_non_numeric_response(self):
       with patch("app.services.employer.matching_service._get_client") as mock_client:
           response = MagicMock()
           response.text = "không thể đánh giá"
           mock_client.return_value.models.generate_content.return_value = response
           result = self.svc._call_gemini("Dev", "desc", [], None, "cv")
           assert result is None


   def test_call_gemini_returns_none_on_api_exception(self):
       with patch("app.services.employer.matching_service._get_client") as mock_client:
           mock_client.return_value.models.generate_content.side_effect = Exception("API down")
           result = self.svc._call_gemini("Dev", "desc", [], None, "cv")
           assert result is None


   def test_call_gemini_no_job_skills_uses_default_string_in_prompt(self):
       with patch("app.services.employer.matching_service._get_client") as mock_client:
           response = MagicMock()
           response.text = "70"
           mock_client.return_value.models.generate_content.return_value = response
           self.svc._call_gemini("Dev", "desc", [], None, "cv")
           prompt = mock_client.return_value.models.generate_content.call_args.kwargs["contents"]
           assert "Không có yêu cầu cụ thể" in prompt


   def test_call_gemini_no_experience_uses_khong_yeu_cau_in_prompt(self):
       with patch("app.services.employer.matching_service._get_client") as mock_client:
           response = MagicMock()
           response.text = "70"
           mock_client.return_value.models.generate_content.return_value = response
           self.svc._call_gemini("Dev", "desc", [], None, "cv")
           prompt = mock_client.return_value.models.generate_content.call_args.kwargs["contents"]
           assert "Không yêu cầu" in prompt




# ══════════════════════════════════════════════════════════════════════
# 20. CVTextExtractor
#     file: app/services/employer/cv_text_extractor.py
# ══════════════════════════════════════════════════════════════════════


class TestCVTextExtractor:


   @pytest.fixture(autouse=True)
   def setup(self):
       import sys
       from unittest.mock import MagicMock

       sys.modules["pdfplumber"] = MagicMock()

       from app.services.employer.cv_text_extractor import CVTextExtractor
       self.extractor = CVTextExtractor


   # ── extract (dispatch) ────────────────────────────────────────────


   def test_extract_online_dispatches_to_from_json(self):
       cv = MagicMock(type="ONLINE")
       with patch.object(self.extractor, "_from_json", return_value="json_text") as mock_fn:
           result = self.extractor.extract(cv)
           mock_fn.assert_called_once_with(cv)
           assert result == "json_text"


   def test_extract_upload_dispatches_to_from_file(self):
       cv = MagicMock(type="UPLOAD")
       with patch.object(self.extractor, "_from_file", return_value="file_text") as mock_fn:
           result = self.extractor.extract(cv)
           mock_fn.assert_called_once_with(cv)
           assert result == "file_text"


   def test_extract_unknown_type_returns_empty_string(self):
       cv = MagicMock(type="OTHER")
       assert self.extractor.extract(cv) == ""


   # ── _from_json ────────────────────────────────────────────────────


   def test_from_json_none_content_json_returns_empty(self):
       cv = MagicMock(type="ONLINE", content_json=None)
       assert self.extractor.extract(cv) == ""


   def test_from_json_includes_full_name(self):
       cv = MagicMock(type="ONLINE", content_json={
           "full_name": "Nguyen Van A",
           "experiences": [], "educations": [], "projects": []
       })
       assert "Nguyen Van A" in self.extractor.extract(cv)


   def test_from_json_includes_email(self):
       cv = MagicMock(type="ONLINE", content_json={
           "email": "test@example.com",
           "experiences": [], "educations": [], "projects": []
       })
       assert "test@example.com" in self.extractor.extract(cv)


   def test_from_json_includes_summary(self):
       cv = MagicMock(type="ONLINE", content_json={
           "summary": "Experienced developer",
           "experiences": [], "educations": [], "projects": []
       })
       assert "Experienced developer" in self.extractor.extract(cv)


   def test_from_json_includes_experience_position_and_company(self):
       cv = MagicMock(type="ONLINE", content_json={
           "experiences": [{"position": "Backend Dev", "company": "TechCorp", "description": ""}],
           "educations": [], "projects": []
       })
       text = self.extractor.extract(cv)
       assert "Backend Dev" in text
       assert "TechCorp" in text


   def test_from_json_includes_education_school_and_degree(self):
       cv = MagicMock(type="ONLINE", content_json={
           "educations": [{"degree": "B.Sc", "school": "HUST"}],
           "experiences": [], "projects": []
       })
       text = self.extractor.extract(cv)
       assert "HUST" in text
       assert "B.Sc" in text


   def test_from_json_includes_project_name(self):
       cv = MagicMock(type="ONLINE", content_json={
           "projects": [{"name": "My App", "description": "A great app"}],
           "experiences": [], "educations": []
       })
       assert "My App" in self.extractor.extract(cv)


   def test_from_json_empty_lists_returns_empty_string(self):
       cv = MagicMock(type="ONLINE", content_json={
           "experiences": [], "educations": [], "projects": []
       })
       assert self.extractor.extract(cv).strip() == ""


   # ── _from_file ────────────────────────────────────────────────────


   def test_from_file_no_file_url_returns_empty(self):
       cv = MagicMock(type="UPLOAD", file_url=None)
       assert self.extractor.extract(cv) == ""


   def test_from_file_file_not_exists_returns_empty(self):
       cv = MagicMock(type="UPLOAD", file_url="/static/uploads/cvs/missing.pdf")
       with patch("app.services.employer.cv_text_extractor.os.path.exists", return_value=False):
           assert self.extractor.extract(cv) == ""


   def test_from_file_doc_extension_returns_empty(self):
       cv = MagicMock(type="UPLOAD", file_url="/static/uploads/cvs/file.doc")
       with patch("app.services.employer.cv_text_extractor.os.path.exists", return_value=True):
           assert self.extractor.extract(cv) == ""

   def test_from_file_pdf_calls_pdf_extractor(self):
       cv = MagicMock(type="UPLOAD", file_url="/static/uploads/cvs/resume.pdf")
       with patch("app.services.employer.cv_text_extractor.os.path.exists", return_value=True), \
               patch.object(self.extractor, "_pdf", return_value="pdf content") as mock_pdf:
           result = self.extractor.extract(cv)
           mock_pdf.assert_called_once()
           assert result == "pdf content"

   def test_from_file_docx_calls_docx_extractor(self):
       cv = MagicMock(type="UPLOAD", file_url="/static/uploads/cvs/resume.docx")
       with patch("app.services.employer.cv_text_extractor.os.path.exists", return_value=True), \
               patch.object(self.extractor, "_docx", return_value="docx content") as mock_docx:
           result = self.extractor.extract(cv)
           mock_docx.assert_called_once()
           assert result == "docx content"

   def test_from_file_pdf_passes_correct_filepath(self):
       cv = MagicMock(type="UPLOAD", file_url="/static/uploads/cvs/myresume.pdf")
       with patch("app.services.employer.cv_text_extractor.os.path.exists", return_value=True), \
               patch.object(self.extractor, "_pdf", return_value="text") as mock_pdf:
           self.extractor.extract(cv)
           filepath_used = mock_pdf.call_args.args[0]
           assert "myresume.pdf" in filepath_used

   def test_from_file_docx_passes_correct_filepath(self):
       cv = MagicMock(type="UPLOAD", file_url="/static/uploads/cvs/myresume.docx")
       with patch("app.services.employer.cv_text_extractor.os.path.exists", return_value=True), \
               patch.object(self.extractor, "_docx", return_value="text") as mock_docx:
           self.extractor.extract(cv)
           filepath_used = mock_docx.call_args.args[0]
           assert "myresume.docx" in filepath_used

   # ── _pdf error handling ───────────────────────────────────────────

   def test_pdf_returns_empty_on_exception(self):
       with patch("pdfplumber.open", side_effect=Exception("corrupted file"), create=True):
           result = self.extractor._pdf("/fake/path.pdf")
           assert result == ""

   def test_pdf_concatenates_all_pages(self):
       page1 = MagicMock()
       page1.extract_text.return_value = "Page 1 text"
       page2 = MagicMock()
       page2.extract_text.return_value = "Page 2 text"

       mock_pdf_ctx = MagicMock()
       mock_pdf_ctx.__enter__ = MagicMock(return_value=MagicMock(pages=[page1, page2]))
       mock_pdf_ctx.__exit__ = MagicMock(return_value=False)

       with patch("pdfplumber.open", return_value=mock_pdf_ctx):
           result = self.extractor._pdf("/fake/path.pdf")
           assert "Page 1 text" in result
           assert "Page 2 text" in result

   def test_pdf_skips_pages_with_no_text(self):
       page1 = MagicMock()
       page1.extract_text.return_value = "Has text"
       page2 = MagicMock()
       page2.extract_text.return_value = None  # trang rỗng

       mock_pdf_ctx = MagicMock()
       mock_pdf_ctx.__enter__ = MagicMock(return_value=MagicMock(pages=[page1, page2]))
       mock_pdf_ctx.__exit__ = MagicMock(return_value=False)

       with patch("pdfplumber.open", return_value=mock_pdf_ctx):
           result = self.extractor._pdf("/fake/path.pdf")
           assert "Has text" in result

   # ── _docx error handling ──────────────────────────────────────────

   def test_docx_returns_empty_on_exception(self):
       with patch("docx.Document", side_effect=Exception("bad file")):
           result = self.extractor._docx("/fake/path.docx")
           assert result == ""

   def test_docx_concatenates_non_empty_paragraphs(self):
       p1 = MagicMock()
       p1.text = "First paragraph"
       p2 = MagicMock()
       p2.text = ""  # rỗng → bỏ qua
       p3 = MagicMock()
       p3.text = "Third paragraph"

       mock_doc = MagicMock()
       mock_doc.paragraphs = [p1, p2, p3]

       with patch("docx.Document", return_value=mock_doc):
           result = self.extractor._docx("/fake/path.docx")
           assert "First paragraph" in result
           assert "Third paragraph" in result
           # Đảm bảo dòng rỗng không được thêm vào
           assert "\n\n" not in result.replace("First paragraph\nThird paragraph", "")
