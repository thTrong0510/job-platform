from app.extensions import db
from app.models.user import User


class UserRepository:

    @staticmethod
    def get_all_users(role=None, status=None, keyword=None, page=1, per_page=10):
        query = User.query

        if role:
            query = query.filter(User.role == role.upper())
        if status:
            query = query.filter(User.status == status.upper())
        if keyword:
            query = query.filter(User.email.ilike(f"%{keyword}%"))

        query = query.order_by(
            db.case(
                (User.status == 'PENDING', 0),
                else_=1
            ),
            User.created_at.desc()
        )

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def find_by_id(user_id: int):
        return User.query.get(user_id)

    @staticmethod
    def count_by_status(status: str) -> int:
        return User.query.filter_by(status=status.upper()).count()

    @staticmethod
    def count_by_role(role: str) -> int:
        return User.query.filter_by(role=role.upper()).count()

    @staticmethod
    def save(user: User):
        db.session.add(user)
        db.session.commit()