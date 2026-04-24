from flask import session
from app.models import Candidate


def get_current_candidate():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return Candidate.query.filter_by(user_id=user_id).first()