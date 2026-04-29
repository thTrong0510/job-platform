from app.models.user import User
from app.extensions import db

class UserRepository:

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def find_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def save(user):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_avatar(user_id, avatar_url):
        user = User.query.get(user_id)

        if not user:
            raise Exception("User not found")

        user.avatar_url = avatar_url
        db.session.commit()
        return user
