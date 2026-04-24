from app.repositories.user_repository import UserRepository

class UserService:
    def save_user(user):
        return UserRepository.save(user)