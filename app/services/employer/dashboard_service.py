from app.repositories.employer.dashboard_repository import DashboardRepository


class DashboardService:

    @staticmethod
    def get_stats(employer_id: int) -> dict:
        return DashboardRepository.get_stats(employer_id)