from app.models.skill import JobSkill, Skill
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
