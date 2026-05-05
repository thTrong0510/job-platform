from pymysql import IntegrityError

from app.models.cv import CVTemplate
from app.extensions import db

class CVTemplateRepository:
    @staticmethod
    def get_all():
        return CVTemplate.query.all()

    @staticmethod
    def get_by_id(template_id):
        return CVTemplate.query.get(template_id)

    @staticmethod
    def create(data):
        try:
            new_temp = CVTemplate(**data)
            db.session.add(new_temp)
            db.session.commit()
            return new_temp
        except IntegrityError as e:
            db.session.rollback()
            raise e  # Ném lỗi lại cho Service xử lý

    @staticmethod
    def delete(template_id):
        temp = CVTemplate.query.get(template_id)
        if temp:
            db.session.delete(temp)
            db.session.commit()
            return True
        return False

    @staticmethod
    def update(template_id, data):
        template = CVTemplate.query.get(template_id)
        if template:
            for key, value in data.items():
                setattr(template, key, value)
            db.session.commit()
            return template
        return None