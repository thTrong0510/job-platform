from flask import Blueprint, redirect, url_for, request, flash, render_template, current_app

from app.services.candidate.cv_extraction_service import CVExtractionService
from app.common.decorators import candidate_required
from app.common.info import get_current_candidate
from app.services.candidate.candidate_service import CandidateService
from app.repositories.candidate.cv_repository import CVRepository

cv_extraction_bp = Blueprint('cv_extraction', __name__, url_prefix='/candidate')


@cv_extraction_bp.route('/profile/fill-from-cv', methods=['GET', 'POST'])
@candidate_required
def fill_from_cv():
    candidate = get_current_candidate()

    if request.method == 'POST':
        try:
            extracted_data = CVExtractionService.process_extraction(
                candidate_id = candidate.id,
                form = request.form,
                files = request.files,
            )

            return render_template("pages/candidate/profile_edit_from_cv.html",
                                   section="all",
                                   candidate=None,
                                   extracted_data=extracted_data,
                                   from_extraction=True)
        except ValueError as e:
            flash(str(e), 'warning')
        except RuntimeError as e:
            flash(str(e), 'danger')
        except Exception:
            flash("Lỗi không xác định", "danger")
        return redirect(url_for('cv_extraction.fill_from_cv'))

    # GET: Hiển thị trang chọn CV
    uploaded_cvs = CVRepository.get_upload_by_candidate(candidate.id)
    return render_template("pages/candidate/fill_from_cv.html", uploaded_cvs=uploaded_cvs)

@cv_extraction_bp.route('/profile/save', methods=['POST'])
@candidate_required
def save_profile():
    candidate_id = get_current_candidate().id

    try:
        skills = [s.strip() for s in request.form.getlist("skills") if s.strip()]
        data = {
            'full_name': request.form.get('full_name'),
            'current_title': request.form.get('current_title'),
            'phone': request.form.get('phone'),
            'location': request.form.get('location'),
            'bio': request.form.get('bio'),
            'experiences': [],
            'educations': [],
            'skills': skills,
        }

        i = 0
        while True:
            company = request.form.get(f'experiences[{i}][company]')
            if company is None:
                break
            data['experiences'].append({
                'company': company,
                'position': request.form.get(f'experiences[{i}][position]'),
                'start_date': request.form.get(f'experiences[{i}][start_date]') or None,
                'end_date': request.form.get(f'experiences[{i}][end_date]') or None,
                'description': request.form.get(f'experiences[{i}][description]')
            })
            i += 1

        i = 0
        while True:
            school = request.form.get(f'educations[{i}][school]')
            if school is None:
                break
            data['educations'].append({
                'school': school,
                'degree': request.form.get(f'educations[{i}][degree]'),
                'start_date': request.form.get(f'educations[{i}][start_date]') or None,
                'end_date': request.form.get(f'educations[{i}][end_date]') or None
            })
            i += 1

        CandidateService.save_extracted_profile(candidate_id=candidate_id, data = data)
        flash("Cập nhật hồ sơ thành công!", "success")
        return redirect(url_for('candidate_profile.view_profile'))

    except Exception as e:
        current_app.logger.error(f"Save profile error: {e}")
        flash("Có lỗi xảy ra khi lưu hồ sơ.", "danger")
        return redirect(url_for('candidate_profile.edit_profile', section='all'))