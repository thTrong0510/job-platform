from app.extensions import mail
from flask_mail import Message
from flask import current_app, render_template

STATUS_MESSAGES = {
    'ACTIVE': {
        'email_subject': '[JobPlatform] Tài khoản của bạn đã được duyệt',
        'email_body': lambda name, reason: f"""
Xin chào {name},

Tài khoản của bạn trên JobPlatform đã được Admin xét duyệt và kích hoạt thành công.

Bạn có thể đăng nhập và bắt đầu sử dụng các tính năng của hệ thống ngay bây giờ.

Trân trọng,
Đội ngũ JobPlatform
"""
    },
    'REJECTED': {
        'email_subject': '[JobPlatform] Tài khoản của bạn bị từ chối',
        'email_body': lambda name, reason: f"""
Xin chào {name},

Rất tiếc, tài khoản của bạn trên JobPlatform đã bị từ chối.

Lý do: {reason or 'Không đáp ứng yêu cầu của hệ thống.'}

Nếu bạn cho rằng đây là nhầm lẫn, vui lòng liên hệ Admin qua email: admin@jobplatform.vn

Trân trọng,
Đội ngũ JobPlatform
"""
    },
    'SUSPENDED': {
        'email_subject': '[JobPlatform] Tài khoản của bạn bị tạm khóa',
        'email_body': lambda name, reason: f"""
Xin chào {name},

Tài khoản của bạn trên JobPlatform đã bị tạm khóa.

Lý do: {reason or 'Vi phạm điều khoản sử dụng.'}

Để khiếu nại hoặc yêu cầu mở lại tài khoản, vui lòng liên hệ Admin qua email: admin@jobplatform.vn

Trân trọng,
Đội ngũ JobPlatform
"""
    }
}


class MailService:

    @staticmethod
    def notify_status_change(user, new_status: str, reason: str = None):
        config = STATUS_MESSAGES.get(new_status)
        if not config:
            return

        display_name = user.email
        if hasattr(user, 'employer') and user.employer:
            display_name = user.employer.company_name
        elif hasattr(user, 'candidate') and user.candidate:
            display_name = user.candidate.full_name

        try:
            msg = Message(
                subject=config['email_subject'],
                recipients=[user.email],
                body=config['email_body'](display_name, reason)
            )
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {user.email}: {e}")


    @staticmethod
    def send_recommendation_email(email, candidate_name, jobs:list):
        msg = Message(
            subject="Việc làm mới nhất phù hợp với bạn",
            recipients = [email]
        )
        msg.html = render_template("pages/admin/recommendation.html",candidate_name=candidate_name, jobs=jobs)
        mail.send(msg)