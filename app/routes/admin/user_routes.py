from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.services.admin.user_service import AdminUserService
from app.common.decorators import admin_required

admin_user_bp = Blueprint('admin_users', __name__, url_prefix='/admin/users')


@admin_user_bp.route('/')
def index():
    role   = request.args.get('role', '')
    status = request.args.get('status', '')
    keyword = request.args.get('keyword', '')
    page   = request.args.get('page', 1, type=int)

    pagination = AdminUserService.get_users_paginated(
        role=role or None,
        status=status or None,
        keyword=keyword or None,
        page=page,
        per_page=2
    )
    stats = AdminUserService.get_dashboard_stats()

    return render_template(
        'pages/admin/user_management.html',
        pagination=pagination,
        users=pagination.items,
        stats=stats,
        current_role=role,
        current_status=status,
        keyword=keyword
    )


@admin_user_bp.route('/<int:user_id>')
def detail(user_id):
    try:
        user = AdminUserService.get_user_detail(user_id)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('admin_users.index'))

    return render_template('pages/admin/user_detail.html', user=user)


@admin_user_bp.route('/<int:user_id>/change-status', methods=['POST'])
def change_status(user_id):
    new_status = request.form.get('status', '').strip()
    reason     = request.form.get('reason', '').strip()
    is_ajax    = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    success, message = AdminUserService.change_status(user_id, new_status, reason)

    if is_ajax:
        return jsonify({'success': success, 'message': message})

    flash(message, 'success' if success else 'danger')

    return redirect(url_for('admin_users.index'))