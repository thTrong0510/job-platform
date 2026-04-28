from repositories.candidate.cv_template_repository import CVTemplateRepository

class CvTemplateService:
    @staticmethod
    def get_template(template_id: int):
        template = CVTemplateRepository.get_by_id(template_id)

        if not template:
            return None

        return {
            "id": template.id,
            "name": template.name,
            "slug": template.slug,
            "description": template.description,
            "preview": template.preview_image,
            "html_content": template.html_content,
            "schema_version": template.schema_version,
            "is_active": template.is_active
        }

    @staticmethod
    def get_active_templates():
        templates = CVTemplateRepository.get_active_templates()

        return [
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "preview": t.preview_image
            }
            for t in templates
        ]