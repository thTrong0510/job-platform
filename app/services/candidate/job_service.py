from app.models import CandidateSkill, CandidateExperience, Job
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

    @staticmethod
    def get_recommended_jobs(candidate_id, limit=10):
        # 1. Lấy danh sách ID kỹ năng của ứng viên
        candidate_skill_ids = [s.skill_id for s in CandidateSkill.query.filter_by(candidate_id=candidate_id).all()]

        # 2. Lấy danh sách các vị trí công việc ứng viên từng làm
        experiences = CandidateExperience.query.filter_by(candidate_id=candidate_id).all()
        positions = [exp.position.lower() for exp in experiences if exp.position]

        if not candidate_skill_ids and not positions:
            return []

        all_jobs = Job.query.filter_by(status='OPEN').all()
        recommended_list = []

        for job in all_jobs:
            score = 0

            # --- Tính điểm theo Kỹ năng (Skill Match) ---
            job_skill_ids = [js.skill_id for js in job.skills]
            if job_skill_ids:
                matches = set(candidate_skill_ids) & set(job_skill_ids)
                skill_score = (len(matches) / len(job_skill_ids)) * 70
                score += skill_score

            if positions:
                job_title = job.title.lower()
                # Kiểm tra xem có từ khóa nào trong position cũ xuất hiện trong job title không
                position_match = any(pos in job_title or job_title in pos for pos in positions)
                if position_match:
                    score += 30

            if score > 20:
                recommended_list.append({
                    'job': job,
                    'score': round(score, 2)
                })

        recommended_list.sort(key=lambda x: x['score'], reverse=True)

        return [item['job'] for item in recommended_list[:limit]]