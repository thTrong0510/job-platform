from app.models.user import User
from app.models.employer import Employer
from app.repositories.user_repository import UserRepository
from app.repositories.employer.employer_repository import EmployerRepository


class EmployerAuthService:

    # ─────────────────────────────────────────
    # REGISTER
    # ─────────────────────────────────────────
    @staticmethod
    def register(data: dict):
        email            = data.get("email", "").strip()
        password         = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        company_name     = data.get("company_name", "").strip()
        location         = data.get("location", "").strip() or None
        website          = data.get("company_website", "").strip() or None
        description      = data.get("company_description", "").strip() or None

        # ── Validate bắt buộc ──
        if not email or not password or not company_name:
            return False, "Vui lòng điền đầy đủ các trường bắt buộc."

        if password != confirm_password:
            return False, "Mật khẩu xác nhận không khớp."

        if len(password) < 6:
            return False, "Mật khẩu phải có ít nhất 6 ký tự."

        # ── Kiểm tra email đã tồn tại ──
        if UserRepository.find_by_email(email):
            return False, "Email này đã được sử dụng để đăng ký tài khoản khác."

        # ── Mỗi công ty chỉ 1 tài khoản ──
        if EmployerRepository.find_by_company_name(company_name):
            return (
                False,
                "Tên công ty này đã được đăng ký. "
                "Mỗi công ty chỉ được tạo một tài khoản duy nhất. "
                "Nếu cần hỗ trợ, vui lòng liên hệ admin."
            )

        # ── Tạo User với status PENDING — chờ admin duyệt ──
        user = User(
            email=email,
            role="EMPLOYER",
            status="PENDING",
            is_active=True,
        )
        user.set_password(password)
        UserRepository.save(user)

        # ── Tạo Employer profile ──
        employer = Employer(
            user_id=user.id,
            company_name=company_name,
            location=location,
            company_website=website,
            company_description=description,
        )
        EmployerRepository.save(employer)

        return (
            True,
            "Đăng ký thành công! Tài khoản đang chờ Admin kiểm duyệt. "
            "Chúng tôi sẽ phản hồi qua email trong vòng 1–3 ngày làm việc."
        )

    # ─────────────────────────────────────────
    # LOGIN
    # ─────────────────────────────────────────
    @staticmethod
    def login(email: str, password: str):
        if not email or not password:
            return False, "Vui lòng nhập email và mật khẩu."

        user = UserRepository.find_by_email(email)

        if not user:
            return False, "Email không tồn tại trong hệ thống."

        if user.role != "EMPLOYER":
            return False, "Tài khoản này không phải tài khoản Nhà tuyển dụng."

        if not user.check_password(password):
            return False, "Mật khẩu không chính xác."

        if user.status == "PENDING":
            return (
                False,
                "Tài khoản đang chờ Admin kiểm duyệt. "
                "Vui lòng chờ email xác nhận từ hệ thống."
            )

        if user.status == "REJECTED":
            return (
                False,
                "Tài khoản đã bị từ chối. "
                "Vui lòng liên hệ hỗ trợ để biết thêm chi tiết."
            )

        if user.status == "SUSPENDED":
            return False, "Tài khoản đang bị tạm khóa. Vui lòng liên hệ hỗ trợ."

        if not user.is_active:
            return False, "Tài khoản đã bị vô hiệu hóa."

        return True, user

    # ─────────────────────────────────────────
    # GET PROFILE
    # ─────────────────────────────────────────
    @staticmethod
    def get_employer_profile(user_id: int):
        return EmployerRepository.find_by_user_id(user_id)