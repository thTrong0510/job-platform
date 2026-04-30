from datetime import datetime

from app.models.application import (Application)
from app.models.skill import JobSkill
from app.models.job import Job
from app.extensions import db
from sqlalchemy import or_


class JobRepository:

    @staticmethod
    def save(job):
        db.session.add(job)
        db.session.commit()
        return job

    @staticmethod
    def save_job_skills(job_id, skills):
        for skill in skills:
            job_skill = JobSkill(job_id=job_id, skill_id=skill.get('skill_id'))
            db.session.add(job_skill)
        db.session.commit()

    @staticmethod
    def find_job_by_id_and_employer(job_id, employer_id):
        return Job.query.filter_by(id=job_id, employer_id=employer_id).first()

    @staticmethod
    def get_job_skills(job_id):
        return JobSkill.query.filter_by(job_id=job_id).all()

    @staticmethod
    def search(keyword=None, status=None, employer_id=None):
        query = Job.query

        if employer_id:
            query = query.filter_by(employer_id=employer_id)

        if keyword:
            query = query.filter(
                or_(
                    Job.title.ilike(f"%{keyword}%"),
                    Job.location.ilike(f"%{keyword}%")
                )
            )

        if status:
            query = query.filter_by(status=status)

        return query.order_by(Job.created_at.desc()).all()

    @staticmethod
    def count_by_employer(employer_id):
        return Job.query.filter_by(employer_id=employer_id).count()

    @staticmethod
    def count_open_by_employer(employer_id):
        return Job.query.filter_by(employer_id=employer_id, status="OPEN").count()


    @staticmethod
    def count_applicants(job_id):
        return db.session.query(Application).filter_by(job_id=job_id).count()


    @staticmethod
    def update_status(job_id, status):
        job = Job.query.get(job_id)
        if job:
            job.status = status
            db.session.commit()


    @staticmethod
    def delete(job_id):
        job = Job.query.get(job_id)
        if job:
            db.session.delete(job)
            db.session.commit()


    @staticmethod
    def find_by_id_and_employer(job_id, employer_id):
        return Job.query.filter_by(id=job_id, employer_id=employer_id).first()

    @staticmethod
    def update(job_id, employer_id, form_data, skill_list):
        try:
            job = Job.query.filter_by(id=job_id, employer_id=employer_id).first()
            if not job:
                return None, "Không tìm thấy tin tuyển dụng."

            # Cập nhật thông tin cơ bản
            job.title = form_data.get('title')
            job.location = form_data.get('location')
            job.description = form_data.get('description')
            job.salary_min = form_data.get('salary_min') or None
            job.salary_max = form_data.get('salary_max') or None
            job.experience_required = int(form_data.get('experience_required', 0))

            if form_data.get('end_date'):
                job.end_date = datetime.strptime(form_data.get('end_date'), '%Y-%m-%d')

            # Xử lý Skills: Xóa các bản ghi cũ trực tiếp qua Query để đạt hiệu suất tốt nhất
            JobSkill.query.filter_by(job_id=job_id).delete()

            # Thêm các bản ghi mới
            if skill_list:
                for s_id in skill_list:
                    new_js = JobSkill(job_id=job_id, skill_id=int(s_id.get("skill_id")))
                    db.session.add(new_js)

            db.session.commit()
            return job, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)