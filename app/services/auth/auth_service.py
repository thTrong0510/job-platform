from app.repositories.user_repository import UserRepository

class AuthService:

    @staticmethod
    def login(email):
        user = UserRepository.find_by_email(email)

        if not user:
            return None

        if not user.is_active:
            return None

        return user