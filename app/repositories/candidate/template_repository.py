from app.models.cv import CVTemplate


class TemplateRepository:

    @staticmethod
    def get_active_templates():
        return CVTemplate.query.filter_by(is_active=True).all()

    @staticmethod
    def get_by_id(template_id):
        return CVTemplate.query.get(template_id)