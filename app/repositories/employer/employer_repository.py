from app.models.employer import Employer
from app.extensions import db


class EmployerRepository:

    @staticmethod
    def find_by_user_id(user_id):
        return Employer.query.filter_by(user_id=user_id).first()

    @staticmethod
    def find_by_company_name(company_name):
        """So sánh không phân biệt hoa thường để kiểm tra trùng tên công ty."""
        return Employer.query.filter(
            Employer.company_name.ilike(company_name)
        ).first()

    @staticmethod
    def save(employer):
        db.session.add(employer)
        db.session.commit()
        return employer