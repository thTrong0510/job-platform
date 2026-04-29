from app.repositories.candidate.job_repository import JobRepository


class JobService:
    @staticmethod
    def search_job(filters: dict, page: int = 1):
        keyword = filters.get('keyword', '').strip() or None
        location = filters.get('location', '').strip() or None

        try:
            salary_min = int(filters['salary_min']) if filters.get('salary_min') else None
            salary_max = int(filters['salary_max']) if filters.get('salary_max') else None
            experience = int(filters['experience']) if filters.get('experience') else None
        except (ValueError, TypeError):
            salary_min = salary_max = experience = None

        pagination = JobRepository.search_jobs(keyword=keyword, location=location, salary_min=salary_min, salary_max=salary_max, experience=experience, page=page)
        print(keyword, salary_min)
        return pagination

    @staticmethod
    def get_filter_options():
        return {
            'locations': JobRepository.get_distinct_locations()
        }

    @staticmethod
    def get_job_detail(job_id):
        return JobRepository.find_by_id(job_id)
