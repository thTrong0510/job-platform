import os

from pymysql import IntegrityError
from werkzeug.utils import secure_filename
from flask import current_app
from app.repositories.admin.cv_template_repository import CVTemplateRepository
from slugify import slugify
from app.extensions import db
from app.models.cv import CVTemplate
from app.common.CloudinaryUtil import CloudinaryUtil


class CVTemplateService:
    @staticmethod
    def create_template(form, file):
        filename = None
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.root_path, 'static/images/cv_templates', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

        form.get('name')
        template_slug = slugify(form.get('name'))

        existing_template = CVTemplate.query.filter_by(slug=template_slug).first()
        if existing_template:
            return "duplicate_slug"

        data = {
            "name": form.get('name'),
            "slug": template_slug,
            "description": form.get('description'),
            "html_content": form.get('html_content'),
            "preview_image": filename,
            "schema_version": "1.0"
        }
        try:
            return CVTemplateRepository.create(data)
        except IntegrityError:
            # Rollback lại session nếu có lỗi để tránh lỗi "Pending Rollback"
            db.session.rollback()
            return "duplicate_slug"  # Trả về mã lỗi để Controller xử lý

    @staticmethod
    def update_template(template_id, form, file):
        template = CVTemplateRepository.get_by_id(template_id)
        if not template:
            return None

        name = form.get('name')
        template_slug = slugify(name)

        data = {
            "name": name,
            "slug": template_slug,
            "description": form.get('description'),
            "html_content": form.get('html_content')
        }

        if file:
            # Lưu file mới
            preview_image = CloudinaryUtil.upload_image(file)
            data["preview_image"] = preview_image

        try:
            # QUAN TRỌNG: Truyền cả template_id vào
            return CVTemplateRepository.update(template_id, data)
        except IntegrityError:
            db.session.rollback()
            return "duplicate_slug"