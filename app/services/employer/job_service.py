from datetime import datetime, timezone
from app.models.job import Job
from app.repositories.employer.job_repository import JobRepository


class JobService:
    @staticmethod
    def parse_skills(form):
        skill_ids = form.getlist("skills[]")
        result = []
        for skill_id in skill_ids:
            result.append({
                "skill_id": int(skill_id),
                "required_level": form.get(f"levels[{skill_id}]", "INTERMEDIATE")
            })
        return result

    @staticmethod
    def create_job(employer_id, form_data, skill_list):
        error = JobService._validate(form_data)
        if error:
            return None, error
        job = Job(
            employer_id=employer_id,
            title=form_data.get("title"),
            end_date=_parse_date(form_data.get("end_date")),
            location=form_data.get("location"),
            salary_min=form_data.get("salary_min") or None,
            salary_max=form_data.get("salary_max") or None,
            experience_required=_to_int_or_zero(form_data.get("experience_required")),
            description=form_data.get("description"),
            status="OPEN"
        )

        JobRepository.save(job)

        if skill_list:
            JobRepository.save_job_skills(job.id, skill_list)

        return job, None

    @staticmethod
    def _validate(form_data):
        title = (form_data.get("title") or "").strip()
        description = (form_data.get("description") or "").strip()
        end_date_str = (form_data.get("end_date") or "").strip()
        location = (form_data.get("location") or "").strip()
        exp = form_data.get("experience_required")

        if not title:
            return "Title is required."

        if not location:
            return "Location is required."

        if exp:
            try:
                if int(exp) < 0:
                    return "Experience must be >= 0."
            except ValueError:
                return "Experience must be a number."

        if not description:
            return "Job description is required."

        if not end_date_str:
            return "Please select a deadline."

        end_date = _parse_date(end_date_str)
        if not end_date:
            return "Application deadline was invalid."

        if end_date.date() < datetime.now(timezone.utc).date():
            return "Application deadline must be in the future."

        salary_min = form_data.get("salary_min")
        salary_max = form_data.get("salary_max")

        if salary_min and salary_max:
            try:
                if float(salary_min) > float(salary_max):
                    return "Salary min must be less than or equal to salary max."
            except ValueError:
                return "Salary was invalid."
        return None

    @staticmethod
    def get_job_detail(job_id, employer_id=None):
        if employer_id:
            job = JobRepository.find_job_by_id_and_employer(job_id, employer_id)

        if not job:
            return None, "Không tìm thấy tin tuyển dụng"

        skills = JobRepository.get_job_skills(job_id)
        return job, skills

    @staticmethod
    def get_stats(employer_id):
        total = JobRepository.count_by_employer(employer_id)
        open_count = JobRepository.count_open_by_employer(employer_id)
        return {
            "total": total,
            "open": open_count,
            "closed": total - open_count
        }

    @staticmethod
    def search_jobs(keyword=None, status=None, employer_id=None):
        return JobRepository.search(
            keyword=keyword,
            status=status,
            employer_id=employer_id
        )


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

def _to_int_or_zero(val):
    try:
        return int(val) if val else 0
    except ValueError:
        return 0
