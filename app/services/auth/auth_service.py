from app.models import User, Candidate
from app.repositories.user_repository import UserRepository
from app.services.candidate.candidate_service import CandidateService
from app.services.candidate.user_service import UserService


class AuthService:

    @staticmethod
    def login(email):
        user = UserRepository.find_by_email(email)

        if not user:
            return None

        if not user.is_active:
            return None

        return user

    @staticmethod
    def login_or_register_google(google_info: dict):
        email = google_info.get('email')
        user = UserRepository.find_by_email(email)
        if user:
            return user

        user = User(
            email=email,
            role="CANDIDATE",
            status="ACTIVE"
        )
        user.set_password(email + "_google_oauth")
        UserService.save_user(user)

        candidate = Candidate(
            full_name=google_info.get("name", ""),
            user=user
        )
        CandidateService.save_candidate(candidate)

        return user
