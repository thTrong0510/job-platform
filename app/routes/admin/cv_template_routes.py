from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.admin.cv_template_service import CVTemplateService
from app.repositories.admin.cv_template_repository import CVTemplateRepository

cv_temp_bp = Blueprint('cv_templates', __name__, url_prefix='/admin/cv-templates')

@cv_temp_bp.route('/')
def index():
    templates = CVTemplateRepository.get_all()
    return render_template('pages/admin/cv_templates.html', templates=templates)

@cv_temp_bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        file = request.files.get('preview_image')
        result = CVTemplateService.create_template(request.form, file)
        if result == "duplicate_slug":
            flash('Lỗi: Tên Template này đã tồn tại hoặc tạo ra Slug trùng lặp!', 'danger')
            return render_template('pages/admin/cv_templates_create.html', old_data=request.form)
        return redirect(url_for('cv_templates.index'))
    return render_template('pages/admin/cv_templates_create.html')

@cv_temp_bp.route('/edit/<int:template_id>', methods=['GET', 'POST'])
def edit(template_id):
    template = CVTemplateRepository.get_by_id(template_id)
    if request.method == 'POST':
        file = request.files.get('preview_image')
        result = CVTemplateService.update_template(template_id, request.form, file)
        if result == "duplicate_slug":
            flash('Lỗi: Tên Template này đã tồn tại hoặc tạo ra Slug trùng lặp!', 'danger')
            return render_template('pages/admin/cv_templates_edit.html', old_data=request.form)
        return redirect(url_for('cv_templates.index'))
    return render_template('pages/admin/cv_templates_edit.html', template=template)

@cv_temp_bp.route('/delete/<int:template_id>', methods=['POST'])
def delete(template_id):
    if CVTemplateRepository.delete(template_id):
        flash('Đã xóa template.', 'info')
    return redirect(url_for('cv_templates.index'))