from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.common.decorators import employer_required
from app.common.info import get_current_employer
from app.repositories.employer.employer_repository import EmployerRepository
from app.extensions import db

company_profile_bp = Blueprint(
    "company_profile", __name__, url_prefix="/employer/company-profile"
)


# ─────────────────────────────────────────
# VIEW  GET /employer/company-profile/
# ─────────────────────────────────────────
@company_profile_bp.route("/")
@employer_required
def view():
    employer = get_current_employer()
    return render_template(
        "pages/employer/company_profile.html",
        employer=employer,
        editing=False,
    )


# ─────────────────────────────────────────
# EDIT  GET /employer/company-profile/edit
# ─────────────────────────────────────────
@company_profile_bp.route("/edit", methods=["GET", "POST"])
@employer_required
def edit():
    employer = get_current_employer()

    if request.method == "POST":
        # company_name        = request.form.get("company_name", "").strip()
        # location            = request.form.get("location", "").strip() or None
        company_website     = request.form.get("company_website", "").strip() or None
        company_description = request.form.get("company_description", "").strip() or None

        # if not company_name:
        #     flash("Tên công ty không được để trống.", "danger")
        #     return render_template(
        #         "pages/employer/company_profile.html",
        #         employer=employer,
        #         editing=True,
        #     )

        # Kiểm tra tên trùng với công ty khác (trừ chính mình)
        # existing = EmployerRepository.find_by_company_name(company_name)
        # if existing and existing.id != employer.id:
        #     flash("Tên công ty này đã được đăng ký bởi công ty khác.", "danger")
        #     return render_template(
        #         "pages/employer/company_profile.html",
        #         employer=employer,
        #         editing=True,
        #     )

        # employer.company_name        = company_name
        # employer.location            = location
        employer.company_website     = company_website
        employer.company_description = company_description

        db.session.commit()
        flash("Cập nhật hồ sơ công ty thành công!", "success")
        return redirect(url_for("company_profile.view"))

    return render_template(
        "pages/employer/company_profile.html",
        employer=employer,
        editing=True,
    )