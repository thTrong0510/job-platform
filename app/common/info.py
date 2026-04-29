from flask import session
from app.models.candidate import Candidate
from app.models.employer import Employer
from app.models.user import User


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.filter_by(id=user_id).first()

def get_current_employer():
    employer_id = session.get("employer_id")
    if not employer_id:
        return None

    return Employer.query.filter_by(id=employer_id).first()

def get_current_candidate():
    candidate_id = session.get("candidate_id")
    if not candidate_id:
        return None
    return Candidate.query.filter_by(id=candidate_id).first()