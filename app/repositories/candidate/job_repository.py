from datetime import datetime

from app.models import Employer, Skill, JobSkill
from app.models.job import Job
from sqlalchemy import or_
from app.extensions import db

class JobRepository:
    @staticmethod
    def search_jobs(keyword=None, location=None, salary_min=None, salary_max=None, experience=None, sort='newest', page=1, per_page=3):
        q = (Job.query.join(Job.employer)
            .outerjoin(JobSkill, JobSkill.job_id == Job.id)
            .outerjoin(Skill, Skill.id == JobSkill.skill_id)
            .filter(Job.status == 'OPEN'))

        # keyword search
        if keyword:
            q = q.filter(
                or_(
                    Job.title.ilike(f"%{keyword}%"),
                    Employer.company_name.ilike(f"%{keyword}%"),
                    Skill.name.ilike(f"%{keyword}%"),
                )
            )

        q = q.distinct()

        # location filter
        if location:
            q = q.filter(Job.location.ilike(f"%{location}%"))

        # salary filter
        if salary_min is not None:
            q = q.filter(
                or_(
                    Job.salary_max >= salary_min,
                    Job.salary_max.is_(None)
                )
            )
        if salary_max is not None:
            q = q.filter(
                or_(
                    Job.salary_min <= salary_max,
                    Job.salary_min.is_(None)
                )
            )
        # experience filter
        if experience is not None:
            q = q.filter(Job.experience_required <= experience)

        # # sort
        # if sort == 'salary_desc':
        #     q = q.order_by(Job.salary_max.desc().nullslast())
        # elif sort == 'salary_asc':
        #     q = q.order_bt(Job.salary_min.asc().nullslast())
        # elif sort == 'deadline':
        #     q = q.order_by(Job.end_date.asc().nullslast())
        # else:
        #     q = q.order_by(Job.created_at.desc())
        #
        # # pagination
        # pagination = q.paginate(page=page, per_page=per_page, error_out=False)
        #
        # return pagination

        q = q.order_by(Job.created_at.desc())
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)

        # print(q.statement.compile(compile_kwargs={"literal_binds": True}))
        print(str(q.statement))

        return pagination

    @staticmethod
    def get_distinct_locations():
        results = db.session.query(Job.location).filter(Job.location.isnot(None), Job.status == 'OPEN').distinct().all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def find_by_id(job_id):
        return Job.query.get_or_404(job_id)